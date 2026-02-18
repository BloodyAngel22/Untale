"""
Модуль системы паттернов атак.
Содержит класс AttackManager для генерации различных типов атак в бою.

Система очередей (Battle Rounds):
- Один "ход" врага состоит из цепочки атак (patterns_per_round)
- В начале раунда случайно выбирается 3 паттерна
- Каждый паттерн длится ATTACK_DURATION кадров
- После завершения всех атак управление возвращается игроку

Доступные паттерны атак:
Базовые:
- "Line Rain": Дождь из линий, падающих сверху
- "Circle Burst": Круговой взрыв из центра рамки
- "Targeting": Снаряды летят к текущей позиции игрока
- "Bouncing Walls": Квадраты отскакивают от стенок рамки
- "Spiral": Снаряды вылетают из центра по спирали
- "Laser Warning": Предупреждение + широкий луч

Сложные:
- "Snake/Wave": Снаряды движутся по синусоиде
- "Homing Blades": Лезвия нацеливаются на игрока
- "Expanding Ring": Расширяющееся кольцо из пуль
- "Gravity Wells": Чёрная дыра притягивает игрока
- "Rotating Cross": Вращающийся крест из пуль
"""

import pygame
import math
import random
from combat.bullet import LineBullet, CircleBullet, TargetingBullet
from core.settings import (
    BULLET_BASE_SPEED, BULLET_SPEED_MULT,
    LINE_RAIN_INTERVAL, LINE_RAIN_BULLET_COUNT,
    CIRCLE_BURST_COUNT, CIRCLE_BURST_INTERVAL,
    TARGETING_INTERVAL, TARGETING_BULLETS_PER_SHOT,
    PATTERNS_PER_ROUND, ATTACK_DURATION, GAP_BETWEEN_ATTACKS,
    COLOR_WHITE, COLOR_YELLOW, COLOR_RED
)


# ============================================================================
# СПЕЦИАЛЬНЫЕ КЛАССЫ СНАРЯДОВ
# ============================================================================

class BouncingBullet(pygame.sprite.Sprite):
    """Крупный снаряд-квадрат, который отскакивает от стенок рамки."""
    
    def __init__(self, x: float, y: float, vx: float, vy: float, 
                 box_rect: pygame.Rect, max_bounces: int = 4):
        super().__init__()
        
        self.size = 20
        self.image = pygame.Surface((self.size, self.size))
        self.image.fill(COLOR_WHITE)
        
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        
        self.vx = vx
        self.vy = vy
        self.box_rect = box_rect
        self.max_bounces = max_bounces
        self.bounce_count = 0
    
    def update(self):
        self.rect.x += self.vx
        self.rect.y += self.vy
        
        if self.rect.left <= self.box_rect.left:
            self.rect.left = self.box_rect.left
            self.vx = abs(self.vx)
            self.bounce_count += 1
        elif self.rect.right >= self.box_rect.right:
            self.rect.right = self.box_rect.right
            self.vx = -abs(self.vx)
            self.bounce_count += 1
        
        if self.rect.top <= self.box_rect.top:
            self.rect.top = self.box_rect.top
            self.vy = abs(self.vy)
            self.bounce_count += 1
        elif self.rect.bottom >= self.box_rect.bottom:
            self.rect.bottom = self.box_rect.bottom
            self.vy = -abs(self.vy)
            self.bounce_count += 1
        
        if self.bounce_count >= self.max_bounces:
            self.kill()


class SpiralBullet(CircleBullet):
    """Снаряд для спирального паттерна."""
    pass


class WaveBullet(pygame.sprite.Sprite):
    """Снаряд, движущийся по синусоидальной траектории."""
    
    def __init__(self, x: float, y: float, speed_x: float, amplitude: float, 
                 frequency: float, box_rect: pygame.Rect):
        super().__init__()
        
        self.radius = 6
        self.image = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(self.image, COLOR_WHITE, (self.radius, self.radius), self.radius)
        
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        
        self.x = x
        self.y = y
        self.start_y = y
        self.speed_x = speed_x
        self.amplitude = amplitude
        self.frequency = frequency
        self.box_rect = box_rect
        self.time = 0
    
    def update(self):
        self.time += 1
        self.x += self.speed_x
        self.y = self.start_y + math.sin(self.time * self.frequency) * self.amplitude
        self.rect.center = (int(self.x), int(self.y))
        
        if (self.rect.right < self.box_rect.left - 20 or 
            self.rect.left > self.box_rect.right + 20):
            self.kill()


class HomingBlade(pygame.sprite.Sprite):
    """Крупное лезвие, которое замирает, нацеливается на игрока и резко летит."""
    
    def __init__(self, x: float, y: float, box_rect: pygame.Rect):
        super().__init__()
        
        self.size = 30
        self.image = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        points = [
            (self.size // 2, 0),
            (self.size, self.size // 2),
            (self.size // 2, self.size),
            (0, self.size // 2)
        ]
        pygame.draw.polygon(self.image, COLOR_YELLOW, points)
        
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        
        self.x = x
        self.y = y
        self.box_rect = box_rect
        
        self.state = 'aiming'
        self.timer = 0
        self.aim_duration = 60
        self.charge_duration = 15
        
        self.target_x = 0
        self.target_y = 0
        self.vx = 0
        self.vy = 0
        self.speed = 15
    
    def set_target(self, target_x: float, target_y: float):
        self.target_x = target_x
        self.target_y = target_y
    
    def update(self):
        if self.state == 'aiming':
            self.timer += 1
            scale = 1.0 + 0.1 * math.sin(self.timer * 0.3)
            self.image = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
            points = [
                (self.size // 2, 0),
                (self.size, self.size // 2),
                (self.size // 2, self.size),
                (0, self.size // 2)
            ]
            pygame.draw.polygon(self.image, COLOR_YELLOW, points)
            
            if self.timer >= self.aim_duration:
                self.state = 'charging'
                self.timer = 0
                dx = self.target_x - self.x
                dy = self.target_y - self.y
                dist = math.sqrt(dx * dx + dy * dy)
                if dist > 0:
                    self.vx = (dx / dist) * self.speed
                    self.vy = (dy / dist) * self.speed
        
        elif self.state == 'charging':
            self.timer += 1
            self.image = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
            points = [
                (self.size // 2, 0),
                (self.size, self.size // 2),
                (self.size // 2, self.size),
                (0, self.size // 2)
            ]
            pygame.draw.polygon(self.image, COLOR_RED, points)
            
            if self.timer >= self.charge_duration:
                self.state = 'flying'
        
        elif self.state == 'flying':
            self.x += self.vx
            self.y += self.vy
            self.rect.center = (int(self.x), int(self.y))
            
            if (self.x < self.box_rect.left - 50 or 
                self.x > self.box_rect.right + 50 or
                self.y < self.box_rect.top - 50 or 
                self.y > self.box_rect.bottom + 50):
                self.kill()


class ExpandingRingBullet(CircleBullet):
    """Снаряд для расширяющегося кольца."""
    pass


class GravityWell:
    """Гравитационная аномалия (чёрная дыра). Притягивает или отталкивает игрока."""
    
    def __init__(self, x: float, y: float, strength: float = 0.5, 
                 repel: bool = False, duration: int = 180):
        self.x = x
        self.y = y
        self.strength = strength
        self.repel = repel
        self.duration = duration
        self.timer = 0
        self.active = True
        self.radius = 40
    
    def update(self):
        self.timer += 1
        if self.timer >= self.duration:
            self.active = False
    
    def apply_force(self, player_x: float, player_y: float) -> tuple:
        if not self.active:
            return (0, 0)
        
        dx = self.x - player_x
        dy = self.y - player_y
        dist = math.sqrt(dx * dx + dy * dy)
        
        if dist < 10:
            dist = 10
        
        force_magnitude = self.strength * (100 / dist)
        
        if self.repel:
            force_magnitude = -force_magnitude
        
        force_x = (dx / dist) * force_magnitude
        force_y = (dy / dist) * force_magnitude
        
        return (force_x, force_y)
    
    def draw(self, surface: pygame.Surface):
        if not self.active:
            return
        
        pulse = 1.0 + 0.2 * math.sin(self.timer * 0.2)
        current_radius = int(self.radius * pulse)
        
        pygame.draw.circle(surface, (20, 0, 30), 
                          (int(self.x), int(self.y)), current_radius)
        pygame.draw.circle(surface, (100, 0, 150), 
                          (int(self.x), int(self.y)), current_radius, 3)
        
        for i in range(4):
            angle = self.timer * 0.05 + i * math.pi / 2
            px = self.x + math.cos(angle) * (current_radius + 10)
            py = self.y + math.sin(angle) * (current_radius + 10)
            pygame.draw.circle(surface, (150, 50, 200), (int(px), int(py)), 3)


class RotatingCrossBullet(CircleBullet):
    """Снаряд для вращающегося креста."""
    pass


class LaserBeam:
    """Лазерный луч с предупреждением."""
    
    def __init__(self, box_rect: pygame.Rect, is_horizontal: bool = None):
        self.box_rect = box_rect
        self.is_horizontal = random.choice([True, False]) if is_horizontal is None else is_horizontal
        
        if self.is_horizontal:
            self.pos = random.randint(box_rect.top + 20, box_rect.bottom - 20)
        else:
            self.pos = random.randint(box_rect.left + 20, box_rect.right - 20)
        
        self.state = 'warning'
        self.timer = 0
        self.warning_duration = 30
        self.active_duration = 15
        
        self.warning_width = 2
        self.beam_width = 30
    
    def update(self):
        self.timer += 1
        
        if self.state == 'warning' and self.timer >= self.warning_duration:
            self.state = 'active'
            self.timer = 0
        elif self.state == 'active' and self.timer >= self.active_duration:
            self.state = 'done'
    
    def draw(self, surface: pygame.Surface):
        if self.state == 'warning':
            if self.is_horizontal:
                for x in range(self.box_rect.left, self.box_rect.right, 10):
                    pygame.draw.rect(surface, COLOR_YELLOW, (x, self.pos - 1, 6, 2))
            else:
                for y in range(self.box_rect.top, self.box_rect.bottom, 10):
                    pygame.draw.rect(surface, COLOR_YELLOW, (self.pos - 1, y, 2, 6))
        
        elif self.state == 'active':
            if self.is_horizontal:
                pygame.draw.rect(surface, COLOR_RED,
                               (self.box_rect.left, self.pos - self.beam_width // 2,
                                self.box_rect.width, self.beam_width))
            else:
                pygame.draw.rect(surface, COLOR_RED,
                               (self.pos - self.beam_width // 2, self.box_rect.top,
                                self.beam_width, self.box_rect.height))
    
    def is_done(self):
        return self.state == 'done'
    
    def check_collision(self, player_rect: pygame.Rect) -> bool:
        if self.state != 'active':
            return False
        
        if self.is_horizontal:
            beam_rect = pygame.Rect(
                self.box_rect.left, 
                self.pos - self.beam_width // 2,
                self.box_rect.width, 
                self.beam_width
            )
        else:
            beam_rect = pygame.Rect(
                self.pos - self.beam_width // 2,
                self.box_rect.top,
                self.beam_width,
                self.box_rect.height
            )
        
        return beam_rect.colliderect(player_rect)


# ============================================================================
# МЕНЕДЖЕР АТАК
# ============================================================================

class AttackManager:
    """
    Менеджер атак с системой очередей.
    Управляет генерацией снарядов по различным паттернам.
    """
    
    # Базовые типы паттернов (простые)
    BASIC_PATTERNS = [
        'line_rain', 
        'circle_burst', 
        'targeting',
        'bouncing_walls',
        'spiral',
        'laser_warning'
    ]
    
    # Сложные паттерны
    COMPLEX_PATTERNS = [
        'snake_wave',
        'homing_blades',
        'expanding_ring',
        'gravity_wells',
        'rotating_cross'
    ]
    
    # Все доступные паттерны
    PATTERN_TYPES = BASIC_PATTERNS + COMPLEX_PATTERNS
    
    def __init__(self, box_rect: pygame.Rect, bullets_group: pygame.sprite.Group):
        self.box_rect = box_rect
        self.bullets_group = bullets_group
        
        # Система очередей
        self.attack_queue = []
        self.current_pattern_index = 0
        self.pattern_timer = 0
        self.gap_timer = 0
        self.in_gap = False
        self.round_active = False
        
        # Текущий паттерн (может быть списком для комбинированных атак)
        self.current_pattern = None
        self.secondary_pattern = None
        
        # Настройки сложности
        self.difficulty = 1.0
        
        # Таймеры для паттернов
        self.pattern_internal_timer = 0
        self.pattern_internal_timer_2 = 0
        
        # Для лазерного паттерна
        self.lasers = []
        self.laser_spawn_timer = 0
        
        # Для гравитационного режима
        self.gravity_mode = False
        self.gravity_wells = []
        
        # Для вращающегося креста
        self.cross_bullets = []
        self.cross_angle = 0
        self.cross_center = (0, 0)
        
        # Для расширяющихся колец
        self.ring_timer = 0
        
        # Для самонаводящихся лезвий
        self.homing_blades = []
        
        # Инициализация первого раунда
        self._start_new_round()
    
    def _start_new_round(self):
        """Начало нового раунда атаки."""
        all_patterns = self.PATTERN_TYPES.copy()
        self.attack_queue = random.sample(
            all_patterns, 
            min(PATTERNS_PER_ROUND, len(all_patterns))
        )
        
        while len(self.attack_queue) < PATTERNS_PER_ROUND:
            self.attack_queue.append(random.choice(self.PATTERN_TYPES))
        
        self.current_pattern_index = 0
        self.current_pattern = self.attack_queue[0]
        
        # Для простых паттернов добавляем второй паттерн (комбинирование)
        if self.current_pattern in self.BASIC_PATTERNS:
            other_basic = [p for p in self.BASIC_PATTERNS if p != self.current_pattern]
            self.secondary_pattern = random.choice(other_basic) if random.random() < 0.3 else None
        else:
            self.secondary_pattern = None
        
        self.pattern_timer = 0
        self.gap_timer = 0
        self.in_gap = False
        self.round_active = True
        self.pattern_internal_timer = 0
        self.pattern_internal_timer_2 = 0
        self.lasers = []
        self.laser_spawn_timer = 0
        self.gravity_mode = False
        self.gravity_wells = []
        self.cross_bullets = []
        self.cross_angle = 0
        self.ring_timer = 0
        self.homing_blades = []
    
    def update(self, player_x: float, player_y: float) -> bool:
        """Обновление менеджера атак."""
        if not self.round_active:
            return False
        
        if self.in_gap:
            self.gap_timer += 1
            if self.gap_timer >= GAP_BETWEEN_ATTACKS:
                self.in_gap = False
                self.gap_timer = 0
                self._next_pattern()
            return True
        
        self.pattern_timer += 1
        
        if self.pattern_timer >= ATTACK_DURATION:
            self._end_current_pattern()
            return True
        
        self._execute_current_pattern(player_x, player_y)
        
        if self.secondary_pattern:
            self._execute_secondary_pattern(player_x, player_y)
        
        return True
    
    def _execute_current_pattern(self, player_x: float, player_y: float):
        """Выполнение логики текущего паттерна."""
        pattern = self.current_pattern
        
        if pattern == 'line_rain':
            self._pattern_line_rain()
        elif pattern == 'circle_burst':
            self._pattern_circle_burst()
        elif pattern == 'targeting':
            self._pattern_targeting(player_x, player_y)
        elif pattern == 'bouncing_walls':
            self._pattern_bouncing_walls()
        elif pattern == 'spiral':
            self._pattern_spiral()
        elif pattern == 'laser_warning':
            self._pattern_laser_warning()
        elif pattern == 'snake_wave':
            self._pattern_snake_wave()
        elif pattern == 'homing_blades':
            self._pattern_homing_blades(player_x, player_y)
        elif pattern == 'expanding_ring':
            self._pattern_expanding_ring()
        elif pattern == 'gravity_wells':
            self._pattern_gravity_wells(player_x, player_y)
        elif pattern == 'rotating_cross':
            self._pattern_rotating_cross(player_x, player_y)
    
    def _execute_secondary_pattern(self, player_x: float, player_y: float):
        """Выполнение второго паттерна (простого)."""
        pattern = self.secondary_pattern
        
        if pattern == 'line_rain':
            self._pattern_line_rain(secondary=True)
        elif pattern == 'circle_burst':
            self._pattern_circle_burst(secondary=True)
        elif pattern == 'targeting':
            self._pattern_targeting(player_x, player_y, secondary=True)
        elif pattern == 'bouncing_walls':
            self._pattern_bouncing_walls(secondary=True)
    
    def _end_current_pattern(self):
        """Завершение текущего паттерна и переход к следующему."""
        self.bullets_group.empty()
        self.lasers = []
        self.gravity_mode = False
        self.gravity_wells = []
        self.cross_bullets = []
        self.homing_blades = []
        self.in_gap = True
        self.gap_timer = 0
    
    def _next_pattern(self):
        """Переход к следующему паттерну в очереди."""
        self.current_pattern_index += 1
        
        if self.current_pattern_index >= len(self.attack_queue):
            self.round_active = False
            self.current_pattern = None
        else:
            self.current_pattern = self.attack_queue[self.current_pattern_index]
            self.pattern_timer = 0
            self.pattern_internal_timer = 0
            self.pattern_internal_timer_2 = 0
            self.laser_spawn_timer = 0
            
            if self.current_pattern in self.BASIC_PATTERNS:
                other_basic = [p for p in self.BASIC_PATTERNS if p != self.current_pattern]
                self.secondary_pattern = random.choice(other_basic) if random.random() < 0.3 else None
            else:
                self.secondary_pattern = None
    
    def is_round_active(self) -> bool:
        return self.round_active
    
    def start_round(self):
        self._start_new_round()
    
    def get_remaining_attacks(self) -> int:
        return len(self.attack_queue) - self.current_pattern_index
    
    # ========================================================================
    # БАЗОВЫЕ ПАТТЕРНЫ АТАК
    # ========================================================================
    
    def _pattern_line_rain(self, secondary: bool = False):
        """Паттерн "Line Rain" - дождь из линий сверху вниз."""
        if secondary:
            self.pattern_internal_timer_2 += 1
            timer = self.pattern_internal_timer_2
        else:
            self.pattern_internal_timer += 1
            timer = self.pattern_internal_timer
        
        interval = int(LINE_RAIN_INTERVAL / self.difficulty)
        
        if timer >= interval:
            for _ in range(LINE_RAIN_BULLET_COUNT):
                x = random.randint(self.box_rect.left + 20, self.box_rect.right - 60)
                y = self.box_rect.top - 20
                speed = BULLET_BASE_SPEED * self.difficulty
                bullet = LineBullet(x, y, 0, speed)
                bullet.set_bounds(self.box_rect)
                self.bullets_group.add(bullet)
            timer = 0
        
        if secondary:
            self.pattern_internal_timer_2 = timer
        else:
            self.pattern_internal_timer = timer
    
    def _pattern_circle_burst(self, secondary: bool = False):
        """Паттерн "Circle Burst" - круговой взрыв из центра."""
        if secondary:
            self.pattern_internal_timer_2 += 1
            timer = self.pattern_internal_timer_2
        else:
            self.pattern_internal_timer += 1
            timer = self.pattern_internal_timer
        
        interval = int(CIRCLE_BURST_INTERVAL / self.difficulty)
        
        if timer >= interval:
            center_x = self.box_rect.centerx
            center_y = self.box_rect.centery
            
            count = int(CIRCLE_BURST_COUNT * self.difficulty)
            for i in range(count):
                angle = (2 * math.pi * i) / count
                speed = BULLET_BASE_SPEED * 1.5
                vx = math.cos(angle) * speed
                vy = math.sin(angle) * speed
                
                bullet = CircleBullet(center_x, center_y, vx, vy)
                bullet.set_bounds(self.box_rect)
                self.bullets_group.add(bullet)
            timer = 0
        
        if secondary:
            self.pattern_internal_timer_2 = timer
        else:
            self.pattern_internal_timer = timer
    
    def _pattern_targeting(self, player_x: float, player_y: float, secondary: bool = False):
        """Паттерн "Targeting" - снаряды летят к игроку."""
        if secondary:
            self.pattern_internal_timer_2 += 1
            timer = self.pattern_internal_timer_2
        else:
            self.pattern_internal_timer += 1
            timer = self.pattern_internal_timer
        
        interval = int(TARGETING_INTERVAL / self.difficulty)
        
        if timer >= interval:
            corners = [
                (self.box_rect.left, self.box_rect.top),
                (self.box_rect.right, self.box_rect.top),
                (self.box_rect.left, self.box_rect.bottom),
                (self.box_rect.right, self.box_rect.bottom),
            ]
            
            shot_corners = random.sample(corners, min(TARGETING_BULLETS_PER_SHOT, len(corners)))
            
            for corner_x, corner_y in shot_corners:
                speed = BULLET_BASE_SPEED * self.difficulty
                bullet = TargetingBullet(corner_x, corner_y, player_x, player_y, speed)
                bullet.set_bounds(self.box_rect)
                self.bullets_group.add(bullet)
            timer = 0
        
        if secondary:
            self.pattern_internal_timer_2 = timer
        else:
            self.pattern_internal_timer = timer
    
    def _pattern_bouncing_walls(self, secondary: bool = False):
        """Паттерн "Bouncing Walls" - квадраты отскакивают от стенок."""
        if secondary:
            self.pattern_internal_timer_2 += 1
            timer = self.pattern_internal_timer_2
        else:
            self.pattern_internal_timer += 1
            timer = self.pattern_internal_timer
        
        interval = int(60 / self.difficulty)
        
        if timer >= interval:
            side = random.choice(['top', 'bottom', 'left', 'right'])
            
            if side == 'top':
                x = random.randint(self.box_rect.left + 20, self.box_rect.right - 40)
                y = self.box_rect.top + 10
                vx = random.choice([-3, 3])
                vy = random.uniform(2, 4)
            elif side == 'bottom':
                x = random.randint(self.box_rect.left + 20, self.box_rect.right - 40)
                y = self.box_rect.bottom - 30
                vx = random.choice([-3, 3])
                vy = random.uniform(-4, -2)
            elif side == 'left':
                x = self.box_rect.left + 10
                y = random.randint(self.box_rect.top + 20, self.box_rect.bottom - 40)
                vx = random.uniform(2, 4)
                vy = random.choice([-3, 3])
            else:
                x = self.box_rect.right - 30
                y = random.randint(self.box_rect.top + 20, self.box_rect.bottom - 40)
                vx = random.uniform(-4, -2)
                vy = random.choice([-3, 3])
            
            bullet = BouncingBullet(x, y, vx * self.difficulty, vy * self.difficulty, 
                                   self.box_rect, max_bounces=random.randint(3, 4))
            self.bullets_group.add(bullet)
            timer = 0
        
        if secondary:
            self.pattern_internal_timer_2 = timer
        else:
            self.pattern_internal_timer = timer
    
    def _pattern_spiral(self):
        """Паттерн "Spiral" - снаряды вылетают из центра по спирали."""
        self.pattern_internal_timer += 1
        
        if self.pattern_internal_timer >= 3:
            base_angle = (self.pattern_timer * 0.1)
            
            for i in range(2):
                angle = base_angle + (i * math.pi)
                speed = BULLET_BASE_SPEED * 1.2
                
                vx = math.cos(angle) * speed
                vy = math.sin(angle) * speed
                
                bullet = SpiralBullet(self.box_rect.centerx, self.box_rect.centery, vx, vy)
                bullet.set_bounds(self.box_rect)
                self.bullets_group.add(bullet)
            
            self.pattern_internal_timer = 0
    
    def _pattern_laser_warning(self):
        """Паттерн "Laser Warning" - пунктирная линия + широкий луч."""
        self.laser_spawn_timer += 1
        
        for laser in self.lasers[:]:
            laser.update()
            if laser.is_done():
                self.lasers.remove(laser)
        
        if self.laser_spawn_timer >= 60:
            self.laser_spawn_timer = 0
            self.lasers.append(LaserBeam(self.box_rect))
    
    # ========================================================================
    # СЛОЖНЫЕ ПАТТЕРНЫ АТАК
    # ========================================================================
    
    def _pattern_snake_wave(self):
        """Паттерн "Snake/Wave" - снаряды движутся по синусоиде."""
        self.pattern_internal_timer += 1
        
        if self.pattern_internal_timer >= 40:
            self.pattern_internal_timer = 0
            
            y_positions = range(self.box_rect.top + 10, self.box_rect.bottom - 10, 40)
            
            for y in y_positions:
                bullet = WaveBullet(
                    self.box_rect.left - 10,
                    y,
                    speed_x=3 * self.difficulty,
                    amplitude=30,
                    frequency=0.1,
                    box_rect=self.box_rect
                )
                self.bullets_group.add(bullet)
    
    def _pattern_homing_blades(self, player_x: float, player_y: float):
        """Паттерн "Homing Blades" - лезвия нацеливаются на игрока."""
        self.pattern_internal_timer += 1
        
        for blade in self.homing_blades[:]:
            blade.update()
            if blade.state == 'aiming':
                blade.set_target(player_x, player_y)
            if not blade.alive():
                self.homing_blades.remove(blade)
        
        if self.pattern_internal_timer >= 90:
            self.pattern_internal_timer = 0
            
            num_blades = random.randint(2, 3)
            edges = ['top', 'bottom', 'left', 'right']
            chosen_edges = random.sample(edges, num_blades)
            
            for edge in chosen_edges:
                if edge == 'top':
                    x = random.randint(self.box_rect.left + 30, self.box_rect.right - 30)
                    y = self.box_rect.top + 20
                elif edge == 'bottom':
                    x = random.randint(self.box_rect.left + 30, self.box_rect.right - 30)
                    y = self.box_rect.bottom - 20
                elif edge == 'left':
                    x = self.box_rect.left + 20
                    y = random.randint(self.box_rect.top + 30, self.box_rect.bottom - 30)
                else:
                    x = self.box_rect.right - 20
                    y = random.randint(self.box_rect.top + 30, self.box_rect.bottom - 30)
                
                blade = HomingBlade(x, y, self.box_rect)
                blade.set_target(player_x, player_y)
                self.homing_blades.append(blade)
                self.bullets_group.add(blade)
    
    def _pattern_expanding_ring(self):
        """Паттерн "Expanding Ring" - расширяющееся кольцо из пуль."""
        self.ring_timer += 1
        
        if self.ring_timer >= 100:
            self.ring_timer = 0
            
            center_x = random.randint(self.box_rect.left + 50, self.box_rect.right - 50)
            center_y = random.randint(self.box_rect.top + 50, self.box_rect.bottom - 50)
            
            num_bullets = 16
            gaps = random.sample(range(num_bullets), 2)
            
            for i in range(num_bullets):
                if i in gaps:
                    continue
                
                angle = (2 * math.pi * i) / num_bullets
                bullet = ExpandingRingBullet(center_x, center_y, 0, 0)
                bullet.set_bounds(self.box_rect)
                bullet.expand_angle = angle
                bullet.expand_speed = 2
                bullet.expand_radius = 10
                bullet.center_x = center_x
                bullet.center_y = center_y
                
                self.bullets_group.add(bullet)
        
        for bullet in self.bullets_group:
            if hasattr(bullet, 'expand_angle'):
                bullet.expand_radius += bullet.expand_speed * self.difficulty
                bullet.rect.center = (
                    int(bullet.center_x + math.cos(bullet.expand_angle) * bullet.expand_radius),
                    int(bullet.center_y + math.sin(bullet.expand_angle) * bullet.expand_radius)
                )
                
                if bullet.expand_radius > max(self.box_rect.width, self.box_rect.height):
                    bullet.kill()
    
    def _pattern_gravity_wells(self, player_x: float, player_y: float):
        """Паттерн "Gravity Wells" - чёрная дыра притягивает/отталкивает игрока."""
        self.pattern_internal_timer += 1
        
        if not self.gravity_wells:
            well = GravityWell(
                self.box_rect.centerx,
                self.box_rect.centery,
                strength=0.4,
                repel=random.choice([True, False]),
                duration=ATTACK_DURATION
            )
            self.gravity_wells.append(well)
        
        for well in self.gravity_wells:
            well.update()
        
        self.gravity_mode = True
        
        if self.pattern_internal_timer >= 30:
            self.pattern_internal_timer = 0
            
            corner_x = random.choice([self.box_rect.left, self.box_rect.right])
            corner_y = random.choice([self.box_rect.top, self.box_rect.bottom])
            
            angle = math.atan2(
                self.box_rect.centery - corner_y,
                self.box_rect.centerx - corner_x
            )
            angle += random.uniform(-0.5, 0.5)
            
            speed = BULLET_BASE_SPEED * 1.2
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            
            bullet = CircleBullet(corner_x, corner_y, vx, vy)
            bullet.set_bounds(self.box_rect)
            self.bullets_group.add(bullet)
    
    def _pattern_rotating_cross(self, player_x: float, player_y: float):
        """Паттерн "Rotating Cross" - вращающийся крест из пуль."""
        if not self.cross_bullets:
            self.cross_center = (self.box_rect.centerx, self.box_rect.centery)
            
            for i in range(4):
                angle = i * math.pi / 2
                for j in range(8):
                    bullet = RotatingCrossBullet(
                        self.cross_center[0],
                        self.cross_center[1],
                        0, 0
                    )
                    bullet.set_bounds(self.box_rect)
                    bullet.beam_index = i
                    bullet.distance = 30 + j * 25
                    bullet.base_angle = angle
                    self.cross_bullets.append(bullet)
                    self.bullets_group.add(bullet)
        
        self.cross_angle += 0.02 * self.difficulty
        
        for bullet in self.cross_bullets:
            if hasattr(bullet, 'beam_index'):
                angle = bullet.base_angle + self.cross_angle
                bullet.rect.center = (
                    int(self.cross_center[0] + math.cos(angle) * bullet.distance),
                    int(self.cross_center[1] + math.sin(angle) * bullet.distance)
                )
        
        self.pattern_internal_timer += 1
        if self.pattern_internal_timer >= 60:
            self.pattern_internal_timer = 0
            
            for _ in range(2):
                x = random.randint(self.box_rect.left + 20, self.box_rect.right - 20)
                y = self.box_rect.top - 10
                speed = BULLET_BASE_SPEED * 0.8
                bullet = CircleBullet(x, y, 0, speed)
                bullet.set_bounds(self.box_rect)
                self.bullets_group.add(bullet)
    
    # ========================================================================
    # МЕТОДЫ ДЛЯ ВНЕШНЕГО ИСПОЛЬЗОВАНИЯ
    # ========================================================================
    
    def draw_lasers(self, surface: pygame.Surface):
        """Отрисовка лазеров."""
        for laser in self.lasers:
            laser.draw(surface)
    
    def draw_gravity_wells(self, surface: pygame.Surface):
        """Отрисовка гравитационных аномалий."""
        for well in self.gravity_wells:
            well.draw(surface)
    
    def check_laser_collision(self, player_rect: pygame.Rect) -> bool:
        """Проверка столкновения игрока с активными лазерами."""
        for laser in self.lasers:
            if laser.check_collision(player_rect):
                return True
        return False
    
    def get_gravity_force(self, player_x: float, player_y: float) -> tuple:
        """Получение суммарной гравитационной силы."""
        total_fx, total_fy = 0, 0
        for well in self.gravity_wells:
            fx, fy = well.apply_force(player_x, player_y)
            total_fx += fx
            total_fy += fy
        return (total_fx, total_fy)
    
    def is_gravity_mode(self) -> bool:
        """Проверка, активен ли гравитационный режим."""
        return self.gravity_mode or len(self.gravity_wells) > 0
    
    def reset(self):
        """Сброс менеджера атак."""
        self.bullets_group.empty()
        self.attack_queue = []
        self.current_pattern = None
        self.secondary_pattern = None
        self.current_pattern_index = 0
        self.pattern_timer = 0
        self.gap_timer = 0
        self.in_gap = False
        self.round_active = False
        self.pattern_internal_timer = 0
        self.pattern_internal_timer_2 = 0
        self.lasers = []
        self.laser_spawn_timer = 0
        self.gravity_mode = False
        self.gravity_wells = []
        self.cross_bullets = []
        self.cross_angle = 0
        self.ring_timer = 0
        self.homing_blades = []
    
    def get_current_pattern_name(self) -> str:
        """Получение названия текущего паттерна."""
        names = {
            'line_rain': 'Line Rain (Дождь)',
            'circle_burst': 'Circle Burst (Взрыв)',
            'targeting': 'Targeting (Наведение)',
            'bouncing_walls': 'Bouncing Walls (Отскоки)',
            'spiral': 'Spiral (Спираль)',
            'laser_warning': 'Laser Warning (Лазер)',
            'snake_wave': 'Snake Wave (Волна)',
            'homing_blades': 'Homing Blades (Лезвия)',
            'expanding_ring': 'Expanding Ring (Кольцо)',
            'gravity_wells': 'Gravity Wells (Гравитация)',
            'rotating_cross': 'Rotating Cross (Крест)'
        }
        base_name = names.get(self.current_pattern, self.current_pattern or 'Ожидание')
        
        if self.secondary_pattern:
            secondary_name = names.get(self.secondary_pattern, '')
            return f"{base_name} + {secondary_name}"
        
        return base_name
    
    def set_difficulty(self, difficulty: float):
        """Установка уровня сложности."""
        self.difficulty = max(0.5, min(difficulty, 3.0))

    def start_round_with_pattern_count(self, patterns_count: int):
        """
        Начало нового раунда с заданным количеством паттернов.
        Используется для босса во второй фазе.
        
        Аргументы:
            patterns_count: Количество паттернов в раунде
        """
        all_patterns = self.PATTERN_TYPES.copy()
        patterns_count = max(1, min(patterns_count, len(all_patterns)))
        
        self.attack_queue = random.sample(all_patterns, patterns_count)
        
        # Если нужно больше паттернов, добавляем случайные
        while len(self.attack_queue) < patterns_count:
            self.attack_queue.append(random.choice(self.PATTERN_TYPES))
        
        self.current_pattern_index = 0
        self.current_pattern = self.attack_queue[0]
        
        # Для простых паттернов добавляем второй паттерн (комбинирование)
        if self.current_pattern in self.BASIC_PATTERNS:
            other_basic = [p for p in self.BASIC_PATTERNS if p != self.current_pattern]
            self.secondary_pattern = random.choice(other_basic) if random.random() < 0.3 else None
        else:
            self.secondary_pattern = None
        
        self.pattern_timer = 0
        self.gap_timer = 0
        self.in_gap = False
        self.round_active = True
        self.pattern_internal_timer = 0
        self.pattern_internal_timer_2 = 0
        self.lasers = []
        self.laser_spawn_timer = 0
        self.gravity_mode = False
        self.gravity_wells = []
        self.cross_bullets = []
        self.cross_angle = 0
        self.ring_timer = 0
        self.homing_blades = []
    
    def clear_bullets(self):
        """Очистка всех снарядов (используется при переключении паттернов в фазе 2 босса)."""
        self.bullets_group.empty()
        self.lasers = []
        self.gravity_mode = False
        self.gravity_wells = []
        self.cross_bullets = []
        self.homing_blades = []
    
    def set_patterns_per_round(self, count: int):
        """
        Установка количества паттернов для следующего раунда.
        
        Аргументы:
            count: Количество паттернов
        """
        self._patterns_per_round = max(1, count)
