# Backend DS2 - Railway Deployment

Este proyecto está configurado para desplegarse en Railway.

## Archivos de Configuración

- `Procfile`: Define el comando para iniciar la aplicación
- `runtime.txt`: Especifica la versión de Python
- `.env.example`: Plantilla de variables de entorno necesarias

## Variables de Entorno Requeridas en Railway

### 1. DJANGO_SECRET_KEY
Clave secreta de Django para producción. Genera una nueva con:
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 2. DEBUG
Debe ser `False` en producción:
```
DEBUG=False
```

### 3. ALLOWED_HOSTS
Dominios permitidos (separados por comas, sin espacios):
```
ALLOWED_HOSTS=.railway.app,tu-dominio-personalizado.com
```

### 4. CORS_ALLOWED_ORIGINS
Orígenes permitidos para CORS (separados por comas, sin espacios):
```
CORS_ALLOWED_ORIGINS=https://tu-frontend.vercel.app,http://localhost:5173
```

### 5. DATABASE_URL
Railway la crea automáticamente cuando agregas PostgreSQL al proyecto.

## Pasos para Desplegar en Railway

1. **Conecta tu repositorio** de GitHub a Railway
2. **Agrega PostgreSQL** al proyecto desde el dashboard
3. **Configura las variables de entorno** listadas arriba
4. **Despliega** - Railway detectará automáticamente el Procfile
5. **Ejecuta migraciones** desde la consola de Railway:
   ```bash
   python manage.py migrate
   ```
6. **Crea un superusuario** (opcional):
   ```bash
   python manage.py createsuperuser
   ```

## Comandos Útiles

### Desarrollo Local
```bash
# Instalar dependencias
pip install -r requirements.txt

# Ejecutar migraciones
python manage.py migrate

# Iniciar servidor de desarrollo
python manage.py runserver
```

### Producción
```bash
# Recolectar archivos estáticos
python manage.py collectstatic --noinput

# Ejecutar con gunicorn
gunicorn config.wsgi --log-file -
```

## Notas

- El archivo `.env` está en `.gitignore` y no debe subirse al repositorio
- Usa `.env.example` como referencia para las variables necesarias
- En producción, DEBUG debe estar siempre en False
- Railway proporciona automáticamente las variables de PostgreSQL
