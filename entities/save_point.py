"""
Модуль точки сохранения.
Реализует объект SavePoint (сверкающая звезда) для сохранения прогресса.
"""

import pygame
import math
from core.settings import (
    TILE_SIZE, SAVEPOINT_COLOR, SAVEPOINT_GLOW_COLOR,
    PLAYER_MAX_HP
)


class SavePoint:
    """
    Класс точки сохранения.
    Сверкающая звезда, при взаимодействии с которой сохраняется игра.
    """
    
    def __init__(self, x: int, y: int):
        """
        Инициализация точки сохранения.
        
        Аргументы:
            x: Позиция X в пикселях
            y: Позиция Y в пикселях
        """
        self.x = x
        self.y = y
        self.size = TILE_SIZE
        
        # Прямоугольник коллизии
        self.rect = pygame.Rect(x, y, self.size, self.size)
        
        # Анимация
        self.animation_timer = 0
        self.glow_phase = 0
        self.sparkle_particles = []
        
        # Состояние
        self.is_active = True
        self.interaction_cooldown = 0
        self.show_save_message = False
        self.save_message_timer = 0
    
    def update(self) -> None:
        """Обновление анимации."""
        self.animation_timer += 1
        self.glow_phase = (self.glow_phase + 0.1) % (2 * math.pi)
        
        # Обновление кулдауна взаимодействия
        if self.interaction_cooldown > 0:
            self.interaction_cooldown -= 1
        
        # Обновление таймера сообщения
        if self.save_message_timer > 0:
            self.save_message_timer -= 1
            if self.save_message_timer <= 0:
                self.show_save_message = False
        
        # Обновление частиц
        self._update_particles()
        
        # Спавн новых частиц
        if self.animation_timer % 15 == 0:
            self._spawn_particle()
    
    def _spawn_particle(self) -> None:
        """Создание новой частицы искры."""
        import random
        particle = {
            'x': self.x + self.size // 2 + random.randint(-10, 10),
            'y': self.y + self.size // 2 + random.randint(-10, 10),
            'vx': random.uniform(-0.5, 0.5),
            'vy': random.uniform(-1, -0.3),
            'life': 30,
            'size': random.randint(2, 4)
        }
        self.sparkle_particles.append(particle)
    
    def _update_particles(self) -> None:
        """Обновление частиц искр."""
        for particle in self.sparkle_particles[:]:
            particle['x'] += particle['vx']
            particle['y'] += particle['vy']
            particle['life'] -= 1
            
            if particle['life'] <= 0:
                self.sparkle_particles.remove(particle)
    
    def check_collision(self, player_rect: pygame.Rect) -> bool:
        """
        Проверка столкновения с игроком.
        
        Аргументы:
            player_rect: Прямоугольник игрока
            
        Возвращает:
            bool: True если игрок касается точки сохранения
        """
        return self.rect.colliderect(player_rect) and self.is_active
    
    def can_interact(self) -> bool:
        """Проверка возможности взаимодействия."""
        return self.is_active and self.interaction_cooldown == 0
    
    def interact(self) -> dict:
        """
        Взаимодействие с точкой сохранения.
        
        Возвращает:
            dict: Данные о сохранении или None
        """
        if not self.can_interact():
            return None
        
        self.interaction_cooldown = 60  # 1 секунда кулдаун
        self.show_save_message = True
        self.save_message_timer = 90  # 1.5 секунды
        
        return {
            'type': 'save_point',
            'heal': True,
            'message': 'Progress Saved'
        }
    
    def draw(self, surface: pygame.Surface) -> None:
        """
        Отрисовка точки сохранения.
        
        Аргументы:
            surface: Поверхность для отрисовки
        """
        if not self.is_active:
            return
        
        center_x = self.x + self.size // 2
        center_y = self.y + self.size // 2
        
        # Эффект свечения (пульсация)
        glow_intensity = 0.5 + 0.5 * math.sin(self.glow_phase)
        glow_size = int(20 + 5 * math.sin(self.glow_phase))
        
        # Внешнее свечение
        glow_color = (
            int(SAVEPOINT_GLOW_COLOR[0] * glow_intensity),
            int(SAVEPOINT_GLOW_COLOR[1] * glow_intensity),
            int(SAVEPOINT_GLOW_COLOR[2] * glow_intensity)
        )
        
        # Рисуем несколько слоёв свечения
        for i in range(3):
            alpha = int(100 * glow_intensity * (1 - i * 0.3))
            glow_surf = pygame.Surface((glow_size * 2, glow_size * 2), pygame.SRCALPHA)
            pygame.draw.circle(
                glow_surf, 
                (*glow_color, alpha), 
                (glow_size, glow_size), 
                glow_size - i * 5
            )
            surface.blit(
                glow_surf, 
                (center_x - glow_size, center_y - glow_size)
            )
        
        # Рисуем звезду
        self._draw_star(surface, center_x, center_y)
        
        # Рисуем частицы
        self._draw_particles(surface)
        
        # Рисуем сообщение о сохранении
        if self.show_save_message:
            self._draw_save_message(surface)
    
    def _draw_star(self, surface: pygame.Surface, cx: int, cy: int) -> None:
        """
        Отрисовка звезды.
        
        Аргументы:
            surface: Поверхность
            cx: Центр X
            cy: Центр Y
        """
        # Размер звезды
        outer_radius = 12
        inner_radius = 5
        num_points = 5
        
        # Вычисляем точки звезды
        points = []
        for i in range(num_points * 2):
            angle = (i * math.pi / num_points) - math.pi / 2
            if i % 2 == 0:
                radius = outer_radius
            else:
                radius = inner_radius
            
            # Добавляем небольшое вращение
            angle += self.animation_timer * 0.02
            
            x = cx + radius * math.cos(angle)
            y = cy + radius * math.sin(angle)
            points.append((x, y))
        
        # Рисуем звезду
        if len(points) >= 3:
            pygame.draw.polygon(surface, SAVEPOINT_COLOR, points)
            pygame.draw.polygon(surface, SAVEPOINT_GLOW_COLOR, points, 2)
    
    def _draw_particles(self, surface: pygame.Surface) -> None:
        """Отрисовка частиц искр."""
        for particle in self.sparkle_particles:
            alpha = int(255 * (particle['life'] / 30))
            color = (*SAVEPOINT_GLOW_COLOR[:3], alpha)
            
            # Создаём поверхность с прозрачностью
            particle_surf = pygame.Surface(
                (particle['size'] * 2, particle['size'] * 2), 
                pygame.SRCALPHA
            )
            pygame.draw.circle(
                particle_surf, 
                color, 
                (particle['size'], particle['size']), 
                particle['size']
            )
            surface.blit(
                particle_surf, 
                (particle['x'] - particle['size'], particle['y'] - particle['size'])
            )
    
    def _draw_save_message(self, surface: pygame.Surface) -> None:
        """Отрисовка сообщения о сохранении."""
        font = pygame.font.Font(None, 28)
        
        # Текст сообщения
        text = font.render("Progress Saved", True, SAVEPOINT_COLOR)
        
        # Позиция над точкой сохранения
        text_x = self.x + (self.size - text.get_width()) // 2
        text_y = self.y - 30
        
        # Фон для текста
        bg_rect = pygame.Rect(
            text_x - 10, text_y - 5,
            text.get_width() + 20, text.get_height() + 10
        )
        
        # Мигание текста
        if self.save_message_timer % 10 < 7:
            pygame.draw.rect(surface, (20, 20, 20), bg_rect)
            pygame.draw.rect(surface, SAVEPOINT_COLOR, bg_rect, 2)
            surface.blit(text, (text_x, text_y))
    
    def get_rect(self) -> pygame.Rect:
        """Получение прямоугольника коллизии."""
        return self.rect
