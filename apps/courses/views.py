"""
Views para la API de cursos y contenido educativo.

Este módulo contiene las vistas para:
- Gestión de cursos
- Lecciones y contenido
- Cuestionarios y preguntas
- Inscripciones y progreso
"""

from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db import models
from django.db.models import Avg, Count, Q, Sum
from rest_framework import generics, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.users.permissions import IsStudent, IsTeacher, IsAdminUser
from .models import (
    Course, Lesson, Quiz, Question,
    CourseEnrollment, LessonProgress, QuizAttempt
)
from .serializers import (
    CourseListSerializer, CourseDetailSerializer, CourseCreateUpdateSerializer,
    LessonListSerializer, LessonDetailSerializer,
    QuizDetailSerializer, QuizSubmissionSerializer,
    CourseEnrollmentSerializer, LessonProgressSerializer, QuizAttemptSerializer
)


class CourseViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de cursos.
    
    Permite CRUD completo de cursos con diferentes permisos según el rol.
    """
    
    queryset = Course.objects.select_related('instructor').prefetch_related('lessons')
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    lookup_field = 'slug'
    
    def get_serializer_class(self):
        """Seleccionar serializer según la acción."""
        if self.action == 'list':
            return CourseListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return CourseCreateUpdateSerializer
        return CourseDetailSerializer
    
    def get_queryset(self):
        """Filtrar cursos según el usuario y parámetros."""
        queryset = super().get_queryset()
        
        # Solo mostrar cursos publicados a estudiantes no autenticados
        if not self.request.user.is_authenticated:
            queryset = queryset.filter(status='published')
        
        # Los instructores solo ven sus cursos en ciertas acciones
        elif (self.request.user.is_teacher() and 
              self.action in ['update', 'partial_update', 'destroy']):
            queryset = queryset.filter(instructor=self.request.user)
        
        # Filtros por parámetros de consulta
        level = self.request.query_params.get('level', None)
        if level:
            queryset = queryset.filter(level=level)
        
        instructor = self.request.query_params.get('instructor', None)
        if instructor:
            queryset = queryset.filter(instructor__username=instructor)
        
        featured = self.request.query_params.get('featured', None)
        if featured and featured.lower() == 'true':
            queryset = queryset.filter(is_featured=True)
        
        # Ordenamiento
        ordering = self.request.query_params.get('ordering', '-created_at')
        if ordering in ['title', '-title', 'price', '-price', 'created_at', '-created_at']:
            queryset = queryset.order_by(ordering)
        
        return queryset
    
    def get_permissions(self):
        """Permisos específicos por acción."""
        if self.action == 'create':
            permission_classes = [IsTeacher]
        elif self.action in ['update', 'partial_update', 'destroy']:
            permission_classes = [IsTeacher]  # Se valida propiedad en get_queryset
        else:
            permission_classes = [permissions.IsAuthenticatedOrReadOnly]
        
        return [permission() for permission in permission_classes]
    
    @action(detail=True, methods=['post'], permission_classes=[IsStudent])
    def enroll(self, request, slug=None):
        """Inscribir al estudiante en el curso."""
        course = self.get_object()
        
        # Verificar si puede inscribirse
        can_enroll, message = course.can_enroll(request.user)
        if not can_enroll:
            return Response(
                {'error': message},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Crear inscripción
        enrollment = CourseEnrollment.objects.create(
            student=request.user,
            course=course
        )
        
        # Actualizar contador de inscripciones del curso
        course.total_enrollments = course.enrollments.count()
        course.save(update_fields=['total_enrollments'])
        
        serializer = CourseEnrollmentSerializer(enrollment, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def lessons(self, request, slug=None):
        """Obtener lecciones del curso."""
        course = self.get_object()
        
        # Verificar acceso
        if request.user.is_student():
            # Verificar inscripción
            if not course.enrollments.filter(student=request.user).exists():
                return Response(
                    {'error': 'No estás inscrito en este curso'},
                    status=status.HTTP_403_FORBIDDEN
                )
        elif not (request.user.is_teacher() and course.instructor == request.user):
            # Solo el instructor puede ver las lecciones sin inscripción
            return Response(
                {'error': 'No tienes permiso para ver las lecciones'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        lessons = course.lessons.filter(is_published=True).order_by('order')
        serializer = LessonListSerializer(lessons, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'], permission_classes=[IsStudent])
    def progress(self, request, slug=None):
        """Obtener progreso del estudiante en el curso."""
        course = self.get_object()
        
        try:
            enrollment = course.enrollments.get(student=request.user)
        except CourseEnrollment.DoesNotExist:
            return Response(
                {'error': 'No estás inscrito en este curso'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Recalcular progreso
        enrollment.calculate_progress()
        
        serializer = CourseEnrollmentSerializer(enrollment, context={'request': request})
        return Response(serializer.data)


class LessonViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para visualización de lecciones.
    
    Solo lectura para estudiantes inscritos e instructores.
    """
    
    queryset = Lesson.objects.select_related('course', 'course__instructor')
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'slug'
    
    def get_serializer_class(self):
        """Seleccionar serializer según la acción."""
        if self.action == 'list':
            return LessonListSerializer
        return LessonDetailSerializer
    
    def get_queryset(self):
        """Filtrar lecciones según acceso del usuario."""
        queryset = super().get_queryset()
        
        # Filtrar solo lecciones publicadas por defecto
        queryset = queryset.filter(is_published=True)
        
        # Filtrar por curso si se especifica
        course_slug = self.request.query_params.get('course', None)
        if course_slug:
            queryset = queryset.filter(course__slug=course_slug)
        
        return queryset.order_by('course__id', 'order')
    
    def retrieve(self, request, *args, **kwargs):
        """Obtener detalle de lección con verificación de acceso."""
        lesson = self.get_object()
        
        # Verificar acceso a la lección
        can_access, message = lesson.can_access(request.user)
        if not can_access:
            return Response(
                {'error': message},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = self.get_serializer(lesson)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], permission_classes=[IsStudent])
    def start_progress(self, request, slug=None):
        """Iniciar progreso en la lección."""
        lesson = self.get_object()
        
        # Verificar inscripción en el curso
        try:
            enrollment = lesson.course.enrollments.get(student=request.user)
        except CourseEnrollment.DoesNotExist:
            return Response(
                {'error': 'No estás inscrito en este curso'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Crear o obtener progreso
        progress, created = LessonProgress.objects.get_or_create(
            enrollment=enrollment,
            lesson=lesson
        )
        
        serializer = LessonProgressSerializer(progress, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], permission_classes=[IsStudent])
    def complete(self, request, slug=None):
        """Marcar lección como completada."""
        lesson = self.get_object()
        
        # Verificar inscripción en el curso
        try:
            enrollment = lesson.course.enrollments.get(student=request.user)
        except CourseEnrollment.DoesNotExist:
            return Response(
                {'error': 'No estás inscrito en este curso'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Obtener progreso
        try:
            progress = LessonProgress.objects.get(
                enrollment=enrollment,
                lesson=lesson
            )
        except LessonProgress.DoesNotExist:
            return Response(
                {'error': 'Debes iniciar la lección primero'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Marcar como completada
        progress.mark_completed()
        
        serializer = LessonProgressSerializer(progress, context={'request': request})
        return Response(serializer.data)


class QuizViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para cuestionarios.
    
    Permite ver quizzes y enviar respuestas.
    """
    
    queryset = Quiz.objects.select_related('lesson', 'lesson__course').prefetch_related('questions')
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = QuizDetailSerializer
    
    def get_queryset(self):
        """Filtrar quizzes según acceso del usuario."""
        queryset = super().get_queryset()
        
        # Filtrar por curso si se especifica
        course_slug = self.request.query_params.get('course', None)
        if course_slug:
            queryset = queryset.filter(lesson__course__slug=course_slug)
        
        return queryset
    
    def retrieve(self, request, *args, **kwargs):
        """Obtener quiz con verificación de acceso."""
        quiz = self.get_object()
        
        # Verificar acceso a la lección
        can_access, message = quiz.lesson.can_access(request.user)
        if not can_access:
            return Response(
                {'error': message},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = self.get_serializer(quiz)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], permission_classes=[IsStudent])
    def submit(self, request, pk=None):
        """Enviar respuestas del quiz."""
        quiz = self.get_object()
        
        # Verificar inscripción en el curso
        try:
            enrollment = quiz.lesson.course.enrollments.get(student=request.user)
        except CourseEnrollment.DoesNotExist:
            return Response(
                {'error': 'No estás inscrito en este curso'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Validar datos
        serializer = QuizSubmissionSerializer(
            data=request.data,
            context={'quiz': quiz, 'request': request}
        )
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # Verificar si puede hacer un intento
        last_attempt = quiz.attempts.filter(enrollment=enrollment).last()
        if last_attempt:
            can_retake, message = last_attempt.can_retake()
            if not can_retake:
                return Response(
                    {'error': message},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Crear nuevo intento
        attempt = QuizAttempt.objects.create(
            enrollment=enrollment,
            quiz=quiz,
            answers=serializer.validated_data['answers']
        )
        
        # Completar el intento y calcular puntuación
        score = attempt.complete_attempt()
        
        # Respuesta
        response_data = {
            'attempt_id': attempt.id,
            'score': score,
            'is_passed': attempt.is_passed,
            'passing_score': quiz.passing_score
        }
        
        # Agregar detalles si se permite mostrar resultados
        if quiz.show_results_immediately:
            response_data.update({
                'total_questions': quiz.total_questions,
                'correct_answers': int((score / 100) * quiz.total_questions),
                'fore_tokens_earned': quiz.fore_tokens_reward if attempt.is_passed else 0
            })
        
        return Response(response_data, status=status.HTTP_201_CREATED)


class StudentDashboardView(generics.GenericAPIView):
    """
    Vista del dashboard del estudiante.
    
    Muestra resumen de cursos inscritos, progreso y estadísticas.
    """
    
    permission_classes = [IsStudent]
    
    def get(self, request):
        """Obtener datos del dashboard."""
        # Inscripciones activas
        enrollments = CourseEnrollment.objects.filter(
            student=request.user
        ).select_related('course').order_by('-enrolled_at')
        
        # Estadísticas generales
        stats = {
            'total_courses': enrollments.count(),
            'active_courses': enrollments.filter(status='active').count(),
            'completed_courses': enrollments.filter(status='completed').count(),
            'total_fore_tokens': enrollments.aggregate(
                total=Sum('fore_tokens_earned')
            )['total'] or 0,
            'average_progress': enrollments.filter(
                status='active'
            ).aggregate(
                avg=Avg('progress_percentage')
            )['avg'] or 0
        }
        
        # Cursos en progreso
        active_enrollments = enrollments.filter(status='active')[:5]
        
        # Últimos quizzes realizados
        recent_quiz_attempts = QuizAttempt.objects.filter(
            enrollment__student=request.user,
            is_completed=True
        ).select_related('quiz', 'quiz__lesson').order_by('-completed_at')[:5]
        
        return Response({
            'stats': stats,
            'active_courses': CourseEnrollmentSerializer(
                active_enrollments, 
                many=True, 
                context={'request': request}
            ).data,
            'recent_quiz_attempts': QuizAttemptSerializer(
                recent_quiz_attempts,
                many=True,
                context={'request': request}
            ).data
        })


class TeacherDashboardView(generics.GenericAPIView):
    """
    Vista del dashboard del instructor.
    
    Muestra resumen de cursos creados, estudiantes y estadísticas.
    """
    
    permission_classes = [IsTeacher]
    
    def get(self, request):
        """Obtener datos del dashboard del instructor."""
        # Cursos del instructor
        courses = Course.objects.filter(
            instructor=request.user
        ).annotate(
            enrollments_count=Count('enrollments')
        ).order_by('-created_at')
        
        # Estadísticas generales
        stats = {
            'total_courses': courses.count(),
            'published_courses': courses.filter(status='published').count(),
            'draft_courses': courses.filter(status='draft').count(),
            'total_students': CourseEnrollment.objects.filter(
                course__instructor=request.user
            ).values('student').distinct().count(),
            'total_enrollments': CourseEnrollment.objects.filter(
                course__instructor=request.user
            ).count()
        }
        
        # Cursos más populares
        popular_courses = courses.filter(
            status='published'
        ).order_by('-total_enrollments')[:5]
        
        return Response({
            'stats': stats,
            'courses': CourseListSerializer(
                courses[:5], 
                many=True, 
                context={'request': request}
            ).data,
            'popular_courses': CourseListSerializer(
                popular_courses,
                many=True,
                context={'request': request}
            ).data
        })
