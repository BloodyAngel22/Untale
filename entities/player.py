"""
Модуль игрока для игры в стиле Undertale.
Содержит класс Player, поддерживающий два режима: Overworld (мир) и Battle (бой).

Игрок имеет разные характеристики в зависимости от режима:
- В мире: красный квадрат 32x32, медленное перемещение, проверка коллизий со стенами
- В бою: красное сердце 10x10, быстрое и точное движение, ограничено рамкой боя
"""

import pygame
from core.settings import (
    PLAYER_OVERWORLD_SIZE, PLAYER_OVERWORLD_SPEED, PLAYER_OVERWORLD_COLOR,
    PLAYER_BATTLE_SIZE, PLAYER_BATTLE_SPEED, PLAYER_BATTLE_COLOR,
    PLAYER_MAX_HP, INVULNERABILITY_TIME
)


class Player:
    """
    Класс игрока.
    Поддерживает два режима: Overworld (мир) и Battle (бой).
    Управляет позицией, перемещением и отрисовкой персонажа.
    """
    
    def __init__(self, x: float, y: float):
        """
        Инициализация игрока.
        
        Аргументы:
            x: Начальная позиция X
            y: Начальная позиция Y
        """
        # Позиция в режиме мира
        self.overworld_x = x
        self.overworld_y = y
        self.overworld_size = PLAYER_OVERWORLD_SIZE
        self.overworld_speed = PLAYER_OVERWORLD_SPEED
        
        # Позиция в режиме боя (устанавливается при переходе в бой)
        self.battle_x = x
        self.battle_y = y
        self.battle_size = PLAYER_BATTLE_SIZE
        self.battle_speed = PLAYER_BATTLE_SPEED
        
        # Прямоугольники коллизий
        self.overworld_rect = pygame.Rect(
            self.overworld_x, self.overworld_y,
            self.overworld_size, self.overworld_size
        )
        self.battle_rect = pygame.Rect(
            self.battle_x, self.battle_y,
            self.battle_size, self.battle_size
        )
        
        # Рамка боя (устанавливается при переходе в бой)
        self.battle_box = None
        
        # HP и неуязвимость
        self.hp = PLAYER_MAX_HP
        self.max_hp = PLAYER_MAX_HP
        self.invulnerability_timer = 0
    
        # Инвентарь
        self.inventory = []
    
    # ========================================================================
    # РЕЖИМ МИРА (OVERWORLD)
    # ========================================================================
    
    def handle_overworld_input(self, keys: pygame.key.ScancodeWrapper, 
                                walls: list) -> None:
        """
        Обработка ввода для режима мира.
        Проверяет коллизии со стенами перед перемещением.
        
        Аргументы:
            keys: Состояние клавиш клавиатуры
            walls: Список прямоугольников стен
        """
        dx, dy = 0, 0
        
        # Проверка нажатых клавиш (WASD и стрелки)
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            dy = -self.overworld_speed
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            dy = self.overworld_speed
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            dx = -self.overworld_speed
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            dx = self.overworld_speed
        
        # Проверка коллизии по оси X
        new_rect = pygame.Rect(
            self.overworld_x + dx, self.overworld_y,
            self.overworld_size, self.overworld_size
        )
        if not any(new_rect.colliderect(wall) for wall in walls):
            self.overworld_x += dx
        
        # Проверка коллизии по оси Y
        new_rect = pygame.Rect(
            self.overworld_x, self.overworld_y + dy,
            self.overworld_size, self.overworld_size
        )
        if not any(new_rect.colliderect(wall) for wall in walls):
            self.overworld_y += dy
        
        # Обновление прямоугольника коллизии
        self.overworld_rect = pygame.Rect(
            self.overworld_x, self.overworld_y,
            self.overworld_size, self.overworld_size
        )
    
    def get_overworld_rect(self) -> pygame.Rect:
        """
        Получение прямоугольника коллизии игрока в режиме мира.
        
        Возвращает:
            pygame.Rect: Прямоугольник для проверки столкновений
        """
        return self.overworld_rect
    
    def draw_overworld(self, surface: pygame.Surface) -> None:
        """
        Отрисовка игрока в режиме мира (красный квадрат).
        
        Аргументы:
            surface: Поверхность для отрисовки
        """
        pygame.draw.rect(surface, PLAYER_OVERWORLD_COLOR, self.overworld_rect)
    
    # ========================================================================
    # РЕЖИМ БОЯ (BATTLE)
    # ========================================================================
    
    def set_battle_box(self, box_rect: pygame.Rect) -> None:
        """
        Установка рамки боя для ограничения перемещения.
        
        Аргументы:
            box_rect: Прямоугольник рамки боя
        """
        self.battle_box = box_rect
        # Устанавливаем позицию в центр рамки
        self.battle_x = box_rect.centerx - self.battle_size // 2
        self.battle_y = box_rect.centery - self.battle_size // 2
        self._update_battle_rect()
    
    def handle_battle_input(self, keys: pygame.key.ScancodeWrapper) -> None:
        """
        Обработка ввода для режима боя.
        Движение более быстрое и точное, ограничено рамкой.
        
        Аргументы:
            keys: Состояние клавиш клавиатуры
        """
        if not self.battle_box:
            return
        
        dx, dy = 0, 0
        
        # Проверка нажатых клавиш (WASD и стрелки)
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            dy = -self.battle_speed
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            dy = self.battle_speed
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            dx = -self.battle_speed
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            dx = self.battle_speed
        
        # Применение движения с ограничением внутри рамки
        new_x = self.battle_x + dx
        new_y = self.battle_y + dy
        
        # Ограничение по горизонтали
        if new_x >= self.battle_box.left and new_x + self.battle_size <= self.battle_box.right:
            self.battle_x = new_x
        
        # Ограничение по вертикали
        if new_y >= self.battle_box.top and new_y + self.battle_size <= self.battle_box.bottom:
            self.battle_y = new_y
        
        self._update_battle_rect()
    
    def _update_battle_rect(self) -> None:
        """
        Обновление прямоугольника коллизии для режима боя.
        """
        self.battle_rect = pygame.Rect(
            self.battle_x, self.battle_y,
            self.battle_size, self.battle_size
        )
    
    def get_battle_rect(self) -> pygame.Rect:
        """
        Получение прямоугольника коллизии игрока в режиме боя.
        
        Возвращает:
            pygame.Rect: Прямоугольник для проверки столкновений
        """
        return self.battle_rect
    
    def get_battle_position(self) -> tuple:
        """
        Получение текущей позиции в бою (центр сердца).
        Используется для наводящихся атак.
        
        Возвращает:
            tuple: (x, y) позиция центра игрока
        """
        return (
            self.battle_x + self.battle_size // 2,
            self.battle_y + self.battle_size // 2
        )
    
    def draw_battle(self, surface: pygame.Surface) -> None:
        """
        Отрисовка игрока в режиме боя (красное сердце).
        Учитывает неуязвимость (мигание).
        
        Аргументы:
            surface: Поверхность для отрисовки
        """
        # Эффект мигания при неуязвимости
        if self.invulnerability_timer > 0:
            if pygame.time.get_ticks() % 200 < 100:
                return  # Пропускаем отрисовку для эффекта мигания
        
        # Рисуем сердце (круг, упрощённо)
        center_x = int(self.battle_x + self.battle_size // 2)
        center_y = int(self.battle_y + self.battle_size // 2)
        pygame.draw.circle(surface, PLAYER_BATTLE_COLOR, (center_x, center_y), self.battle_size // 2)
    
    # ========================================================================
    # HP И НЕУЯЗВИМОСТЬ
    # ========================================================================
    
    def update_invulnerability(self) -> None:
        """
        Обновление таймера неуязвимости.
        Вызывается каждый кадр в режиме боя.
        """
        if self.invulnerability_timer > 0:
            self.invulnerability_timer -= 1
    
    def take_damage(self, damage: int) -> bool:
        """
        Нанесение урона игроку.
        Учитывает неуязвимость.
        
        Аргументы:
            damage: Величина урона
            
        Возвращает:
            bool: True если урон был нанесён, False если игрок неуязвим
        """
        if self.invulnerability_timer > 0:
            return False
        
        self.hp = max(0, self.hp - damage)
        self.invulnerability_timer = INVULNERABILITY_TIME
        return True
    
    def reset_battle_state(self) -> None:
        """
        Сброс состояния боя.
        Восстанавливает HP и сбрасывает неуязвимость.
        """
        self.hp = self.max_hp
        self.invulnerability_timer = 0
    
    def apply_gravity_force(self, force_x: float, force_y: float) -> None:
        """
        Применение гравитационной силы к игроку.
        
        Аргументы:
            force_x: Сила по оси X
            force_y: Сила по оси Y
        """
        self.battle_x += force_x
        self.battle_y += force_y
        
        # Ограничение в рамках боевой рамки
        if self.battle_box:
            margin = self.battle_size // 2
            self.battle_x = max(self.battle_box.left + margin, 
                               min(self.battle_box.right - margin, self.battle_x))
            self.battle_y = max(self.battle_box.top + margin, 
                               min(self.battle_box.bottom - margin, self.battle_y))
            self._update_battle_rect()
    
    def is_alive(self) -> bool:
        """
        Проверка, жив ли игрок.
        
        Возвращает:
            bool: True если HP > 0
        """
        return self.hp > 0
    
    # ========================================================================
    # УТИЛИТЫ
    # ========================================================================
    
    def set_overworld_position(self, x: float, y: float) -> None:
        """
        Установка позиции в режиме мира.
        
        Аргументы:
            x: Новая позиция X
            y: Новая позиция Y
        """
        self.overworld_x = x
        self.overworld_y = y
        self.overworld_rect = pygame.Rect(
            self.overworld_x, self.overworld_y,
            self.overworld_size, self.overworld_size
        )

    # ========================================================================
    # ИНВЕНТАРЬ
    # ========================================================================
    
    def add_item(self, item_data: dict) -> None:
        """
        Добавление предмета в инвентарь.
        
        Аргументы:
            item_data: Данные предмета
        """
        if item_data:
            self.inventory.append(item_data)
    
    def use_item(self, index: int) -> dict:
        """
        Использование предмета из инвентаря.
        
        Аргументы:
            index: Индекс предмета
            
        Возвращает:
            dict: Данные использованного предмета или None
        """
        if 0 <= index < len(self.inventory):
            item = self.inventory.pop(index)
            # Восстановление HP
            heal_value = item.get('heal_value', 0)
            self.hp = min(self.max_hp, self.hp + heal_value)
            return item
        return None
    
    def get_inventory_items(self) -> list:
        """
        Получение списка предметов инвентаря.
        
        Возвращает:
            list: Список данных предметов
        """
        return self.inventory
    
    def has_items(self) -> bool:
        """
        Проверка наличия предметов в инвентаре.
        
        Возвращает:
            bool: True если есть предметы
        """
        return len(self.inventory) > 0
    
    def heal(self, amount: int) -> int:
        """
        Восстановление HP.
        
        Аргументы:
            amount: Количество HP для восстановления
            
        Возвращает:
            int: Фактически восстановленное количество HP
        """
        old_hp = self.hp
        self.hp = min(self.max_hp, self.hp + amount)
        return self.hp - old_hp
    
    def full_heal(self) -> None:
        """Полное восстановление HP."""
        self.hp = self.max_hp
    
    def reset_for_restart(self) -> None:
        """
        Полный сброс игрока для перезапуска игры.
        Восстанавливает HP, очищает инвентарь.
        """
        self.hp = self.max_hp
        self.invulnerability_timer = 0
        self.inventory = []
