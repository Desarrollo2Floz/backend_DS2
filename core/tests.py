from django.test import TestCase
from .utils import es_mayor_de_edad, validar_email, validar_nombre_actividad
from rest_framework.test import APITestCase
from rest_framework import status
from datetime import date, timedelta
from django.contrib.auth import get_user_model
from activities.models import Activity, Subtask
from users.models import DailyCapacity

User = get_user_model()

# Test Integrante 1
class MayorEdadTest(TestCase):
    def test_mayor_de_edad(self):
        self.assertTrue(es_mayor_de_edad(18))

    def test_menor_de_edad(self):
        self.assertFalse(es_mayor_de_edad(17))

    def test_justo_en_el_limite(self):
        self.assertTrue(es_mayor_de_edad(18))

# Test Integrante 2
class EmailTest(TestCase):
    def test_email_valido(self):
        self.assertTrue(validar_email("test@gmail.com"))

    def test_email_invalido(self):
        self.assertFalse(validar_email("testgmail.com"))

    def test_email_sin_punto(self):
        self.assertFalse(validar_email("test@gmailcom"))

# Test Integrante 3
class ValidarNombreActividadTest(TestCase):
    def test_nombre_valido(self):
        self.assertEqual(validar_nombre_actividad("  Estudiar Django  "), "Estudiar Django")

    def test_nombre_vacio(self):
        with self.assertRaises(ValueError):
            validar_nombre_actividad("")

    def test_nombre_solo_espacios(self):
        with self.assertRaises(ValueError):
            validar_nombre_actividad("   ")


# Test Integrante 4
class ValidarNombreActividadEspaciosTest(TestCase):
    def test_nombre_con_saltos_y_tabs(self):
        self.assertEqual(
            validar_nombre_actividad("\n\t  Estudiar Django  \t\n"),
            "Estudiar Django"
        )

# Test de Vistas de Activities 
class ActivitiesViewsTest(APITestCase):
    def setUp(self):
        # 1. Crear un usuario de prueba
        import os
        dummy_pass = os.environ.get('TEST_PASS', 'test_pass_123!')
        self.user = User.objects.create_user(
            username='testuser',
            password=dummy_pass, 
            email='test@test.com'
        )
        self.client.force_authenticate(user=self.user)
        
        # 2. Configurar la capacidad diaria del usuario
        self.capacity = DailyCapacity.objects.create(
            user=self.user, 
            daily_limit_hours=8.0
        )
        
        # 3. Crear una Actividad base
        self.activity = Activity.objects.create(
            user=self.user,
            title='Actividad de Prueba',
            course='Matemáticas',
            status='pending',
            due_date=date.today() + timedelta(days=5)
        )

    def test_today_subtasks_actualiza_estados(self):
        # Prueba que actualiza estados entre overdue y pending
        hoy = date.today()
        ayer = hoy - timedelta(days=1)
        manana = hoy + timedelta(days=1)

        tarea_pasada = Subtask.objects.create(
            activity=self.activity, title='A', status='pending',
            target_date=ayer, estimated_hours=1.0
        )
        tarea_futura = Subtask.objects.create(
            activity=self.activity, title='B', status='overdue',
            target_date=manana, estimated_hours=1.0
        )

        response = self.client.get('/api/subtasks/today/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        tarea_pasada.refresh_from_db()
        tarea_futura.refresh_from_db()
        self.assertEqual(tarea_pasada.status, 'overdue')
        self.assertEqual(tarea_futura.status, 'pending')

    def test_subtask_detail_calcula_horas(self):
        tarea_hoy = Subtask.objects.create(
            activity=self.activity, title='Hoy', status='pending',
            target_date=date.today(), estimated_hours=2.0
        )

        url = f'/api/subtasks/{tarea_hoy.id}/'
        # Enviamos los datos completos que el serializador espera
        data = {
            'title': 'Actualizado',
            'target_date': str(date.today()), 
            'estimated_hours': 2.0
        }
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['limit_hours'], 8.0)
        self.assertEqual(response.data['planned_hours'], 2.0)

    def test_calculo_sin_capacidad(self):
        self.capacity.delete()
        tarea = Subtask.objects.create(
            activity=self.activity, title='C', status='pending',
            target_date=date.today(), estimated_hours=3.0
        )

        url = f'/api/subtasks/{tarea.id}/'
        # Enviamos los datos completos
        data = {
            'estimated_hours': 4.0,
            'target_date': str(date.today()),
            'title': 'C'
        }
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['limit_hours'], 6.0)