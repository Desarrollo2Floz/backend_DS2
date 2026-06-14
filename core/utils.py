def calcular_descuento(precio, porcentaje):
    if porcentaje < 0 or porcentaje > 100:
        raise ValueError("Porcentaje inválido")
    return precio - (precio * porcentaje / 100)

def es_mayor_de_edad(edad):
    return edad >= 18

def validar_email(email):
    return "@" in email and "." in email

def calcular_promedio(notas):
    if len(notas) == 0:
        raise ValueError("La lista de notas no puede estar vacía")
    return sum(notas) / len(notas)
