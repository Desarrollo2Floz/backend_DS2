from datetime import date
# pyrefly: ignore [missing-import]
from rest_framework import serializers

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
    
    def validate(self, data):
        """
        La target_date de la subtarea no puede ser mayor
        que la due_date de la actividad asociada.
        """
        target_date = data.get('target_date', getattr(self.instance, 'target_date', None))
        
        # La actividad se inyecta en el contexto desde la vista
        activity = self.context.get('activity')
        if not activity and self.instance:
            activity = self.instance.activity

        if target_date and activity and target_date > activity.due_date:
            raise serializers.ValidationError({
                'target_date': (
                    f'La fecha de la subtarea ({target_date}) no puede ser '
                    f'posterior a la fecha límite de la actividad ({activity.due_date}).'
                )
            })
        
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

    def validate(self, data):
        """
        Validación cruzada para la creación anidada.
        Asegura que ninguna subtarea del payload supere la due_date de la actividad.
        """
        due_date = data.get('due_date', getattr(self.instance, 'due_date', None))

        # --- Validación: due_date no puede ser anterior al target_date de subtareas ---
        if self.instance and due_date:
            # Buscar subtareas cuyo target_date sea posterior al nuevo due_date
            conflicting_subtasks = self.instance.subtasks.filter(
                target_date__gt=due_date
            ).exclude(status='done')

            if conflicting_subtasks.exists():
                subtask_names = list(
                    conflicting_subtasks.values_list('title', flat=True)[:5]
                )
                names_str = ', '.join(f'"{name}"' for name in subtask_names)
                count = conflicting_subtasks.count()
                raise serializers.ValidationError({
                    'due_date': [
                        f'No puedes mover la fecha límite al {due_date} porque '
                        f'{count} subtarea(s) tienen fecha objetivo posterior: {names_str}. '
                        f'Reprograma esas subtareas primero.'
                    ]
                })
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