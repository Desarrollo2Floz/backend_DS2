# pyrefly: ignore [missing-import]
import logging
from datetime import date
from django.shortcuts import render
from django.db import transaction
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiParameter
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
            user_id=request.user.id  # <-- Corregido aquí
        )
        serializer = ActivitySerializer(activities, many=True)
        return Response({
            'status': 'success',
            'data': serializer.data,
        }, status=status.HTTP_200_OK)

    # POST
    serializer = ActivitySerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        try:
            with transaction.atomic():
                activity = serializer.save(user_id=request.user.id)  # <-- Corregido aquí
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
    POST /api/activities/<uuid:activity_id>/subtasks/ — Crea una subtarea para una actividad.
    """
    try:
        activity = Activity.objects.get(
            pk=activity_id,
            user_id=request.user.id  # <-- Corregido aquí
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


@extend_schema(methods=['PUT', 'PATCH'], request=ActivitySerializer, responses=ActivitySerializer)
@extend_schema(methods=['DELETE'], responses={204: None})
@api_view(['PUT', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def activity_detail(request, pk):
    """
    PUT/PATCH /api/activities/<int:pk>/ — Edita una actividad.
    DELETE /api/activities/<int:pk>/ — Elimina una actividad.
    """
    try:
        activity = Activity.objects.get(pk=pk, user_id=request.user.id)  # <-- Corregido aquí
    except Activity.DoesNotExist:
        return Response({
            'status': 'error',
            'message': 'Actividad no encontrada',
        }, status=status.HTTP_404_NOT_FOUND)

    if request.method in ['PUT', 'PATCH']:
        partial = request.method == 'PATCH'
        serializer = ActivitySerializer(activity, data=request.data, partial=partial, context={'request': request})
        if serializer.is_valid():
            with transaction.atomic():
                serializer.save()
            return Response({
                'status': 'success',
                'message': 'Actividad actualizada exitosamente',
                'data': serializer.data,
            }, status=status.HTTP_200_OK)
        return Response({
            'status': 'error',
            'message': 'Error de validación',
            'errors': serializer.errors,
        }, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        with transaction.atomic():
            activity.delete()
        return Response({
            'status': 'success',
            'message': 'Actividad eliminada exitosamente',
        }, status=status.HTTP_200_OK)


@extend_schema(methods=['PUT', 'PATCH'], request=SubtaskSerializer, responses=SubtaskSerializer)
@extend_schema(methods=['DELETE'], responses={204: None})
@api_view(['PUT', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def subtask_detail(request, pk):
    """
    PUT/PATCH /api/subtasks/<int:pk>/ — Edita una subtarea.
    DELETE /api/subtasks/<int:pk>/ — Elimina una subtarea.
    """
    try:
        subtask = Subtask.objects.get(pk=pk, activity__user_id=request.user.id)  # <-- Corregido aquí
    except Subtask.DoesNotExist:
        return Response({
            'status': 'error',
            'message': 'Subtarea no encontrada',
        }, status=status.HTTP_404_NOT_FOUND)

    if request.method in ['PUT', 'PATCH']:
        partial = request.method == 'PATCH'
        serializer = SubtaskSerializer(subtask, data=request.data, partial=partial)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'status': 'success',
                'message': 'Subtarea actualizada exitosamente',
                'data': serializer.data,
            }, status=status.HTTP_200_OK)
        return Response({
            'status': 'error',
            'message': 'Error de validación',
            'errors': serializer.errors,
        }, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        subtask.delete()
        return Response({
            'status': 'success',
            'message': 'Subtarea eliminada exitosamente',
        }, status=status.HTTP_200_OK)


@extend_schema(
    methods=['GET'],
    responses=SubtaskSerializer(many=True),
    parameters=[
        OpenApiParameter(name='course', description='Filter by course name', required=False, type=str),
        OpenApiParameter(name='status', description='Filter by subtask status', required=False, type=str),
    ]
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def today_subtasks(request):
    """
    GET /api/today/ — Obtiene las prioridades agrupadas por Vencidas, Para hoy y Próximas (US-04).
    """
    today = date.today()
    
    subtasks = Subtask.objects.filter(
        activity__user_id=request.user.id,  # <-- Corregido aquí
        target_date__isnull=False
    )
    
    course_param = request.GET.get('course')
    status_param = request.GET.get('status')
    
    if course_param:
        subtasks = subtasks.filter(activity__course__icontains=course_param)
        
    if status_param:
        subtasks = subtasks.filter(status=status_param)
    else:
        subtasks = subtasks.exclude(status='done')
    
    overdue = []
    today_list = []
    upcoming = []
    
    for subtask in subtasks:
        if subtask.target_date < today:
            overdue.append(subtask)
        elif subtask.target_date == today:
            today_list.append(subtask)
        else:
            upcoming.append(subtask)
            
    # Ordenamiento
    overdue.sort(key=lambda x: (x.target_date, x.estimated_hours or 0))
    today_list.sort(key=lambda x: x.estimated_hours or 0)
    upcoming.sort(key=lambda x: (x.target_date, x.estimated_hours or 0))
    
    return Response({
        'status': 'success',
        'data': {
            'overdue': SubtaskSerializer(overdue, many=True).data,
            'today': SubtaskSerializer(today_list, many=True).data,
            'upcoming': SubtaskSerializer(upcoming, many=True).data,
            'rule': 'Orden: Vencidas (más antiguas), Hoy, Próximas (más cercanas). Empate: menor esfuerzo.'
        }
    }, status=status.HTTP_200_OK)