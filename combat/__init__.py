"""
Пакет combat - система боя.
Содержит классы снарядов, паттернов атак и боевого UI.
"""

from .bullet import Projectile, LineBullet, CircleBullet, TargetingBullet
from .patterns import AttackManager
from .battle_ui import BattleUI, Button
