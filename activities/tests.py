from django.test import TestCase
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import Client
from datetime import date, timedelta
from activities.models import Activity, Subtask
from activities.serializers import (
    ActivitySerializer,
    SubtaskSerializer,
    TodaySubtaskSerializer,
)
from unittest.mock import MagicMock
import pytest

# =============================================
# Tests US-01 - Crear actividad evaluativa
# Tests US-02 - Crear plan inicial (subtareas)
# Autor: Luis Yair Valencia Garcia
# Descripcion: Pruebas unitarias para crear
# actividades y subtareas
# =============================================

User = get_user_model()
client = Client()

def test_activity_list_view():
    url = reverse("activities:list")
    response = client.get(url)
    assert response.status_code == 200
    assert "activities" in response.context

def test_activity_detail_404():
    url = reverse("activities:detail", args=[9999])
    response = client.get(url)
    assert response.status_code == 404

@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user():
    return User.objects.create_user(
        username="tester",
        password="Pass1234!",
        email="tester@example.com",
    )


@pytest.fixture
def auth_client(api_client, user):
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def activity(auth_client):
    """Crea una actividad básica para usar en los tests."""
    resp = auth_client.post(
        "/api/activities/",
        {
            "title": "Parcial de Cálculo",
            "course": "Cálculo",
            "type": "exam",
            "due_date": (date.today() + timedelta(days=30)).isoformat(),
        },
        format="json",
    )
    return resp.data["data"]


class CrearActividadTest(TestCase):

    def setUp(self):
        # Crea usuario y lo autentica antes de cada test
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='Test1234Ab', #NOSONAR
            email='test@test.com'
        )
        self.client.force_authenticate(user=self.user)

    def test_crear_actividad_exitosa(self):
        # Verifica que se puede crear una actividad con campos validos (US-01 Escenario 1)
        response = self.client.post('/api/activities/', {
            'title': 'Parcial de Calculo',
            'course': 'Calculo',
            'type': 'exam',
            'due_date': '2026-12-01'
        }, format='json')
        self.assertIn(response.status_code, [200, 201])

    def test_crear_actividad_sin_titulo_falla(self):
        # Verifica que sin titulo el sistema retorna error (US-01 Escenario 2)
        response = self.client.post('/api/activities/', {
            'course': 'Calculo',
            'type': 'exam',
            'due_date': '2026-12-01'
        }, format='json')
        self.assertEqual(response.status_code, 400)

    def test_crear_actividad_sin_autenticar_falla(self):
        # Verifica que sin autenticacion no se puede crear actividad (US-11 Escenario 3)
        self.client.force_authenticate(user=None)
        response = self.client.post('/api/activities/', {
            'title': 'Parcial de Calculo',
            'type': 'exam',
            'due_date': '2026-12-01'
        }, format='json')
        self.assertEqual(response.status_code, 401)

    def test_listar_actividades_exitoso(self):
        # Verifica que se pueden listar las actividades del usuario (US-01 Escenario 1)
        response = self.client.get('/api/activities/')
        self.assertEqual(response.status_code, 200)


class CrearSubtareaTest(TestCase):

    def setUp(self):
        # Crea usuario, lo autentica y crea una actividad base para las subtareas
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='Test1234Ab', #NOSONAR
            email='test@test.com'
        )
        self.client.force_authenticate(user=self.user)
        response = self.client.post('/api/activities/', {
            'title': 'Parcial de Calculo',
            'course': 'Calculo',
            'type': 'exam',
            'due_date': '2026-12-01'
        }, format='json')
        self.activity_id = response.data['data']['id']

    def test_crear_subtarea_exitosa(self):
        # Verifica que se puede crear una subtarea valida (US-02 Escenario 1)
        response = self.client.post(f'/api/activities/{self.activity_id}/subtasks/', {
            'title': 'Estudiar derivadas',
            'target_date': '2026-11-25',
            'estimated_hours': 2
        }, format='json')
        self.assertIn(response.status_code, [200, 201])

    def test_crear_subtarea_sin_titulo_falla(self):
        # Verifica que sin titulo la subtarea no se crea (US-02 Escenario 2)
        response = self.client.post(f'/api/activities/{self.activity_id}/subtasks/', {
            'target_date': '2026-11-25',
            'estimated_hours': 2
        }, format='json')
        self.assertEqual(response.status_code, 400)

    def test_crear_subtarea_horas_cero_falla(self):
        # Verifica que horas estimadas en 0 retorna error (US-02 Escenario 2)
        response = self.client.post(f'/api/activities/{self.activity_id}/subtasks/', {
            'title': 'Estudiar derivadas',
            'target_date': '2026-11-25',
            'estimated_hours': 0
        }, format='json')
        self.assertEqual(response.status_code, 400)


# =============================================
# Tests de serializers
# =============================================

class ActivitySerializerTests(TestCase):
    def test_activity_serializer_fields(self):
        user = User.objects.create_user(username='actuser', password='pass')
        activity = Activity.objects.create(
            user=user,
            title='Test Activity',
            type='exam',
            due_date=date.today() + timedelta(days=10),
        )
        serializer = ActivitySerializer(activity)
        self.assertIn('id', serializer.data)
        self.assertIn('title', serializer.data)
        self.assertIn('type', serializer.data)
        self.assertIn('due_date', serializer.data)
        self.assertIn('status', serializer.data)
        self.assertIn('subtasks', serializer.data)

    def test_activity_serializer_create(self):
        user = User.objects.create_user(username='actuser', password='pass')
        data = {
            'title': 'New Activity',
            'type': 'exam',
            'due_date': (date.today() + timedelta(days=10)).isoformat(),
            'course': 'Math',
            'weight': 20,
        }
        request = MagicMock()
        request.user = user
        serializer = ActivitySerializer(data=data, context={'request': request})
        self.assertTrue(serializer.is_valid(), serializer.errors)
        activity = serializer.save(user_id=user.id)
        self.assertEqual(activity.user_id, user.id)
        self.assertEqual(activity.title, 'New Activity')


class SubtaskSerializerTests(TestCase):
    def test_subtask_serializer_fields(self):
        user = User.objects.create_user(username='subuser', password='pass')
        activity = Activity.objects.create(
            user=user,
            title='Act',
            type='exam',
            due_date=date.today() + timedelta(days=10),
        )
        subtask = Subtask.objects.create(
            activity=activity,
            title='Sub',
            estimated_hours=2.0,
            status='pending',
        )
        serializer = SubtaskSerializer(subtask)
        self.assertIn('id', serializer.data)
        self.assertIn('title', serializer.data)
        self.assertIn('status', serializer.data)
        self.assertIn('estimated_hours', serializer.data)

    def test_subtask_serializer_update(self):
        user = User.objects.create_user(username='subuser', password='pass')
        activity = Activity.objects.create(
            user=user,
            title='Act',
            type='exam',
            due_date=date.today() + timedelta(days=10),
        )
        subtask = Subtask.objects.create(
            activity=activity,
            title='Sub',
            estimated_hours=2.0,
            status='pending',
        )
        serializer = SubtaskSerializer(
            subtask,
            data={'status': 'done'},
            partial=True,
            context={'activity': activity},
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        serializer.save()
        subtask.refresh_from_db()
        self.assertEqual(subtask.status, 'done')


class TodaySubtaskSerializerTests(TestCase):
    def test_today_subtask_serializer_output(self):
        user = User.objects.create_user(username='todayuser', password='pass')
        activity = Activity.objects.create(
            user=user,
            title='Act',
            type='exam',
            due_date=date.today() + timedelta(days=10),
        )
        subtask = Subtask.objects.create(
            activity=activity,
            title='Sub',
            estimated_hours=1.5,
            target_date=date.today(),
            status='pending',
        )
        serializer = TodaySubtaskSerializer(subtask)
        self.assertIn('id', serializer.data)
        self.assertIn('title', serializer.data)
        self.assertIn('estimated_hours', serializer.data)
        self.assertIn('parent_activity', serializer.data)