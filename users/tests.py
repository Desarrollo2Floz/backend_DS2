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
            'password': 'Test1234Ab', #NOSONAR
            'email': 'test@test.com',
            'first_name': 'Luis',
            'last_name': 'Valencia'
        }, format='json')
        self.assertEqual(response.status_code, 201)

    def test_registro_usuario_duplicado_falla(self):
        # Verifica que no se puede registrar dos usuarios con el mismo username (US-11 Escenario 2)
        self.client.post('/api/register/', {
            'username': 'testuser',
            'password': 'Test1234Ab', #NOSONAR
            'email': 'test@test.com',
            'first_name': 'Luis',
            'last_name': 'Valencia'
        }, format='json')
        response = self.client.post('/api/register/', {
            'username': 'testuser',
            'password': 'Test1234Ab', #NOSONAR
            'email': 'test2@test.com', 
            'first_name': 'Luis',
            'last_name': 'Valencia'
        }, format='json')
        self.assertEqual(response.status_code, 400)

    def test_registro_sin_password_falla(self):
        # Verifica que sin passwordd el sistema retorna error (US-11 Escenario 2)
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
            password='Test1234Ab', #NOSONAR
            email='test@test.com'
        )

    def test_login_exitoso(self):
        # Verifica login exitoso y devolucion de token JWT (US-11 Escenario 1)
        response = self.client.post('/api/login/', {
            'username': 'testuser',
            'password': 'Test1234Ab' #NOSONAR
        }, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertIn('access', response.data)

    def test_login_password_incorrecta(self):
        # Verifica que credenciales invalidas son rechazadas (US-11 Escenario 2)
        response = self.client.post('/api/login/', {
            'username': 'testuser',
            'password': 'wrongpass' #NOSONAR
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


from datetime import date, timedelta

class StreakTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='streakuser',
            password='Test1234Ab',
            email='streak@test.com'
        )

    def test_streak_starts_at_one(self):
        # Al iniciar actividad por primera vez la racha debe ser 1
        self.user.update_streak()
        self.assertEqual(self.user.streak_current, 1)
        self.assertEqual(self.user.streak_best, 1)
        self.assertEqual(self.user.streak_last_day, date.today())

    def test_streak_same_day_does_not_increment(self):
        # Repetir actividad el mismo día no debe incrementar la racha
        self.user.update_streak()
        self.user.update_streak()
        self.assertEqual(self.user.streak_current, 1)
        self.assertEqual(self.user.streak_best, 1)

    def test_streak_increments_consecutive_days(self):
        # Actividad en días consecutivos debe incrementar la racha
        self.user.streak_last_day = date.today() - timedelta(days=1)
        self.user.streak_current = 1
        self.user.streak_best = 1
        self.user.save()

        self.user.update_streak()
        self.assertEqual(self.user.streak_current, 2)
        self.assertEqual(self.user.streak_best, 2)

    def test_streak_resets_after_gap(self):
        # Dejar pasar más de 1 día debe reiniciar la racha a 1
        self.user.streak_last_day = date.today() - timedelta(days=2)
        self.user.streak_current = 5
        self.user.streak_best = 5
        self.user.save()

        self.user.update_streak()
        self.assertEqual(self.user.streak_current, 1)
        self.assertEqual(self.user.streak_best, 5) # Conserva el mejor histórico