def es_mayor_de_edad(edad):
    return edad >= 18

def validar_email(email):
    return "@" in email and "." in email

def validar_nombre_actividad(nombre):
    if not nombre or len(nombre.strip()) == 0:
        raise ValueError("El nombre de la actividad no puede estar vacío")
    return nombre.strip()
