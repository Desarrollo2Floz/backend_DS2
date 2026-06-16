from django.test import TestCase
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

# =============================================
# Tests US-01 - Crear actividad evaluativa
# Tests US-02 - Crear plan inicial (subtareas)
# Autor: Luis Yair Valencia Garcia
# Descripcion: Pruebas unitarias para crear
# actividades y subtareas
# =============================================

User = get_user_model()


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