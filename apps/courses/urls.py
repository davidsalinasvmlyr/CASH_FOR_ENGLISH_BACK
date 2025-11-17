"""
URLs para la API de cursos y contenido educativo.

Este módulo define las rutas para:
- Cursos (CRUD completo)
- Lecciones (visualización)
- Cuestionarios (visualización y envío)
- Dashboards de estudiantes e instructores
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views

app_name = 'courses'

# Router para ViewSets
router = DefaultRouter()
router.register(r'courses', views.CourseViewSet, basename='course')
router.register(r'lessons', views.LessonViewSet, basename='lesson')
router.register(r'quizzes', views.QuizViewSet, basename='quiz')

urlpatterns = [
    # API Router
    path('api/', include(router.urls)),
    
    # Dashboards
    path('api/dashboard/student/', views.StudentDashboardView.as_view(), name='student-dashboard'),
    path('api/dashboard/teacher/', views.TeacherDashboardView.as_view(), name='teacher-dashboard'),
]