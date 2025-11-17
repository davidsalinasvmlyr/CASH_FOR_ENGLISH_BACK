"""
Configuración del admin para la aplicación de usuarios.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Configuración personalizada del admin para el modelo User.
    """
    
    # Campos mostrados en la lista
    list_display = (
        'email',
        'username', 
        'full_name',
        'role',
        'current_level',
        'is_verified',
        'is_active',
        'created_at',
        'avatar_preview'
    )
    
    # Campos por los que se puede filtrar
    list_filter = (
        'role',
        'current_level',
        'is_verified',
        'is_active',
        'is_staff',
        'preferred_language',
        'created_at',
        'last_login'
    )
    
    # Campos de búsqueda
    search_fields = (
        'email',
        'username',
        'first_name',
        'last_name',
        'phone'
    )
    
    # Orden por defecto
    ordering = ('-created_at',)
    
    # Campos editables desde la lista
    list_editable = ('is_active', 'is_verified')
    
    # Configuración de fieldsets para el detalle
    fieldsets = (
        ('Información Básica', {
            'fields': ('email', 'username', 'password')
        }),
        ('Información Personal', {
            'fields': (
                'first_name', 
                'last_name',
                'phone',
                'birth_date',
                'bio',
                'avatar'
            )
        }),
        ('Configuración de la Cuenta', {
            'fields': (
                'role',
                'is_verified',
                'preferred_language',
                'timezone'
            )
        }),
        ('Configuración de Aprendizaje', {
            'fields': (
                'current_level',
                'total_study_time'
            ),
            'classes': ('collapse',)  # Sección colapsable
        }),
        ('Notificaciones', {
            'fields': (
                'email_notifications',
                'push_notifications'
            ),
            'classes': ('collapse',)
        }),
        ('Permisos', {
            'fields': (
                'is_active',
                'is_staff', 
                'is_superuser',
                'groups',
                'user_permissions'
            ),
            'classes': ('collapse',)
        }),
        ('Fechas Importantes', {
            'fields': (
                'last_login',
                'date_joined',
                'created_at',
                'updated_at',
                'last_activity'
            ),
            'classes': ('collapse',)
        }),
    )
    
    # Campos para agregar usuario
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'email',
                'username',
                'first_name',
                'last_name',
                'role',
                'password1',
                'password2'
            ),
        }),
    )
    
    # Campos de solo lectura
    readonly_fields = (
        'created_at',
        'updated_at',
        'last_activity',
        'total_study_time',
        'avatar_preview'
    )
    
    def full_name(self, obj):
        """Mostrar nombre completo en la lista."""
        return obj.get_full_name()
    full_name.short_description = 'Nombre Completo'
    
    def avatar_preview(self, obj):
        """Mostrar preview del avatar."""
        if obj.avatar:
            return format_html(
                '<img src="{}" width="50" height="50" style="border-radius: 50%;" />',
                obj.avatar.url
            )
        return format_html(
            '<div style="width: 50px; height: 50px; background: #ddd; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 12px;">Sin avatar</div>'
        )
    avatar_preview.short_description = 'Avatar'
    
    # Acciones personalizadas
    actions = ['verify_users', 'activate_users', 'deactivate_users']
    
    def verify_users(self, request, queryset):
        """Verificar usuarios seleccionados."""
        updated = queryset.update(is_verified=True)
        self.message_user(
            request, 
            f'{updated} usuarios verificados exitosamente.'
        )
    verify_users.short_description = "Verificar usuarios seleccionados"
    
    def activate_users(self, request, queryset):
        """Activar usuarios seleccionados."""
        updated = queryset.update(is_active=True)
        self.message_user(
            request,
            f'{updated} usuarios activados exitosamente.'
        )
    activate_users.short_description = "Activar usuarios seleccionados"
    
    def deactivate_users(self, request, queryset):
        """Desactivar usuarios seleccionados."""
        updated = queryset.update(is_active=False)
        self.message_user(
            request,
            f'{updated} usuarios desactivados exitosamente.'
        )
    deactivate_users.short_description = "Desactivar usuarios seleccionados"
    
    # Personalizar título del admin
    def get_queryset(self, request):
        """Optimizar consultas con select_related."""
        return super().get_queryset(request).select_related()


# Personalizar títulos del sitio admin
admin.site.site_header = 'Cash for English - Administración'
admin.site.site_title = 'Cash for English Admin'
admin.site.index_title = 'Panel de Administración'
