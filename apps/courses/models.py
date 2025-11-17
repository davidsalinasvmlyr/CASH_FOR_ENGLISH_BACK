"""
Modelos para el sistema de cursos y contenido educativo.

Este módulo contiene los modelos para:
- Cursos
- Lecciones
- Cuestionarios (Quizzes)
- Preguntas
- Progreso del estudiante
"""

from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _


class CourseLevel(models.TextChoices):
    """Niveles de dificultad de los cursos."""
    BEGINNER = 'beginner', _('Principiante')
    ELEMENTARY = 'elementary', _('Elemental')
    INTERMEDIATE = 'intermediate', _('Intermedio')
    UPPER_INTERMEDIATE = 'upper_intermediate', _('Intermedio Superior')
    ADVANCED = 'advanced', _('Avanzado')
    PROFICIENCY = 'proficiency', _('Competencia')


class CourseStatus(models.TextChoices):
    """Estados del curso."""
    DRAFT = 'draft', _('Borrador')
    PUBLISHED = 'published', _('Publicado')
    ARCHIVED = 'archived', _('Archivado')


class Course(models.Model):
    """
    Modelo para representar un curso de inglés.
    
    Cada curso puede tener múltiples lecciones y está asociado
    con un instructor. Los estudiantes pueden inscribirse en cursos.
    """
    
    # Información básica del curso
    title = models.CharField(
        max_length=200,
        verbose_name=_('Título'),
        help_text=_('Título del curso')
    )
    
    slug = models.SlugField(
        max_length=250,
        unique=True,
        blank=True,
        verbose_name=_('Slug'),
        help_text=_('URL amigable generada automáticamente')
    )
    
    description = models.TextField(
        verbose_name=_('Descripción'),
        help_text=_('Descripción detallada del curso')
    )
    
    short_description = models.CharField(
        max_length=300,
        verbose_name=_('Descripción corta'),
        help_text=_('Resumen breve para mostrar en listas')
    )
    
    # Configuración del curso
    level = models.CharField(
        max_length=20,
        choices=CourseLevel.choices,
        default=CourseLevel.BEGINNER,
        verbose_name=_('Nivel'),
        help_text=_('Nivel de dificultad del curso')
    )
    
    language = models.CharField(
        max_length=10,
        default='en-US',
        verbose_name=_('Idioma'),
        help_text=_('Idioma principal del curso (ej: en-US, es-ES)')
    )
    
    # Instructor y precio
    instructor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='courses_taught',
        limit_choices_to={'role': 'teacher'},
        verbose_name=_('Instructor'),
        help_text=_('Profesor que imparte el curso')
    )
    
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(0)],
        verbose_name=_('Precio'),
        help_text=_('Precio del curso en USD')
    )
    
    fore_tokens_reward = models.PositiveIntegerField(
        default=100,
        verbose_name=_('FORE Tokens de Recompensa'),
        help_text=_('Tokens FORE que el estudiante recibe al completar el curso')
    )
    
    # Multimedia
    thumbnail = models.ImageField(
        upload_to='courses/thumbnails/',
        blank=True,
        null=True,
        verbose_name=_('Miniatura'),
        help_text=_('Imagen de portada del curso (recomendado: 1280x720px)')
    )
    
    trailer_video = models.URLField(
        blank=True,
        null=True,
        verbose_name=_('Video promocional'),
        help_text=_('URL del video promocional del curso')
    )
    
    # Configuración temporal
    estimated_hours = models.PositiveIntegerField(
        verbose_name=_('Horas estimadas'),
        help_text=_('Tiempo estimado para completar el curso')
    )
    
    max_enrollments = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name=_('Máximo de inscripciones'),
        help_text=_('Límite de estudiantes (vacío = sin límite)')
    )
    
    # Estado y fechas
    status = models.CharField(
        max_length=20,
        choices=CourseStatus.choices,
        default=CourseStatus.DRAFT,
        verbose_name=_('Estado')
    )
    
    is_featured = models.BooleanField(
        default=False,
        verbose_name=_('Curso destacado'),
        help_text=_('Marcar como curso destacado')
    )
    
    enrollment_start_date = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_('Inicio de inscripciones'),
        help_text=_('Fecha de inicio de inscripciones (vacío = siempre abierto)')
    )
    
    enrollment_end_date = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_('Fin de inscripciones'),
        help_text=_('Fecha de fin de inscripciones')
    )
    
    # Metadatos
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Fecha de creación')
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Última actualización')
    )
    
    # Campos de SEO
    meta_title = models.CharField(
        max_length=60,
        blank=True,
        verbose_name=_('Meta título'),
        help_text=_('Título para SEO (máx 60 caracteres)')
    )
    
    meta_description = models.CharField(
        max_length=160,
        blank=True,
        verbose_name=_('Meta descripción'),
        help_text=_('Descripción para SEO (máx 160 caracteres)')
    )
    
    # Estadísticas (se actualizan automáticamente)
    total_lessons = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Total de lecciones'),
        help_text=_('Número total de lecciones (calculado automáticamente)')
    )
    
    total_enrollments = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Total de inscripciones'),
        help_text=_('Número total de inscripciones (calculado automáticamente)')
    )
    
    average_rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(0), MaxValueValidator(5)],
        verbose_name=_('Calificación promedio'),
        help_text=_('Calificación promedio del curso (0-5 estrellas)')
    )
    
    class Meta:
        verbose_name = _('Curso')
        verbose_name_plural = _('Cursos')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['level', 'status']),
            models.Index(fields=['instructor', 'status']),
            models.Index(fields=['is_featured', 'status']),
        ]
    
    def __str__(self):
        return f"{self.title} ({self.get_level_display()})"
    
    def save(self, *args, **kwargs):
        """Generar slug automáticamente si no existe."""
        if not self.slug:
            self.slug = slugify(self.title)
            # Asegurar que el slug sea único
            counter = 1
            original_slug = self.slug
            while Course.objects.filter(slug=self.slug).exists():
                self.slug = f"{original_slug}-{counter}"
                counter += 1
        
        super().save(*args, **kwargs)
    
    @property
    def is_enrollment_open(self):
        """Verificar si las inscripciones están abiertas."""
        from django.utils import timezone
        now = timezone.now()
        
        if self.status != CourseStatus.PUBLISHED:
            return False
        
        if self.enrollment_start_date and now < self.enrollment_start_date:
            return False
            
        if self.enrollment_end_date and now > self.enrollment_end_date:
            return False
            
        if self.max_enrollments and self.total_enrollments >= self.max_enrollments:
            return False
            
        return True
    
    @property
    def completion_rate(self):
        """Calcular la tasa de finalización del curso."""
        if self.total_enrollments == 0:
            return 0
        
        completed_enrollments = self.enrollments.filter(
            status='completed'
        ).count()
        
        return (completed_enrollments / self.total_enrollments) * 100
    
    def get_absolute_url(self):
        """URL absoluta del curso."""
        from django.urls import reverse
        return reverse('courses:course-detail', kwargs={'slug': self.slug})
    
    def can_enroll(self, user):
        """Verificar si un usuario puede inscribirse en el curso."""
        if not self.is_enrollment_open:
            return False, "Las inscripciones no están abiertas"
        
        if hasattr(user, 'enrollments') and self.enrollments.filter(student=user).exists():
            return False, "Ya estás inscrito en este curso"
        
        if not user.is_student():
            return False, "Solo los estudiantes pueden inscribirse en cursos"
        
        return True, "Puede inscribirse"


class LessonType(models.TextChoices):
    """Tipos de lección."""
    VIDEO = 'video', _('Video')
    TEXT = 'text', _('Texto')
    AUDIO = 'audio', _('Audio')
    INTERACTIVE = 'interactive', _('Interactivo')
    QUIZ = 'quiz', _('Cuestionario')


class Lesson(models.Model):
    """
    Modelo para representar una lección dentro de un curso.
    
    Las lecciones son el contenido educativo principal que los
    estudiantes consumen para aprender.
    """
    
    # Relación con el curso
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='lessons',
        verbose_name=_('Curso')
    )
    
    # Información básica
    title = models.CharField(
        max_length=200,
        verbose_name=_('Título'),
        help_text=_('Título de la lección')
    )
    
    slug = models.SlugField(
        max_length=250,
        blank=True,
        verbose_name=_('Slug'),
        help_text=_('URL amigable generada automáticamente')
    )
    
    description = models.TextField(
        blank=True,
        verbose_name=_('Descripción'),
        help_text=_('Descripción de la lección')
    )
    
    # Tipo y contenido
    lesson_type = models.CharField(
        max_length=20,
        choices=LessonType.choices,
        default=LessonType.TEXT,
        verbose_name=_('Tipo de lección')
    )
    
    content = models.TextField(
        blank=True,
        verbose_name=_('Contenido'),
        help_text=_('Contenido de texto de la lección (Markdown soportado)')
    )
    
    # Multimedia
    video_url = models.URLField(
        blank=True,
        null=True,
        verbose_name=_('URL del video'),
        help_text=_('URL del video (YouTube, Vimeo, etc.)')
    )
    
    video_duration = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name=_('Duración del video (segundos)'),
        help_text=_('Duración en segundos')
    )
    
    audio_file = models.FileField(
        upload_to='lessons/audio/',
        blank=True,
        null=True,
        verbose_name=_('Archivo de audio'),
        help_text=_('Archivo de audio para la lección')
    )
    
    # Archivos adjuntos
    attachments = models.FileField(
        upload_to='lessons/attachments/',
        blank=True,
        null=True,
        verbose_name=_('Archivos adjuntos'),
        help_text=_('PDFs, documentos, etc.')
    )
    
    # Orden y configuración
    order = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Orden'),
        help_text=_('Orden de la lección dentro del curso')
    )
    
    estimated_duration = models.PositiveIntegerField(
        default=10,
        verbose_name=_('Duración estimada (minutos)'),
        help_text=_('Tiempo estimado para completar la lección')
    )
    
    is_preview = models.BooleanField(
        default=False,
        verbose_name=_('Vista previa'),
        help_text=_('Permitir vista previa gratuita de esta lección')
    )
    
    is_mandatory = models.BooleanField(
        default=True,
        verbose_name=_('Obligatoria'),
        help_text=_('La lección es obligatoria para completar el curso')
    )
    
    # Estados
    is_published = models.BooleanField(
        default=True,
        verbose_name=_('Publicada'),
        help_text=_('Lección visible para los estudiantes')
    )
    
    # Recompensas
    fore_tokens_reward = models.PositiveIntegerField(
        default=10,
        verbose_name=_('FORE Tokens de Recompensa'),
        help_text=_('Tokens FORE que el estudiante recibe al completar la lección')
    )
    
    # Metadatos
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Fecha de creación')
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Última actualización')
    )
    
    # Campos para interactividad
    has_quiz = models.BooleanField(
        default=False,
        verbose_name=_('Tiene cuestionario'),
        help_text=_('Esta lección incluye un cuestionario')
    )
    
    completion_criteria = models.CharField(
        max_length=20,
        choices=[
            ('view', _('Solo ver')),
            ('time', _('Tiempo mínimo')),
            ('quiz', _('Completar cuestionario')),
            ('interaction', _('Interacción requerida')),
        ],
        default='view',
        verbose_name=_('Criterio de finalización')
    )
    
    min_completion_time = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name=_('Tiempo mínimo (segundos)'),
        help_text=_('Tiempo mínimo que debe pasar en la lección')
    )
    
    class Meta:
        verbose_name = _('Lección')
        verbose_name_plural = _('Lecciones')
        ordering = ['course', 'order']
        unique_together = [['course', 'order']]
        indexes = [
            models.Index(fields=['course', 'order']),
            models.Index(fields=['course', 'is_published']),
            models.Index(fields=['lesson_type']),
        ]
    
    def __str__(self):
        return f"{self.course.title} - {self.title}"
    
    def save(self, *args, **kwargs):
        """Generar slug automáticamente si no existe."""
        if not self.slug:
            self.slug = slugify(f"{self.course.slug}-{self.title}")
            # Asegurar que el slug sea único dentro del curso
            counter = 1
            original_slug = self.slug
            while Lesson.objects.filter(
                course=self.course, 
                slug=self.slug
            ).exclude(pk=self.pk).exists():
                self.slug = f"{original_slug}-{counter}"
                counter += 1
        
        super().save(*args, **kwargs)
    
    @property
    def next_lesson(self):
        """Obtener la siguiente lección."""
        return Lesson.objects.filter(
            course=self.course,
            order__gt=self.order,
            is_published=True
        ).first()
    
    @property
    def previous_lesson(self):
        """Obtener la lección anterior."""
        return Lesson.objects.filter(
            course=self.course,
            order__lt=self.order,
            is_published=True
        ).last()
    
    def get_absolute_url(self):
        """URL absoluta de la lección."""
        from django.urls import reverse
        return reverse('courses:lesson-detail', kwargs={
            'course_slug': self.course.slug,
            'lesson_slug': self.slug
        })
    
    def can_access(self, user):
        """Verificar si un usuario puede acceder a esta lección."""
        # Vista previa disponible para todos
        if self.is_preview:
            return True, "Vista previa disponible"
        
        # Verificar inscripción en el curso
        if not hasattr(user, 'enrollments'):
            return False, "Debes inscribirte en el curso"
        
        enrollment = self.course.enrollments.filter(student=user).first()
        if not enrollment:
            return False, "No estás inscrito en este curso"
        
        if enrollment.status != 'active':
            return False, "Tu inscripción no está activa"
        
        return True, "Acceso permitido"


class Quiz(models.Model):
    """
    Modelo para representar un cuestionario asociado a una lección.
    
    Los cuestionarios evalúan el conocimiento del estudiante
    y pueden ser requeridos para avanzar.
    """
    
    # Relación con la lección
    lesson = models.OneToOneField(
        Lesson,
        on_delete=models.CASCADE,
        related_name='quiz',
        verbose_name=_('Lección')
    )
    
    # Información básica
    title = models.CharField(
        max_length=200,
        verbose_name=_('Título'),
        help_text=_('Título del cuestionario')
    )
    
    description = models.TextField(
        blank=True,
        verbose_name=_('Descripción'),
        help_text=_('Instrucciones o descripción del cuestionario')
    )
    
    # Configuración del cuestionario
    time_limit = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name=_('Tiempo límite (minutos)'),
        help_text=_('Tiempo límite en minutos (vacío = sin límite)')
    )
    
    max_attempts = models.PositiveIntegerField(
        default=3,
        validators=[MinValueValidator(1)],
        verbose_name=_('Intentos máximos'),
        help_text=_('Número máximo de intentos permitidos')
    )
    
    passing_score = models.PositiveIntegerField(
        default=70,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name=_('Puntuación mínima (%)'),
        help_text=_('Porcentaje mínimo para aprobar el cuestionario')
    )
    
    randomize_questions = models.BooleanField(
        default=True,
        verbose_name=_('Aleatorizar preguntas'),
        help_text=_('Mostrar las preguntas en orden aleatorio')
    )
    
    show_results_immediately = models.BooleanField(
        default=True,
        verbose_name=_('Mostrar resultados inmediatamente'),
        help_text=_('Mostrar resultados al completar el cuestionario')
    )
    
    allow_review = models.BooleanField(
        default=True,
        verbose_name=_('Permitir revisión'),
        help_text=_('Permitir revisar respuestas después de completar')
    )
    
    # Recompensas
    fore_tokens_reward = models.PositiveIntegerField(
        default=20,
        verbose_name=_('FORE Tokens de Recompensa'),
        help_text=_('Tokens FORE por aprobar el cuestionario')
    )
    
    # Estadísticas
    total_questions = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Total de preguntas'),
        help_text=_('Número total de preguntas (calculado automáticamente)')
    )
    
    average_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00,
        verbose_name=_('Puntuación promedio'),
        help_text=_('Puntuación promedio de todos los intentos')
    )
    
    # Metadatos
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Fecha de creación')
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Última actualización')
    )
    
    class Meta:
        verbose_name = _('Cuestionario')
        verbose_name_plural = _('Cuestionarios')
        ordering = ['lesson__order']
    
    def __str__(self):
        return f"{self.lesson.title} - {self.title}"
    
    def calculate_score(self, answers):
        """Calcular la puntuación de un intento."""
        if not self.questions.exists():
            return 0
        
        correct_answers = 0
        total_questions = self.questions.count()
        
        for question in self.questions.all():
            user_answer = answers.get(str(question.id))
            if question.check_answer(user_answer):
                correct_answers += 1
        
        return (correct_answers / total_questions) * 100
    
    def is_passing_score(self, score):
        """Verificar si una puntuación es aprobatoria."""
        return score >= self.passing_score


class QuestionType(models.TextChoices):
    """Tipos de preguntas."""
    MULTIPLE_CHOICE = 'multiple_choice', _('Opción múltiple')
    TRUE_FALSE = 'true_false', _('Verdadero/Falso')
    SHORT_ANSWER = 'short_answer', _('Respuesta corta')
    ESSAY = 'essay', _('Ensayo')
    FILL_BLANK = 'fill_blank', _('Llenar espacios')
    MATCHING = 'matching', _('Emparejar')


class Question(models.Model):
    """
    Modelo para representar una pregunta dentro de un cuestionario.
    
    Soporta múltiples tipos de preguntas con diferentes
    métodos de evaluación.
    """
    
    # Relación con el cuestionario
    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.CASCADE,
        related_name='questions',
        verbose_name=_('Cuestionario')
    )
    
    # Información básica
    question_text = models.TextField(
        verbose_name=_('Texto de la pregunta'),
        help_text=_('El enunciado de la pregunta')
    )
    
    question_type = models.CharField(
        max_length=20,
        choices=QuestionType.choices,
        default=QuestionType.MULTIPLE_CHOICE,
        verbose_name=_('Tipo de pregunta')
    )
    
    # Configuración
    points = models.PositiveIntegerField(
        default=1,
        verbose_name=_('Puntos'),
        help_text=_('Puntos que vale esta pregunta')
    )
    
    order = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Orden'),
        help_text=_('Orden de la pregunta en el cuestionario')
    )
    
    # Multimedia
    image = models.ImageField(
        upload_to='questions/images/',
        blank=True,
        null=True,
        verbose_name=_('Imagen'),
        help_text=_('Imagen asociada a la pregunta')
    )
    
    audio_file = models.FileField(
        upload_to='questions/audio/',
        blank=True,
        null=True,
        verbose_name=_('Audio'),
        help_text=_('Archivo de audio para preguntas de listening')
    )
    
    # Opciones y respuestas (para preguntas de opción múltiple)
    option_a = models.CharField(
        max_length=500,
        blank=True,
        verbose_name=_('Opción A')
    )
    
    option_b = models.CharField(
        max_length=500,
        blank=True,
        verbose_name=_('Opción B')
    )
    
    option_c = models.CharField(
        max_length=500,
        blank=True,
        verbose_name=_('Opción C')
    )
    
    option_d = models.CharField(
        max_length=500,
        blank=True,
        verbose_name=_('Opción D')
    )
    
    # Respuesta correcta
    correct_answer = models.CharField(
        max_length=1000,
        verbose_name=_('Respuesta correcta'),
        help_text=_('Respuesta correcta o clave de respuesta')
    )
    
    # Para preguntas de opción múltiple: A, B, C, D
    # Para verdadero/falso: True, False
    # Para respuesta corta: texto exacto o palabras clave separadas por comas
    
    # Explicación
    explanation = models.TextField(
        blank=True,
        verbose_name=_('Explicación'),
        help_text=_('Explicación de la respuesta correcta')
    )
    
    # Configuración avanzada
    is_case_sensitive = models.BooleanField(
        default=False,
        verbose_name=_('Sensible a mayúsculas'),
        help_text=_('Para respuestas de texto, considerar mayúsculas/minúsculas')
    )
    
    partial_credit = models.BooleanField(
        default=False,
        verbose_name=_('Crédito parcial'),
        help_text=_('Permitir crédito parcial en respuestas aproximadas')
    )
    
    # Metadatos
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Fecha de creación')
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Última actualización')
    )
    
    class Meta:
        verbose_name = _('Pregunta')
        verbose_name_plural = _('Preguntas')
        ordering = ['quiz', 'order']
        unique_together = [['quiz', 'order']]
        indexes = [
            models.Index(fields=['quiz', 'order']),
            models.Index(fields=['question_type']),
        ]
    
    def __str__(self):
        return f"{self.quiz.title} - Pregunta {self.order + 1}"
    
    def get_options(self):
        """Obtener las opciones como lista."""
        options = []
        if self.option_a:
            options.append(('A', self.option_a))
        if self.option_b:
            options.append(('B', self.option_b))
        if self.option_c:
            options.append(('C', self.option_c))
        if self.option_d:
            options.append(('D', self.option_d))
        return options
    
    def check_answer(self, user_answer):
        """Verificar si la respuesta del usuario es correcta."""
        if not user_answer:
            return False
        
        user_answer = str(user_answer).strip()
        
        if self.question_type == QuestionType.MULTIPLE_CHOICE:
            return user_answer.upper() == self.correct_answer.upper()
        
        elif self.question_type == QuestionType.TRUE_FALSE:
            return user_answer.lower() == self.correct_answer.lower()
        
        elif self.question_type == QuestionType.SHORT_ANSWER:
            if not self.is_case_sensitive:
                user_answer = user_answer.lower()
                correct_answer = self.correct_answer.lower()
            else:
                correct_answer = self.correct_answer
            
            # Permitir múltiples respuestas correctas separadas por comas
            correct_answers = [ans.strip() for ans in correct_answer.split(',')]
            return user_answer in correct_answers
        
        elif self.question_type == QuestionType.FILL_BLANK:
            # Para llenar espacios, verificar palabras clave
            if not self.is_case_sensitive:
                user_answer = user_answer.lower()
                correct_answer = self.correct_answer.lower()
            else:
                correct_answer = self.correct_answer
            
            keywords = [kw.strip() for kw in correct_answer.split(',')]
            return any(keyword in user_answer for keyword in keywords)
        
        # Para ensayos y emparejar, requerirán evaluación manual
        return False


# Modelos para tracking del progreso del estudiante

class EnrollmentStatus(models.TextChoices):
    """Estados de inscripción."""
    ACTIVE = 'active', _('Activa')
    COMPLETED = 'completed', _('Completada')
    DROPPED = 'dropped', _('Abandonada')
    SUSPENDED = 'suspended', _('Suspendida')


class CourseEnrollment(models.Model):
    """
    Modelo para representar la inscripción de un estudiante en un curso.
    
    Rastrea el progreso general y el estado de la inscripción.
    """
    
    # Relaciones
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='enrollments',
        limit_choices_to={'role': 'student'},
        verbose_name=_('Estudiante')
    )
    
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='enrollments',
        verbose_name=_('Curso')
    )
    
    # Estado y progreso
    status = models.CharField(
        max_length=20,
        choices=EnrollmentStatus.choices,
        default=EnrollmentStatus.ACTIVE,
        verbose_name=_('Estado')
    )
    
    progress_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name=_('Progreso (%)'),
        help_text=_('Porcentaje de finalización del curso')
    )
    
    # Fechas importantes
    enrolled_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Fecha de inscripción')
    )
    
    completed_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_('Fecha de finalización')
    )
    
    last_accessed = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Último acceso')
    )
    
    # Puntuación y certificación
    final_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name=_('Puntuación final')
    )
    
    certificate_issued = models.BooleanField(
        default=False,
        verbose_name=_('Certificado emitido')
    )
    
    certificate_url = models.URLField(
        blank=True,
        null=True,
        verbose_name=_('URL del certificado')
    )
    
    # Tokens FORE ganados
    fore_tokens_earned = models.PositiveIntegerField(
        default=0,
        verbose_name=_('FORE Tokens ganados')
    )
    
    class Meta:
        verbose_name = _('Inscripción en Curso')
        verbose_name_plural = _('Inscripciones en Cursos')
        unique_together = [['student', 'course']]
        ordering = ['-enrolled_at']
        indexes = [
            models.Index(fields=['student', 'status']),
            models.Index(fields=['course', 'status']),
            models.Index(fields=['enrolled_at']),
        ]
    
    def __str__(self):
        return f"{self.student.get_full_name()} - {self.course.title}"
    
    def calculate_progress(self):
        """Calcular el progreso del estudiante en el curso."""
        total_lessons = self.course.lessons.filter(
            is_published=True,
            is_mandatory=True
        ).count()
        
        if total_lessons == 0:
            return 0
        
        completed_lessons = self.lesson_progress.filter(
            lesson__is_published=True,
            lesson__is_mandatory=True,
            is_completed=True
        ).count()
        
        progress = (completed_lessons / total_lessons) * 100
        
        # Actualizar el progreso
        self.progress_percentage = progress
        self.save(update_fields=['progress_percentage'])
        
        # Marcar como completado si llegó al 100%
        if progress >= 100 and self.status == EnrollmentStatus.ACTIVE:
            self.complete_course()
        
        return progress
    
    def complete_course(self):
        """Marcar el curso como completado."""
        from django.utils import timezone
        
        self.status = EnrollmentStatus.COMPLETED
        self.completed_at = timezone.now()
        
        # Calcular puntuación final (promedio de quizzes)
        quiz_attempts = QuizAttempt.objects.filter(
            enrollment=self,
            is_completed=True
        ).values('quiz').annotate(
            best_score=models.Max('score')
        )
        
        if quiz_attempts:
            total_score = sum(attempt['best_score'] for attempt in quiz_attempts)
            self.final_score = total_score / len(quiz_attempts)
        
        # Otorgar tokens FORE del curso
        self.fore_tokens_earned += self.course.fore_tokens_reward
        
        self.save()
        
        # TODO: Generar certificado
        # self.generate_certificate()
    
    def get_next_lesson(self):
        """Obtener la siguiente lección a completar."""
        completed_lesson_ids = self.lesson_progress.filter(
            is_completed=True
        ).values_list('lesson_id', flat=True)
        
        return self.course.lessons.filter(
            is_published=True
        ).exclude(
            id__in=completed_lesson_ids
        ).order_by('order').first()


class LessonProgress(models.Model):
    """
    Modelo para rastrear el progreso de un estudiante en una lección específica.
    """
    
    # Relaciones
    enrollment = models.ForeignKey(
        CourseEnrollment,
        on_delete=models.CASCADE,
        related_name='lesson_progress',
        verbose_name=_('Inscripción')
    )
    
    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.CASCADE,
        related_name='student_progress',
        verbose_name=_('Lección')
    )
    
    # Estado de progreso
    is_completed = models.BooleanField(
        default=False,
        verbose_name=_('Completada')
    )
    
    completion_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name=_('Progreso (%)')
    )
    
    # Tiempo en la lección
    time_spent = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Tiempo transcurrido (segundos)')
    )
    
    # Fechas
    started_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Iniciada en')
    )
    
    completed_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_('Completada en')
    )
    
    last_accessed = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Último acceso')
    )
    
    # Notas del estudiante
    notes = models.TextField(
        blank=True,
        verbose_name=_('Notas del estudiante')
    )
    
    class Meta:
        verbose_name = _('Progreso de Lección')
        verbose_name_plural = _('Progreso de Lecciones')
        unique_together = [['enrollment', 'lesson']]
        ordering = ['lesson__order']
        indexes = [
            models.Index(fields=['enrollment', 'is_completed']),
            models.Index(fields=['lesson', 'is_completed']),
        ]
    
    def __str__(self):
        return f"{self.enrollment.student.get_full_name()} - {self.lesson.title}"
    
    def mark_completed(self):
        """Marcar la lección como completada."""
        if not self.is_completed:
            from django.utils import timezone
            
            self.is_completed = True
            self.completion_percentage = 100.00
            self.completed_at = timezone.now()
            self.save()
            
            # Otorgar tokens FORE de la lección
            self.enrollment.fore_tokens_earned += self.lesson.fore_tokens_reward
            self.enrollment.save(update_fields=['fore_tokens_earned'])
            
            # Recalcular progreso del curso
            self.enrollment.calculate_progress()


class QuizAttempt(models.Model):
    """
    Modelo para representar un intento de cuestionario por parte de un estudiante.
    """
    
    # Relaciones
    enrollment = models.ForeignKey(
        CourseEnrollment,
        on_delete=models.CASCADE,
        related_name='quiz_attempts',
        verbose_name=_('Inscripción')
    )
    
    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.CASCADE,
        related_name='attempts',
        verbose_name=_('Cuestionario')
    )
    
    # Información del intento
    attempt_number = models.PositiveIntegerField(
        verbose_name=_('Número de intento')
    )
    
    score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name=_('Puntuación')
    )
    
    is_passed = models.BooleanField(
        default=False,
        verbose_name=_('Aprobado')
    )
    
    is_completed = models.BooleanField(
        default=False,
        verbose_name=_('Completado')
    )
    
    # Respuestas (JSON field para almacenar las respuestas)
    answers = models.JSONField(
        default=dict,
        verbose_name=_('Respuestas'),
        help_text=_('Respuestas del estudiante en formato JSON')
    )
    
    # Tiempo
    time_taken = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name=_('Tiempo empleado (segundos)')
    )
    
    # Fechas
    started_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Iniciado en')
    )
    
    completed_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_('Completado en')
    )
    
    class Meta:
        verbose_name = _('Intento de Cuestionario')
        verbose_name_plural = _('Intentos de Cuestionarios')
        unique_together = [['enrollment', 'quiz', 'attempt_number']]
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['enrollment', 'quiz']),
            models.Index(fields=['quiz', 'is_completed']),
        ]
    
    def __str__(self):
        return f"{self.enrollment.student.get_full_name()} - {self.quiz.title} (Intento {self.attempt_number})"
    
    def save(self, *args, **kwargs):
        """Asignar número de intento automáticamente."""
        if not self.attempt_number:
            last_attempt = QuizAttempt.objects.filter(
                enrollment=self.enrollment,
                quiz=self.quiz
            ).order_by('-attempt_number').first()
            
            self.attempt_number = (last_attempt.attempt_number + 1) if last_attempt else 1
        
        super().save(*args, **kwargs)
    
    def complete_attempt(self):
        """Completar el intento y calcular la puntuación."""
        from django.utils import timezone
        
        # Calcular puntuación
        self.score = self.quiz.calculate_score(self.answers)
        self.is_passed = self.quiz.is_passing_score(self.score)
        self.is_completed = True
        self.completed_at = timezone.now()
        
        # Calcular tiempo empleado
        if self.started_at:
            time_diff = self.completed_at - self.started_at
            self.time_taken = int(time_diff.total_seconds())
        
        self.save()
        
        # Si aprobó, otorgar tokens FORE
        if self.is_passed:
            self.enrollment.fore_tokens_earned += self.quiz.fore_tokens_reward
            self.enrollment.save(update_fields=['fore_tokens_earned'])
        
        return self.score
    
    def can_retake(self):
        """Verificar si puede hacer otro intento."""
        if not self.is_completed:
            return True, "Intento actual no completado"
        
        if self.is_passed:
            return False, "Ya aprobó el cuestionario"
        
        total_attempts = QuizAttempt.objects.filter(
            enrollment=self.enrollment,
            quiz=self.quiz,
            is_completed=True
        ).count()
        
        if total_attempts >= self.quiz.max_attempts:
            return False, f"Se alcanzó el límite de {self.quiz.max_attempts} intentos"
        
        return True, "Puede realizar otro intento"
