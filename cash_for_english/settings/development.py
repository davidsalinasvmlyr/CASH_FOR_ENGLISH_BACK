"""
Settings para entorno de desarrollo.
Extiende base.py con configuraciones específicas de desarrollo.
"""

from .base import *

# ==============================================================================
# DEBUG
# ==============================================================================
DEBUG = True

# ==============================================================================
# ALLOWED HOSTS
# ==============================================================================
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0', '*']

# ==============================================================================
# CORS (Permisivo en desarrollo)
# ==============================================================================
CORS_ALLOW_ALL_ORIGINS = True

# ==============================================================================
# LOGGING (Verbose en desarrollo)
# ==============================================================================
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# ==============================================================================
# DEBUG TOOLBAR (Opcional para desarrollo)
# ==============================================================================
# Descomenta si instalas django-debug-toolbar
# INSTALLED_APPS += ['debug_toolbar']
# MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
# INTERNAL_IPS = ['127.0.0.1']
