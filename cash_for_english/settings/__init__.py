"""
Importa settings según la variable de entorno DJANGO_SETTINGS_MODULE.
Por defecto usa development si no se especifica.
"""

import os

# Determinar qué configuración usar
ENVIRONMENT = os.getenv('DJANGO_SETTINGS_MODULE', 'cash_for_english.settings.development')

if 'production' in ENVIRONMENT:
    from .production import *
elif 'development' in ENVIRONMENT:
    from .development import *
else:
    from .development import *  # Default a development
