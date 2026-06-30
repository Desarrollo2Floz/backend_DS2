from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from . import views

urlpatterns = [
    path('login/', views.LoginView.as_view(), name='user-login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('me/', views.me, name='me'),
    path('register/', views.register, name='user-register'),
    path('capacity/', views.daily_capacity_view, name='user-capacity'),
    path('user/streak/', views.get_user_streak, name='user-streak'),
]