# pyrefly: ignore [missing-import]
from django.urls import path
from . import views

urlpatterns = [
    # Ruta para enlistar y crear actividades (US-01)
    path('activities/', views.activity_list_create, name='activity-list-create'),
    # Ruta para crear subtareas (US-02)
    path('activities/<uuid:activity_id>/subtasks/', views.subtask_create, name='subtask-create'),
]