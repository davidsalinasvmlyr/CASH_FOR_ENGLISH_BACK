"""
Modelos para gestión de usuarios en Cash for English.

Este módulo define el modelo User extendido con roles y campos adicionales
necesarios para la plataforma de aprendizaje.
"""

from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models
from PIL import Image


class User(AbstractUser):
    """
    Modelo de Usuario extendido para Cash for English.
    
    Roles disponibles:
    - STUDENT: Estudiantes que toman cursos
    - TEACHER: Profesores que crean contenido
    - ADMIN: Administradores del sistema
    """
    
    class UserRole(models.TextChoices):
        STUDENT = 'student', 'Estudiante'
        TEACHER = 'teacher', 'Profesor'
        ADMIN = 'admin', 'Administrador'
    
    # ==============================================================================
    # CAMPOS BÁSICOS EXTENDIDOS
    # ==============================================================================
    email = models.EmailField(
        unique=True,
        verbose_name='Email',
        help_text='Email único del usuario'
    )
    
    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        validators=[
            RegexValidator(
                regex=r'^\+?[\d\s\-\(\)]+$',
                message='Ingrese un número de teléfono válido'
            )
        ],
        verbose_name='Teléfono',
        help_text='Número de teléfono del usuario'
    )
    
    # ==============================================================================
    # ROL Y PERMISOS
    # ==============================================================================
    role = models.CharField(
        max_length=10,
        choices=UserRole.choices,
        default=UserRole.STUDENT,
        verbose_name='Rol',
        help_text='Rol del usuario en la plataforma'
    )
    
    # ==============================================================================
    # INFORMACIÓN ADICIONAL
    # ==============================================================================
    avatar = models.ImageField(
        upload_to='avatars/',
        blank=True,
        null=True,
        verbose_name='Avatar',
        help_text='Imagen de perfil del usuario'
    )
    
    birth_date = models.DateField(
        blank=True,
        null=True,
        verbose_name='Fecha de nacimiento'
    )
    
    bio = models.TextField(
        max_length=500,
        blank=True,
        verbose_name='Biografía',
        help_text='Descripción corta del usuario'
    )
    
    # ==============================================================================
    # CONFIGURACIONES DE APRENDIZAJE
    # ==============================================================================
    preferred_language = models.CharField(
        max_length=10,
        choices=[
            ('es', 'Español'),
            ('en', 'English'),
            ('pt', 'Português'),
            ('fr', 'Français'),
        ],
        default='es',
        verbose_name='Idioma preferido'
    )
    
    timezone = models.CharField(
        max_length=50,
        default='America/Bogota',
        verbose_name='Zona horaria',
        help_text='Zona horaria del usuario'
    )
    
    # ==============================================================================
    # CONFIGURACIONES DE NOTIFICACIONES
    # ==============================================================================
    email_notifications = models.BooleanField(
        default=True,
        verbose_name='Notificaciones por email',
        help_text='Recibir notificaciones por correo electrónico'
    )
    
    push_notifications = models.BooleanField(
        default=True,
        verbose_name='Notificaciones push',
        help_text='Recibir notificaciones push en la app'
    )
    
    # ==============================================================================
    # ESTADÍSTICAS DE APRENDIZAJE (Para estudiantes)
    # ==============================================================================
    current_level = models.CharField(
        max_length=20,
        choices=[
            ('beginner', 'Principiante'),
            ('elementary', 'Elemental'),
            ('intermediate', 'Intermedio'),
            ('upper_intermediate', 'Intermedio Alto'),
            ('advanced', 'Avanzado'),
            ('proficient', 'Competente'),
        ],
        default='beginner',
        verbose_name='Nivel actual de inglés'
    )
    
    total_study_time = models.PositiveIntegerField(
        default=0,
        verbose_name='Tiempo total de estudio (minutos)',
        help_text='Tiempo acumulado de estudio en minutos'
    )
    
    # ==============================================================================
    # METADATOS
    # ==============================================================================
    is_verified = models.BooleanField(
        default=False,
        verbose_name='Usuario verificado',
        help_text='Si el usuario ha verificado su email'
    )
    
    last_activity = models.DateTimeField(
        auto_now=True,
        verbose_name='Última actividad'
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de creación'
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Última actualización'
    )
    
    # ==============================================================================
    # CONFIGURACIÓN DEL MODELO
    # ==============================================================================
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']
    
    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['role']),
            models.Index(fields=['is_active']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.email})"
    
    # ==============================================================================
    # MÉTODOS PERSONALIZADOS
    # ==============================================================================
    def get_full_name(self):
        """Retorna el nombre completo del usuario."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username
    
    def get_short_name(self):
        """Retorna el nombre corto del usuario."""
        return self.first_name if self.first_name else self.username
    
    def is_student(self):
        """Verifica si el usuario es estudiante."""
        return self.role == self.UserRole.STUDENT
    
    def is_teacher(self):
        """Verifica si el usuario es profesor."""
        return self.role == self.UserRole.TEACHER
    
    def is_admin_user(self):
        """Verifica si el usuario es administrador."""
        return self.role == self.UserRole.ADMIN or self.is_superuser
    
    def save(self, *args, **kwargs):
        """
        Override del método save para realizar validaciones adicionales.
        """
        # Si es superuser, asignar rol admin automáticamente
        if self.is_superuser and self.role != self.UserRole.ADMIN:
            self.role = self.UserRole.ADMIN
        
        super().save(*args, **kwargs)
