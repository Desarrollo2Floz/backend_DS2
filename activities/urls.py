# pyrefly: ignore [missing-import]
from django.urls import path
from . import views

urlpatterns = [
    # Ruta para enlistar y crear actividades (US-01)
    path('activities/', views.activity_list_create, name='activity-list-create'),
    # Rutas para editar y eliminar actividades (US-03)
    path('activities/<int:pk>/', views.activity_detail, name='activity-detail'),
    # Ruta para crear subtareas (US-02)
    path('activities/<uuid:activity_id>/subtasks/', views.subtask_create, name='subtask-create'),
    # Rutas para editar y eliminar subtareas (US-03)
    path('subtasks/<int:pk>/', views.subtask_detail, name='subtask-detail'),
    # Ruta para la vista "Hoy" (US-04)
    path('today/', views.today_subtasks, name='today-subtasks'),
]