from datetime import date
from django.db.models import Sum
from rest_framework import serializers
from users.models import DailyCapacity

from .models import Activity, Subtask

class SubtaskSerializer(serializers.ModelSerializer):
    """
    Serializer para la US-02 (Crear plan inicial / subtareas).
    Maneja las validaciones del Escenario 2.
    """
    title = serializers.CharField(
        required=True,
        allow_blank=False,
        error_messages={
            'required': 'El título de la subtarea es obligatorio.',
            'blank': 'El título de la subtarea no puede estar vacío.',
        },
    )
    estimated_hours = serializers.FloatField(
        required=True,
        error_messages={
            'required': 'Las horas estimadas son obligatorias.',
        },
    )
    target_date = serializers.DateField(
        required=False,
        allow_null=True,
    )
    
    class Meta:
        model = Subtask
        fields = [
            'id', 'activity', 'title', 'description', 'status',
            'target_date', 'estimated_hours', 'note', 'done_at',
        ]
        read_only_fields = ['id', 'activity']
    
    def validate_estimated_hours(self, value):
        """Las horas estimadas deben ser > 0 y <= 16."""
        if value <= 0:
            raise serializers.ValidationError(
                'Las horas estimadas deben ser mayores a 0.'
            )
        if value > 16:
            raise serializers.ValidationError(
                'Las horas estimadas no pueden superar 16 horas.'
            )
        return value

    def validate_target_date(self, value):
        """La fecha de la subtarea debe ser >= hoy."""
        if value and value < date.today():
            raise serializers.ValidationError(
                'La fecha de la subtarea no puede ser anterior a hoy.'
            )
        return value
    
    def _protect_status(self, data, target_date, status_val):
        if self.instance:
            old_status = self.instance.status
            old_target_date = self.instance.target_date
            if old_status in ['postponed', 'overdue'] and target_date and target_date != old_target_date:
                data['status'] = 'pending'
                status_val = 'pending'
            elif status_val != old_status and status_val not in ['done', 'pending', 'postponed']:
                raise serializers.ValidationError({
                    'status': f'Estado inválido: "{status_val}". Los valores permitidos son: done, pending o postponed.'
                })
        else:
            if status_val not in ['pending', 'done']:
                data['status'] = 'pending'
                status_val = 'pending'
        return status_val

    def _handle_done_at_and_note(self, data, status_val):
        from django.utils import timezone
        if self.instance and self.instance.note:
            new_note = data.get('note', None)
            if new_note == '' or new_note is None:
                data['note'] = self.instance.note

        if status_val == 'done':
            if not data.get('done_at') and not getattr(self.instance, 'done_at', None):
                data['done_at'] = timezone.now()
        else:
            data['done_at'] = None

    def _get_capacity_limit(self, user_id):
        try:
            return float(DailyCapacity.objects.get(user_id=user_id).daily_limit_hours)
        except DailyCapacity.DoesNotExist:
            return 6.0

    def _get_alternative_dates(self, target_date, activity, user_id, exceeds_by, limit_hours):
        from datetime import timedelta
        alternative_dates = []
        check_date = target_date + timedelta(days=1)
        for _ in range(30):
            if len(alternative_dates) >= 1:
                break
            if activity and activity.due_date and check_date > activity.due_date:
                break
            day_planned = Subtask.objects.filter(
                activity__user_id=user_id,
                target_date=check_date
            ).exclude(status='done').aggregate(total=Sum('estimated_hours'))['total'] or 0.0
            if (day_planned + exceeds_by) <= limit_hours:
                alternative_dates.append(str(check_date))
            check_date += timedelta(days=1)
        return alternative_dates

    def _check_daily_overload(self, data, target_date, activity, status_val):
        if not target_date or not activity:
            return
        
        user_id = activity.user_id
        limit_hours = self._get_capacity_limit(user_id)
            
        qs = Subtask.objects.filter(
            activity__user_id=user_id,
            target_date=target_date
        ).exclude(status='done')
        
        if self.instance:
            qs = qs.exclude(id=self.instance.id)
            
        planned_hours = qs.aggregate(total=Sum('estimated_hours'))['total'] or 0.0
        
        new_estimated = data.get('estimated_hours', getattr(self.instance, 'estimated_hours', 0.0))
        if status_val == 'done':
            new_estimated = 0.0
            
        total_after_save = planned_hours + new_estimated
        
        if total_after_save > limit_hours:
            exceeds_by = total_after_save - limit_hours
            alternative_dates = self._get_alternative_dates(target_date, activity, user_id, exceeds_by, limit_hours)
            
            raise serializers.ValidationError({
                'overload_conflict': [{
                    'status': 'error',
                    'resolved': False,
                    'message': f'Quedarías con {total_after_save:g}h planificadas (límite {limit_hours:g}h)',
                    'planned_hours': planned_hours,
                    'limit_hours': limit_hours,
                    'exceeds_by': exceeds_by,
                    'hours_to_reduce': exceeds_by,
                    'alternative_dates': alternative_dates
                }]
            })

    def validate(self, data):
        """
        Validación general de la subtarea, maneja estados, fechas 
        y evita la sobrecarga diaria.
        """
        target_date = data.get('target_date', getattr(self.instance, 'target_date', None))
        status_val = data.get('status', getattr(self.instance, 'status', 'pending'))
        
        status_val = self._protect_status(data, target_date, status_val)
        self._handle_done_at_and_note(data, status_val)
            
        activity = self.context.get('activity') or (self.instance.activity if self.instance else None)
        
        if target_date and activity and target_date > activity.due_date:
            raise serializers.ValidationError({
                'target_date': (
                    f'La fecha de la subtarea ({target_date}) no puede ser '
                    f'posterior a la fecha límite de la actividad ({activity.due_date}).'
                )
            })
        
        self._check_daily_overload(data, target_date, activity, status_val)
        return data
    


class ActivitySerializer(serializers.ModelSerializer):
    """
    Serializer para actividades evaluativas.
    Campos obligatorios: title, type, due_date.
    Campos opcionales: course, weight, user_id, subtasks.
    Status por defecto: pending.
    """
    subtasks = SubtaskSerializer(many=True, required=False)

    TYPE_LABELS = {
        'exam': 'Examen',
        'quiz': 'Quiz',
        'project': 'Proyecto',
        'homework': 'Tarea',
        'presentation': 'Presentación',
    }

    STATUS_LABELS = {
        'pending': 'Pendiente',
        'done': 'Completada',
        'postponed': 'Postergada',
        'overdue': 'Vencida',
    }

    title = serializers.CharField(
        required=True,
        allow_blank=False,
        error_messages={
            'required': 'El título de la actividad es obligatorio.',
            'blank': 'El título de la actividad no puede estar vacío.',
        },
    )

    type = serializers.ChoiceField(
        choices=['exam', 'quiz', 'project', 'homework', 'presentation'],
        error_messages={
            'required': 'El tipo de actividad es obligatorio.',
            'invalid_choice': 'Tipo inválido. Opciones: exam, quiz, project, homework, presentation.',
        }
    )

    due_date = serializers.DateField(
        required=True,
        error_messages={
            'required': 'La fecha límite es obligatoria.',
        }
    )

    class Meta:
        model = Activity
        fields = [
            'id', 'title', 'type', 'course', 'status', 
            'due_date', 'weight', 'user_id', 'subtasks'
        ]
        read_only_fields = ['id', 'user_id', 'status']

    def validate_due_date(self, value):
        """La fecha límite de la actividad debe ser >= hoy."""
        if value < date.today():
            raise serializers.ValidationError(
                'La fecha límite no puede ser anterior a hoy.'
            )
        return value
    
    def validate_weight(self, value):
        """El peso debe estar entre 0 y 100."""
        if value is not None:
            if value < 0:
                raise serializers.ValidationError('El peso no puede ser negativo.')
            if value > 100:
                raise serializers.ValidationError('El peso no puede ser mayor a 100.')
        return value

    def _validate_due_date_against_subtasks(self, due_date):
        if not self.instance or not due_date:
            return
        
        conflicting_subtasks = self.instance.subtasks.filter(
            target_date__gt=due_date
        ).exclude(status='done')

        if conflicting_subtasks.exists():
            subtask_names = list(conflicting_subtasks.values_list('title', flat=True)[:5])
            names_str = ', '.join(f'"{name}"' for name in subtask_names)
            count = conflicting_subtasks.count()
            raise serializers.ValidationError({
                'due_date': [
                    f'No puedes mover la fecha límite al {due_date} porque '
                    f'{count} subtarea(s) tienen fecha objetivo posterior: {names_str}. '
                    f'Reprograma esas subtareas primero.'
                ]
            })

    def _get_capacity_limit(self, user_id):
        try:
            return float(DailyCapacity.objects.get(user_id=user_id).daily_limit_hours)
        except DailyCapacity.DoesNotExist:
            return 6.0

    def _get_alternative_dates_activity(self, target_date, due_date, user_id, exceeds_by, limit_hours):
        from datetime import timedelta
        alternative_dates = []
        check_date = target_date + timedelta(days=1)
        for _ in range(30):
            if len(alternative_dates) >= 1:
                break
            if due_date and check_date > due_date:
                break
            day_planned = Subtask.objects.filter(
                activity__user_id=user_id,
                target_date=check_date
            ).exclude(status='done').aggregate(total=Sum('estimated_hours'))['total'] or 0.0
            if (day_planned + exceeds_by) <= limit_hours:
                alternative_dates.append(str(check_date))
            check_date += timedelta(days=1)
        return alternative_dates

    def _check_subtasks_overload(self, subtasks_data, due_date):
        request = self.context.get('request')
        if not request or not hasattr(request, 'user'):
            return
            
        user_id = request.user.id
        limit_hours = self._get_capacity_limit(user_id)

        dates_hours = {}
        for st in subtasks_data:
            td = st.get('target_date')
            est = st.get('estimated_hours', 0.0)
            if td:
                dates_hours[td] = dates_hours.get(td, 0.0) + est
                
        for target_date, added_hours in dates_hours.items():
            planned_hours = Subtask.objects.filter(
                activity__user_id=user_id,
                target_date=target_date
            ).exclude(status='done').aggregate(total=Sum('estimated_hours'))['total'] or 0.0
            
            total_after_save = planned_hours + added_hours
            if total_after_save > limit_hours:
                exceeds_by = total_after_save - limit_hours
                alternative_dates = self._get_alternative_dates_activity(
                    target_date, due_date, user_id, exceeds_by, limit_hours
                )
                raise serializers.ValidationError({
                    'overload_conflict': [{
                        'status': 'error',
                        'resolved': False,
                        'message': f'La fecha {target_date} quedaría con {total_after_save:g}h (límite {limit_hours:g}h)',
                        'planned_hours': planned_hours,
                        'limit_hours': limit_hours,
                        'exceeds_by': exceeds_by,
                        'hours_to_reduce': exceeds_by,
                        'alternative_dates': alternative_dates
                    }]
                })

    def validate(self, data):
        """
        Validación cruzada para la creación anidada.
        Asegura que ninguna subtarea del payload supere la due_date de la actividad.
        """
        due_date = data.get('due_date', getattr(self.instance, 'due_date', None))
        self._validate_due_date_against_subtasks(due_date)

        if self.instance:
            return data

        subtasks_data = data.get('subtasks', [])
        if subtasks_data:
            self._check_subtasks_overload(subtasks_data, due_date)
            
        return data


    def create(self, validated_data):
        """Crea la actividad junto con sus subtareas si se incluyen."""
        subtasks_data = validated_data.pop('subtasks', [])
        activity = Activity.objects.create(**validated_data)
        for subtask_data in subtasks_data:
            Subtask.objects.create(activity=activity, **subtask_data)
        return activity
    
class ActivityBriefSerializer(serializers.ModelSerializer):
    """ Info minima de la actividad padre"""
    class Meta:
        model = Activity
        fields = ['id', 'title', 'type', 'course', 'weight', 'due_date']
        
class TodaySubtaskSerializer(serializers.ModelSerializer):
    """Subtarea enriqueceda con su actividad padre + fecha efectiva """
    parent_activity = ActivityBriefSerializer(source='activity', read_only=True)

    class Meta:
        model = Subtask
        fields = ['id', 'title', 'description', 'status',
                  'target_date', 'estimated_hours', 'note', 'done_at',
                  'parent_activity']