"""
Tests para la aplicación de usuarios.
"""

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


class UserModelTest(TestCase):
    """Tests para el modelo User."""
    
    def setUp(self):
        """Configuración inicial para los tests."""
        self.user_data = {
            'email': 'test@example.com',
            'username': 'testuser',
            'first_name': 'Test',
            'last_name': 'User',
            'password': 'testpassword123'
        }
    
    def test_create_user(self):
        """Test crear usuario básico."""
        user = User.objects.create_user(**self.user_data)
        
        self.assertEqual(user.email, 'test@example.com')
        self.assertEqual(user.username, 'testuser')
        self.assertEqual(user.role, User.UserRole.STUDENT)
        self.assertTrue(user.check_password('testpassword123'))
        self.assertFalse(user.is_verified)
        self.assertTrue(user.is_active)
    
    def test_create_superuser(self):
        """Test crear superusuario."""
        user = User.objects.create_superuser(
            email='admin@example.com',
            username='admin',
            first_name='Admin',
            last_name='User',
            password='adminpass123'
        )
        
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)
        self.assertEqual(user.role, User.UserRole.ADMIN)
    
    def test_user_str_method(self):
        """Test método __str__ del usuario."""
        user = User.objects.create_user(**self.user_data)
        expected = "Test User (test@example.com)"
        self.assertEqual(str(user), expected)
    
    def test_user_methods(self):
        """Test métodos personalizados del usuario."""
        # Crear estudiante
        student = User.objects.create_user(
            email='student@example.com',
            username='student',
            first_name='Student',
            last_name='Test',
            password='pass123',
            role=User.UserRole.STUDENT
        )
        
        self.assertTrue(student.is_student())
        self.assertFalse(student.is_teacher())
        self.assertFalse(student.is_admin_user())
        
        # Crear profesor
        teacher = User.objects.create_user(
            email='teacher@example.com',
            username='teacher',
            first_name='Teacher',
            last_name='Test',
            password='pass123',
            role=User.UserRole.TEACHER
        )
        
        self.assertFalse(teacher.is_student())
        self.assertTrue(teacher.is_teacher())
        self.assertFalse(teacher.is_admin_user())


class UserRegistrationAPITest(APITestCase):
    """Tests para registro de usuarios via API."""
    
    def setUp(self):
        """Configuración inicial."""
        self.register_url = reverse('users:register')
        self.valid_data = {
            'email': 'newuser@example.com',
            'username': 'newuser',
            'first_name': 'New',
            'last_name': 'User',
            'password': 'newpass123!',
            'password_confirm': 'newpass123!',
            'role': 'student'
        }
    
    def test_valid_registration(self):
        """Test registro válido."""
        response = self.client.post(self.register_url, self.valid_data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('user', response.data)
        self.assertIn('tokens', response.data)
        self.assertEqual(response.data['user']['email'], 'newuser@example.com')
        
        # Verificar que el usuario se creó en la BD
        user = User.objects.get(email='newuser@example.com')
        self.assertEqual(user.username, 'newuser')
        self.assertEqual(user.role, User.UserRole.STUDENT)
    
    def test_registration_with_invalid_email(self):
        """Test registro con email inválido."""
        self.valid_data['email'] = 'invalid-email'
        response = self.client.post(self.register_url, self.valid_data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)
    
    def test_registration_with_mismatched_passwords(self):
        """Test registro con contraseñas que no coinciden."""
        self.valid_data['password_confirm'] = 'different_password'
        response = self.client.post(self.register_url, self.valid_data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password_confirm', response.data)
    
    def test_registration_with_duplicate_email(self):
        """Test registro con email duplicado."""
        # Crear usuario primero
        User.objects.create_user(
            email='newuser@example.com',
            username='existing',
            password='pass123'
        )
        
        response = self.client.post(self.register_url, self.valid_data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)


class UserAuthenticationAPITest(APITestCase):
    """Tests para autenticación de usuarios."""
    
    def setUp(self):
        """Configuración inicial."""
        self.login_url = reverse('users:token_obtain_pair')
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            first_name='Test',
            last_name='User',
            password='testpass123'
        )
    
    def test_valid_login(self):
        """Test login válido."""
        data = {
            'email': 'test@example.com',
            'password': 'testpass123'
        }
        response = self.client.post(self.login_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertIn('user', response.data)
        self.assertEqual(response.data['user']['email'], 'test@example.com')
    
    def test_login_with_invalid_credentials(self):
        """Test login con credenciales inválidas."""
        data = {
            'email': 'test@example.com',
            'password': 'wrongpassword'
        }
        response = self.client.post(self.login_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_login_with_nonexistent_email(self):
        """Test login con email que no existe."""
        data = {
            'email': 'nonexistent@example.com',
            'password': 'testpass123'
        }
        response = self.client.post(self.login_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class UserProfileAPITest(APITestCase):
    """Tests para gestión de perfil de usuario."""
    
    def setUp(self):
        """Configuración inicial."""
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            first_name='Test',
            last_name='User',
            password='testpass123'
        )
        self.me_url = reverse('users:user-me')
        
        # Autenticar usuario
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}'
        )
    
    def test_get_own_profile(self):
        """Test obtener perfil propio."""
        response = self.client.get(self.me_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], 'test@example.com')
        self.assertEqual(response.data['username'], 'testuser')
    
    def test_update_own_profile(self):
        """Test actualizar perfil propio."""
        data = {
            'first_name': 'Updated',
            'last_name': 'Name',
            'bio': 'Updated bio',
            'phone': '+1234567890'
        }
        response = self.client.patch(self.me_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['user']['first_name'], 'Updated')
        self.assertEqual(response.data['user']['bio'], 'Updated bio')
        
        # Verificar en la BD
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Updated')
        self.assertEqual(self.user.bio, 'Updated bio')
    
    def test_profile_access_without_authentication(self):
        """Test acceso a perfil sin autenticación."""
        self.client.credentials()  # Remover credenciales
        response = self.client.get(self.me_url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class UserPermissionsTest(APITestCase):
    """Tests para permisos de usuarios."""
    
    def setUp(self):
        """Configuración inicial."""
        # Crear usuarios con diferentes roles
        self.admin = User.objects.create_user(
            email='admin@example.com',
            username='admin',
            password='pass123',
            role=User.UserRole.ADMIN
        )
        
        self.teacher = User.objects.create_user(
            email='teacher@example.com',
            username='teacher',
            password='pass123',
            role=User.UserRole.TEACHER
        )
        
        self.student = User.objects.create_user(
            email='student@example.com',
            username='student',
            password='pass123',
            role=User.UserRole.STUDENT
        )
        
        self.users_list_url = reverse('users:user-list')
    
    def test_admin_can_access_user_list(self):
        """Test admin puede ver lista de usuarios."""
        refresh = RefreshToken.for_user(self.admin)
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}'
        )
        
        response = self.client.get(self.users_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_student_cannot_access_user_list(self):
        """Test estudiante no puede ver lista completa de usuarios."""
        refresh = RefreshToken.for_user(self.student)
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}'
        )
        
        response = self.client.get(self.users_list_url)
        # Debería ver solo su propio perfil
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], self.student.id)
