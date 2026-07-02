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
import os

TEST_PASS = os.environ.get('TEST_PASS', 'Test1234Ab!')

# =============================================
# Tests US-01 - Crear actividad evaluativa
# Tests US-02 - Crear plan inicial (subtareas)
# Autor: Luis Yair Valencia Garcia
# Descripcion: Pruebas unitarias para crear
# actividades y subtareas
# =============================================

User = get_user_model()
client = Client()

@pytest.mark.django_db
def test_activity_list_view(auth_client):
    url = reverse("activity-list-create")
    response = auth_client.get(url)
    assert response.status_code == 200
    assert response.data is not None

@pytest.mark.django_db
def test_activity_detail_404(auth_client):
    url = reverse("activity-detail", args=[9999])
    response = auth_client.get(url)
    assert response.status_code == 404

@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user():
    return User.objects.create_user(
        username="tester",
        password=TEST_PASS,
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
            password=TEST_PASS,
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
            password=TEST_PASS,
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
        user = User.objects.create_user(username='actuser', password=TEST_PASS)
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
        user = User.objects.create_user(username='actuser', password=TEST_PASS)
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
        user = User.objects.create_user(username='subuser', password=TEST_PASS)
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
        user = User.objects.create_user(username='subuser', password=TEST_PASS)
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
        user = User.objects.create_user(username='todayuser', password=TEST_PASS)
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

class ActivityDetailTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='detailuser', password=TEST_PASS)
        self.client.force_authenticate(user=self.user)
        self.activity = Activity.objects.create(
            user=self.user,
            title='Old Title',
            type='exam',
            due_date=date.today() + timedelta(days=10),
        )
        self.url = f'/api/activities/{self.activity.id}/'

    def test_get_activity(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['data']['title'], 'Old Title')

    def test_update_activity(self):
        response = self.client.put(self.url, {
            'title': 'New Title',
            'type': 'project',
            'due_date': (date.today() + timedelta(days=15)).isoformat(),
        }, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['data']['title'], 'New Title')

    def test_delete_activity(self):
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, 204)
        self.assertEqual(Activity.objects.count(), 0)

    def test_get_activity_not_found(self):
        response = self.client.get('/api/activities/999999/')
        self.assertEqual(response.status_code, 404)


class SubtaskDetailTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='subuser2', password=TEST_PASS)
        self.client.force_authenticate(user=self.user)
        self.activity = Activity.objects.create(
            user=self.user, title='Act', type='exam', due_date=date.today() + timedelta(days=10)
        )
        self.subtask = Subtask.objects.create(
            activity=self.activity, title='Sub', estimated_hours=2.0, target_date=date.today(), status='pending'
        )
        self.url = f'/api/subtasks/{self.subtask.id}/'

    def test_get_subtask(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['data']['title'], 'Sub')

    def test_update_subtask(self):
        response = self.client.patch(self.url, {'title': 'Updated Sub', 'status': 'done'}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['data']['title'], 'Updated Sub')
        self.assertEqual(response.data['data']['status'], 'done')

    def test_delete_subtask(self):
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, 204)
        self.assertEqual(Subtask.objects.count(), 0)


class ValidateOverloadTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='overloaduser', password=TEST_PASS)
        self.client.force_authenticate(user=self.user)
        self.url = '/api/conflicts/overload/'

    def test_validate_overload_ok(self):
        response = self.client.post(self.url, {
            'target_date': date.today().isoformat(),
            'estimated_hours': 2.0
        }, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['status'], 'ok')

    def test_validate_overload_conflict(self):
        response = self.client.post(self.url, {
            'target_date': date.today().isoformat(),
            'estimated_hours': 10.0
        }, format='json')
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.data['status'], 'conflict')

    def test_validate_overload_missing_fields(self):
        response = self.client.post(self.url, {'estimated_hours': 2.0}, format='json')
        self.assertEqual(response.status_code, 400)