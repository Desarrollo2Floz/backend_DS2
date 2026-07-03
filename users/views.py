from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema
from rest_framework_simplejwt.views import TokenObtainPairView

from .serializers import LoginSerializer, RegisterSerializer, UserSerializer, DailyCapacitySerializer, StreakSerializer
from .models import User, DailyCapacity

class LoginView(TokenObtainPairView):
    serializer_class = LoginSerializer

@extend_schema(methods=['POST'], request=RegisterSerializer, responses=UserSerializer)
@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    serializer = RegisterSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        return Response({
            'status': 'success',
            'message': 'Usuario registrado exitosamente.',
            'data': UserSerializer(user).data,
        }, status=status.HTTP_201_CREATED)

    return Response({
        'status': 'error',
        'message': 'Error de validación',
        'errors': serializer.errors,
    }, status=status.HTTP_400_BAD_REQUEST)

@extend_schema(methods=['GET'], responses=DailyCapacitySerializer)
@extend_schema(methods=['PUT', 'PATCH'], request=DailyCapacitySerializer, responses=DailyCapacitySerializer)
@api_view(['GET', 'PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def daily_capacity_view(request):
    """
    GET: Obtener límite actual del usuario. Si no existe, devuelve el por defecto (6.0h).
    PUT/PATCH: Actualiza o guarda un nuevo valor de límite para el usuario.
    """
    try:
        capacity = DailyCapacity.objects.get(user=request.user)
    except DailyCapacity.DoesNotExist:
        capacity = None

    if request.method == 'GET':
        if capacity:
            serializer = DailyCapacitySerializer(capacity)
            return Response({
                'status': 'success',
                'data': serializer.data,
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'status': 'success',
                'data': {
                    'daily_limit_hours': 6.0
                },
            }, status=status.HTTP_200_OK)

    elif request.method in ['PUT', 'PATCH']:
        serializer = DailyCapacitySerializer(
            capacity,
            data=request.data,
            partial=(request.method == 'PATCH'),
            context={'request': request}
        )
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response({
                'status': 'success',
                'message': 'Capacidad actualizada',
                'data': serializer.data,
            }, status=status.HTTP_200_OK)

        return Response({
            'status': 'error',
            'message': 'El límite debe estar entre 1 y 16 horas. Intenta de nuevo.',
            'errors': serializer.errors,
        }, status=status.HTTP_400_BAD_REQUEST)
    
@extend_schema(methods=['GET'], responses=StreakSerializer)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_streak(request):
    """Obtiene la racha actual del usuario autenticado."""
    serializer = StreakSerializer(request.user)
    return Response({
        'status': 'success',
        'data': serializer.data,
    }, status=status.HTTP_200_OK)

@extend_schema(methods=['GET'], responses=UserSerializer)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def me(request):
    return Response({
        'status': 'success',
        'data': UserSerializer(request.user).data,
    }, status=status.HTTP_200_OK)
