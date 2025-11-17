"""
URLs para la API del sistema de recompensas FORE.

Incluye endpoints para:
- Billeteras FORE y transacciones
- Logros y achievements
- Rankings y leaderboards  
- Marketplace y canjes
- Dashboard de gamificación
- Administración del sistema
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    FOREWalletViewSet, AchievementViewSet, LeaderboardViewSet, 
    RewardViewSet, GamificationDashboardView, AdminRewardsView
)

app_name = 'rewards'

# Router para ViewSets
router = DefaultRouter()
router.register(r'wallet', FOREWalletViewSet, basename='wallet')
router.register(r'achievements', AchievementViewSet, basename='achievements')  
router.register(r'leaderboards', LeaderboardViewSet, basename='leaderboards')
router.register(r'rewards', RewardViewSet, basename='rewards')

urlpatterns = [
    # ViewSets con router
    path('', include(router.urls)),
    
    # Dashboard de gamificación para estudiantes
    path('dashboard/', GamificationDashboardView.as_view(), name='dashboard'),
    
    # Administración del sistema (solo admin)
    path('admin/', AdminRewardsView.as_view(), name='admin'),
    
    # Endpoints adicionales específicos
    path('wallet/my/', FOREWalletViewSet.as_view({'get': 'my_wallet'}), name='my-wallet'),
    path('wallet/transactions/', FOREWalletViewSet.as_view({'get': 'transactions'}), name='wallet-transactions'),
    
    path('achievements/my/', AchievementViewSet.as_view({'get': 'my_achievements'}), name='my-achievements'),
    path('achievements/check/', AchievementViewSet.as_view({'post': 'check_all'}), name='check-achievements'),
    
    path('leaderboards/my-rankings/', LeaderboardViewSet.as_view({'get': 'my_rankings'}), name='my-rankings'),
    
    path('rewards/my-redemptions/', RewardViewSet.as_view({'get': 'my_redemptions'}), name='my-redemptions'),
]