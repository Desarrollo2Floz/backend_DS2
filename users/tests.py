from django.test import TestCase
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

# =============================================
# Tests US-11 - Autenticacion minima
# Autor: Luis Yair Valencia Garcia
# Descripcion: Pruebas unitarias para registro,
# login y acceso a rutas protegidas
# =============================================

User = get_user_model()


class RegistroTest(TestCase):

    def setUp(self):
        # Inicializa el cliente de pruebas antes de cada test
        self.client = APIClient()

    def test_registro_usuario_exitoso(self):
        # Verifica registro correcto con campos obligatorios (US-11 Escenario 1)
        response = self.client.post('/api/register/', {
            'username': 'testuser',
            'password': 'Test1234Ab',
            'email': 'test@test.com',
            'first_name': 'Luis',
            'last_name': 'Valencia'
        }, format='json')
        self.assertEqual(response.status_code, 201)

    def test_registro_usuario_duplicado_falla(self):
        # Verifica que no se puede registrar dos usuarios con el mismo username (US-11 Escenario 2)
        self.client.post('/api/register/', {
            'username': 'testuser',
            'password': 'Test1234Ab',
            'email': 'test@test.com',
            'first_name': 'Luis',
            'last_name': 'Valencia'
        }, format='json')
        response = self.client.post('/api/register/', {
            'username': 'testuser',
            'password': 'Test1234Ab',
            'email': 'test2@test.com',
            'first_name': 'Luis',
            'last_name': 'Valencia'
        }, format='json')
        self.assertEqual(response.status_code, 400)

    def test_registro_sin_password_falla(self):
        # Verifica que sin password el sistema retorna error (US-11 Escenario 2)
        response = self.client.post('/api/register/', {
            'username': 'testuser',
            'email': 'test@test.com'
        }, format='json')
        self.assertEqual(response.status_code, 400)


class LoginTest(TestCase):

    def setUp(self):
        # Crea usuario de prueba antes de cada test
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='Test1234Ab',
            email='test@test.com'
        )

    def test_login_exitoso(self):
        # Verifica login exitoso y devolucion de token JWT (US-11 Escenario 1)
        response = self.client.post('/api/login/', {
            'username': 'testuser',
            'password': 'Test1234Ab'
        }, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertIn('access', response.data)

    def test_login_password_incorrecta(self):
        # Verifica que credenciales invalidas son rechazadas (US-11 Escenario 2)
        response = self.client.post('/api/login/', {
            'username': 'testuser',
            'password': 'wrongpass'
        }, format='json')
        self.assertEqual(response.status_code, 401)

    def test_me_sin_autenticar(self):
        # Verifica que ruta protegida bloquea sin token (US-11 Escenario 3)
        response = self.client.get('/api/me/')
        self.assertEqual(response.status_code, 401)

    def test_me_autenticado(self):
        # Verifica acceso a datos personales con token valido (US-11 Escenario 1)
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/me/')
        self.assertEqual(response.status_code, 200)