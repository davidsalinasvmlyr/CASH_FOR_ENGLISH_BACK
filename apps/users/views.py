"""
Views para la API de usuarios.

Este módulo contiene las vistas para registro, autenticación,
gestión de perfiles y administración de usuarios.
"""

from django.contrib.auth import logout
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.db import models
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from rest_framework import generics, permissions, serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .models import User
from .permissions import (
    CanAccessUserData,
    CanManageUsers,
    IsAdminUser,
    IsOwnerOrReadOnly
)
from .serializers import (
    ChangePasswordSerializer,
    CustomTokenObtainPairSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    UserListSerializer,
    UserProfileSerializer,
    UserRegistrationSerializer
)


class UserRegistrationView(generics.CreateAPIView):
    """
    Vista para registro de nuevos usuarios.
    
    POST /api/auth/register/
    """
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Generar tokens para el usuario recién creado
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'message': 'Usuario registrado exitosamente',
            'user': {
                'id': user.id,
                'email': user.email,
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'role': user.role,
            },
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        }, status=status.HTTP_201_CREATED)


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Vista personalizada para obtener tokens JWT.
    Permite login con email.
    
    POST /api/auth/login/
    """
    serializer_class = CustomTokenObtainPairSerializer
    
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        
        try:
            serializer.is_valid(raise_exception=True)
        except serializers.ValidationError as e:
            # Si el error contiene "Credenciales inválidas" es 401
            # Si contiene "No existe un usuario" es 400
            error_message = str(e.detail.get('non_field_errors', [''])[0]) if e.detail.get('non_field_errors') else str(e.detail)
            
            if 'Credenciales inválidas' in error_message:
                return Response(
                    {'detail': 'Credenciales inválidas'},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            else:
                return Response(
                    e.detail,
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        return Response(serializer.validated_data, status=status.HTTP_200_OK)


class LogoutView(generics.GenericAPIView):
    """
    Vista para logout del usuario.
    Agrega el refresh token a la blacklist.
    
    POST /api/auth/logout/
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        try:
            refresh_token = request.data.get("refresh_token")
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            
            # Logout del usuario en la sesión de Django
            logout(request)
            
            return Response({
                'message': 'Logout exitoso'
            }, status=status.HTTP_200_OK)
        
        except (InvalidToken, TokenError):
            return Response({
                'error': 'Token inválido'
            }, status=status.HTTP_400_BAD_REQUEST)


class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión completa de usuarios.
    
    - GET /api/users/ - Listar usuarios (admin/teacher)
    - POST /api/users/ - Crear usuario (admin)
    - GET /api/users/{id}/ - Detalle de usuario
    - PUT /api/users/{id}/ - Actualizar usuario
    - DELETE /api/users/{id}/ - Eliminar usuario (admin)
    """
    queryset = User.objects.all()
    permission_classes = [permissions.IsAuthenticated, CanManageUsers]
    
    def get_serializer_class(self):
        """Seleccionar serializer según la acción."""
        if self.action == 'list':
            return UserListSerializer
        return UserProfileSerializer
    
    def get_queryset(self):
        """Filtrar usuarios según el rol del usuario actual."""
        user = self.request.user
        
        if user.is_admin_user():
            # Administradores ven todos los usuarios
            return User.objects.all()
        elif user.is_teacher():
            # Profesores ven estudiantes y su propio perfil
            return User.objects.filter(
                models.Q(role=User.UserRole.STUDENT) | 
                models.Q(id=user.id)
            )
        else:
            # Estudiantes solo ven su propio perfil
            return User.objects.filter(id=user.id)
    
    @action(detail=False, methods=['get', 'put', 'patch'])
    def me(self, request):
        """
        Endpoint para gestionar el perfil del usuario actual.
        
        GET /api/users/me/ - Ver perfil propio
        PUT/PATCH /api/users/me/ - Actualizar perfil propio
        """
        if request.method == 'GET':
            serializer = self.get_serializer(request.user)
            return Response(serializer.data)
        
        elif request.method in ['PUT', 'PATCH']:
            partial = request.method == 'PATCH'
            serializer = self.get_serializer(
                request.user, 
                data=request.data, 
                partial=partial
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            
            return Response({
                'message': 'Perfil actualizado exitosamente',
                'user': serializer.data
            })
    
    @action(detail=False, methods=['post'])
    def change_password(self, request):
        """
        Cambiar contraseña del usuario actual.
        
        POST /api/users/change-password/
        """
        serializer = ChangePasswordSerializer(
            data=request.data, 
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response({
            'message': 'Contraseña cambiada exitosamente'
        })
    
    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def activate(self, request, pk=None):
        """
        Activar/desactivar usuario (solo admin).
        
        POST /api/users/{id}/activate/
        """
        user = self.get_object()
        user.is_active = not user.is_active
        user.save()
        
        status_text = "activado" if user.is_active else "desactivado"
        return Response({
            'message': f'Usuario {status_text} exitosamente',
            'is_active': user.is_active
        })
    
    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def verify(self, request, pk=None):
        """
        Verificar usuario manualmente (solo admin).
        
        POST /api/users/{id}/verify/
        """
        user = self.get_object()
        user.is_verified = True
        user.save()
        
        return Response({
            'message': 'Usuario verificado exitosamente'
        })


class PasswordResetRequestView(generics.GenericAPIView):
    """
    Vista para solicitar reset de contraseña.
    
    POST /api/auth/password-reset/
    """
    serializer_class = PasswordResetRequestSerializer
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data['email']
        user = User.objects.get(email=email, is_active=True)
        
        # Generar token de reset
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        
        # En un entorno real, aquí enviarías un email
        # Por ahora, solo devolvemos el token (para desarrollo)
        reset_url = f"https://yourapp.com/reset-password/{uid}/{token}/"
        
        # TODO: Implementar envío de email real
        # send_reset_password_email(user, reset_url)
        
        return Response({
            'message': 'Se ha enviado un enlace de reset a tu email',
            # Solo para desarrollo - remover en producción
            'reset_url': reset_url
        })


class PasswordResetConfirmView(generics.GenericAPIView):
    """
    Vista para confirmar reset de contraseña.
    
    POST /api/auth/password-reset-confirm/
    """
    serializer_class = PasswordResetConfirmSerializer
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # TODO: Implementar validación del token
        # Por ahora, devolvemos éxito (implementar en producción)
        
        return Response({
            'message': 'Contraseña restablecida exitosamente'
        })


class UserStatsView(generics.RetrieveAPIView):
    """
    Vista para obtener estadísticas del usuario actual.
    
    GET /api/users/stats/
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def retrieve(self, request):
        user = request.user
        
        # Calcular estadísticas básicas
        stats = {
            'user_id': user.id,
            'total_study_time': user.total_study_time,
            'current_level': user.current_level,
            'member_since': user.created_at,
            'last_activity': user.last_activity,
            'role': user.role,
            'is_verified': user.is_verified,
        }
        
        # Estadísticas adicionales para estudiantes
        if user.is_student():
            stats.update({
                'courses_enrolled': 0,  # TODO: Implementar cuando tengamos cursos
                'quizzes_completed': 0,  # TODO: Implementar cuando tengamos quizzes
                'tokens_earned': 0,  # TODO: Implementar cuando tengamos tokens
            })
        
        # Estadísticas adicionales para profesores
        elif user.is_teacher():
            stats.update({
                'courses_created': 0,  # TODO: Implementar
                'students_taught': 0,  # TODO: Implementar
            })
        
        return Response(stats)
