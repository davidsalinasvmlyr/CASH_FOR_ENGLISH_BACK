"""
Signals para el sistema de recompensas FORE.

Este módulo maneja la integración automática entre las actividades
educativas y el sistema de recompensas, otorgando tokens FORE y
logros cuando los estudiantes completan actividades.
"""

from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from apps.courses.models import CourseEnrollment, LessonProgress, QuizAttempt
from .models import (
    FOREWallet, Transaction, TransactionType, Achievement, UserAchievement
)

User = get_user_model()


@receiver(post_save, sender=User)
def create_fore_wallet(sender, instance, created, **kwargs):
    """
    Crear billetera FORE automáticamente para nuevos usuarios estudiantes.
    """
    if created and instance.is_student():
        FOREWallet.objects.create(user=instance)


@receiver(post_save, sender=LessonProgress)
def reward_lesson_completion(sender, instance, created, **kwargs):
    """
    Otorgar tokens FORE cuando se completa una lección.
    """
    if instance.is_completed and hasattr(instance, '_lesson_just_completed'):
        # Evitar múltiples ejecuciones
        return
    
    if instance.is_completed:
        instance._lesson_just_completed = True
        
        try:
            wallet = instance.enrollment.student.fore_wallet
            
            # Otorgar tokens de la lección
            if instance.lesson.fore_tokens_reward > 0:
                wallet.add_tokens(
                    amount=instance.lesson.fore_tokens_reward,
                    description=f"Lección completada: {instance.lesson.title}",
                    transaction_type=TransactionType.LESSON_COMPLETED
                )
                
                # Crear transacción con referencia
                Transaction.objects.filter(
                    user=instance.enrollment.student,
                    description__contains=instance.lesson.title
                ).update(
                    related_lesson=instance.lesson,
                    related_course=instance.lesson.course
                )
            
            # Verificar logros relacionados con lecciones
            check_achievements_for_user(instance.enrollment.student, 'lesson_completed')
            
        except FOREWallet.DoesNotExist:
            # Crear billetera si no existe
            FOREWallet.objects.create(user=instance.enrollment.student)


@receiver(post_save, sender=QuizAttempt)
def reward_quiz_completion(sender, instance, created, **kwargs):
    """
    Otorgar tokens FORE cuando se aprueba un quiz.
    """
    if instance.is_passed and instance.is_completed and not hasattr(instance, '_quiz_just_passed'):
        instance._quiz_just_passed = True
        
        try:
            wallet = instance.enrollment.student.fore_wallet
            
            # Otorgar tokens del quiz
            if instance.quiz.fore_tokens_reward > 0:
                wallet.add_tokens(
                    amount=instance.quiz.fore_tokens_reward,
                    description=f"Quiz aprobado: {instance.quiz.title}",
                    transaction_type=TransactionType.QUIZ_PASSED
                )
                
                # Actualizar transacción con referencias
                Transaction.objects.filter(
                    user=instance.enrollment.student,
                    description__contains=instance.quiz.title
                ).update(
                    related_quiz=instance.quiz,
                    related_lesson=instance.quiz.lesson,
                    related_course=instance.quiz.lesson.course
                )
            
            # Verificar logros relacionados con quizzes
            check_achievements_for_user(instance.enrollment.student, 'quiz_passed')
            
        except FOREWallet.DoesNotExist:
            FOREWallet.objects.create(user=instance.enrollment.student)


@receiver(post_save, sender=CourseEnrollment)
def reward_course_completion(sender, instance, created, **kwargs):
    """
    Otorgar tokens FORE cuando se completa un curso.
    """
    if instance.status == 'completed' and not hasattr(instance, '_course_just_completed'):
        instance._course_just_completed = True
        
        try:
            wallet = instance.student.fore_wallet
            
            # Otorgar tokens del curso
            if instance.course.fore_tokens_reward > 0:
                wallet.add_tokens(
                    amount=instance.course.fore_tokens_reward,
                    description=f"Curso completado: {instance.course.title}",
                    transaction_type=TransactionType.COURSE_COMPLETED
                )
                
                # Actualizar transacción con referencia
                Transaction.objects.filter(
                    user=instance.student,
                    description__contains=instance.course.title
                ).update(
                    related_course=instance.course
                )
            
            # Verificar logros relacionados con cursos
            check_achievements_for_user(instance.student, 'course_completed')
            
        except FOREWallet.DoesNotExist:
            FOREWallet.objects.create(user=instance.student)


@receiver(post_save, sender=UserAchievement)
def reward_achievement_earned(sender, instance, created, **kwargs):
    """
    Otorgar tokens FORE cuando se obtiene un logro.
    """
    if created:
        try:
            wallet = instance.user.fore_wallet
            
            # Otorgar tokens del logro
            wallet.add_tokens(
                amount=instance.fore_tokens_awarded,
                description=f"Logro obtenido: {instance.achievement.title}",
                transaction_type=TransactionType.ACHIEVEMENT_EARNED
            )
            
            # Actualizar transacción con referencia
            Transaction.objects.filter(
                user=instance.user,
                description__contains=instance.achievement.title
            ).update(
                related_achievement=instance.achievement
            )
            
        except FOREWallet.DoesNotExist:
            FOREWallet.objects.create(user=instance.user)


def check_achievements_for_user(user, activity_type):
    """
    Verificar si un usuario ha desbloqueado nuevos logros.
    
    Args:
        user: Usuario a verificar
        activity_type: Tipo de actividad que desencadenó la verificación
    """
    # Obtener logros activos que el usuario no tiene
    available_achievements = Achievement.objects.filter(
        is_active=True
    ).exclude(
        user_achievements__user=user
    )
    
    # Verificar cada logro
    for achievement in available_achievements:
        if achievement.check_achievement(user):
            # Crear el logro para el usuario
            user_achievement = UserAchievement.objects.create(
                user=user,
                achievement=achievement,
                progress_when_earned={
                    'activity_type': activity_type,
                    'timestamp': timezone.now().isoformat(),
                    'total_courses': user.enrollments.filter(status='completed').count(),
                    'total_lessons': LessonProgress.objects.filter(
                        enrollment__student=user,
                        is_completed=True
                    ).count(),
                    'total_quizzes': QuizAttempt.objects.filter(
                        enrollment__student=user,
                        is_passed=True
                    ).values('quiz').distinct().count(),
                    'total_fore_earned': float(user.fore_wallet.total_earned) if hasattr(user, 'fore_wallet') else 0
                }
            )
            
            # El signal reward_achievement_earned se ejecutará automáticamente
            

def create_initial_achievements():
    """
    Crear logros iniciales para la plataforma.
    Esta función debe ejecutarse una vez después de las migraciones.
    """
    achievements_data = [
        # Logros de aprendizaje básico
        {
            'title': 'Primera Lección',
            'description': 'Completa tu primera lección en la plataforma',
            'category': 'learning',
            'achievement_type': 'bronze',
            'fore_tokens_reward': 50,
            'required_lessons': 1,
            'icon_name': 'first_lesson.png'
        },
        {
            'title': 'Primer Quiz',
            'description': 'Aprueba tu primer cuestionario',
            'category': 'learning',
            'achievement_type': 'bronze',
            'fore_tokens_reward': 75,
            'required_quizzes': 1,
            'icon_name': 'first_quiz.png'
        },
        {
            'title': 'Primer Curso',
            'description': 'Completa tu primer curso completo',
            'category': 'learning',
            'achievement_type': 'silver',
            'fore_tokens_reward': 200,
            'required_courses': 1,
            'icon_name': 'first_course.png'
        },
        
        # Logros de progreso
        {
            'title': 'Estudiante Dedicado',
            'description': 'Completa 10 lecciones',
            'category': 'progress',
            'achievement_type': 'bronze',
            'fore_tokens_reward': 150,
            'required_lessons': 10,
            'icon_name': 'dedicated_student.png'
        },
        {
            'title': 'Experto en Evaluaciones',
            'description': 'Aprueba 5 cuestionarios diferentes',
            'category': 'progress',
            'achievement_type': 'silver',
            'fore_tokens_reward': 250,
            'required_quizzes': 5,
            'icon_name': 'quiz_expert.png'
        },
        {
            'title': 'Completador de Cursos',
            'description': 'Completa 3 cursos',
            'category': 'progress',
            'achievement_type': 'gold',
            'fore_tokens_reward': 500,
            'required_courses': 3,
            'icon_name': 'course_completer.png'
        },
        
        # Logros de dominio
        {
            'title': 'Estudiante Avanzado',
            'description': 'Completa 50 lecciones',
            'category': 'mastery',
            'achievement_type': 'gold',
            'fore_tokens_reward': 750,
            'required_lessons': 50,
            'icon_name': 'advanced_student.png'
        },
        {
            'title': 'Maestro de Evaluaciones',
            'description': 'Aprueba 20 cuestionarios',
            'category': 'mastery',
            'achievement_type': 'platinum',
            'fore_tokens_reward': 1000,
            'required_quizzes': 20,
            'icon_name': 'quiz_master.png'
        },
        {
            'title': 'Coleccionista de FORE',
            'description': 'Gana 1000 tokens FORE en total',
            'category': 'mastery',
            'achievement_type': 'gold',
            'fore_tokens_reward': 500,
            'required_fore_tokens': 1000,
            'icon_name': 'fore_collector.png'
        },
        
        # Logros especiales
        {
            'title': 'Pionero',
            'description': 'Uno de los primeros 100 estudiantes en la plataforma',
            'category': 'special',
            'achievement_type': 'diamond',
            'fore_tokens_reward': 2000,
            'required_courses': 1,
            'max_recipients': 100,
            'icon_name': 'pioneer.png'
        },
        {
            'title': 'Millonario FORE',
            'description': 'Gana 10,000 tokens FORE en total',
            'category': 'special',
            'achievement_type': 'diamond',
            'fore_tokens_reward': 5000,
            'required_fore_tokens': 10000,
            'icon_name': 'fore_millionaire.png'
        }
    ]
    
    for achievement_data in achievements_data:
        achievement, created = Achievement.objects.get_or_create(
            title=achievement_data['title'],
            defaults=achievement_data
        )
        
        if created:
            print(f"Logro creado: {achievement.title}")


def create_initial_leaderboards():
    """
    Crear rankings iniciales para la plataforma.
    """
    from .models import Leaderboard, LeaderboardCategory, LeaderboardPeriod
    
    leaderboards_data = [
        {
            'title': 'Top FORE Tokens - Semanal',
            'description': 'Estudiantes que más tokens FORE han ganado esta semana',
            'category': LeaderboardCategory.FORE_TOKENS,
            'period': LeaderboardPeriod.WEEKLY,
            'first_place_reward': 500,
            'second_place_reward': 300,
            'third_place_reward': 200
        },
        {
            'title': 'Top FORE Tokens - Todo el tiempo',
            'description': 'Estudiantes que más tokens FORE han ganado en total',
            'category': LeaderboardCategory.FORE_TOKENS,
            'period': LeaderboardPeriod.ALL_TIME,
            'first_place_reward': 1000,
            'second_place_reward': 750,
            'third_place_reward': 500
        },
        {
            'title': 'Top Cursos Completados - Mensual',
            'description': 'Estudiantes que más cursos han completado este mes',
            'category': LeaderboardCategory.COURSES_COMPLETED,
            'period': LeaderboardPeriod.MONTHLY,
            'first_place_reward': 400,
            'second_place_reward': 250,
            'third_place_reward': 150
        },
        {
            'title': 'Top Lecciones Completadas - Diario',
            'description': 'Estudiantes más activos del día',
            'category': LeaderboardCategory.LESSONS_COMPLETED,
            'period': LeaderboardPeriod.DAILY,
            'first_place_reward': 100,
            'second_place_reward': 75,
            'third_place_reward': 50
        },
        {
            'title': 'Top Logros Obtenidos - Semanal',
            'description': 'Estudiantes que más logros han conseguido esta semana',
            'category': LeaderboardCategory.ACHIEVEMENTS_EARNED,
            'period': LeaderboardPeriod.WEEKLY,
            'first_place_reward': 300,
            'second_place_reward': 200,
            'third_place_reward': 100
        }
    ]
    
    for leaderboard_data in leaderboards_data:
        leaderboard, created = Leaderboard.objects.get_or_create(
            title=leaderboard_data['title'],
            defaults=leaderboard_data
        )
        
        if created:
            print(f"Ranking creado: {leaderboard.title}")


def create_initial_rewards():
    """
    Crear recompensas iniciales para el marketplace.
    """
    from .models import Reward, RewardCategory
    
    rewards_data = [
        # Recompensas digitales
        {
            'title': 'Certificado Digital Premium',
            'description': 'Certificado digital con diseño premium y verificación blockchain',
            'category': RewardCategory.DIGITAL,
            'fore_cost': 500,
        },
        {
            'title': 'Acceso Premium por 1 Mes',
            'description': 'Acceso a todas las funciones premium durante un mes',
            'category': RewardCategory.DIGITAL,
            'fore_cost': 1000,
        },
        {
            'title': 'Mentoría Personal 1 Hora',
            'description': 'Sesión de mentoría personalizada con un instructor experto',
            'category': RewardCategory.EDUCATION,
            'fore_cost': 2000,
        },
        
        # Recompensas físicas
        {
            'title': 'Camiseta Cash for English',
            'description': 'Camiseta oficial de la plataforma Cash for English',
            'category': RewardCategory.PHYSICAL,
            'fore_cost': 1500,
            'requires_shipping': True,
            'stock_quantity': 100,
        },
        {
            'title': 'Taza Personalizada',
            'description': 'Taza con tu nombre y logros principales',
            'category': RewardCategory.PHYSICAL,
            'fore_cost': 800,
            'requires_shipping': True,
        },
        
        # Experiencias
        {
            'title': 'Webinar Exclusivo con Expertos',
            'description': 'Acceso a webinar exclusivo sobre técnicas avanzadas de inglés',
            'category': RewardCategory.EXPERIENCE,
            'fore_cost': 600,
            'max_per_user': 1,
        },
        
        # Entretenimiento
        {
            'title': 'Acceso Netflix 1 Mes',
            'description': 'Cupón para 1 mes gratuito de Netflix',
            'category': RewardCategory.ENTERTAINMENT,
            'fore_cost': 3000,
            'stock_quantity': 20,
        },
        {
            'title': 'Audible Premium 2 Meses',
            'description': 'Suscripción premium de Audible por 2 meses',
            'category': RewardCategory.ENTERTAINMENT,
            'fore_cost': 2500,
            'stock_quantity': 50,
        },
        
        # Caridad
        {
            'title': 'Donación Educación Rural',
            'description': 'Donación de $10 USD para educación en zonas rurales',
            'category': RewardCategory.CHARITY,
            'fore_cost': 1000,
        }
    ]
    
    for reward_data in rewards_data:
        reward, created = Reward.objects.get_or_create(
            title=reward_data['title'],
            defaults=reward_data
        )
        
        if created:
            print(f"Recompensa creada: {reward.title}")


def create_initial_achievements():
    """Crear logros iniciales del sistema."""
    from .models import Achievement
    
    initial_achievements = [
        # Logros de lecciones
        {
            'title': 'Primer Paso',
            'description': 'Completa tu primera lección',
            'category': 'lesson',
            'achievement_type': 'bronze',
            'required_lessons': 1,
            'fore_tokens_reward': 10,
            'badge_color': '#CD7F32'
        },
        {
            'title': 'Estudiante Activo',
            'description': 'Completa 10 lecciones',
            'category': 'lesson',
            'achievement_type': 'silver',
            'required_lessons': 10,
            'fore_tokens_reward': 50,
            'badge_color': '#C0C0C0'
        },
        {
            'title': 'Experto en Lecciones',
            'description': 'Completa 50 lecciones',
            'category': 'lesson',
            'achievement_type': 'gold',
            'required_lessons': 50,
            'fore_tokens_reward': 200,
            'badge_color': '#FFD700'
        },
        
        # Logros de quizzes
        {
            'title': 'Primera Evaluación',
            'description': 'Aprueba tu primer quiz',
            'category': 'quiz',
            'achievement_type': 'bronze',
            'required_quizzes': 1,
            'fore_tokens_reward': 15,
            'badge_color': '#CD7F32'
        },
        {
            'title': 'Maestro de Quizzes',
            'description': 'Aprueba 25 quizzes',
            'category': 'quiz',
            'achievement_type': 'gold',
            'required_quizzes': 25,
            'fore_tokens_reward': 150,
            'badge_color': '#FFD700'
        },
        
        # Logros de cursos
        {
            'title': 'Graduado',
            'description': 'Completa tu primer curso completo',
            'category': 'course',
            'achievement_type': 'silver',
            'required_courses': 1,
            'fore_tokens_reward': 100,
            'badge_color': '#C0C0C0'
        },
        {
            'title': 'Estudiante Dedicado',
            'description': 'Completa 3 cursos',
            'category': 'course',
            'achievement_type': 'platinum',
            'required_courses': 3,
            'fore_tokens_reward': 300,
            'badge_color': '#E5E4E2'
        },
        
        # Logros de racha
        {
            'title': 'Constancia',
            'description': 'Mantén una racha de 7 días estudiando',
            'category': 'streak',
            'achievement_type': 'silver',
            'required_streak_days': 7,
            'fore_tokens_reward': 75,
            'badge_color': '#C0C0C0'
        },
        {
            'title': 'Disciplina Total',
            'description': 'Mantén una racha de 30 días estudiando',
            'category': 'streak',
            'achievement_type': 'platinum',
            'required_streak_days': 30,
            'fore_tokens_reward': 500,
            'badge_color': '#E5E4E2'
        },
        
        # Logros especiales
        {
            'title': 'Perfeccionista',
            'description': 'Obtén 100% en 10 quizzes seguidos',
            'category': 'special',
            'achievement_type': 'legendary',
            'required_quizzes': 10,
            'fore_tokens_reward': 250,
            'badge_color': '#FF6B35',
            'is_secret': True
        },
        {
            'title': 'Coleccionista FORE',
            'description': 'Acumula 1000 FORE tokens',
            'category': 'tokens',
            'achievement_type': 'gold',
            'required_fore_tokens': 1000,
            'fore_tokens_reward': 100,
            'badge_color': '#FFD700'
        }
    ]
    
    created_count = 0
    for achievement_data in initial_achievements:
        achievement, created = Achievement.objects.get_or_create(
            title=achievement_data['title'],
            defaults=achievement_data
        )
        if created:
            created_count += 1
    
    return created_count


def create_initial_leaderboards():
    """Crear leaderboards iniciales del sistema."""
    from .models import Leaderboard
    
    initial_leaderboards = [
        {
            'title': 'Ranking FORE Semanal',
            'description': 'Los estudiantes con más tokens FORE ganados esta semana',
            'category': 'fore_tokens',
            'period': 'weekly',
            'first_place_reward': 200,
            'second_place_reward': 150,
            'third_place_reward': 100
        },
        {
            'title': 'Ranking FORE Mensual',
            'description': 'Los estudiantes con más tokens FORE ganados este mes',
            'category': 'fore_tokens',
            'period': 'monthly',
            'first_place_reward': 500,
            'second_place_reward': 300,
            'third_place_reward': 200
        },
        {
            'title': 'Ranking de Lecciones',
            'description': 'Los estudiantes que han completado más lecciones',
            'category': 'lessons_completed',
            'period': 'all_time',
            'first_place_reward': 300,
            'second_place_reward': 200,
            'third_place_reward': 100
        },
        {
            'title': 'Maestros de Quizzes',
            'description': 'Los estudiantes que han aprobado más quizzes',
            'category': 'quizzes_passed',
            'period': 'all_time',
            'first_place_reward': 250,
            'second_place_reward': 175,
            'third_place_reward': 100
        },
        {
            'title': 'Rachas Activas',
            'description': 'Los estudiantes con las rachas más largas',
            'category': 'streak_days',
            'period': 'all_time',
            'first_place_reward': 400,
            'second_place_reward': 250,
            'third_place_reward': 150
        }
    ]
    
    created_count = 0
    for leaderboard_data in initial_leaderboards:
        leaderboard, created = Leaderboard.objects.get_or_create(
            title=leaderboard_data['title'],
            defaults=leaderboard_data
        )
        if created:
            created_count += 1
    
    return created_count


def create_initial_rewards_v2():
    """Crear recompensas iniciales del marketplace (versión simplificada)."""
    from .models import Reward
    
    initial_rewards = [
        # Recompensas digitales
        {
            'title': 'Certificado Digital Personalizado',
            'description': 'Certificado digital con tu nombre y progreso académico en Cash for English',
            'category': 'digital',
            'fore_cost': 100,
            'requires_shipping': False,
            'delivery_info': 'Se enviará por correo electrónico en formato PDF en 24-48 horas.'
        },
        {
            'title': 'Clase Premium Adicional',
            'description': 'Acceso a una clase premium extra con tutor nativo de 45 minutos',
            'category': 'education',
            'fore_cost': 250,
            'stock_quantity': 20,
            'requires_shipping': False,
            'delivery_info': 'Se programará la sesión dentro de 7 días. Requiere coordinación telefónica.'
        },
        {
            'title': 'Guía de Pronunciación Avanzada',
            'description': 'Material exclusivo digital para mejorar tu pronunciación con ejercicios interactivos',
            'category': 'digital',
            'fore_cost': 75,
            'requires_shipping': False,
            'delivery_info': 'Acceso inmediato al material digital tras el canje.'
        },
        
        # Recompensas físicas
        {
            'title': 'Libro de Inglés Físico',
            'description': 'Libro de gramática inglesa "English Grammar in Use" enviado a tu domicilio',
            'category': 'physical',
            'fore_cost': 500,
            'stock_quantity': 50,
            'requires_shipping': True,
            'delivery_info': 'Envío gratuito. Tiempo de entrega: 5-10 días hábiles.'
        },
        {
            'title': 'Taza "Cash for English"',
            'description': 'Taza oficial de cerámica con el logo de Cash for English',
            'category': 'physical',
            'fore_cost': 200,
            'stock_quantity': 100,
            'requires_shipping': True,
            'delivery_info': 'Envío gratuito. Tiempo de entrega: 3-7 días hábiles.'
        },
        
        # Entretenimiento
        {
            'title': 'Suscripción Netflix 1 mes',
            'description': 'Código para 1 mes de suscripción a Netflix',
            'category': 'entertainment',
            'fore_cost': 600,
            'stock_quantity': 15,
            'requires_shipping': False,
            'delivery_info': 'Código enviado por correo electrónico en 24 horas.'
        }
    ]
    
    created_count = 0
    for reward_data in initial_rewards:
        reward, created = Reward.objects.get_or_create(
            title=reward_data['title'],
            defaults=reward_data
        )
        if created:
            created_count += 1
    
    return created_count