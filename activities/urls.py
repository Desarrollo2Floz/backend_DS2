# pyrefly: ignore [missing-import]
from django.urls import path
from . import views

urlpatterns = [
    # Ruta para enlistar y crear actividades (US-01)
    path('activities/', views.activity_list_create, name='activity-list-create'),
    # Ruta para crear subtareas (US-02)
    path('activities/<int:activity_id>/subtasks/', views.subtask_create, name='subtask-create'),
    path('activities/<int:pk>/', views.activity_detail, name='activity-detail'),
    path('subtasks/today/', views.today_subtasks, name='today-subtasks'),
    path('subtasks/<int:pk>/', views.subtask_detail, name='subtask-detail'),
]