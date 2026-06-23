import re
# pyrefly: ignore [missing-import]
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth.password_validation import validate_password

from .models import DailyCapacity, User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'uuid_user', 'first_name', 'last_name', 'streak_current', 'streak_last_day', 'streak_best']
        read_only_fields = ['id', 'uuid_user', 'streak_current', 'streak_last_day', 'streak_best']

    def validate_first_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("El nombre no puede estar vacío.")
        if len(value) < 2:
            raise serializers.ValidationError("El nombre debe tener al menos 2 caracteres.")
        if len(value) > 50:
            raise serializers.ValidationError("El nombre no puede tener más de 50 caracteres.")
        if not re.match(r"^[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ\s\-']+$", value):
            raise serializers.ValidationError("El nombre solo puede contener letras, espacios, guiones y apóstrofes.")
        return value

    def validate_last_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("El apellido no puede estar vacío.")
        if len(value) < 2:
            raise serializers.ValidationError("El apellido debe tener al menos 2 caracteres.")
        if len(value) > 50:
            raise serializers.ValidationError("El apellido no puede tener más de 50 caracteres.")
        if not re.match(r"^[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ\s\-']+$", value):
            raise serializers.ValidationError("El apellido solo puede contener letras, espacios, guiones y apóstrofes.")
        return value


class RegisterSerializer(UserSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'password',
            'streak_current',
            'streak_last_day',
            'streak_best',
        ]
        read_only_fields = ['id', 'streak_current', 'streak_last_day', 'streak_best']

    def validate_username(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError('El nombre de usuario no puede estar vacío.')
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError('El nombre de usuario ya está en uso.')
        return value

    def validate_email(self, value):
        value = value.strip().lower() if value else ''
        if value and User.objects.filter(email=value).exists():
            raise serializers.ValidationError('El correo electrónico ya está en uso.')
        return value

    def validate_password(self, value):
        validate_password(value)
        return value

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        return user


class LoginSerializer(TokenObtainPairSerializer):
    default_error_messages = {
        'no_active_account': 'Credenciales inválidas.',
    }

    def validate(self, attrs):
        data = super().validate(attrs)
        data['user'] = UserSerializer(self.user).data
        return data
    
class DailyCapacitySerializer(serializers.ModelSerializer):
    class Meta:
        model = DailyCapacity
        fields = ['daily_limit_hours']

    def validate_daily_limit_hours(self, value):
        if value < 1 or value > 16:
            raise serializers.ValidationError("El límite diario debe estar entre 1 y 16 horas.")
        return value

    def validate(self, data):
        request = self.context.get('request')
        if not request or not hasattr(request, 'user'):
            return data

        new_limit = data.get('daily_limit_hours')
        if new_limit is None:
            if self.instance:
                new_limit = self.instance.daily_limit_hours
            else:
                return data

        user_id = request.user.id

        from activities.models import Subtask
        from django.db.models import Sum
        from datetime import date

        today = date.today()

        # Single fast aggregate query: find dates with planned hours > new limit
        overloaded_dates = list(
            Subtask.objects.filter(
                activity__user_id=user_id,
                target_date__gte=today
            ).exclude(status='done').values('target_date').annotate(
                total_hours=Sum('estimated_hours')
            ).filter(total_hours__gt=new_limit)
        )

        if overloaded_dates:
            conflicts = []
            for item in overloaded_dates:
                exceeds_by = float(item['total_hours']) - float(new_limit)
                conflicts.append({
                    'date': str(item['target_date']),
                    'planned_hours': float(item['total_hours']),
                    'limit_hours': float(new_limit),
                    'exceeds_by': exceeds_by,
                })

            raise serializers.ValidationError({
                'overload_conflict': [{
                    'status': 'error',
                    'resolved': False,
                    'message': 'No puedes reducir tu capacidad porque tienes días planificados que superan este nuevo límite.',
                    'conflicts': conflicts
                }]
            })

        return data