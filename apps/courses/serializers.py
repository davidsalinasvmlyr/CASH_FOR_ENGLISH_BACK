"""
Serializers para la API de cursos y contenido educativo.

Este módulo contiene los serializers para:
- Cursos
- Lecciones
- Cuestionarios
- Preguntas
- Progreso del estudiante
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model

from .models import (
    Course, Lesson, Quiz, Question,
    CourseEnrollment, LessonProgress, QuizAttempt
)

User = get_user_model()


class InstructorSerializer(serializers.ModelSerializer):
    """Serializer para información básica del instructor."""
    
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'full_name', 'email']
        read_only_fields = ['id', 'username', 'email']


class CourseListSerializer(serializers.ModelSerializer):
    """Serializer para listar cursos (vista resumida)."""
    
    instructor = InstructorSerializer(read_only=True)
    level_display = serializers.CharField(source='get_level_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    is_enrollment_open = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Course
        fields = [
            'id', 'title', 'slug', 'short_description', 'level', 'level_display',
            'status', 'status_display', 'instructor', 'price', 'fore_tokens_reward',
            'thumbnail', 'estimated_hours', 'total_lessons', 'total_enrollments',
            'average_rating', 'is_featured', 'is_enrollment_open', 'created_at'
        ]
        read_only_fields = [
            'id', 'slug', 'total_lessons', 'total_enrollments', 
            'average_rating', 'created_at'
        ]


class CourseDetailSerializer(serializers.ModelSerializer):
    """Serializer para detalles completos del curso."""
    
    instructor = InstructorSerializer(read_only=True)
    level_display = serializers.CharField(source='get_level_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    is_enrollment_open = serializers.BooleanField(read_only=True)
    completion_rate = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)
    
    # Información del usuario actual sobre este curso
    user_enrollment = serializers.SerializerMethodField()
    can_enroll = serializers.SerializerMethodField()
    
    class Meta:
        model = Course
        fields = [
            'id', 'title', 'slug', 'description', 'short_description',
            'level', 'level_display', 'language', 'status', 'status_display',
            'instructor', 'price', 'fore_tokens_reward', 'thumbnail', 'trailer_video',
            'estimated_hours', 'max_enrollments', 'is_featured',
            'enrollment_start_date', 'enrollment_end_date',
            'total_lessons', 'total_enrollments', 'average_rating',
            'completion_rate', 'is_enrollment_open',
            'user_enrollment', 'can_enroll',
            'meta_title', 'meta_description', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'slug', 'total_lessons', 'total_enrollments',
            'average_rating', 'completion_rate', 'created_at', 'updated_at'
        ]
    
    def get_user_enrollment(self, obj):
        """Obtener información de inscripción del usuario actual."""
        request = self.context.get('request')
        if request and request.user.is_authenticated and request.user.is_student():
            try:
                enrollment = obj.enrollments.get(student=request.user)
                return {
                    'id': enrollment.id,
                    'status': enrollment.status,
                    'progress_percentage': enrollment.progress_percentage,
                    'enrolled_at': enrollment.enrolled_at
                }
            except CourseEnrollment.DoesNotExist:
                return None
        return None
    
    def get_can_enroll(self, obj):
        """Verificar si el usuario actual puede inscribirse."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            can_enroll, message = obj.can_enroll(request.user)
            return {'can_enroll': can_enroll, 'message': message}
        return {'can_enroll': False, 'message': 'Debes iniciar sesión'}


class CourseCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer para crear/actualizar cursos."""
    
    class Meta:
        model = Course
        fields = [
            'title', 'description', 'short_description', 'level', 'language',
            'price', 'fore_tokens_reward', 'thumbnail', 'trailer_video',
            'estimated_hours', 'max_enrollments', 'status', 'is_featured',
            'enrollment_start_date', 'enrollment_end_date',
            'meta_title', 'meta_description'
        ]
    
    def create(self, validated_data):
        """Crear curso con el instructor actual."""
        request = self.context.get('request')
        validated_data['instructor'] = request.user
        return super().create(validated_data)


class LessonListSerializer(serializers.ModelSerializer):
    """Serializer para listar lecciones."""
    
    lesson_type_display = serializers.CharField(source='get_lesson_type_display', read_only=True)
    completion_criteria_display = serializers.CharField(source='get_completion_criteria_display', read_only=True)
    
    # Información del progreso del usuario
    user_progress = serializers.SerializerMethodField()
    
    class Meta:
        model = Lesson
        fields = [
            'id', 'title', 'slug', 'description', 'lesson_type', 'lesson_type_display',
            'order', 'estimated_duration', 'is_published', 'is_preview',
            'is_mandatory', 'completion_criteria', 'completion_criteria_display',
            'fore_tokens_reward', 'has_quiz', 'user_progress'
        ]
        read_only_fields = ['id', 'slug']
    
    def get_user_progress(self, obj):
        """Obtener progreso del usuario en esta lección."""
        request = self.context.get('request')
        if request and request.user.is_authenticated and request.user.is_student():
            try:
                enrollment = obj.course.enrollments.get(student=request.user)
                progress = obj.student_progress.get(enrollment=enrollment)
                return {
                    'is_completed': progress.is_completed,
                    'completion_percentage': progress.completion_percentage,
                    'time_spent': progress.time_spent
                }
            except (CourseEnrollment.DoesNotExist, LessonProgress.DoesNotExist):
                return None
        return None


class LessonDetailSerializer(serializers.ModelSerializer):
    """Serializer para detalles completos de la lección."""
    
    course = CourseListSerializer(read_only=True)
    lesson_type_display = serializers.CharField(source='get_lesson_type_display', read_only=True)
    completion_criteria_display = serializers.CharField(source='get_completion_criteria_display', read_only=True)
    
    # Navegación
    next_lesson = serializers.SerializerMethodField()
    previous_lesson = serializers.SerializerMethodField()
    
    # Progreso del usuario
    user_progress = serializers.SerializerMethodField()
    can_access = serializers.SerializerMethodField()
    
    class Meta:
        model = Lesson
        fields = [
            'id', 'title', 'slug', 'description', 'course',
            'lesson_type', 'lesson_type_display', 'content',
            'video_url', 'video_duration', 'audio_file', 'attachments',
            'order', 'estimated_duration', 'is_published', 'is_preview',
            'is_mandatory', 'completion_criteria', 'completion_criteria_display',
            'min_completion_time', 'fore_tokens_reward', 'has_quiz',
            'next_lesson', 'previous_lesson', 'user_progress', 'can_access',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'slug', 'created_at', 'updated_at']
    
    def get_next_lesson(self, obj):
        """Obtener información de la siguiente lección."""
        next_lesson = obj.next_lesson
        if next_lesson:
            return {
                'id': next_lesson.id,
                'title': next_lesson.title,
                'slug': next_lesson.slug
            }
        return None
    
    def get_previous_lesson(self, obj):
        """Obtener información de la lección anterior."""
        previous_lesson = obj.previous_lesson
        if previous_lesson:
            return {
                'id': previous_lesson.id,
                'title': previous_lesson.title,
                'slug': previous_lesson.slug
            }
        return None
    
    def get_user_progress(self, obj):
        """Obtener progreso detallado del usuario."""
        request = self.context.get('request')
        if request and request.user.is_authenticated and request.user.is_student():
            try:
                enrollment = obj.course.enrollments.get(student=request.user)
                progress = obj.student_progress.get(enrollment=enrollment)
                return {
                    'is_completed': progress.is_completed,
                    'completion_percentage': progress.completion_percentage,
                    'time_spent': progress.time_spent,
                    'started_at': progress.started_at,
                    'completed_at': progress.completed_at,
                    'notes': progress.notes
                }
            except (CourseEnrollment.DoesNotExist, LessonProgress.DoesNotExist):
                return None
        return None
    
    def get_can_access(self, obj):
        """Verificar si el usuario puede acceder a esta lección."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            can_access, message = obj.can_access(request.user)
            return {'can_access': can_access, 'message': message}
        return {'can_access': False, 'message': 'Debes iniciar sesión'}


class QuestionOptionSerializer(serializers.ModelSerializer):
    """Serializer para opciones de preguntas (sin respuesta correcta)."""
    
    options = serializers.SerializerMethodField()
    
    class Meta:
        model = Question
        fields = [
            'id', 'question_text', 'question_type', 'points', 'order',
            'image', 'audio_file', 'options'
        ]
        read_only_fields = ['id']
    
    def get_options(self, obj):
        """Obtener opciones de la pregunta sin revelar la respuesta correcta."""
        if obj.question_type == 'multiple_choice':
            return obj.get_options()
        elif obj.question_type == 'true_false':
            return [('True', 'Verdadero'), ('False', 'Falso')]
        return []


class QuizDetailSerializer(serializers.ModelSerializer):
    """Serializer para detalles del quiz."""
    
    lesson = LessonListSerializer(read_only=True)
    questions = QuestionOptionSerializer(many=True, read_only=True)
    
    # Información del usuario
    user_attempts = serializers.SerializerMethodField()
    can_attempt = serializers.SerializerMethodField()
    
    class Meta:
        model = Quiz
        fields = [
            'id', 'title', 'description', 'lesson',
            'time_limit', 'max_attempts', 'passing_score',
            'randomize_questions', 'show_results_immediately', 'allow_review',
            'fore_tokens_reward', 'total_questions', 'average_score',
            'questions', 'user_attempts', 'can_attempt',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'total_questions', 'average_score', 'created_at', 'updated_at']
    
    def get_user_attempts(self, obj):
        """Obtener intentos del usuario actual."""
        request = self.context.get('request')
        if request and request.user.is_authenticated and request.user.is_student():
            try:
                enrollment = obj.lesson.course.enrollments.get(student=request.user)
                attempts = obj.attempts.filter(enrollment=enrollment).order_by('-started_at')
                return [{
                    'id': attempt.id,
                    'attempt_number': attempt.attempt_number,
                    'score': attempt.score,
                    'is_passed': attempt.is_passed,
                    'is_completed': attempt.is_completed,
                    'started_at': attempt.started_at,
                    'completed_at': attempt.completed_at
                } for attempt in attempts[:5]]  # Últimos 5 intentos
            except CourseEnrollment.DoesNotExist:
                return []
        return []
    
    def get_can_attempt(self, obj):
        """Verificar si puede hacer un nuevo intento."""
        request = self.context.get('request')
        if request and request.user.is_authenticated and request.user.is_student():
            try:
                enrollment = obj.lesson.course.enrollments.get(student=request.user)
                last_attempt = obj.attempts.filter(enrollment=enrollment).last()
                
                if not last_attempt:
                    return {'can_attempt': True, 'message': 'Primer intento disponible'}
                
                can_retake, message = last_attempt.can_retake()
                return {'can_attempt': can_retake, 'message': message}
            except CourseEnrollment.DoesNotExist:
                return {'can_attempt': False, 'message': 'No estás inscrito en el curso'}
        return {'can_attempt': False, 'message': 'Debes iniciar sesión'}


class QuizSubmissionSerializer(serializers.Serializer):
    """Serializer para enviar respuestas del quiz."""
    
    answers = serializers.JSONField(
        help_text="Respuestas en formato: {'question_id': 'answer', ...}"
    )
    
    def validate_answers(self, value):
        """Validar formato de respuestas."""
        if not isinstance(value, dict):
            raise serializers.ValidationError("Las respuestas deben ser un objeto JSON")
        
        # Validar que todas las claves sean IDs de preguntas válidas
        quiz = self.context.get('quiz')
        if quiz:
            valid_question_ids = set(str(q.id) for q in quiz.questions.all())
            provided_question_ids = set(value.keys())
            
            if not provided_question_ids.issubset(valid_question_ids):
                invalid_ids = provided_question_ids - valid_question_ids
                raise serializers.ValidationError(
                    f"IDs de preguntas inválidos: {list(invalid_ids)}"
                )
        
        return value


class CourseEnrollmentSerializer(serializers.ModelSerializer):
    """Serializer para inscripciones en cursos."""
    
    student = serializers.StringRelatedField(read_only=True)
    course = CourseListSerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = CourseEnrollment
        fields = [
            'id', 'student', 'course', 'status', 'status_display',
            'progress_percentage', 'final_score', 'fore_tokens_earned',
            'certificate_issued', 'certificate_url',
            'enrolled_at', 'completed_at', 'last_accessed'
        ]
        read_only_fields = [
            'id', 'student', 'progress_percentage', 'final_score',
            'fore_tokens_earned', 'certificate_issued', 'certificate_url',
            'enrolled_at', 'completed_at', 'last_accessed'
        ]


class LessonProgressSerializer(serializers.ModelSerializer):
    """Serializer para progreso de lecciones."""
    
    lesson = LessonListSerializer(read_only=True)
    
    class Meta:
        model = LessonProgress
        fields = [
            'id', 'lesson', 'is_completed', 'completion_percentage',
            'time_spent', 'started_at', 'completed_at', 'notes'
        ]
        read_only_fields = [
            'id', 'started_at', 'completed_at'
        ]


class QuizAttemptSerializer(serializers.ModelSerializer):
    """Serializer para intentos de cuestionarios."""
    
    quiz = serializers.StringRelatedField(read_only=True)
    
    class Meta:
        model = QuizAttempt
        fields = [
            'id', 'quiz', 'attempt_number', 'score', 'is_passed',
            'is_completed', 'time_taken', 'started_at', 'completed_at'
        ]
        read_only_fields = [
            'id', 'attempt_number', 'score', 'is_passed', 'is_completed',
            'time_taken', 'started_at', 'completed_at'
        ]