"""
Configuración del admin de Django para los modelos de cursos.

Este módulo configura las interfaces administrativas para:
- Cursos
- Lecciones  
- Cuestionarios
- Preguntas
- Progreso de estudiantes
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe

from .models import (
    Course, Lesson, Quiz, Question,
    CourseEnrollment, LessonProgress, QuizAttempt
)


class LessonInline(admin.TabularInline):
    """Inline para mostrar lecciones dentro del curso."""
    model = Lesson
    extra = 0
    fields = ['title', 'lesson_type', 'order', 'estimated_duration', 'is_published']
    readonly_fields = ['slug']
    ordering = ['order']


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    """Administración de cursos."""
    
    list_display = [
        'title', 'instructor', 'level', 'status', 'price', 
        'total_lessons', 'total_enrollments', 'average_rating',
        'is_featured', 'created_at'
    ]
    
    list_filter = [
        'level', 'status', 'is_featured', 'language',
        'created_at', 'instructor'
    ]
    
    search_fields = ['title', 'description', 'instructor__username', 'instructor__email']
    
    readonly_fields = [
        'slug', 'total_lessons', 'total_enrollments', 
        'average_rating', 'created_at', 'updated_at'
    ]
    
    prepopulated_fields = {'slug': ('title',)}
    
    fieldsets = (
        ('Información Básica', {
            'fields': (
                'title', 'slug', 'description', 'short_description'
            )
        }),
        ('Configuración del Curso', {
            'fields': (
                'instructor', 'level', 'language', 'estimated_hours'
            )
        }),
        ('Precios y Recompensas', {
            'fields': (
                'price', 'fore_tokens_reward'
            )
        }),
        ('Multimedia', {
            'fields': (
                'thumbnail', 'trailer_video'
            ),
            'classes': ('collapse',)
        }),
        ('Configuración Avanzada', {
            'fields': (
                'status', 'is_featured', 'max_enrollments',
                'enrollment_start_date', 'enrollment_end_date'
            ),
            'classes': ('collapse',)
        }),
        ('SEO', {
            'fields': (
                'meta_title', 'meta_description'
            ),
            'classes': ('collapse',)
        }),
        ('Estadísticas', {
            'fields': (
                'total_lessons', 'total_enrollments', 'average_rating'
            ),
            'classes': ('collapse',)
        }),
        ('Metadatos', {
            'fields': (
                'created_at', 'updated_at'
            ),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [LessonInline]
    
    def get_queryset(self, request):
        """Optimizar consultas."""
        return super().get_queryset(request).select_related('instructor')


class QuestionInline(admin.TabularInline):
    """Inline para mostrar preguntas dentro del quiz."""
    model = Question
    extra = 0
    fields = ['question_text', 'question_type', 'correct_answer', 'points', 'order']
    ordering = ['order']


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    """Administración de lecciones."""
    
    list_display = [
        'title', 'course', 'lesson_type', 'order', 
        'estimated_duration', 'is_published', 'is_preview'
    ]
    
    list_filter = [
        'lesson_type', 'is_published', 'is_preview', 
        'is_mandatory', 'course__level'
    ]
    
    search_fields = ['title', 'description', 'course__title']
    
    readonly_fields = ['slug', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Información Básica', {
            'fields': (
                'course', 'title', 'slug', 'description'
            )
        }),
        ('Configuración', {
            'fields': (
                'lesson_type', 'order', 'estimated_duration',
                'is_published', 'is_preview', 'is_mandatory'
            )
        }),
        ('Contenido', {
            'fields': (
                'content',
            )
        }),
        ('Multimedia', {
            'fields': (
                'video_url', 'video_duration', 'audio_file', 'attachments'
            ),
            'classes': ('collapse',)
        }),
        ('Configuración Avanzada', {
            'fields': (
                'completion_criteria', 'min_completion_time',
                'has_quiz', 'fore_tokens_reward'
            ),
            'classes': ('collapse',)
        }),
        ('Metadatos', {
            'fields': (
                'created_at', 'updated_at'
            ),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        """Optimizar consultas."""
        return super().get_queryset(request).select_related('course')


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    """Administración de cuestionarios."""
    
    list_display = [
        'title', 'lesson', 'total_questions', 'passing_score',
        'max_attempts', 'time_limit', 'average_score'
    ]
    
    list_filter = [
        'lesson__course', 'randomize_questions', 
        'show_results_immediately', 'allow_review'
    ]
    
    search_fields = ['title', 'description', 'lesson__title']
    
    readonly_fields = ['total_questions', 'average_score', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Información Básica', {
            'fields': (
                'lesson', 'title', 'description'
            )
        }),
        ('Configuración', {
            'fields': (
                'time_limit', 'max_attempts', 'passing_score'
            )
        }),
        ('Opciones', {
            'fields': (
                'randomize_questions', 'show_results_immediately', 
                'allow_review', 'fore_tokens_reward'
            )
        }),
        ('Estadísticas', {
            'fields': (
                'total_questions', 'average_score'
            ),
            'classes': ('collapse',)
        }),
        ('Metadatos', {
            'fields': (
                'created_at', 'updated_at'
            ),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [QuestionInline]
    
    def get_queryset(self, request):
        """Optimizar consultas."""
        return super().get_queryset(request).select_related('lesson', 'lesson__course')


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    """Administración de preguntas."""
    
    list_display = [
        'quiz', 'question_text_short', 'question_type', 
        'points', 'order', 'is_case_sensitive'
    ]
    
    list_filter = [
        'question_type', 'is_case_sensitive', 'partial_credit',
        'quiz__lesson__course'
    ]
    
    search_fields = ['question_text', 'quiz__title']
    
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Información Básica', {
            'fields': (
                'quiz', 'question_text', 'question_type', 
                'points', 'order'
            )
        }),
        ('Multimedia', {
            'fields': (
                'image', 'audio_file'
            ),
            'classes': ('collapse',)
        }),
        ('Opciones (Solo para opción múltiple)', {
            'fields': (
                'option_a', 'option_b', 'option_c', 'option_d'
            ),
            'classes': ('collapse',)
        }),
        ('Respuesta', {
            'fields': (
                'correct_answer', 'explanation'
            )
        }),
        ('Configuración Avanzada', {
            'fields': (
                'is_case_sensitive', 'partial_credit'
            ),
            'classes': ('collapse',)
        }),
        ('Metadatos', {
            'fields': (
                'created_at', 'updated_at'
            ),
            'classes': ('collapse',)
        }),
    )
    
    def question_text_short(self, obj):
        """Mostrar versión corta del texto de la pregunta."""
        return obj.question_text[:50] + "..." if len(obj.question_text) > 50 else obj.question_text
    question_text_short.short_description = "Texto de la pregunta"
    
    def get_queryset(self, request):
        """Optimizar consultas."""
        return super().get_queryset(request).select_related('quiz', 'quiz__lesson')


@admin.register(CourseEnrollment)
class CourseEnrollmentAdmin(admin.ModelAdmin):
    """Administración de inscripciones."""
    
    list_display = [
        'student', 'course', 'status', 'progress_percentage',
        'final_score', 'fore_tokens_earned', 'enrolled_at'
    ]
    
    list_filter = [
        'status', 'certificate_issued', 'course__level',
        'enrolled_at', 'completed_at'
    ]
    
    search_fields = [
        'student__username', 'student__email', 'student__first_name',
        'student__last_name', 'course__title'
    ]
    
    readonly_fields = [
        'enrolled_at', 'last_accessed', 'progress_percentage'
    ]
    
    fieldsets = (
        ('Información Básica', {
            'fields': (
                'student', 'course', 'status'
            )
        }),
        ('Progreso', {
            'fields': (
                'progress_percentage', 'final_score', 'fore_tokens_earned'
            )
        }),
        ('Certificación', {
            'fields': (
                'certificate_issued', 'certificate_url'
            ),
            'classes': ('collapse',)
        }),
        ('Fechas', {
            'fields': (
                'enrolled_at', 'completed_at', 'last_accessed'
            ),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['recalculate_progress']
    
    def recalculate_progress(self, request, queryset):
        """Recalcular progreso para las inscripciones seleccionadas."""
        count = 0
        for enrollment in queryset:
            enrollment.calculate_progress()
            count += 1
        
        self.message_user(
            request, 
            f"Se recalculó el progreso de {count} inscripciones."
        )
    recalculate_progress.short_description = "Recalcular progreso"
    
    def get_queryset(self, request):
        """Optimizar consultas."""
        return super().get_queryset(request).select_related('student', 'course')


@admin.register(LessonProgress)
class LessonProgressAdmin(admin.ModelAdmin):
    """Administración de progreso de lecciones."""
    
    list_display = [
        'enrollment_info', 'lesson', 'completion_percentage',
        'is_completed', 'time_spent', 'last_accessed'
    ]
    
    list_filter = [
        'is_completed', 'lesson__lesson_type',
        'started_at', 'completed_at'
    ]
    
    search_fields = [
        'enrollment__student__username', 'enrollment__student__email',
        'lesson__title', 'enrollment__course__title'
    ]
    
    readonly_fields = ['started_at', 'completed_at', 'last_accessed']
    
    def enrollment_info(self, obj):
        """Mostrar información de la inscripción."""
        return f"{obj.enrollment.student.get_full_name()} - {obj.enrollment.course.title}"
    enrollment_info.short_description = "Estudiante - Curso"
    
    def get_queryset(self, request):
        """Optimizar consultas."""
        return super().get_queryset(request).select_related(
            'enrollment', 'enrollment__student', 'enrollment__course', 'lesson'
        )


@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    """Administración de intentos de cuestionarios."""
    
    list_display = [
        'enrollment_info', 'quiz', 'attempt_number',
        'score', 'is_passed', 'is_completed', 'started_at'
    ]
    
    list_filter = [
        'is_passed', 'is_completed', 'quiz__lesson__course',
        'started_at', 'completed_at'
    ]
    
    search_fields = [
        'enrollment__student__username', 'enrollment__student__email',
        'quiz__title', 'enrollment__course__title'
    ]
    
    readonly_fields = [
        'attempt_number', 'started_at', 'completed_at', 'time_taken'
    ]
    
    fieldsets = (
        ('Información Básica', {
            'fields': (
                'enrollment', 'quiz', 'attempt_number'
            )
        }),
        ('Resultados', {
            'fields': (
                'score', 'is_passed', 'is_completed'
            )
        }),
        ('Respuestas', {
            'fields': (
                'answers',
            ),
            'classes': ('collapse',)
        }),
        ('Tiempos', {
            'fields': (
                'time_taken', 'started_at', 'completed_at'
            ),
            'classes': ('collapse',)
        }),
    )
    
    def enrollment_info(self, obj):
        """Mostrar información de la inscripción."""
        return f"{obj.enrollment.student.get_full_name()} - {obj.enrollment.course.title}"
    enrollment_info.short_description = "Estudiante - Curso"
    
    def get_queryset(self, request):
        """Optimizar consultas."""
        return super().get_queryset(request).select_related(
            'enrollment', 'enrollment__student', 'enrollment__course', 'quiz'
        )
