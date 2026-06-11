# pyrefly: ignore [missing-import]
from django.contrib.auth.models import AbstractUser
# pyrefly: ignore [missing-import]
from django.db import models
from datetime import date, timedelta
import uuid


class User(AbstractUser):
    """
    Modelo de usuario personalizado para FLOZ.
    Extiende AbstractUser (hereda username, password, email, is_active, etc.)
    y agrega los campos de perfil específicos de la app.
    """
    # Campo heredado de Supabase por compatibilidad
    uuid_user = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    # AbstractUser ya provee: id (PK), username, password, email,
    # first_name, last_name, is_active
    streak_current = models.IntegerField(default=0)
    streak_last_day = models.DateField(null=True, blank=True)
    streak_best = models.IntegerField(default=0)

    class Meta:
        db_table = 'user'

    def __str__(self):
        return f"{self.username} ({self.first_name} {self.last_name})"

    def update_streak(self):
        """
        Actualiza la racha del usuario basado en su última actividad.
        - Si completó algo HOY: no cambia nada
        - Si completó algo AYER: incrementa racha
        - Si streak_last_day es null o pasó más de 1 día: inicia/resetea a 1
        """
        today = date.today()

        if self.streak_last_day == today:
            # Ya completó algo hoy, no cambiar
            return

        if self.streak_last_day is None:
            # Primera vez que hace algo
            self.streak_current = 1
        elif self.streak_last_day == today - timedelta(days=1):
            # Completó algo ayer, incrementar racha
            self.streak_current += 1
        else:
            # Pasó más de 1 día sin hacer nada, resetear a 1
            self.streak_current = 1

        if self.streak_current > self.streak_best:
            self.streak_best = self.streak_current

        self.streak_last_day = today
        self.save()


class DailyCapacity(models.Model):
    """
    Mapea la tabla public.daily_capacity para el control de horas de estudio.
    """
    daily_capacity_id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, db_column='user_id')
    daily_limit_hours = models.DecimalField(max_digits=4, decimal_places=2, default=6)

    class Meta:
        db_table = 'daily_capacity'

    def __str__(self):
        return f"{self.user.username} - Limite: {self.daily_limit_hours}h"