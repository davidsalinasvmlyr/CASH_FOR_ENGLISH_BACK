"""
Serializers para la API de usuarios.

Este módulo contiene los serializers para registro, autenticación,
y gestión de perfiles de usuario.
"""

from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer para registro de nuevos usuarios.
    """
    password = serializers.CharField(
        write_only=True,
        min_length=8,
        style={'input_type': 'password'},
        help_text='Contraseña debe tener al menos 8 caracteres'
    )
    password_confirm = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'},
        help_text='Confirmar contraseña'
    )
    
    class Meta:
        model = User
        fields = (
            'email',
            'username', 
            'first_name',
            'last_name',
            'password',
            'password_confirm',
            'role',
            'phone',
            'preferred_language',
            'current_level'
        )
        extra_kwargs = {
            'email': {'required': True},
            'first_name': {'required': True},
            'last_name': {'required': True},
        }
    
    def validate_email(self, value):
        """Validar que el email no exista."""
        if User.objects.filter(email=value.lower()).exists():
            raise serializers.ValidationError(
                "Ya existe un usuario con este email."
            )
        return value.lower()
    
    def validate_username(self, value):
        """Validar que el username no exista."""
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError(
                "Ya existe un usuario con este nombre de usuario."
            )
        return value
    
    def validate_password(self, value):
        """Validar fortaleza de la contraseña."""
        try:
            validate_password(value)
        except ValidationError as e:
            raise serializers.ValidationError(list(e.messages))
        return value
    
    def validate(self, attrs):
        """Validar que las contraseñas coincidan."""
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({
                'password_confirm': 'Las contraseñas no coinciden.'
            })
        return attrs
    
    def create(self, validated_data):
        """Crear nuevo usuario."""
        # Remover password_confirm antes de crear
        validated_data.pop('password_confirm', None)
        
        # Crear usuario
        user = User.objects.create_user(
            email=validated_data['email'],
            username=validated_data['username'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            password=validated_data['password'],
            role=validated_data.get('role', User.UserRole.STUDENT),
            phone=validated_data.get('phone', ''),
            preferred_language=validated_data.get('preferred_language', 'es'),
            current_level=validated_data.get('current_level', 'beginner')
        )
        
        return user


class CustomTokenObtainPairSerializer(serializers.Serializer):
    """
    Serializer customizado para obtener tokens JWT.
    Permite login con email en lugar de username.
    """
    email = serializers.EmailField()
    password = serializers.CharField(
        style={'input_type': 'password'},
        trim_whitespace=False
    )
    
    def validate(self, attrs):
        """Validar credenciales usando email."""
        email = attrs.get('email')
        password = attrs.get('password')
        
        if email and password:
            # Buscar usuario por email
            try:
                user = User.objects.get(email=email.lower(), is_active=True)
            except User.DoesNotExist:
                raise serializers.ValidationError(
                    'No existe un usuario activo con este email.'
                )
            
            # Verificar contraseña
            if not user.check_password(password):
                raise serializers.ValidationError(
                    'Credenciales inválidas.'
                )
            
            # Generar tokens
            refresh = RefreshToken.for_user(user)
            
            return {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'username': user.username,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'role': user.role,
                    'is_verified': user.is_verified,
                }
            }
        
        raise serializers.ValidationError(
            'Debe proporcionar email y contraseña.'
        )


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer para el perfil completo del usuario.
    """
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = (
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'full_name',
            'role',
            'phone',
            'avatar',
            'birth_date',
            'bio',
            'preferred_language',
            'timezone',
            'email_notifications',
            'push_notifications',
            'current_level',
            'total_study_time',
            'is_verified',
            'last_activity',
            'created_at',
        )
        read_only_fields = (
            'id',
            'email',
            'role',
            'total_study_time',
            'is_verified',
            'last_activity',
            'created_at',
        )
    
    def get_full_name(self, obj):
        """Obtener nombre completo."""
        return obj.get_full_name()
    
    def validate_avatar(self, value):
        """Validar tamaño y formato del avatar."""
        if value:
            # Validar tamaño (máximo 5MB)
            if value.size > 5 * 1024 * 1024:
                raise serializers.ValidationError(
                    "El archivo es demasiado grande. Máximo 5MB."
                )
            
            # Validar formato
            valid_formats = ['image/jpeg', 'image/png', 'image/gif']
            if value.content_type not in valid_formats:
                raise serializers.ValidationError(
                    "Formato no válido. Use JPG, PNG o GIF."
                )
        
        return value


class UserListSerializer(serializers.ModelSerializer):
    """
    Serializer para listar usuarios (versión resumida).
    """
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = (
            'id',
            'email',
            'username',
            'full_name',
            'role',
            'avatar',
            'current_level',
            'is_active',
            'created_at',
        )
    
    def get_full_name(self, obj):
        """Obtener nombre completo."""
        return obj.get_full_name()


class ChangePasswordSerializer(serializers.Serializer):
    """
    Serializer para cambio de contraseña.
    """
    old_password = serializers.CharField(
        style={'input_type': 'password'},
        help_text='Contraseña actual'
    )
    new_password = serializers.CharField(
        min_length=8,
        style={'input_type': 'password'},
        help_text='Nueva contraseña (mínimo 8 caracteres)'
    )
    confirm_password = serializers.CharField(
        style={'input_type': 'password'},
        help_text='Confirmar nueva contraseña'
    )
    
    def validate_old_password(self, value):
        """Validar que la contraseña actual sea correcta."""
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Contraseña actual incorrecta.')
        return value
    
    def validate_new_password(self, value):
        """Validar fortaleza de la nueva contraseña."""
        try:
            validate_password(value, self.context['request'].user)
        except ValidationError as e:
            raise serializers.ValidationError(list(e.messages))
        return value
    
    def validate(self, attrs):
        """Validar que las nuevas contraseñas coincidan."""
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError({
                'confirm_password': 'Las contraseñas no coinciden.'
            })
        return attrs
    
    def save(self):
        """Guardar la nueva contraseña."""
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user


class PasswordResetRequestSerializer(serializers.Serializer):
    """
    Serializer para solicitud de reset de contraseña.
    """
    email = serializers.EmailField(
        help_text='Email del usuario para resetear contraseña'
    )
    
    def validate_email(self, value):
        """Validar que el email exista."""
        try:
            User.objects.get(email=value.lower(), is_active=True)
        except User.DoesNotExist:
            raise serializers.ValidationError(
                'No existe un usuario activo con este email.'
            )
        return value.lower()


class PasswordResetConfirmSerializer(serializers.Serializer):
    """
    Serializer para confirmar reset de contraseña.
    """
    token = serializers.CharField(
        help_text='Token de reset recibido por email'
    )
    new_password = serializers.CharField(
        min_length=8,
        style={'input_type': 'password'},
        help_text='Nueva contraseña (mínimo 8 caracteres)'
    )
    confirm_password = serializers.CharField(
        style={'input_type': 'password'},
        help_text='Confirmar nueva contraseña'
    )
    
    def validate_new_password(self, value):
        """Validar fortaleza de la nueva contraseña."""
        try:
            validate_password(value)
        except ValidationError as e:
            raise serializers.ValidationError(list(e.messages))
        return value
    
    def validate(self, attrs):
        """Validar que las contraseñas coincidan."""
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError({
                'confirm_password': 'Las contraseñas no coinciden.'
            })
        return attrs