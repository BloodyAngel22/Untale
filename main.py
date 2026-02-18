"""
Главный модуль игры в стиле Undertale.
Точка входа, инициализация Pygame и игровой цикл.

Структура проекта:
- main.py: точка входа
- core/settings.py: константы и настройки
- core/engine.py: GameManager, World, Battle
- entities/player.py: класс Player
- combat/bullet.py: классы снарядов
- combat/patterns.py: AttackManager с паттернами атак
"""

import pygame
import sys

from core.settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS,
    FULLSCREEN, FULLSCREEN_SCALE, WINDOW_WIDTH, WINDOW_HEIGHT
)
from core.engine import GameManager


class DisplayManager:
    """Менеджер дисплея для управления полноэкранным режимом."""
    
    def __init__(self):
        self.is_fullscreen = FULLSCREEN
        self.base_width = SCREEN_WIDTH
        self.base_height = SCREEN_HEIGHT
        self.screen = None
        self.game_surface = None
        self._create_display()
    
    def _create_display(self):
        """Создание окна или полноэкранного режима."""
        if self.is_fullscreen:
            # Получаем разрешение экрана
            info = pygame.display.Info()
            self.display_width = info.current_w
            self.display_height = info.current_h
            
            # Создаём полноэкранную поверхность
            self.screen = pygame.display.set_mode(
                (self.display_width, self.display_height),
                pygame.FULLSCREEN
            )
            
            # Создаём поверхность для рендеринга игры
            if FULLSCREEN_SCALE:
                self.game_surface = pygame.Surface((self.base_width, self.base_height))
            else:
                self.game_surface = pygame.Surface((self.display_width, self.display_height))
        else:
            self.display_width = WINDOW_WIDTH
            self.display_height = WINDOW_HEIGHT
            self.screen = pygame.display.set_mode((self.display_width, self.display_height))
            self.game_surface = pygame.Surface((self.base_width, self.base_height))
        
        pygame.display.set_caption("Undertale-style Game - Modular Edition")
    
    def toggle_fullscreen(self):
        """Переключение между полноэкранным и оконным режимом."""
        self.is_fullscreen = not self.is_fullscreen
        self._create_display()
    
    def get_render_surface(self) -> pygame.Surface:
        """Получение поверхности для рендеринга игры."""
        return self.game_surface
    
    def present(self):
        """Отображение игрового экрана на мониторе."""
        if self.is_fullscreen and FULLSCREEN_SCALE:
            # Масштабирование с сохранением пропорций
            scale = min(
                self.display_width / self.base_width,
                self.display_height / self.base_height
            )
            scaled_width = int(self.base_width * scale)
            scaled_height = int(self.base_height * scale)
            
            # Центрирование
            offset_x = (self.display_width - scaled_width) // 2
            offset_y = (self.display_height - scaled_height) // 2
            
            # Масштабирование
            scaled_surface = pygame.transform.scale(
                self.game_surface,
                (scaled_width, scaled_height)
            )
            
            # Заполнение фона
            self.screen.fill((0, 0, 0))
            self.screen.blit(scaled_surface, (offset_x, offset_y))
        else:
            # Прямое копирование
            self.screen.blit(self.game_surface, (0, 0))
        
        pygame.display.flip()
        

def main():
    """
    Точка входа в игру.
    Инициализирует Pygame, создаёт окно и запускает игровой цикл.
    """
    # Инициализация Pygame
    pygame.init()
    
    # Инициализация аудио миксера (должна быть до создания AudioManager)
    # frequency=44100 - частота дискретизации
    # size=-16 - 16-битный звук (отрицательное значение = signed)
    # channels=2 - стерео
    # buffer=512 - размер буфера (меньше = меньше задержка)
    pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
    
    # Создание менеджера дисплея
    display = DisplayManager()
    
    # Создание менеджера игры
    game_manager = GameManager(SCREEN_WIDTH, SCREEN_HEIGHT)
    
    # Передаём ссылку на менеджер дисплея
    game_manager.set_display_manager(display)
    
    # Часы для контроля FPS
    clock = pygame.time.Clock()
    
    # Флаг работы игры
    running = True
    
    # Главный игровой цикл
    while running:
        # Обработка событий
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            else:
                game_manager.handle_event(event)
        
        # Получение состояния клавиш
        keys = pygame.key.get_pressed()
        
        # Обновление игры
        game_manager.update(keys)
        
        # Отрисовка на игровой поверхности
        game_surface = display.get_render_surface()
        game_manager.draw(game_surface)
        
        # Отображение на экране
        display.present()
        
        # Контроль FPS
        clock.tick(FPS)
    
    # Остановка музыки перед выходом
    game_manager.audio_manager.stop_music(fadeout=False)
    
    # Завершение работы Pygame
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
