"""
URLs para la aplicación de usuarios.
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from . import views

# Router para ViewSets
router = DefaultRouter()
router.register(r'users', views.UserViewSet)

app_name = 'users'

urlpatterns = [
    # ==============================================================================
    # AUTENTICACIÓN JWT
    # ==============================================================================
    path('auth/register/', views.UserRegistrationView.as_view(), name='register'),
    path('auth/login/', views.CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/logout/', views.LogoutView.as_view(), name='logout'),
    
    # ==============================================================================
    # RESET DE CONTRASEÑA
    # ==============================================================================
    path('auth/password-reset/', views.PasswordResetRequestView.as_view(), name='password_reset'),
    path('auth/password-reset-confirm/', views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    
    # ==============================================================================
    # ESTADÍSTICAS
    # ==============================================================================
    path('users/stats/', views.UserStatsView.as_view(), name='user_stats'),
    
    # ==============================================================================
    # ROUTER URLS (ViewSets)
    # ==============================================================================
    path('', include(router.urls)),
]