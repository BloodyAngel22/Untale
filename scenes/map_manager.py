"""
Модуль управления тайловыми картами.
Реализует загрузку карт из матрицы, отрисовку тайлов и переходы между локациями.

Система тайлов:
- '0' — пустой пол (проходимый)
- '1' — стена (коллизия)
- '2' — переход на другую карту
- 'E' — враг (триггер боя)
- 'S' — точка сохранения (SavePoint)
"""

import pygame
from core.settings import (
    TILE_SIZE, SCREEN_WIDTH, SCREEN_HEIGHT,
    TILE_EMPTY, TILE_WALL, TILE_TRANSITION, TILE_ENEMY, TILE_SAVEPOINT,
    TILE_EMPTY_COLOR, TILE_WALL_COLOR, TILE_TRANSITION_COLOR, TILE_ENEMY_COLOR,
    SAVEPOINT_COLOR,
    ENEMY_DEFAULT_NAME, ENEMY_DEFAULT_HP
)
from entities.save_point import SavePoint


class Enemy:
    """
    Класс врага в мире.
    Содержит данные о враге для использования в бою.
    """
    
    def __init__(self, x: int, y: int, name: str = None, hp: int = None, 
                 attack_damage: int = None, is_boss: bool = False):
        """
        Инициализация врага.
        
        Аргументы:
            x: Позиция X в тайлах
            y: Позиция Y в тайлах
            name: Имя врага
            hp: Здоровье врага
            attack_damage: Урон, наносимый игроку
            is_boss: Является ли враг боссом
        """
        self.x = x
        self.y = y
        self.is_boss = is_boss
        
        # Имя врага
        if name is None:
            self.name = "БОСС" if is_boss else ENEMY_DEFAULT_NAME
        else:
            self.name = name
        
        # Импортируем настройки здесь, чтобы избежать циклических импортов
        from core.settings import (
            BOSS_HP, BOSS_ATTACK_DAMAGE, 
            MOB_HP, MOB_ATTACK_DAMAGE
        )
    
        # HP и урон в зависимости от типа врага
        if is_boss:
            self.max_hp = hp if hp is not None else BOSS_HP
            self.attack_damage = attack_damage if attack_damage is not None else BOSS_ATTACK_DAMAGE
        else:
            self.max_hp = hp if hp is not None else MOB_HP
            self.attack_damage = attack_damage if attack_damage is not None else MOB_ATTACK_DAMAGE
        
        self.hp = self.max_hp
        
        # Фаза босса (1 или 2)
        self.phase = 1
        self.phase2_triggered = False  # Флаг для показа сообщения о переходе
        
        self.is_sparable = False  # Можно ли пощадить
        self.rect = pygame.Rect(
            x * TILE_SIZE, y * TILE_SIZE,
            TILE_SIZE, TILE_SIZE
        )
    
    def get_rect(self) -> pygame.Rect:
        """Получение прямоугольника коллизии врага."""
        return self.rect

    def take_damage(self, damage: int) -> bool:
        """
        Нанесение урона врагу.
        
        Аргументы:
            damage: Величина урона
            
        Возвращает:
            bool: True если враг погиб
        """
        self.hp = max(0, self.hp - damage)
        
        # Проверка перехода во вторую фазу для босса
        if self.is_boss and self.phase == 1:
            from core.settings import BOSS_PHASE2_THRESHOLD
            if self.hp <= self.max_hp * BOSS_PHASE2_THRESHOLD:
                self.phase = 2
                self.phase2_triggered = True
        
        return self.hp <= 0
    
    def is_dead(self) -> bool:
        """Проверка, погиб ли враг."""
        return self.hp <= 0
    
    def get_hp_percent(self) -> float:
        """Получение процента оставшегося HP."""
        return self.hp / self.max_hp if self.max_hp > 0 else 0


# ============================================================================
# КАРТЫ ЛОКАЦИЙ (МАТРИЦЫ ТАЙЛОВ)
# Размер экрана 800x600, размер тайла 32px
# 800/32 = 25 тайлов по ширине, 600/32 = 18 тайлов по высоте
# ============================================================================

# Карта 1: Начальная локация
# E - враг, 2 - переход на другую карту (внизу), S - точка сохранения
MAP_START = [
    "1111111111111111111111111",
    "1000000000000000000000001",
    "1000000000000000000000001",
    "1000000111100000000000001",
    "1000000100000000000000001",
    "100000010E001000000000001",
    "1000000100001000S00000001",
    "1000000111111000000000001",
    "1000000000000000000000001",
    "10000000000000000000E0001",
    "1000000000000000000000001",
    "1000000000000000000000001",
    "1000000000000000000000001",
    "1000000000000022222220001",
    "1111111111111111111111111",
]

# Карта 2: Лес (переход с карты 1)
# E - враг, 2 - переход назад (вверху), S - точка сохранения
MAP_FOREST = [
    "1111111111111111111111111",
    "1000000000000022222220001",
    "1000000000000000000000001",
    "1000000001100000000000001",
    "1000000000100000000000001",
    "10000010001000S0000000001",
    "1000001000100000000000001",
    "1000001111100000000E00001",
    "1000000000000000000000001",
    "1000000000111111111111101",
    "1000000000100000000000101",
    "1000000000100000000000101",
    "1000000000100000000000101",
    "1000000000100000000000101",
    "1111111111111111111111111",
]

# Словарь всех карт
MAPS = {
    'start': MAP_START,
    'forest': MAP_FOREST,
}

# Связь имён карт с ID локаций (для музыки)
MAP_LOCATION_ID = {
    'start': 1,
    'forest': 2,
}

# Переходы между картами: (имя_карты, направление) -> (новая_карта, новая_позиция_x, новая_позиция_y)
MAP_TRANSITIONS = {
    ('start', 'down'): ('forest', 12, 3),   # С карты start вниз -> forest, появление ниже перехода
    ('forest', 'up'): ('start', 12, 11),    # С карты forest вверх -> start, появление выше перехода
}


class MapManager:
    """
    Менеджер карт.
    Управляет загрузкой, отрисовкой и переходами между локациями.
    """
    
    def __init__(self):
        """Инициализация менеджера карт."""
        self.current_map_name = 'start'
        self.current_map = MAPS['start']
        self.map_width = len(self.current_map[0])
        self.map_height = len(self.current_map)
        
        # Списки объектов карты
        self.walls = []
        self.transitions = []
        self.enemies = []
        self.save_points = []
        
        # Парсинг карты
        self._parse_map()
        
    def _parse_map(self) -> None:
        """Парсинг текущей карты и создание объектов."""
        self.walls = []
        self.transitions = []
        self.enemies = []
        self.save_points = []
        
        for y, row in enumerate(self.current_map):
            for x, tile in enumerate(row):
                rect = pygame.Rect(
                    x * TILE_SIZE, y * TILE_SIZE,
                    TILE_SIZE, TILE_SIZE
                )
                
                if tile == TILE_WALL:
                    self.walls.append(rect)
                elif tile == TILE_TRANSITION:
                    self.transitions.append((rect, x, y))
                elif tile == TILE_ENEMY:
                    # Определяем, является ли враг боссом
                    # Босс на карте forest (позиция 19, 7)
                    is_boss = (self.current_map_name == 'forest' and x == 19 and y == 7)
                    
                    if is_boss:
                        enemy = Enemy(x, y, name="БОСС", is_boss=True)
                    else:
                        enemy = Enemy(x, y)
                    
                    self.enemies.append(enemy)
                elif tile == TILE_SAVEPOINT:
                    # Создаём точку сохранения
                    save_point = SavePoint(x * TILE_SIZE, y * TILE_SIZE)
                    self.save_points.append(save_point)
    
    def load_map(self, map_name: str, player_x: int = None, player_y: int = None) -> tuple:
        """
        Загрузка новой карты.
        
        Аргументы:
            map_name: Имя карты для загрузки
            player_x: Новая позиция игрока X (в тайлах)
            player_y: Новая позиция игрока Y (в тайлах)
            
        Возвращает:
            tuple: (новая_позиция_x_пиксели, новая_позиция_y_пиксели) или None
        """
        if map_name not in MAPS:
            return None
        
        self.current_map_name = map_name
        self.current_map = MAPS[map_name]
        self.map_width = len(self.current_map[0])
        self.map_height = len(self.current_map)
        
        self._parse_map()
        
        # Возвращаем новую позицию игрока
        if player_x is not None and player_y is not None:
            return (player_x * TILE_SIZE, player_y * TILE_SIZE)
        return None
    
    def check_transition(self, player_rect: pygame.Rect) -> tuple:
        """
        Проверка перехода на другую карту.
        
        Аргументы:
            player_rect: Прямоугольник игрока
            
        Возвращает:
            tuple: (новая_карта, новый_x, новый_y) или None
        """
        for rect, x, y in self.transitions:
            if player_rect.colliderect(rect):
                # Определяем направление перехода
                direction = self._get_transition_direction(x, y)
                key = (self.current_map_name, direction)
                
                if key in MAP_TRANSITIONS:
                    return MAP_TRANSITIONS[key]
        
        return None
    
    def _get_transition_direction(self, x: int, y: int) -> str:
        """
        Определение направления перехода по позиции тайла.
        
        Аргументы:
            x: Позиция X тайла перехода
            y: Позиция Y тайла перехода
            
        Возвращает:
            str: Направление ('up', 'down', 'left', 'right')
        """
        # Переход в верхней части карты (y <= 1)
        if y <= 1:
            return 'up'
        # Переход в нижней части карты
        elif y >= self.map_height - 2:
            return 'down'
        # Переход в левой части карты
        elif x <= 1:
            return 'left'
        # Переход в правой части карты
        elif x >= self.map_width - 2:
            return 'right'
        return 'down'
    
    def check_enemy_collision(self, player_rect: pygame.Rect) -> Enemy:
        """
        Проверка столкновения с врагом.
        
        Аргументы:
            player_rect: Прямоугольник игрока
            
        Возвращает:
            Enemy: Объект врага при столкновении или None
        """
        for enemy in self.enemies:
            if player_rect.colliderect(enemy.get_rect()):
                return enemy
        return None
    
    def remove_enemy(self, enemy: Enemy) -> None:
        """
        Удаление врага с карты (после победы/пощады).
        
        Аргументы:
            enemy: Объект врага для удаления
        """
        if enemy in self.enemies:
            self.enemies.remove(enemy)
    
    def get_walls(self) -> list:
        """Получение списка стен."""
        return self.walls
    
    def get_location_id(self) -> int:
        """Получение ID текущей локации для музыки."""
        return MAP_LOCATION_ID.get(self.current_map_name, 1)
    
    def update_save_points(self) -> None:
        """Обновление всех точек сохранения (анимация)."""
        for save_point in self.save_points:
            save_point.update()
    
    def check_save_point_collision(self, player_rect: pygame.Rect) -> SavePoint:
        """
        Проверка столкновения с точкой сохранения.
        
        Аргументы:
            player_rect: Прямоугольник игрока
            
        Возвращает:
            SavePoint: Объект точки сохранения при столкновении или None
        """
        for save_point in self.save_points:
            if save_point.check_collision(player_rect):
                return save_point
        return None
    
    def draw_save_points(self, surface: pygame.Surface) -> None:
        """
        Отрисовка точек сохранения.
        
        Аргументы:
            surface: Поверхность для отрисовки
        """
        for save_point in self.save_points:
            save_point.draw(surface)
    
    def draw(self, surface: pygame.Surface) -> None:
        """
        Отрисовка карты.
        
        Аргументы:
            surface: Поверхность для отрисовки
        """
        for y, row in enumerate(self.current_map):
            for x, tile in enumerate(row):
                rect = pygame.Rect(
                    x * TILE_SIZE, y * TILE_SIZE,
                    TILE_SIZE, TILE_SIZE
                )
                
                # Выбор цвета в зависимости от типа тайла
                if tile == TILE_EMPTY:
                    color = TILE_EMPTY_COLOR
                elif tile == TILE_WALL:
                    color = TILE_WALL_COLOR
                elif tile == TILE_TRANSITION:
                    color = TILE_TRANSITION_COLOR
                elif tile == TILE_ENEMY:
                    # Проверяем, является ли враг боссом
                    is_boss = (self.current_map_name == 'forest' and x == 19 and y == 7)
                    color = (255, 100, 0) if is_boss else TILE_ENEMY_COLOR  # Оранжевый для босса
                elif tile == TILE_SAVEPOINT:
                    color = TILE_EMPTY_COLOR  # Фон под точкой сохранения прозрачный
                else:
                    color = TILE_EMPTY_COLOR
                
                pygame.draw.rect(surface, color, rect)
                
                # Рисуем границу для стен
                if tile == TILE_WALL:
                    pygame.draw.rect(surface, (150, 150, 150), rect, 1)

                # Рисуем рамку для босса
                if tile == TILE_ENEMY:
                    is_boss = (self.current_map_name == 'forest' and x == 19 and y == 7)
                    if is_boss:
                        pygame.draw.rect(surface, (255, 255, 0), rect, 2)  # Жёлтая рамка для босса
