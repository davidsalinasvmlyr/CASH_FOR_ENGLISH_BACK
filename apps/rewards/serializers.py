"""
Serializers para la API del sistema de recompensas FORE.

Este módulo contiene los serializers para:
- Billeteras y balance FORE
- Transacciones
- Logros y achievements
- Rankings y leaderboards
- Marketplace y recompensas
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model

from .models import (
    FOREWallet, Transaction, Achievement, UserAchievement,
    Leaderboard, UserRanking, Reward, RewardRedemption
)

User = get_user_model()


class FOREWalletSerializer(serializers.ModelSerializer):
    """Serializer para billeteras FORE."""
    
    user_info = serializers.SerializerMethodField()
    available_balance = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    
    class Meta:
        model = FOREWallet
        fields = [
            'balance', 'available_balance', 'total_earned', 'total_spent',
            'frozen_amount', 'created_at', 'updated_at', 'user_info'
        ]
        read_only_fields = [
            'balance', 'total_earned', 'total_spent', 'frozen_amount',
            'created_at', 'updated_at'
        ]
    
    def get_user_info(self, obj):
        """Obtener información básica del usuario."""
        return {
            'id': obj.user.id,
            'username': obj.user.username,
            'full_name': obj.user.get_full_name(),
            'email': obj.user.email
        }


class TransactionSerializer(serializers.ModelSerializer):
    """Serializer para transacciones FORE."""
    
    transaction_type_display = serializers.CharField(source='get_transaction_type_display', read_only=True)
    is_earning = serializers.BooleanField(read_only=True)
    is_spending = serializers.BooleanField(read_only=True)
    
    # Referencias opcionales
    course_info = serializers.SerializerMethodField()
    lesson_info = serializers.SerializerMethodField()
    quiz_info = serializers.SerializerMethodField()
    achievement_info = serializers.SerializerMethodField()
    
    class Meta:
        model = Transaction
        fields = [
            'id', 'transaction_type', 'transaction_type_display',
            'amount', 'balance_after', 'description', 'created_at',
            'is_earning', 'is_spending',
            'course_info', 'lesson_info', 'quiz_info', 'achievement_info'
        ]
        read_only_fields = ['id', 'balance_after', 'created_at']
    
    def get_course_info(self, obj):
        """Información del curso relacionado."""
        if obj.related_course:
            return {
                'id': obj.related_course.id,
                'title': obj.related_course.title,
                'slug': obj.related_course.slug
            }
        return None
    
    def get_lesson_info(self, obj):
        """Información de la lección relacionada."""
        if obj.related_lesson:
            return {
                'id': obj.related_lesson.id,
                'title': obj.related_lesson.title,
                'slug': obj.related_lesson.slug
            }
        return None
    
    def get_quiz_info(self, obj):
        """Información del quiz relacionado."""
        if obj.related_quiz:
            return {
                'id': obj.related_quiz.id,
                'title': obj.related_quiz.title
            }
        return None
    
    def get_achievement_info(self, obj):
        """Información del logro relacionado."""
        if obj.related_achievement:
            return {
                'id': obj.related_achievement.id,
                'title': obj.related_achievement.title,
                'achievement_type': obj.related_achievement.achievement_type
            }
        return None


class AchievementSerializer(serializers.ModelSerializer):
    """Serializer para logros disponibles."""
    
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    achievement_type_display = serializers.CharField(source='get_achievement_type_display', read_only=True)
    recipients_count = serializers.IntegerField(read_only=True)
    is_available = serializers.BooleanField(read_only=True)
    
    # Estado para el usuario actual
    user_has_achievement = serializers.SerializerMethodField()
    user_progress = serializers.SerializerMethodField()
    
    class Meta:
        model = Achievement
        fields = [
            'id', 'title', 'description', 'category', 'category_display',
            'achievement_type', 'achievement_type_display', 'icon', 'badge_color',
            'fore_tokens_reward', 'required_courses', 'required_lessons',
            'required_quizzes', 'required_streak_days', 'required_fore_tokens',
            'is_active', 'is_secret', 'max_recipients', 'recipients_count',
            'is_available', 'created_at', 'user_has_achievement', 'user_progress'
        ]
        read_only_fields = ['id', 'recipients_count', 'created_at']
    
    def get_user_has_achievement(self, obj):
        """Verificar si el usuario actual tiene este logro."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.user_achievements.filter(user=request.user).exists()
        return False
    
    def get_user_progress(self, obj):
        """Calcular progreso del usuario hacia este logro."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            from apps.courses.models import CourseEnrollment, LessonProgress, QuizAttempt
            
            user = request.user
            
            # Calcular estadísticas actuales del usuario
            completed_courses = CourseEnrollment.objects.filter(
                student=user, status='completed'
            ).count()
            
            completed_lessons = LessonProgress.objects.filter(
                enrollment__student=user, is_completed=True
            ).count()
            
            passed_quizzes = QuizAttempt.objects.filter(
                enrollment__student=user, is_passed=True
            ).values('quiz').distinct().count()
            
            try:
                total_fore = float(user.fore_wallet.total_earned)
            except:
                total_fore = 0
            
            # Calcular progreso por criterio
            progress = {}
            
            if obj.required_courses > 0:
                progress['courses'] = {
                    'current': completed_courses,
                    'required': obj.required_courses,
                    'percentage': min(100, (completed_courses / obj.required_courses) * 100)
                }
            
            if obj.required_lessons > 0:
                progress['lessons'] = {
                    'current': completed_lessons,
                    'required': obj.required_lessons,
                    'percentage': min(100, (completed_lessons / obj.required_lessons) * 100)
                }
            
            if obj.required_quizzes > 0:
                progress['quizzes'] = {
                    'current': passed_quizzes,
                    'required': obj.required_quizzes,
                    'percentage': min(100, (passed_quizzes / obj.required_quizzes) * 100)
                }
            
            if obj.required_fore_tokens > 0:
                progress['fore_tokens'] = {
                    'current': total_fore,
                    'required': obj.required_fore_tokens,
                    'percentage': min(100, (total_fore / obj.required_fore_tokens) * 100)
                }
            
            return progress
        
        return {}


class UserAchievementSerializer(serializers.ModelSerializer):
    """Serializer para logros obtenidos por usuarios."""
    
    achievement = AchievementSerializer(read_only=True)
    user_info = serializers.SerializerMethodField()
    
    class Meta:
        model = UserAchievement
        fields = [
            'id', 'achievement', 'earned_at', 'fore_tokens_awarded',
            'progress_when_earned', 'user_info'
        ]
        read_only_fields = ['id', 'earned_at', 'fore_tokens_awarded']
    
    def get_user_info(self, obj):
        """Información básica del usuario."""
        return {
            'id': obj.user.id,
            'username': obj.user.username,
            'full_name': obj.user.get_full_name()
        }


class LeaderboardSerializer(serializers.ModelSerializer):
    """Serializer para rankings/leaderboards."""
    
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    period_display = serializers.CharField(source='get_period_display', read_only=True)
    
    # Top usuarios
    top_users = serializers.SerializerMethodField()
    user_position = serializers.SerializerMethodField()
    
    class Meta:
        model = Leaderboard
        fields = [
            'id', 'title', 'description', 'category', 'category_display',
            'period', 'period_display', 'is_active', 'max_positions',
            'first_place_reward', 'second_place_reward', 'third_place_reward',
            'period_start', 'period_end', 'created_at', 'last_updated',
            'top_users', 'user_position'
        ]
        read_only_fields = ['id', 'created_at', 'last_updated']
    
    def get_top_users(self, obj):
        """Obtener top 10 usuarios del ranking."""
        top_rankings = obj.user_rankings.select_related('user')[:10]
        return UserRankingSerializer(top_rankings, many=True).data
    
    def get_user_position(self, obj):
        """Obtener posición del usuario actual."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            try:
                ranking = obj.user_rankings.get(user=request.user)
                return UserRankingSerializer(ranking).data
            except UserRanking.DoesNotExist:
                return None
        return None


class UserRankingSerializer(serializers.ModelSerializer):
    """Serializer para posiciones individuales en rankings."""
    
    user_info = serializers.SerializerMethodField()
    leaderboard_info = serializers.SerializerMethodField()
    
    class Meta:
        model = UserRanking
        fields = [
            'id', 'position', 'score', 'reward_claimed', 'reward_amount',
            'created_at', 'user_info', 'leaderboard_info'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_user_info(self, obj):
        """Información del usuario."""
        return {
            'id': obj.user.id,
            'username': obj.user.username,
            'full_name': obj.user.get_full_name()
        }
    
    def get_leaderboard_info(self, obj):
        """Información básica del leaderboard (solo si es necesaria)."""
        if self.context.get('include_leaderboard', False):
            return {
                'id': obj.leaderboard.id,
                'title': obj.leaderboard.title,
                'period': obj.leaderboard.period
            }
        return None


class RewardSerializer(serializers.ModelSerializer):
    """Serializer para recompensas del marketplace."""
    
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    is_available = serializers.BooleanField(read_only=True)
    
    # Estado para el usuario actual
    can_redeem_info = serializers.SerializerMethodField()
    user_redemptions_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Reward
        fields = [
            'id', 'title', 'description', 'category', 'category_display',
            'fore_cost', 'image', 'is_active', 'stock_quantity',
            'max_per_user', 'available_from', 'available_until',
            'delivery_info', 'requires_shipping', 'total_redeemed',
            'is_available', 'can_redeem_info', 'user_redemptions_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'total_redeemed', 'created_at', 'updated_at']
    
    def get_can_redeem_info(self, obj):
        """Verificar si el usuario actual puede canjear."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            can_redeem, message = obj.can_redeem(request.user)
            return {'can_redeem': can_redeem, 'message': message}
        return {'can_redeem': False, 'message': 'Debes iniciar sesión'}
    
    def get_user_redemptions_count(self, obj):
        """Número de veces que el usuario ha canjeado esta recompensa."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.redemptions.filter(user=request.user).count()
        return 0


class RewardRedemptionSerializer(serializers.ModelSerializer):
    """Serializer para canjes de recompensas."""
    
    reward = RewardSerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    user_info = serializers.SerializerMethodField()
    
    class Meta:
        model = RewardRedemption
        fields = [
            'id', 'reward', 'fore_cost', 'status', 'status_display',
            'delivery_address', 'delivery_phone', 'tracking_code',
            'redemption_code', 'redeemed_at', 'processed_at', 'completed_at',
            'user_info'
        ]
        read_only_fields = [
            'id', 'fore_cost', 'tracking_code', 'redemption_code',
            'redeemed_at', 'processed_at', 'completed_at'
        ]
    
    def get_user_info(self, obj):
        """Información del usuario."""
        return {
            'id': obj.user.id,
            'username': obj.user.username,
            'full_name': obj.user.get_full_name(),
            'email': obj.user.email
        }


class RedemptionRequestSerializer(serializers.Serializer):
    """Serializer para solicitudes de canje."""
    
    reward_id = serializers.IntegerField()
    delivery_address = serializers.CharField(
        max_length=500,
        required=False,
        allow_blank=True,
        help_text="Requerido para recompensas físicas"
    )
    delivery_phone = serializers.CharField(
        max_length=20,
        required=False,
        allow_blank=True,
        help_text="Teléfono de contacto"
    )
    
    def validate_reward_id(self, value):
        """Validar que la recompensa existe y está disponible."""
        try:
            reward = Reward.objects.get(id=value)
            if not reward.is_available:
                raise serializers.ValidationError("Esta recompensa no está disponible")
            return value
        except Reward.DoesNotExist:
            raise serializers.ValidationError("Recompensa no encontrada")
    
    def validate(self, attrs):
        """Validaciones cruzadas."""
        try:
            reward = Reward.objects.get(id=attrs['reward_id'])
            
            # Verificar si requiere dirección de envío
            if reward.requires_shipping and not attrs.get('delivery_address'):
                raise serializers.ValidationError({
                    'delivery_address': 'Esta recompensa requiere dirección de envío'
                })
        except Reward.DoesNotExist:
            pass  # Ya validado en validate_reward_id
        
        return attrs


class GamificationStatsSerializer(serializers.Serializer):
    """Serializer para estadísticas de gamificación del usuario."""
    
    # Balance FORE
    fore_balance = serializers.DecimalField(max_digits=12, decimal_places=2)
    fore_total_earned = serializers.DecimalField(max_digits=12, decimal_places=2)
    fore_total_spent = serializers.DecimalField(max_digits=12, decimal_places=2)
    
    # Logros
    total_achievements = serializers.IntegerField()
    achievements_by_type = serializers.DictField()
    recent_achievements = UserAchievementSerializer(many=True)
    
    # Rankings
    current_rankings = UserRankingSerializer(many=True)
    best_ranking_position = serializers.IntegerField(allow_null=True)
    
    # Actividad educativa
    total_courses_completed = serializers.IntegerField()
    total_lessons_completed = serializers.IntegerField()
    total_quizzes_passed = serializers.IntegerField()
    
    # Canjes
    total_redemptions = serializers.IntegerField()
    redemptions_by_category = serializers.DictField()
    
    # Progreso hacia siguiente logro
    next_achievements = AchievementSerializer(many=True)