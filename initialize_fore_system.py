#!/usr/bin/env python
"""
Script para crear datos iniciales del sistema FORE.
"""
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cash_for_english.settings')
django.setup()

from apps.rewards.signals import create_initial_achievements, create_initial_leaderboards, create_initial_rewards_v2

def main():
    print('🚀 Inicializando sistema FORE...')
    
    print('\n📚 Creando logros iniciales...')
    achievements_created = create_initial_achievements()
    print(f'✅ Creados {achievements_created} logros')
    
    print('\n🏆 Creando leaderboards iniciales...')
    leaderboards_created = create_initial_leaderboards()
    print(f'✅ Creados {leaderboards_created} leaderboards')
    
    print('\n🎁 Creando recompensas iniciales...')
    rewards_created = create_initial_rewards_v2()
    print(f'✅ Creadas {rewards_created} recompensas')
    
    print('\n🎉 Sistema FORE inicializado correctamente!')
    print(f'Total de elementos creados: {achievements_created + leaderboards_created + rewards_created}')

if __name__ == '__main__':
    main()