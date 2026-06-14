# pyrefly: ignore [missing-import]
from django.contrib import admin
from .models import Activity, Subtask

@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    # Esto hace que en el panel se vean columnas ordenadas con datos clave
    list_display = ('id', 'title', 'type', 'status', 'due_date', 'user_id')
    list_filter = ('type', 'status')
    search_fields = ('title', 'course')

@admin.register(Subtask)
class SubtaskAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'activity', 'status', 'target_date', 'estimated_hours')
    list_filter = ('status', 'target_date')
    search_fields = ('title',)