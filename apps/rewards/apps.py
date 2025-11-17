from django.apps import AppConfig


class RewardsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.rewards'
    verbose_name = 'Sistema de Recompensas FORE y Gamificación'
    
    def ready(self):
        """Importar signals cuando la app esté lista."""
        try:
            import apps.rewards.signals
        except ImportError:
            pass
