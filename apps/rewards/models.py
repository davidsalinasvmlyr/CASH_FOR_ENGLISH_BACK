"""
Modelos para el sistema de recompensas FORE y gamificación.

Este módulo contiene los modelos para:
- Gestión de tokens FORE
- Sistema de transacciones
- Logros y badges
- Rankings y leaderboards
- Marketplace de recompensas
"""

from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from decimal import Decimal


class FOREWallet(models.Model):
    """
    Modelo para la billetera de tokens FORE de cada usuario.
    
    Gestiona el balance actual y estadísticas de tokens.
    """
    
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='fore_wallet',
        verbose_name=_('Usuario')
    )
    
    # Balance actual
    balance = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name=_('Balance FORE'),
        help_text=_('Balance actual de tokens FORE')
    )
    
    # Estadísticas históricas
    total_earned = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name=_('Total ganado'),
        help_text=_('Total de tokens FORE ganados históricamente')
    )
    
    total_spent = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name=_('Total gastado'),
        help_text=_('Total de tokens FORE gastados históricamente')
    )
    
    # Metadatos
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Fecha de creación')
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Última actualización')
    )
    
    # Bloqueos temporales (para transacciones en proceso)
    frozen_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name=_('Cantidad congelada'),
        help_text=_('Tokens temporalmente no disponibles')
    )
    
    class Meta:
        verbose_name = _('Billetera FORE')
        verbose_name_plural = _('Billeteras FORE')
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['balance']),
        ]
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.balance} FORE"
    
    @property
    def available_balance(self):
        """Balance disponible para gastar."""
        return self.balance - self.frozen_amount
    
    def can_spend(self, amount):
        """Verificar si puede gastar una cantidad específica."""
        return self.available_balance >= Decimal(str(amount))
    
    def add_tokens(self, amount, description="", transaction_type="EARNED"):
        """
        Agregar tokens a la billetera.
        
        Args:
            amount: Cantidad de tokens a agregar
            description: Descripción de la transacción
            transaction_type: Tipo de transacción
        """
        amount = Decimal(str(amount))
        
        if amount <= 0:
            raise ValueError("La cantidad debe ser positiva")
        
        # Actualizar balance
        self.balance += amount
        self.total_earned += amount
        self.save()
        
        # Crear transacción
        Transaction.objects.create(
            user=self.user,
            transaction_type=transaction_type,
            amount=amount,
            balance_after=self.balance,
            description=description
        )
        
        return self.balance
    
    def spend_tokens(self, amount, description="", transaction_type="SPENT"):
        """
        Gastar tokens de la billetera.
        
        Args:
            amount: Cantidad de tokens a gastar
            description: Descripción de la transacción  
            transaction_type: Tipo de transacción
        """
        amount = Decimal(str(amount))
        
        if not self.can_spend(amount):
            raise ValueError("Balance insuficiente")
        
        # Actualizar balance
        self.balance -= amount
        self.total_spent += amount
        self.save()
        
        # Crear transacción
        Transaction.objects.create(
            user=self.user,
            transaction_type=transaction_type,
            amount=-amount,  # Negativo para gastos
            balance_after=self.balance,
            description=description
        )
        
        return self.balance


class TransactionType(models.TextChoices):
    """Tipos de transacciones FORE."""
    # Ganancias
    LESSON_COMPLETED = 'lesson_completed', _('Lección completada')
    QUIZ_PASSED = 'quiz_passed', _('Quiz aprobado')
    COURSE_COMPLETED = 'course_completed', _('Curso completado')
    ACHIEVEMENT_EARNED = 'achievement_earned', _('Logro obtenido')
    DAILY_LOGIN = 'daily_login', _('Login diario')
    REFERRAL_BONUS = 'referral_bonus', _('Bonus por referido')
    ADMIN_BONUS = 'admin_bonus', _('Bonus administrativo')
    
    # Gastos
    REWARD_PURCHASE = 'reward_purchase', _('Compra de recompensa')
    PREMIUM_FEATURE = 'premium_feature', _('Función premium')
    MARKETPLACE_PURCHASE = 'marketplace_purchase', _('Compra en marketplace')
    
    # Otros
    TRANSFER_IN = 'transfer_in', _('Transferencia recibida')
    TRANSFER_OUT = 'transfer_out', _('Transferencia enviada')
    REFUND = 'refund', _('Reembolso')
    ADJUSTMENT = 'adjustment', _('Ajuste manual')


class Transaction(models.Model):
    """
    Modelo para el historial de transacciones de tokens FORE.
    
    Registra cada movimiento de tokens con detalles completos.
    """
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='fore_transactions',
        verbose_name=_('Usuario')
    )
    
    transaction_type = models.CharField(
        max_length=30,
        choices=TransactionType.choices,
        verbose_name=_('Tipo de transacción')
    )
    
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name=_('Cantidad'),
        help_text=_('Cantidad de tokens (positiva para ganancias, negativa para gastos)')
    )
    
    balance_after = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name=_('Balance después'),
        help_text=_('Balance total después de la transacción')
    )
    
    description = models.TextField(
        blank=True,
        verbose_name=_('Descripción'),
        help_text=_('Descripción detallada de la transacción')
    )
    
    # Referencias a objetos relacionados
    related_course = models.ForeignKey(
        'courses.Course',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name=_('Curso relacionado')
    )
    
    related_lesson = models.ForeignKey(
        'courses.Lesson',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name=_('Lección relacionada')
    )
    
    related_quiz = models.ForeignKey(
        'courses.Quiz',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name=_('Quiz relacionado')
    )
    
    related_achievement = models.ForeignKey(
        'Achievement',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name=_('Logro relacionado')
    )
    
    # Metadatos
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Fecha de transacción')
    )
    
    # Campo para transacciones administrativas
    created_by_admin = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='fore_transactions_created',
        verbose_name=_('Creada por admin')
    )
    
    class Meta:
        verbose_name = _('Transacción FORE')
        verbose_name_plural = _('Transacciones FORE')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['transaction_type']),
            models.Index(fields=['-created_at']),
        ]
    
    def __str__(self):
        sign = "+" if self.amount >= 0 else ""
        return f"{self.user.get_full_name()} - {sign}{self.amount} FORE ({self.get_transaction_type_display()})"
    
    @property
    def is_earning(self):
        """Verificar si es una transacción de ganancia."""
        return self.amount > 0
    
    @property
    def is_spending(self):
        """Verificar si es una transacción de gasto."""
        return self.amount < 0


class AchievementCategory(models.TextChoices):
    """Categorías de logros."""
    LEARNING = 'learning', _('Aprendizaje')
    PROGRESS = 'progress', _('Progreso')
    SOCIAL = 'social', _('Social')
    CONSISTENCY = 'consistency', _('Consistencia')
    MASTERY = 'mastery', _('Dominio')
    SPECIAL = 'special', _('Especial')


class AchievementType(models.TextChoices):
    """Tipos de logros según su dificultad."""
    BRONZE = 'bronze', _('Bronce')
    SILVER = 'silver', _('Plata')
    GOLD = 'gold', _('Oro')
    PLATINUM = 'platinum', _('Platino')
    DIAMOND = 'diamond', _('Diamante')


class Achievement(models.Model):
    """
    Modelo para definir logros disponibles en la plataforma.
    
    Los logros son metas que los estudiantes pueden alcanzar
    para ganar tokens FORE adicionales y badges.
    """
    
    title = models.CharField(
        max_length=100,
        verbose_name=_('Título'),
        help_text=_('Nombre del logro')
    )
    
    description = models.TextField(
        verbose_name=_('Descripción'),
        help_text=_('Descripción detallada de cómo obtener el logro')
    )
    
    category = models.CharField(
        max_length=20,
        choices=AchievementCategory.choices,
        verbose_name=_('Categoría')
    )
    
    achievement_type = models.CharField(
        max_length=20,
        choices=AchievementType.choices,
        default=AchievementType.BRONZE,
        verbose_name=_('Tipo')
    )
    
    # Icono y visual
    icon = models.ImageField(
        upload_to='achievements/icons/',
        blank=True,
        null=True,
        verbose_name=_('Icono'),
        help_text=_('Imagen del logro (recomendado: 128x128px)')
    )
    
    badge_color = models.CharField(
        max_length=7,
        default='#FFD700',
        verbose_name=_('Color del badge'),
        help_text=_('Color en formato hexadecimal (#RRGGBB)')
    )
    
    # Recompensa
    fore_tokens_reward = models.PositiveIntegerField(
        verbose_name=_('Recompensa FORE'),
        help_text=_('Tokens FORE otorgados al obtener el logro')
    )
    
    # Criterios de obtención
    required_courses = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Cursos requeridos'),
        help_text=_('Número de cursos que se deben completar')
    )
    
    required_lessons = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Lecciones requeridas'),
        help_text=_('Número de lecciones que se deben completar')
    )
    
    required_quizzes = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Quizzes requeridos'),
        help_text=_('Número de quizzes que se deben aprobar')
    )
    
    required_streak_days = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Días de racha requeridos'),
        help_text=_('Días consecutivos de actividad requeridos')
    )
    
    required_fore_tokens = models.PositiveIntegerField(
        default=0,
        verbose_name=_('FORE tokens requeridos'),
        help_text=_('Total de tokens FORE que se deben haber ganado')
    )
    
    # Configuración
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Activo'),
        help_text=_('Si el logro está disponible para obtener')
    )
    
    is_secret = models.BooleanField(
        default=False,
        verbose_name=_('Secreto'),
        help_text=_('Los logros secretos no se muestran hasta obtenerlos')
    )
    
    max_recipients = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name=_('Máximo de receptores'),
        help_text=_('Límite de usuarios que pueden obtener este logro')
    )
    
    # Metadatos
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Fecha de creación')
    )
    
    class Meta:
        verbose_name = _('Logro')
        verbose_name_plural = _('Logros')
        ordering = ['category', 'achievement_type', 'title']
        indexes = [
            models.Index(fields=['category', 'is_active']),
            models.Index(fields=['achievement_type']),
        ]
    
    def __str__(self):
        return f"{self.title} ({self.get_achievement_type_display()})"
    
    @property
    def recipients_count(self):
        """Número de usuarios que han obtenido este logro."""
        return self.user_achievements.count()
    
    @property
    def is_available(self):
        """Verificar si el logro está disponible."""
        if not self.is_active:
            return False
        
        if self.max_recipients and self.recipients_count >= self.max_recipients:
            return False
        
        return True
    
    def check_achievement(self, user):
        """
        Verificar si un usuario cumple los criterios para este logro.
        
        Args:
            user: Usuario a verificar
            
        Returns:
            bool: True si cumple los criterios
        """
        # Verificar si ya tiene el logro
        if self.user_achievements.filter(user=user).exists():
            return False
        
        # Verificar si el logro está disponible
        if not self.is_available:
            return False
        
        # Obtener estadísticas del usuario
        from apps.courses.models import CourseEnrollment, LessonProgress, QuizAttempt
        
        # Verificar cursos completados
        if self.required_courses > 0:
            completed_courses = CourseEnrollment.objects.filter(
                student=user,
                status='completed'
            ).count()
            if completed_courses < self.required_courses:
                return False
        
        # Verificar lecciones completadas
        if self.required_lessons > 0:
            completed_lessons = LessonProgress.objects.filter(
                enrollment__student=user,
                is_completed=True
            ).count()
            if completed_lessons < self.required_lessons:
                return False
        
        # Verificar quizzes aprobados
        if self.required_quizzes > 0:
            passed_quizzes = QuizAttempt.objects.filter(
                enrollment__student=user,
                is_passed=True
            ).values('quiz').distinct().count()
            if passed_quizzes < self.required_quizzes:
                return False
        
        # Verificar tokens FORE ganados
        if self.required_fore_tokens > 0:
            try:
                wallet = user.fore_wallet
                if wallet.total_earned < self.required_fore_tokens:
                    return False
            except FOREWallet.DoesNotExist:
                return False
        
        # Verificar racha de días (implementación básica)
        # TODO: Implementar sistema de racha más sofisticado
        
        return True


class UserAchievement(models.Model):
    """
    Modelo para registrar logros obtenidos por usuarios.
    
    Representa la relación many-to-many entre usuarios y logros
    con información adicional sobre cuándo se obtuvo.
    """
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='achievements_earned',
        verbose_name=_('Usuario')
    )
    
    achievement = models.ForeignKey(
        Achievement,
        on_delete=models.CASCADE,
        related_name='user_achievements',
        verbose_name=_('Logro')
    )
    
    earned_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Obtenido en')
    )
    
    # Información adicional del momento de obtención
    fore_tokens_awarded = models.PositiveIntegerField(
        verbose_name=_('FORE tokens otorgados'),
        help_text=_('Cantidad de tokens otorgados al obtener el logro')
    )
    
    progress_when_earned = models.JSONField(
        default=dict,
        verbose_name=_('Progreso al obtener'),
        help_text=_('Estadísticas del usuario al momento de obtener el logro')
    )
    
    class Meta:
        verbose_name = _('Logro de Usuario')
        verbose_name_plural = _('Logros de Usuarios')
        unique_together = [['user', 'achievement']]
        ordering = ['-earned_at']
        indexes = [
            models.Index(fields=['user', '-earned_at']),
            models.Index(fields=['achievement']),
        ]
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.achievement.title}"
    
    def save(self, *args, **kwargs):
        """Asignar tokens FORE automáticamente."""
        if not self.fore_tokens_awarded:
            self.fore_tokens_awarded = self.achievement.fore_tokens_reward
        
        super().save(*args, **kwargs)


class LeaderboardPeriod(models.TextChoices):
    """Períodos para leaderboards."""
    DAILY = 'daily', _('Diario')
    WEEKLY = 'weekly', _('Semanal')
    MONTHLY = 'monthly', _('Mensual')
    ALL_TIME = 'all_time', _('Todo el tiempo')


class LeaderboardCategory(models.TextChoices):
    """Categorías de rankings."""
    FORE_TOKENS = 'fore_tokens', _('FORE Tokens Ganados')
    COURSES_COMPLETED = 'courses_completed', _('Cursos Completados')
    LESSONS_COMPLETED = 'lessons_completed', _('Lecciones Completadas')
    QUIZZES_PASSED = 'quizzes_passed', _('Quizzes Aprobados')
    ACHIEVEMENTS_EARNED = 'achievements_earned', _('Logros Obtenidos')
    STREAK_DAYS = 'streak_days', _('Días de Racha')


class Leaderboard(models.Model):
    """
    Modelo para gestionar diferentes tipos de clasificaciones.
    
    Define los diferentes rankings disponibles en la plataforma.
    """
    
    title = models.CharField(
        max_length=100,
        verbose_name=_('Título'),
        help_text=_('Nombre del ranking')
    )
    
    description = models.TextField(
        blank=True,
        verbose_name=_('Descripción'),
        help_text=_('Descripción del criterio de ranking')
    )
    
    category = models.CharField(
        max_length=20,
        choices=LeaderboardCategory.choices,
        verbose_name=_('Categoría')
    )
    
    period = models.CharField(
        max_length=20,
        choices=LeaderboardPeriod.choices,
        verbose_name=_('Período')
    )
    
    # Configuración
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Activo')
    )
    
    max_positions = models.PositiveIntegerField(
        default=100,
        verbose_name=_('Máximo de posiciones'),
        help_text=_('Número máximo de posiciones a mostrar')
    )
    
    # Recompensas por posición
    first_place_reward = models.PositiveIntegerField(
        default=100,
        verbose_name=_('Recompensa 1er lugar'),
        help_text=_('FORE tokens para el primer lugar')
    )
    
    second_place_reward = models.PositiveIntegerField(
        default=75,
        verbose_name=_('Recompensa 2do lugar'),
        help_text=_('FORE tokens para el segundo lugar')
    )
    
    third_place_reward = models.PositiveIntegerField(
        default=50,
        verbose_name=_('Recompensa 3er lugar'),
        help_text=_('FORE tokens para el tercer lugar')
    )
    
    # Fechas para rankings periódicos
    period_start = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_('Inicio del período')
    )
    
    period_end = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_('Fin del período')
    )
    
    # Metadatos
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Fecha de creación')
    )
    
    last_updated = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Última actualización')
    )
    
    class Meta:
        verbose_name = _('Ranking')
        verbose_name_plural = _('Rankings')
        ordering = ['category', 'period']
        indexes = [
            models.Index(fields=['category', 'period']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"{self.title} ({self.get_period_display()})"
    
    def update_rankings(self):
        """Actualizar las posiciones del ranking."""
        from apps.courses.models import CourseEnrollment, LessonProgress, QuizAttempt
        from django.contrib.auth import get_user_model
        
        User = get_user_model()
        
        # Limpiar rankings existentes para este período
        self.user_rankings.all().delete()
        
        # Obtener usuarios activos (solo estudiantes)
        users = User.objects.filter(role='student', is_active=True)
        
        user_scores = []
        
        for user in users:
            score = 0
            
            if self.category == LeaderboardCategory.FORE_TOKENS:
                try:
                    wallet = user.fore_wallet
                    if self.period == LeaderboardPeriod.ALL_TIME:
                        score = float(wallet.total_earned)
                    else:
                        # Calcular por período específico
                        period_start = self._get_period_start()
                        period_transactions = user.fore_transactions.filter(
                            created_at__gte=period_start,
                            amount__gt=0  # Solo ganancias
                        )
                        score = float(sum(t.amount for t in period_transactions))
                except FOREWallet.DoesNotExist:
                    score = 0
            
            elif self.category == LeaderboardCategory.COURSES_COMPLETED:
                query = CourseEnrollment.objects.filter(
                    student=user,
                    status='completed'
                )
                if self.period != LeaderboardPeriod.ALL_TIME:
                    period_start = self._get_period_start()
                    query = query.filter(completed_at__gte=period_start)
                score = query.count()
            
            elif self.category == LeaderboardCategory.LESSONS_COMPLETED:
                query = LessonProgress.objects.filter(
                    enrollment__student=user,
                    is_completed=True
                )
                if self.period != LeaderboardPeriod.ALL_TIME:
                    period_start = self._get_period_start()
                    query = query.filter(completed_at__gte=period_start)
                score = query.count()
            
            elif self.category == LeaderboardCategory.QUIZZES_PASSED:
                query = QuizAttempt.objects.filter(
                    enrollment__student=user,
                    is_passed=True
                ).values('quiz').distinct()
                if self.period != LeaderboardPeriod.ALL_TIME:
                    period_start = self._get_period_start()
                    query = QuizAttempt.objects.filter(
                        enrollment__student=user,
                        is_passed=True,
                        completed_at__gte=period_start
                    ).values('quiz').distinct()
                score = query.count()
            
            elif self.category == LeaderboardCategory.ACHIEVEMENTS_EARNED:
                query = user.achievements_earned.all()
                if self.period != LeaderboardPeriod.ALL_TIME:
                    period_start = self._get_period_start()
                    query = query.filter(earned_at__gte=period_start)
                score = query.count()
            
            if score > 0:  # Solo incluir usuarios con puntuación
                user_scores.append((user, score))
        
        # Ordenar por puntuación descendente
        user_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Crear rankings
        for position, (user, score) in enumerate(user_scores[:self.max_positions], 1):
            UserRanking.objects.create(
                leaderboard=self,
                user=user,
                position=position,
                score=score
            )
        
        self.last_updated = timezone.now()
        self.save(update_fields=['last_updated'])
    
    def _get_period_start(self):
        """Obtener la fecha de inicio del período."""
        now = timezone.now()
        
        if self.period == LeaderboardPeriod.DAILY:
            return now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif self.period == LeaderboardPeriod.WEEKLY:
            days_since_monday = now.weekday()
            return (now - timezone.timedelta(days=days_since_monday)).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
        elif self.period == LeaderboardPeriod.MONTHLY:
            return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        return None  # All time


class UserRanking(models.Model):
    """
    Modelo para posiciones individuales en rankings.
    
    Representa la posición de un usuario en un ranking específico.
    """
    
    leaderboard = models.ForeignKey(
        Leaderboard,
        on_delete=models.CASCADE,
        related_name='user_rankings',
        verbose_name=_('Ranking')
    )
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='ranking_positions',
        verbose_name=_('Usuario')
    )
    
    position = models.PositiveIntegerField(
        verbose_name=_('Posición')
    )
    
    score = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name=_('Puntuación')
    )
    
    # Recompensa otorgada por esta posición
    reward_claimed = models.BooleanField(
        default=False,
        verbose_name=_('Recompensa reclamada')
    )
    
    reward_amount = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Cantidad de recompensa')
    )
    
    # Metadatos
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Fecha de creación')
    )
    
    class Meta:
        verbose_name = _('Posición en Ranking')
        verbose_name_plural = _('Posiciones en Rankings')
        unique_together = [['leaderboard', 'user'], ['leaderboard', 'position']]
        ordering = ['leaderboard', 'position']
        indexes = [
            models.Index(fields=['leaderboard', 'position']),
            models.Index(fields=['user']),
        ]
    
    def __str__(self):
        return f"{self.user.get_full_name()} - Posición {self.position} ({self.leaderboard.title})"
    
    def save(self, *args, **kwargs):
        """Calcular recompensa automáticamente."""
        if not self.reward_amount:
            if self.position == 1:
                self.reward_amount = self.leaderboard.first_place_reward
            elif self.position == 2:
                self.reward_amount = self.leaderboard.second_place_reward
            elif self.position == 3:
                self.reward_amount = self.leaderboard.third_place_reward
        
        super().save(*args, **kwargs)
    
    def claim_reward(self):
        """Reclamar la recompensa de la posición."""
        if self.reward_claimed or self.reward_amount == 0:
            return False
        
        try:
            wallet = self.user.fore_wallet
            wallet.add_tokens(
                amount=self.reward_amount,
                description=f"Recompensa por posición {self.position} en {self.leaderboard.title}",
                transaction_type=TransactionType.ADMIN_BONUS
            )
            
            self.reward_claimed = True
            self.save(update_fields=['reward_claimed'])
            
            return True
        except Exception:
            return False


class RewardCategory(models.TextChoices):
    """Categorías de recompensas del marketplace."""
    DIGITAL = 'digital', _('Digital')
    PHYSICAL = 'physical', _('Físico')
    EXPERIENCE = 'experience', _('Experiencia')
    EDUCATION = 'education', _('Educación')
    ENTERTAINMENT = 'entertainment', _('Entretenimiento')
    CHARITY = 'charity', _('Caridad')


class Reward(models.Model):
    """
    Modelo para recompensas disponibles en el marketplace.
    
    Define los artículos/servicios que los usuarios pueden
    canjear con sus tokens FORE.
    """
    
    title = models.CharField(
        max_length=200,
        verbose_name=_('Título'),
        help_text=_('Nombre de la recompensa')
    )
    
    description = models.TextField(
        verbose_name=_('Descripción'),
        help_text=_('Descripción detallada de la recompensa')
    )
    
    category = models.CharField(
        max_length=20,
        choices=RewardCategory.choices,
        verbose_name=_('Categoría')
    )
    
    # Costo en tokens FORE
    fore_cost = models.PositiveIntegerField(
        verbose_name=_('Costo FORE'),
        help_text=_('Cantidad de tokens FORE necesarios')
    )
    
    # Multimedia
    image = models.ImageField(
        upload_to='rewards/images/',
        blank=True,
        null=True,
        verbose_name=_('Imagen'),
        help_text=_('Imagen de la recompensa')
    )
    
    # Disponibilidad
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Activo')
    )
    
    stock_quantity = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name=_('Cantidad en stock'),
        help_text=_('Cantidad disponible (vacío = ilimitado)')
    )
    
    max_per_user = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name=_('Máximo por usuario'),
        help_text=_('Límite de canjes por usuario')
    )
    
    # Fechas de disponibilidad
    available_from = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_('Disponible desde')
    )
    
    available_until = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_('Disponible hasta')
    )
    
    # Información de entrega
    delivery_info = models.TextField(
        blank=True,
        verbose_name=_('Información de entrega'),
        help_text=_('Instrucciones para reclamar/recibir la recompensa')
    )
    
    requires_shipping = models.BooleanField(
        default=False,
        verbose_name=_('Requiere envío'),
        help_text=_('Si requiere dirección de envío física')
    )
    
    # Estadísticas
    total_redeemed = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Total canjeado'),
        help_text=_('Número total de veces que se ha canjeado')
    )
    
    # Metadatos
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Fecha de creación')
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Última actualización')
    )
    
    class Meta:
        verbose_name = _('Recompensa')
        verbose_name_plural = _('Recompensas')
        ordering = ['category', 'fore_cost']
        indexes = [
            models.Index(fields=['category', 'is_active']),
            models.Index(fields=['fore_cost']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.fore_cost} FORE"
    
    @property
    def is_available(self):
        """Verificar si la recompensa está disponible."""
        if not self.is_active:
            return False
        
        now = timezone.now()
        
        if self.available_from and now < self.available_from:
            return False
        
        if self.available_until and now > self.available_until:
            return False
        
        if self.stock_quantity is not None and self.stock_quantity <= 0:
            return False
        
        return True
    
    def can_redeem(self, user):
        """Verificar si un usuario puede canjear esta recompensa."""
        if not self.is_available:
            return False, "Recompensa no disponible"
        
        # Verificar balance FORE
        try:
            wallet = user.fore_wallet
            if not wallet.can_spend(self.fore_cost):
                return False, "Balance FORE insuficiente"
        except FOREWallet.DoesNotExist:
            return False, "No tienes una billetera FORE"
        
        # Verificar límite por usuario
        if self.max_per_user:
            user_redemptions = self.redemptions.filter(user=user).count()
            if user_redemptions >= self.max_per_user:
                return False, f"Límite de {self.max_per_user} canjes por usuario alcanzado"
        
        return True, "Puede canjear"


class RedemptionStatus(models.TextChoices):
    """Estados de canje de recompensas."""
    PENDING = 'pending', _('Pendiente')
    PROCESSING = 'processing', _('Procesando')
    SHIPPED = 'shipped', _('Enviado')
    DELIVERED = 'delivered', _('Entregado')
    COMPLETED = 'completed', _('Completado')
    CANCELLED = 'cancelled', _('Cancelado')


class RewardRedemption(models.Model):
    """
    Modelo para registrar canjes de recompensas.
    
    Registra cuando un usuario canjea tokens FORE por recompensas.
    """
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reward_redemptions',
        verbose_name=_('Usuario')
    )
    
    reward = models.ForeignKey(
        Reward,
        on_delete=models.CASCADE,
        related_name='redemptions',
        verbose_name=_('Recompensa')
    )
    
    fore_cost = models.PositiveIntegerField(
        verbose_name=_('Costo FORE'),
        help_text=_('Tokens FORE gastados en el momento del canje')
    )
    
    status = models.CharField(
        max_length=20,
        choices=RedemptionStatus.choices,
        default=RedemptionStatus.PENDING,
        verbose_name=_('Estado')
    )
    
    # Información de entrega
    delivery_address = models.TextField(
        blank=True,
        verbose_name=_('Dirección de entrega'),
        help_text=_('Para recompensas físicas')
    )
    
    delivery_phone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_('Teléfono de contacto')
    )
    
    # Códigos de seguimiento
    tracking_code = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Código de seguimiento')
    )
    
    redemption_code = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_('Código de canje'),
        help_text=_('Código único para reclamar la recompensa')
    )
    
    # Fechas importantes
    redeemed_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Fecha de canje')
    )
    
    processed_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_('Fecha de procesamiento')
    )
    
    completed_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_('Fecha de completado')
    )
    
    # Notas administrativas
    admin_notes = models.TextField(
        blank=True,
        verbose_name=_('Notas administrativas')
    )
    
    class Meta:
        verbose_name = _('Canje de Recompensa')
        verbose_name_plural = _('Canjes de Recompensas')
        ordering = ['-redeemed_at']
        indexes = [
            models.Index(fields=['user', '-redeemed_at']),
            models.Index(fields=['status']),
            models.Index(fields=['reward']),
        ]
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.reward.title}"
    
    def save(self, *args, **kwargs):
        """Generar código de canje y establecer costo."""
        if not self.redemption_code:
            import uuid
            self.redemption_code = str(uuid.uuid4())[:8].upper()
        
        if not self.fore_cost:
            self.fore_cost = self.reward.fore_cost
        
        super().save(*args, **kwargs)
