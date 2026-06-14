# pyrefly: ignore [missing-import]
import logging
from django.shortcuts import render
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db import transaction
from drf_spectacular.utils import extend_schema
from .models import Activity, Subtask
from .serializers import ActivitySerializer, SubtaskSerializer

logger = logging.getLogger(__name__)

@extend_schema(methods=['GET'], responses=ActivitySerializer(many=True))
@extend_schema(methods=['POST'], request=ActivitySerializer, responses=ActivitySerializer)
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def activity_list_create(request):
    """
    GET  /api/activities/ — Lista todas las actividades con sus subtareas.
    POST /api/activities/ — Crea una actividad con subtareas anidadas.
    """
    if request.method == 'GET':
        activities = Activity.objects.prefetch_related('subtasks').filter(
            user_id=request.user.id
        )
        serializer = ActivitySerializer(activities, many=True)
        return Response({
            'status': 'success',
            'data': serializer.data,
        }, status=status.HTTP_200_OK)

    # POST
    # Request needed to get user_id in the serializer validate context
    serializer = ActivitySerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        try:
            with transaction.atomic():
                activity = serializer.save(user_id=request.user.id)
            return Response({
                'status': 'success',
                'message': 'Actividad creada exitosamente',
                'data': ActivitySerializer(activity).data,
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error(f"Error al crear actividad: {str(e)}")
            return Response({
                'status': 'error',
                'message': 'No se pudo guardar la actividad de forma segura.',
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return Response({
        'status': 'error',
        'message': 'Error de validación',
        'errors': serializer.errors,
    }, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(methods=['POST'], request=SubtaskSerializer, responses=SubtaskSerializer)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def subtask_create(request, activity_id):
    """
    POST /api/activities/<int:activity_id>/subtasks/ — Crea una subtarea para una actividad.
    """
    try:
        activity = Activity.objects.get(
            pk=activity_id,
            user_id=request.user.id
        )
    except Activity.DoesNotExist:
        return Response({
            'status': 'error',
            'message': 'Actividad no encontrada',
        }, status=status.HTTP_404_NOT_FOUND)

    serializer = SubtaskSerializer(data=request.data, context={'activity': activity})
    if serializer.is_valid():
        try:
            serializer.save(activity=activity)
            return Response({
                'status': 'success',
                'message': 'Subtarea creada exitosamente',
                'data': serializer.data,
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            # Registrar el error real en los logs del servidor
            logger.error(f"Error al crear subtarea: {str(e)}")

            return Response({
                'status': 'error',
                'message': 'No se pudo guardar la subtarea. Ocurrió un error inesperado en el servidor.',
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return Response({
        'status': 'error',
        'message': 'Error de validación',
        'errors': serializer.errors,
    }, status=status.HTTP_400_BAD_REQUEST)