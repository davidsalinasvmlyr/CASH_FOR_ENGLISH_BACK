"""
Configuración del admin para el sistema de recompensas FORE.

Incluye interfaces de administración para:
- Billeteras y transacciones FORE
- Logros y achievements
- Rankings y leaderboards
- Recompensas y canjes
- Estadísticas del sistema
"""

from django.contrib import admin
from django.db.models import Sum, Count
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe

from .models import (
    FOREWallet, Transaction, Achievement, UserAchievement,
    Leaderboard, UserRanking, Reward, RewardRedemption
)


@admin.register(FOREWallet)
class FOREWalletAdmin(admin.ModelAdmin):
    """Administración de billeteras FORE."""
    
    list_display = [
        'user', 'balance', 'total_earned', 'total_spent', 
        'transaction_count', 'created_at', 'updated_at'
    ]
    list_filter = ['created_at', 'updated_at']
    search_fields = ['user__username', 'user__email', 'user__first_name', 'user__last_name']
    readonly_fields = ['created_at', 'updated_at', 'transaction_count', 'last_transaction_link']
    ordering = ['-balance']
    
    fieldsets = (
        ('Usuario', {
            'fields': ('user',)
        }),
        ('Balance FORE', {
            'fields': ('balance', 'total_earned', 'total_spent'),
            'classes': ('wide',),
        }),
        ('Estadísticas', {
            'fields': ('transaction_count', 'last_transaction_link'),
            'classes': ('collapse',),
        }),
        ('Fechas', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    
    def transaction_count(self, obj):
        """Contador de transacciones."""
        count = obj.transactions.count()
        if count > 0:
            url = reverse('admin:rewards_transaction_changelist')
            return format_html(
                '<a href="{}?user__id__exact={}">{} transacciones</a>',
                url, obj.user.id, count
            )
        return '0 transacciones'
    transaction_count.short_description = 'Transacciones'
    
    def last_transaction_link(self, obj):
        """Link a la última transacción."""
        last_transaction = obj.transactions.first()
        if last_transaction:
            url = reverse('admin:rewards_transaction_change', args=[last_transaction.id])
            return format_html(
                '<a href="{}">{}</a>',
                url, last_transaction.created_at.strftime('%d/%m/%Y %H:%M')
            )
        return 'Sin transacciones'
    last_transaction_link.short_description = 'Última transacción'


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    """Administración de transacciones FORE."""
    
    list_display = [
        'user', 'transaction_type', 'amount', 'description',
        'related_content', 'created_at'
    ]
    list_filter = ['transaction_type', 'created_at']
    search_fields = ['user__username', 'description']
    readonly_fields = ['created_at', 'related_content']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    
    fieldsets = (
        ('Transacción', {
            'fields': ('user', 'transaction_type', 'amount', 'description')
        }),
        ('Contenido Relacionado', {
            'fields': ('related_content', 'related_course', 'related_lesson', 'related_quiz', 'related_achievement'),
            'classes': ('collapse',),
        }),
        ('Fecha', {
            'fields': ('created_at',),
            'classes': ('collapse',),
        }),
    )
    
    def related_content(self, obj):
        """Mostrar contenido relacionado."""
        content = []
        if obj.related_course:
            content.append(f"Curso: {obj.related_course.title}")
        if obj.related_lesson:
            content.append(f"Lección: {obj.related_lesson.title}")
        if obj.related_quiz:
            content.append(f"Quiz: {obj.related_quiz.title}")
        if obj.related_achievement:
            content.append(f"Logro: {obj.related_achievement.title}")
        
        return ' | '.join(content) if content else 'Sin contenido relacionado'
    related_content.short_description = 'Contenido relacionado'


@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    """Administración de logros."""
    
    list_display = [
        'title', 'category', 'achievement_type', 'fore_tokens_reward',
        'users_earned_count', 'is_active', 'is_secret'
    ]
    list_filter = ['category', 'achievement_type', 'is_active', 'is_secret']
    search_fields = ['title', 'description']
    readonly_fields = ['users_earned_count', 'created_at']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('title', 'description', 'icon_name')
        }),
        ('Configuración', {
            'fields': ('category', 'achievement_type', 'fore_tokens_reward', 'condition_value')
        }),
        ('Estado', {
            'fields': ('is_active', 'is_secret'),
            'classes': ('wide',),
        }),
        ('Estadísticas', {
            'fields': ('users_earned_count',),
            'classes': ('collapse',),
        }),
        ('Fechas', {
            'fields': ('created_at',),
            'classes': ('collapse',),
        }),
    )
    
    def users_earned_count(self, obj):
        """Contador de usuarios que han ganado el logro."""
        count = obj.user_achievements.count()
        if count > 0:
            url = reverse('admin:rewards_userachievement_changelist')
            return format_html(
                '<a href="{}?achievement__id__exact={}">{} usuarios</a>',
                url, obj.id, count
            )
        return '0 usuarios'
    users_earned_count.short_description = 'Usuarios que lo han ganado'


@admin.register(UserAchievement)
class UserAchievementAdmin(admin.ModelAdmin):
    """Administración de logros de usuarios."""
    
    list_display = ['user', 'achievement', 'earned_at', 'progress_when_earned']
    list_filter = ['achievement__category', 'achievement__achievement_type', 'earned_at']
    search_fields = ['user__username', 'achievement__title']
    readonly_fields = ['earned_at']
    date_hierarchy = 'earned_at'
    ordering = ['-earned_at']
    
    fieldsets = (
        ('Logro Ganado', {
            'fields': ('user', 'achievement', 'progress_when_earned')
        }),
        ('Fecha', {
            'fields': ('earned_at',),
        }),
    )


@admin.register(Leaderboard)
class LeaderboardAdmin(admin.ModelAdmin):
    """Administración de leaderboards."""
    
    list_display = [
        'title', 'category', 'period', 'participants_count',
        'last_updated', 'is_active'
    ]
    list_filter = ['category', 'period', 'is_active', 'last_updated']
    search_fields = ['title', 'description']
    readonly_fields = ['last_updated', 'participants_count', 'top_users']
    actions = ['update_rankings']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('title', 'description', 'icon_name')
        }),
        ('Configuración', {
            'fields': ('category', 'period', 'is_active')
        }),
        ('Estadísticas', {
            'fields': ('participants_count', 'top_users', 'last_updated'),
            'classes': ('collapse',),
        }),
    )
    
    def participants_count(self, obj):
        """Contador de participantes."""
        count = obj.user_rankings.count()
        if count > 0:
            url = reverse('admin:rewards_userranking_changelist')
            return format_html(
                '<a href="{}?leaderboard__id__exact={}">{} participantes</a>',
                url, obj.id, count
            )
        return '0 participantes'
    participants_count.short_description = 'Participantes'
    
    def top_users(self, obj):
        """Top 3 usuarios."""
        top_rankings = obj.user_rankings.select_related('user')[:3]
        if top_rankings:
            users_html = []
            for ranking in top_rankings:
                users_html.append(
                    f"{ranking.position}. {ranking.user.get_full_name() or ranking.user.username} "
                    f"({ranking.score} puntos)"
                )
            return mark_safe('<br>'.join(users_html))
        return 'Sin usuarios'
    top_users.short_description = 'Top 3'
    
    def update_rankings(self, request, queryset):
        """Acción para actualizar rankings."""
        count = 0
        for leaderboard in queryset:
            leaderboard.update_rankings()
            count += 1
        
        self.message_user(
            request,
            f'Se actualizaron {count} leaderboards exitosamente.'
        )
    update_rankings.short_description = 'Actualizar rankings seleccionados'


@admin.register(UserRanking)
class UserRankingAdmin(admin.ModelAdmin):
    """Administración de rankings de usuarios."""
    
    list_display = ['user', 'leaderboard', 'position', 'score', 'created_at']
    list_filter = ['leaderboard__category', 'leaderboard__period', 'created_at']
    search_fields = ['user__username', 'leaderboard__title']
    readonly_fields = ['created_at']
    ordering = ['leaderboard', 'position']
    
    fieldsets = (
        ('Ranking', {
            'fields': ('user', 'leaderboard', 'position', 'score')
        }),
        ('Fecha', {
            'fields': ('created_at',),
        }),
    )


@admin.register(Reward)
class RewardAdmin(admin.ModelAdmin):
    """Administración de recompensas."""
    
    list_display = [
        'title', 'category', 'fore_cost', 'stock_status',
        'total_redeemed', 'is_active'
    ]
    list_filter = ['category', 'is_active', 'created_at']
    search_fields = ['title', 'description']
    readonly_fields = ['total_redeemed', 'created_at', 'updated_at', 'redemptions_link']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('title', 'description', 'image_url')
        }),
        ('Configuración', {
            'fields': ('category', 'fore_cost', 'stock_quantity', 'is_active')
        }),
        ('Restricciones', {
            'fields': ('requires_address', 'requires_phone', 'terms_conditions'),
            'classes': ('collapse',),
        }),
        ('Estadísticas', {
            'fields': ('total_redeemed', 'redemptions_link'),
            'classes': ('collapse',),
        }),
        ('Fechas', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    
    def stock_status(self, obj):
        """Estado del stock."""
        if obj.stock_quantity is None:
            return format_html('<span style="color: green;">Ilimitado</span>')
        elif obj.stock_quantity <= 0:
            return format_html('<span style="color: red;">Agotado</span>')
        elif obj.stock_quantity <= 5:
            return format_html('<span style="color: orange;">{} restantes</span>', obj.stock_quantity)
        else:
            return format_html('<span style="color: green;">{} disponibles</span>', obj.stock_quantity)
    stock_status.short_description = 'Stock'
    
    def redemptions_link(self, obj):
        """Link a los canjes."""
        count = obj.redemptions.count()
        if count > 0:
            url = reverse('admin:rewards_rewardredemption_changelist')
            return format_html(
                '<a href="{}?reward__id__exact={}">{} canjes</a>',
                url, obj.id, count
            )
        return '0 canjes'
    redemptions_link.short_description = 'Canjes realizados'


@admin.register(RewardRedemption)
class RewardRedemptionAdmin(admin.ModelAdmin):
    """Administración de canjes de recompensas."""
    
    list_display = [
        'user', 'reward', 'status', 'redeemed_at',
        'processed_at', 'tracking_code'
    ]
    list_filter = ['status', 'redeemed_at', 'processed_at']
    search_fields = ['user__username', 'reward__title', 'tracking_code']
    readonly_fields = ['redeemed_at', 'reward_cost']
    date_hierarchy = 'redeemed_at'
    ordering = ['-redeemed_at']
    actions = ['mark_as_shipped', 'mark_as_delivered']
    
    fieldsets = (
        ('Canje', {
            'fields': ('user', 'reward', 'reward_cost', 'redeemed_at')
        }),
        ('Entrega', {
            'fields': ('status', 'delivery_address', 'delivery_phone', 'tracking_code', 'processed_at')
        }),
        ('Códigos', {
            'fields': ('redemption_code',),
            'classes': ('collapse',),
        }),
    )
    
    def reward_cost(self, obj):
        """Costo de la recompensa."""
        return f"{obj.reward.fore_cost} FORE tokens"
    reward_cost.short_description = 'Costo'
    
    def mark_as_shipped(self, request, queryset):
        """Marcar como enviado."""
        count = queryset.update(status='shipped')
        self.message_user(
            request,
            f'Se marcaron {count} canjes como enviados.'
        )
    mark_as_shipped.short_description = 'Marcar como enviado'
    
    def mark_as_delivered(self, request, queryset):
        """Marcar como entregado."""
        from django.utils import timezone
        count = queryset.update(status='delivered', processed_at=timezone.now())
        self.message_user(
            request,
            f'Se marcaron {count} canjes como entregados.'
        )
    mark_as_delivered.short_description = 'Marcar como entregado'


# Configuración adicional del admin site
admin.site.site_header = 'Cash for English - Sistema FORE'
admin.site.site_title = 'Admin FORE'
admin.site.index_title = 'Administración del Sistema de Recompensas'
