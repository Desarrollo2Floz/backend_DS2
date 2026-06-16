from django.test import TestCase
from .utils import calcular_descuento, es_mayor_de_edad, validar_email, calcular_promedio, validar_nombre_actividad

# Test Integrante 1
class DescuentoTest(TestCase):
    def test_descuento_normal(self):
        self.assertEqual(calcular_descuento(100, 20), 80.0)

    def test_descuento_cero(self):
        self.assertEqual(calcular_descuento(50, 0), 50.0)

    def test_descuento_invalido(self):
        with self.assertRaises(ValueError):
            calcular_descuento(100, -5)

# Test Integrante 2
class MayorEdadTest(TestCase):
    def test_mayor_de_edad(self):
        self.assertTrue(es_mayor_de_edad(18))

    def test_menor_de_edad(self):
        self.assertFalse(es_mayor_de_edad(17))

    def test_justo_en_el_limite(self):
        self.assertTrue(es_mayor_de_edad(18))

# Test Integrante 3
class EmailTest(TestCase):
    def test_email_valido(self):
        self.assertTrue(validar_email("test@gmail.com"))

    def test_email_invalido(self):
        self.assertFalse(validar_email("testgmail.com"))

    def test_email_sin_punto(self):
        self.assertFalse(validar_email("test@gmailcom"))

# Test Integrante 4
class ValidarNombreActividadTest(TestCase):
    def test_nombre_valido(self):
        self.assertEqual(validar_nombre_actividad("  Estudiar Django  "), "Estudiar Django")

    def test_nombre_vacio(self):
        with self.assertRaises(ValueError):
            validar_nombre_actividad("")

    def test_nombre_solo_espacios(self):
        with self.assertRaises(ValueError):
            validar_nombre_actividad("   ")

# Test Extra
class PromedioTest(TestCase):
    def test_promedio_normal(self):
        self.assertEqual(calcular_promedio([3, 4, 5]), 4.0)

    def test_promedio_lista_vacia(self):
        with self.assertRaises(ValueError):
            calcular_promedio([])
