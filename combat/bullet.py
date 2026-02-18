"""
Модуль снарядов для системы боя.
Содержит базовый класс Projectile и специализированные типы снарядов.
"""

import pygame
import math
from core.settings import (
    BULLET_COLOR, BULLET_BASE_SPEED, BULLET_SPEED_MULT,
    BATTLE_BOX_WIDTH, BATTLE_BOX_HEIGHT
)


class Projectile(pygame.sprite.Sprite):
    """
    Базовый класс снаряда.
    Использует pygame.sprite.Sprite для интеграции с pygame.sprite.Group.
    Автоматически удаляется при выходе за границы рамки боя.
    """
    
    def __init__(self, x: float, y: float, vx: float, vy: float, 
                 width: int = 8, height: int = 8, color: tuple = None):
        """
        Инициализация снаряда.
        
        Аргументы:
            x: Начальная позиция X
            y: Начальная позиция Y
            vx: Скорость по оси X
            vy: Скорость по оси Y
            width: Ширина снаряда (по умолчанию 8)
            height: Высота снаряда (по умолчанию 8)
            color: Цвет снаряда (по умолчанию белый)
        """
        super().__init__()
        
        # Создание поверхности снаряда
        self.image = pygame.Surface((width, height))
        self.image.fill(color or BULLET_COLOR)
        
        # Прямоугольник для позиционирования и коллизий
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        
        # Скорость снаряда
        self.vx = vx * BULLET_SPEED_MULT
        self.vy = vy * BULLET_SPEED_MULT
        
        # Границы для удаления (будут установлены при привязке к рамке)
        self.bounds = None
    
    def set_bounds(self, box_rect: pygame.Rect) -> None:
        """
        Установка границ рамки боя для автоматического удаления.
        
        Аргументы:
            box_rect: Прямоугольник рамки боя
        """
        # Расширяем границы для удаления снарядов за пределами видимости
        margin = 100
        self.bounds = pygame.Rect(
            box_rect.left - margin,
            box_rect.top - margin,
            box_rect.width + margin * 2,
            box_rect.height + margin * 2
        )
    
    def update(self) -> None:
        """
        Обновление позиции снаряда.
        Вызывается автоматически при обновлении sprite.Group.
        Удаляет снаряд при выходе за границы.
        """
        # Перемещение снаряда
        self.rect.x += self.vx
        self.rect.y += self.vy
        
        # Проверка выхода за границы и удаление
        if self.bounds and not self.bounds.contains(self.rect):
            self.kill()
    
    def get_rect(self) -> pygame.Rect:
        """
        Получение прямоугольника коллизии снаряда.
        
        Возвращает:
            pygame.Rect: Прямоугольник для проверки столкновений
        """
        return self.rect


class LineBullet(Projectile):
    """
    Линейный снаряд (прямоугольник).
    Используется в паттерне "Line Rain" - падающие линии.
    """
    
    def __init__(self, x: float, y: float, vx: float, vy: float):
        """
        Инициализация линейного снаряда.
        
        Аргументы:
            x: Начальная позиция X
            y: Начальная позиция Y
            vx: Скорость по оси X
            vy: Скорость по оси Y
        """
        # Линейный снаряд - вытянутый прямоугольник
        super().__init__(x, y, vx, vy, width=40, height=6)


class CircleBullet(Projectile):
    """
    Круглый снаряд (квадрат, визуально представляющий круг).
    Используется в паттерне "Circle Burst".
    """
    
    def __init__(self, x: float, y: float, vx: float, vy: float):
        """
        Инициализация круглого снаряда.
        
        Аргументы:
            x: Начальная позиция X
            y: Начальная позиция Y
            vx: Скорость по оси X
            vy: Скорость по оси Y
        """
        # Круглый снаряд - маленький квадрат
        super().__init__(x, y, vx, vy, width=8, height=8)


class TargetingBullet(Projectile):
    """
    Самонаводящийся снаряд.
    Летит в направлении позиции игрока в момент выстрела.
    """
    
    def __init__(self, x: float, y: float, target_x: float, target_y: float, speed: float = None):
        """
        Инициализация самонаводящегося снаряда.
        
        Аргументы:
            x: Начальная позиция X
            y: Начальная позиция Y
            target_x: Целевая позиция X (позиция игрока)
            target_y: Целевая позиция Y (позиция игрока)
            speed: Скорость снаряда (по умолчанию из настроек)
        """
        # Вычисляем направление к цели
        dx = target_x - x
        dy = target_y - y
        distance = math.sqrt(dx * dx + dy * dy)
        
        # Нормализуем и применяем скорость
        speed = speed or (BULLET_BASE_SPEED * BULLET_SPEED_MULT)
        if distance > 0:
            vx = (dx / distance) * speed
            vy = (dy / distance) * speed
        else:
            vx, vy = 0, speed
        
        # Круглый снаряд
        super().__init__(x, y, vx, vy, width=10, height=10)
