# pyrefly: ignore [missing-import]
from django.db import models

class Activity(models.Model):
    """Modelo de actividad evaluativa según el diagrama ER."""

    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('done', 'Completada'),
        ('postponed', 'Postergada'),
        ('overdue', 'Vencida'),
    ]

    TYPE_CHOICES = [
        ('exam', 'Examen'),
        ('quiz', 'Quiz'),
        ('project', 'Proyecto'),
        ('homework', 'Tarea'),
        ('presentation', 'Presentación'),
    ]

    id = models.BigAutoField(primary_key=True, db_column='activity_id')
    title = models.CharField(max_length=255)
    type = models.CharField(max_length=100, choices=TYPE_CHOICES)
    course = models.CharField(max_length=255, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    due_date = models.DateField()
    weight = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='activities', db_column='user_id')

    class Meta:
        db_table = 'activity'
        ordering = ['-due_date']

    def __str__(self):
        return f"{self.title} ({self.course})"

class Subtask(models.Model):
    """Modelo de subtarea asociada a una actividad evaluativa."""

    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('done', 'Completada'),
        ('postponed', 'Postergada'),
        ('overdue', 'Vencida'),
    ]

    id = models.BigAutoField(primary_key=True, db_column='subtask_id')
    activity = models.ForeignKey(
        Activity,
        on_delete=models.CASCADE,
        related_name='subtasks',
        db_column='activity_id'
    )
    title = models.CharField(max_length=255)
    target_date = models.DateField(null=True, blank=True)
    estimated_hours = models.FloatField(null=True, blank=True)
    description = models.TextField(blank=True, default='')
    note = models.TextField(blank=True, null=True, default='', help_text="Nota opcional al posponer o cambiar estado")
    done_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    class Meta:
        db_table = 'subtask'

    def __str__(self):
        return self.title