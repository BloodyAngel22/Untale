"""
Модуль предметов на карте.
Содержит класс PickupItem для подбираемых предметов в мире.
"""

import pygame
from core.settings import COLOR_YELLOW, TILE_SIZE


class ItemData:
    """
    Данные о предмете (тип и свойства).
    """
    
    # Типы предметов
    TYPES = {
        'healing_candy': {
            'name': 'Конфета',
            'heal_value': 10,
            'color': (255, 100, 100),
            'description': 'Восстанавливает 10 HP'
        },
        'healing_pie': {
            'name': 'Пирог',
            'heal_value': 50,
            'color': (255, 200, 100),
            'description': 'Восстанавливает 50 HP'
        },
        'bandage': {
            'name': 'Бинт',
            'heal_value': 20,
            'color': (200, 200, 200),
            'description': 'Восстанавливает 20 HP'
        }
    }
    
    @classmethod
    def get_item(cls, item_type: str) -> dict:
        """
        Получение данных о предмете по типу.
        
        Аргументы:
            item_type: Тип предмета
            
        Возвращает:
            dict: Данные предмета или None
        """
        return cls.TYPES.get(item_type)
    
    @classmethod
    def get_all_types(cls) -> list:
        """Получение списка всех типов предметов."""
        return list(cls.TYPES.keys())


class PickupItem:
    """
    Подбираемый предмет на карте.
    При контакте с игроком и нажатии Z предмет попадает в инвентарь.
    """
    
    def __init__(self, x: float, y: float, item_type: str):
        """
        Инициализация предмета.
        
        Аргументы:
            x: Позиция X
            y: Позиция Y
            item_type: Тип предмета (из ItemData.TYPES)
        """
        self.x = x
        self.y = y
        self.item_type = item_type
        self.data = ItemData.get_item(item_type)
        
        # Размер предмета
        self.size = TILE_SIZE // 2
        
        # Прямоугольник коллизии
        self.rect = pygame.Rect(
            x + TILE_SIZE // 4,  # Центрируем в тайле
            y + TILE_SIZE // 4,
            self.size,
            self.size
        )
        
        # Собран ли предмет
        self.collected = False
        
        # Анимация (пульсация)
        self.animation_timer = 0
    
    def update(self) -> None:
        """Обновление анимации предмета."""
        self.animation_timer += 1
    
    def check_collision(self, player_rect: pygame.Rect) -> bool:
        """
        Проверка столкновения с игроком.
        
        Аргументы:
            player_rect: Прямоугольник игрока
            
        Возвращает:
            bool: True если есть столкновение
        """
        return self.rect.colliderect(player_rect) and not self.collected
    
    def collect(self) -> dict:
        """
        Сбор предмета.
        
        Возвращает:
            dict: Данные предмета или None если уже собран
        """
        if self.collected:
            return None
        
        self.collected = True
        return self.data
    
    def draw(self, surface: pygame.Surface) -> None:
        """
        Отрисовка предмета.
        
        Аргументы:
            surface: Поверхность для отрисовки
        """
        if self.collected:
            return
        
        # Пульсация
        pulse = abs(math.sin(self.animation_timer * 0.1)) * 3
        size = self.size + int(pulse)
        
        # Цвет предмета
        color = self.data['color'] if self.data else COLOR_YELLOW
        
        # Рисуем предмет (круг)
        center_x = self.rect.centerx
        center_y = self.rect.centery
        pygame.draw.circle(surface, color, (center_x, center_y), size // 2)
        
        # Обводка
        pygame.draw.circle(surface, (255, 255, 255), (center_x, center_y), size // 2, 1)
        
        # Блик
        highlight_pos = (center_x - size // 6, center_y - size // 6)
        pygame.draw.circle(surface, (255, 255, 255), highlight_pos, size // 6)


# Импорт math для анимации
import math
