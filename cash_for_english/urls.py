"""
URL configuration for cash_for_english project.
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

urlpatterns = [
    # ==============================================================================
    # ADMIN
    # ==============================================================================
    path('admin/', admin.site.urls),
    
    # ==============================================================================
    # API DOCUMENTATION
    # ==============================================================================
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    
    # ==============================================================================
    # API ENDPOINTS
    # ==============================================================================
    path('api/', include('apps.users.urls')),
    path('api/v1/courses/', include('apps.courses.urls')),
    path('api/v1/rewards/', include('apps.rewards.urls')),
    
    # TODO: Agregar URLs de otras apps cuando se implementen
    # path('api/', include('apps.quizzes.urls')),
]

# Servir archivos de media y static en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
