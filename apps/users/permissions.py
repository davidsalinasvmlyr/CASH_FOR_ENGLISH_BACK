"""
Permisos personalizados para la aplicación de usuarios.

Este módulo define clases de permisos que se utilizan para controlar
el acceso a diferentes endpoints según el rol del usuario.
"""

from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Permiso personalizado que permite a los usuarios editar solo sus propios objetos.
    
    - Los usuarios autenticados pueden leer cualquier objeto
    - Solo el propietario puede editar/eliminar el objeto
    """
    
    def has_object_permission(self, request, view, obj):
        # Permisos de lectura para cualquier request (GET, HEAD, OPTIONS)
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Permisos de escritura solo para el propietario del objeto
        if hasattr(obj, 'user'):
            return obj.user == request.user
        
        # Si el objeto es el usuario mismo
        return obj == request.user


class IsStudent(permissions.BasePermission):
    """
    Permiso que solo permite acceso a usuarios con rol de estudiante.
    """
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.is_student()
        )


class IsTeacher(permissions.BasePermission):
    """
    Permiso que solo permite acceso a usuarios con rol de profesor.
    """
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.is_teacher()
        )


class IsAdminUser(permissions.BasePermission):
    """
    Permiso que solo permite acceso a usuarios administradores.
    """
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.is_admin_user()
        )


class IsStudentOrTeacher(permissions.BasePermission):
    """
    Permiso que permite acceso a estudiantes o profesores.
    """
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            (request.user.is_student() or request.user.is_teacher())
        )


class IsTeacherOrAdmin(permissions.BasePermission):
    """
    Permiso que permite acceso a profesores o administradores.
    """
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            (request.user.is_teacher() or request.user.is_admin_user())
        )


class IsVerifiedUser(permissions.BasePermission):
    """
    Permiso que solo permite acceso a usuarios verificados.
    """
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.is_verified
        )


class CanManageUsers(permissions.BasePermission):
    """
    Permiso complejo para gestión de usuarios.
    
    - Administradores: pueden gestionar cualquier usuario
    - Profesores: pueden ver estudiantes
    - Estudiantes: solo pueden ver/editar su propio perfil
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Administradores pueden hacer todo
        if request.user.is_admin_user():
            return True
        
        # Profesores pueden ver listas de usuarios (solo lectura para otros)
        if request.user.is_teacher():
            return request.method in permissions.SAFE_METHODS
        
        # Estudiantes pueden acceder (se verificará a nivel de objeto)
        if request.user.is_student():
            return True
        
        return False
    
    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Administradores pueden hacer todo
        if request.user.is_admin_user():
            return True
        
        # El usuario puede ver/editar su propio perfil
        if obj == request.user:
            return True
        
        # Profesores pueden ver perfiles de estudiantes (solo lectura)
        if (request.user.is_teacher() and 
            obj.is_student() and 
            request.method in permissions.SAFE_METHODS):
            return True
        
        return False


class CanAccessUserData(permissions.BasePermission):
    """
    Permiso para acceso a datos sensibles del usuario.
    
    Solo permite acceso a:
    - El propio usuario
    - Administradores
    - Profesores (solo lectura de estudiantes)
    """
    
    message = "No tiene permisos para acceder a estos datos de usuario."
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # El usuario siempre puede acceder a sus propios datos
        if obj == request.user:
            return True
        
        # Administradores pueden acceder a cualquier dato
        if request.user.is_admin_user():
            return True
        
        # Profesores pueden ver datos básicos de estudiantes (solo lectura)
        if (request.user.is_teacher() and 
            obj.is_student() and 
            request.method in permissions.SAFE_METHODS):
            # Limitar campos que pueden ver los profesores
            restricted_fields = ['email', 'phone', 'birth_date']
            if hasattr(view, 'get_serializer'):
                serializer = view.get_serializer(obj)
                for field in restricted_fields:
                    if field in serializer.fields:
                        serializer.fields[field].read_only = True
            return True
        
        return False