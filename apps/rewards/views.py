"""
Views para la API del sistema de recompensas FORE.

Este módulo contiene las vistas para:
- Gestión de billeteras y balance FORE  
- Historial de transacciones
- Logros y achievements
- Rankings y leaderboards
- Marketplace y canjes
"""

from django.db import models
from django.db.models import Count, Sum, Max, Avg, Min, Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.users.permissions import IsStudent, IsTeacher, IsAdminUser
from .models import (
    FOREWallet, Transaction, Achievement, UserAchievement,
    Leaderboard, UserRanking, Reward, RewardRedemption
)
from .serializers import (
    FOREWalletSerializer, TransactionSerializer, AchievementSerializer,
    UserAchievementSerializer, LeaderboardSerializer, UserRankingSerializer,
    RewardSerializer, RewardRedemptionSerializer, RedemptionRequestSerializer,
    GamificationStatsSerializer
)


class FOREWalletViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para consultar información de billeteras FORE.
    
    Solo permite lectura para el usuario propietario.
    """
    
    serializer_class = FOREWalletSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Solo la billetera del usuario actual."""
        return FOREWallet.objects.filter(user=self.request.user)
    
    def get_object(self):
        """Obtener o crear billetera del usuario actual."""
        wallet, created = FOREWallet.objects.get_or_create(
            user=self.request.user
        )
        return wallet
    
    @action(detail=False, methods=['get'])
    def my_wallet(self, request):
        """Obtener billetera del usuario actual."""
        wallet = self.get_object()
        serializer = self.get_serializer(wallet)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def transactions(self, request):
        """Obtener historial de transacciones del usuario."""
        transactions = Transaction.objects.filter(
            user=request.user
        ).select_related(
            'related_course', 'related_lesson', 'related_quiz', 'related_achievement'
        ).order_by('-created_at')
        
        # Filtros opcionales
        transaction_type = request.query_params.get('type', None)
        if transaction_type:
            transactions = transactions.filter(transaction_type=transaction_type)
        
        # Paginación
        page = self.paginate_queryset(transactions)
        if page is not None:
            serializer = TransactionSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = TransactionSerializer(transactions, many=True, context={'request': request})
        return Response(serializer.data)


class AchievementViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para visualizar logros disponibles.
    
    Permite ver todos los logros y el progreso del usuario.
    """
    
    serializer_class = AchievementSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Obtener logros según el usuario."""
        queryset = Achievement.objects.filter(is_active=True)
        
        # Los logros secretos solo se muestran si ya los tiene el usuario
        if not self.request.user.is_staff:
            user_achievements = self.request.user.achievements_earned.values_list(
                'achievement_id', flat=True
            )
            queryset = queryset.filter(
                Q(is_secret=False) | Q(id__in=user_achievements)
            )
        
        # Filtros opcionales
        category = self.request.query_params.get('category', None)
        if category:
            queryset = queryset.filter(category=category)
        
        achievement_type = self.request.query_params.get('type', None)
        if achievement_type:
            queryset = queryset.filter(achievement_type=achievement_type)
        
        return queryset.order_by('category', 'achievement_type', 'fore_tokens_reward')
    
    @action(detail=False, methods=['get'])
    def my_achievements(self, request):
        """Obtener logros del usuario actual."""
        user_achievements = UserAchievement.objects.filter(
            user=request.user
        ).select_related('achievement').order_by('-earned_at')
        
        serializer = UserAchievementSerializer(
            user_achievements, 
            many=True, 
            context={'request': request}
        )
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def check_all(self, request):
        """Verificar todos los logros para el usuario actual."""
        from .signals import check_achievements_for_user
        
        check_achievements_for_user(request.user, 'manual_check')
        
        return Response({
            'message': 'Verificación de logros completada',
            'timestamp': timezone.now()
        })


class LeaderboardViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para visualizar rankings y leaderboards.
    
    Permite ver diferentes tipos de clasificaciones.
    """
    
    serializer_class = LeaderboardSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Leaderboard.objects.filter(is_active=True)
    
    def get_queryset(self):
        """Filtrar leaderboards activos."""
        queryset = super().get_queryset()
        
        # Filtros opcionales
        category = self.request.query_params.get('category', None)
        if category:
            queryset = queryset.filter(category=category)
        
        period = self.request.query_params.get('period', None)
        if period:
            queryset = queryset.filter(period=period)
        
        return queryset.order_by('category', 'period')
    
    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def update_rankings(self, request, pk=None):
        """Actualizar rankings de un leaderboard (solo admin)."""
        leaderboard = self.get_object()
        leaderboard.update_rankings()
        
        return Response({
            'message': f'Rankings actualizados para {leaderboard.title}',
            'last_updated': leaderboard.last_updated
        })
    
    @action(detail=True, methods=['get'])
    def full_rankings(self, request, pk=None):
        """Obtener rankings completos de un leaderboard."""
        leaderboard = self.get_object()
        rankings = leaderboard.user_rankings.select_related('user').all()
        
        # Paginación
        page = self.paginate_queryset(rankings)
        if page is not None:
            serializer = UserRankingSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = UserRankingSerializer(rankings, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def my_rankings(self, request):
        """Obtener todas las posiciones del usuario actual."""
        rankings = UserRanking.objects.filter(
            user=request.user,
            leaderboard__is_active=True
        ).select_related('leaderboard').order_by('position')
        
        serializer = UserRankingSerializer(
            rankings, 
            many=True,
            context={'include_leaderboard': True}
        )
        return Response(serializer.data)


class RewardViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para el marketplace de recompensas.
    
    Permite ver recompensas disponibles y realizar canjes.
    """
    
    serializer_class = RewardSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Obtener recompensas disponibles."""
        queryset = Reward.objects.filter(is_active=True)
        
        # Filtros opcionales
        category = self.request.query_params.get('category', None)
        if category:
            queryset = queryset.filter(category=category)
        
        min_cost = self.request.query_params.get('min_cost', None)
        if min_cost:
            queryset = queryset.filter(fore_cost__gte=int(min_cost))
        
        max_cost = self.request.query_params.get('max_cost', None)
        if max_cost:
            queryset = queryset.filter(fore_cost__lte=int(max_cost))
        
        # Ordenamiento
        ordering = self.request.query_params.get('ordering', 'fore_cost')
        if ordering in ['fore_cost', '-fore_cost', 'title', '-title', '-created_at']:
            queryset = queryset.order_by(ordering)
        
        return queryset
    
    @action(detail=True, methods=['post'], permission_classes=[IsStudent])
    def redeem(self, request, pk=None):
        """Canjear una recompensa por tokens FORE."""
        reward = self.get_object()
        
        # Validar datos de canje
        serializer = RedemptionRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # Verificar si puede canjear
        can_redeem, message = reward.can_redeem(request.user)
        if not can_redeem:
            return Response(
                {'error': message},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Obtener billetera
            wallet = request.user.fore_wallet
            
            # Gastar tokens
            wallet.spend_tokens(
                amount=reward.fore_cost,
                description=f"Canje de recompensa: {reward.title}",
                transaction_type='reward_purchase'
            )
            
            # Crear registro de canje
            redemption = RewardRedemption.objects.create(
                user=request.user,
                reward=reward,
                delivery_address=serializer.validated_data.get('delivery_address', ''),
                delivery_phone=serializer.validated_data.get('delivery_phone', '')
            )
            
            # Actualizar estadísticas de la recompensa
            reward.total_redeemed += 1
            if reward.stock_quantity is not None:
                reward.stock_quantity -= 1
            reward.save()
            
            # Respuesta
            response_serializer = RewardRedemptionSerializer(
                redemption, 
                context={'request': request}
            )
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['get'], permission_classes=[IsStudent])
    def my_redemptions(self, request):
        """Obtener canjes del usuario actual."""
        redemptions = RewardRedemption.objects.filter(
            user=request.user
        ).select_related('reward').order_by('-redeemed_at')
        
        # Paginación
        page = self.paginate_queryset(redemptions)
        if page is not None:
            serializer = RewardRedemptionSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = RewardRedemptionSerializer(redemptions, many=True, context={'request': request})
        return Response(serializer.data)


class GamificationDashboardView(generics.GenericAPIView):
    """
    Vista para el dashboard de gamificación del estudiante.
    
    Proporciona un resumen completo de estadísticas FORE, logros,
    rankings y progreso del usuario.
    """
    
    permission_classes = [IsStudent]
    serializer_class = GamificationStatsSerializer
    
    def get(self, request):
        """Obtener estadísticas completas de gamificación."""
        user = request.user
        
        # Balance FORE
        try:
            wallet = user.fore_wallet
            fore_balance = wallet.balance
            fore_total_earned = wallet.total_earned
            fore_total_spent = wallet.total_spent
        except FOREWallet.DoesNotExist:
            fore_balance = fore_total_earned = fore_total_spent = 0
        
        # Logros
        user_achievements = user.achievements_earned.select_related('achievement')
        total_achievements = user_achievements.count()
        
        achievements_by_type = user_achievements.values(
            'achievement__achievement_type'
        ).annotate(count=Count('id'))
        
        achievements_by_type_dict = {
            item['achievement__achievement_type']: item['count'] 
            for item in achievements_by_type
        }
        
        recent_achievements = user_achievements.order_by('-earned_at')[:5]
        
        # Rankings actuales
        current_rankings = user.ranking_positions.filter(
            leaderboard__is_active=True
        ).select_related('leaderboard')
        
        best_ranking_position = current_rankings.aggregate(
            best=Min('position')
        )['best']
        
        # Actividad educativa
        from apps.courses.models import CourseEnrollment, LessonProgress, QuizAttempt
        
        total_courses_completed = CourseEnrollment.objects.filter(
            student=user, status='completed'
        ).count()
        
        total_lessons_completed = LessonProgress.objects.filter(
            enrollment__student=user, is_completed=True
        ).count()
        
        total_quizzes_passed = QuizAttempt.objects.filter(
            enrollment__student=user, is_passed=True
        ).values('quiz').distinct().count()
        
        # Canjes
        redemptions = user.reward_redemptions.all()
        total_redemptions = redemptions.count()
        
        redemptions_by_category = redemptions.values(
            'reward__category'
        ).annotate(count=Count('id'))
        
        redemptions_by_category_dict = {
            item['reward__category']: item['count']
            for item in redemptions_by_category
        }
        
        # Próximos logros (hasta 5)
        available_achievements = Achievement.objects.filter(
            is_active=True,
            is_secret=False
        ).exclude(
            user_achievements__user=user
        )[:5]
        
        # Construir respuesta
        data = {
            'fore_balance': fore_balance,
            'fore_total_earned': fore_total_earned,
            'fore_total_spent': fore_total_spent,
            'total_achievements': total_achievements,
            'achievements_by_type': achievements_by_type_dict,
            'recent_achievements': UserAchievementSerializer(
                recent_achievements, 
                many=True, 
                context={'request': request}
            ).data,
            'current_rankings': UserRankingSerializer(
                current_rankings, 
                many=True,
                context={'include_leaderboard': True}
            ).data,
            'best_ranking_position': best_ranking_position,
            'total_courses_completed': total_courses_completed,
            'total_lessons_completed': total_lessons_completed,
            'total_quizzes_passed': total_quizzes_passed,
            'total_redemptions': total_redemptions,
            'redemptions_by_category': redemptions_by_category_dict,
            'next_achievements': AchievementSerializer(
                available_achievements,
                many=True,
                context={'request': request}
            ).data
        }
        
        return Response(data)


class AdminRewardsView(generics.GenericAPIView):
    """
    Vista administrativa para gestionar el sistema de recompensas.
    
    Solo disponible para administradores.
    """
    
    permission_classes = [IsAdminUser]
    
    @action(detail=False, methods=['post'])
    def update_all_leaderboards(self, request):
        """Actualizar todos los leaderboards activos."""
        leaderboards = Leaderboard.objects.filter(is_active=True)
        
        updated_count = 0
        for leaderboard in leaderboards:
            leaderboard.update_rankings()
            updated_count += 1
        
        return Response({
            'message': f'Se actualizaron {updated_count} leaderboards',
            'timestamp': timezone.now()
        })
    
    @action(detail=False, methods=['post'])
    def create_initial_data(self, request):
        """Crear datos iniciales (logros, leaderboards, recompensas)."""
        from .signals import (
            create_initial_achievements, 
            create_initial_leaderboards,
            create_initial_rewards
        )
        
        try:
            create_initial_achievements()
            create_initial_leaderboards() 
            create_initial_rewards()
            
            return Response({
                'message': 'Datos iniciales creados exitosamente',
                'timestamp': timezone.now()
            })
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def get(self, request):
        """Obtener estadísticas administrativas del sistema."""
        # Estadísticas generales
        total_wallets = FOREWallet.objects.count()
        total_transactions = Transaction.objects.count()
        total_fore_in_circulation = FOREWallet.objects.aggregate(
            total=Sum('balance')
        )['total'] or 0
        
        total_achievements_earned = UserAchievement.objects.count()
        total_redemptions = RewardRedemption.objects.count()
        
        # Top usuarios por FORE ganado
        top_earners = FOREWallet.objects.select_related('user').order_by(
            '-total_earned'
        )[:10]
        
        return Response({
            'stats': {
                'total_wallets': total_wallets,
                'total_transactions': total_transactions,
                'total_fore_in_circulation': float(total_fore_in_circulation),
                'total_achievements_earned': total_achievements_earned,
                'total_redemptions': total_redemptions,
            },
            'top_earners': [{
                'user_id': wallet.user.id,
                'username': wallet.user.username,
                'full_name': wallet.user.get_full_name(),
                'total_earned': float(wallet.total_earned),
                'balance': float(wallet.balance)
            } for wallet in top_earners]
        })
