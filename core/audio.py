"""
Модуль управления аудио.
Управляет фоновой музыкой через pygame.mixer.music.
Автоматически меняет треки при смене состояний игры.
"""

import pygame
import random
import os
from core.settings import (
    MUSIC_LOCATION_1, MUSIC_LOCATION_2,
    MUSIC_FIGHT_1, MUSIC_FIGHT_2, MUSIC_BOSS, MUSIC_GAME_OVER,
    MUSIC_FADEOUT_TIME, MUSIC_VOLUME
)


class AudioManager:
    """
    Менеджер аудио для управления фоновой музыкой.
    
    Поддерживает:
    - Музыку локаций (location1.mp3, location2.mp3)
    - Боевую музыку (fight1.mp3, fight2.mp3 для мобов, boss.mp3 для босса)
    - Музыку Game Over (game_over.mp3)
    """
    
    def __init__(self):
        """Инициализация менеджера аудио."""
        self.current_track = None
        self.current_state = None
        self.current_location = None
        self.is_boss_battle = False
        self.volume = MUSIC_VOLUME
        self.enabled = True
        
        # Проверяем наличие папки с музыкой
        self.music_dir = "assets/music"
        self._ensure_music_directory()
    
    def _ensure_music_directory(self) -> None:
        """Создаёт директорию для музыки, если она не существует."""
        if not os.path.exists(self.music_dir):
            os.makedirs(self.music_dir)
    
    def _file_exists(self, filepath: str) -> bool:
        """Проверяет существование файла."""
        return os.path.exists(filepath)
    
    def _play_music(self, filepath: str, loops: int = -1) -> bool:
        """
        Воспроизведение музыкального файла.
        
        Аргументы:
            filepath: Путь к файлу
            loops: Количество повторов (-1 = бесконечно)
            
        Возвращает:
            bool: True если музыка начала играть
        """
        if not self.enabled:
            return False
        
        if not self._file_exists(filepath):
            # Файл не найден - silently skip
            self.current_track = None
            return False
        
        try:
            # Останавливаем текущую музыку с затуханием
            if pygame.mixer.music.get_busy():
                pygame.mixer.music.fadeout(MUSIC_FADEOUT_TIME)
            
            # Загружаем и воспроизводим новый трек
            pygame.mixer.music.load(filepath)
            pygame.mixer.music.set_volume(self.volume)
            pygame.mixer.music.play(loops)
            self.current_track = filepath
            return True
        except pygame.error:
            self.current_track = None
            return False
    
    def stop_music(self, fadeout: bool = True) -> None:
        """
        Остановка музыки.
        
        Аргументы:
            fadeout: Использовать плавное затухание
        """
        try:
            if pygame.mixer.music.get_busy():
                if fadeout:
                    pygame.mixer.music.fadeout(MUSIC_FADEOUT_TIME)
                else:
                    pygame.mixer.music.stop()
            self.current_track = None
        except pygame.error:
            pass
    
    def pause_music(self) -> None:
        """Пауза музыки."""
        try:
            pygame.mixer.music.pause()
        except pygame.error:
            pass
    
    def unpause_music(self) -> None:
        """Возобновление музыки."""
        try:
            pygame.mixer.music.unpause()
        except pygame.error:
            pass
    
    def set_volume(self, volume: float) -> None:
        """
        Установка громкости.
        
        Аргументы:
            volume: Громкость от 0.0 до 1.0
        """
        self.volume = max(0.0, min(1.0, volume))
        try:
            pygame.mixer.music.set_volume(self.volume)
        except pygame.error:
            pass
    
    def toggle_mute(self) -> bool:
        """
        Переключение звука (вкл/выкл).
        
        Возвращает:
            bool: Новое состояние (True = звук включен)
        """
        self.enabled = not self.enabled
        if not self.enabled:
            self.stop_music(fadeout=False)
        elif self.current_track:
            self._play_music(self.current_track)
        return self.enabled
    
    # ========================================================================
    # МУЗЫКА ЛОКАЦИЙ
    # ========================================================================
    
    def play_location_music(self, location_id: int) -> None:
        """
        Воспроизведение музыки локации.
        
        Аргументы:
            location_id: Номер локации (1 или 2)
        """
        self.current_state = 'overworld'
        self.current_location = location_id
        
        if location_id == 1:
            self._play_music(MUSIC_LOCATION_1)
        elif location_id == 2:
            self._play_music(MUSIC_LOCATION_2)
        else:
            self._play_music(MUSIC_LOCATION_1)
    
    # ========================================================================
    # БОЕВАЯ МУЗЫКА
    # ========================================================================
    
    def play_battle_music(self, is_boss: bool = False) -> None:
        """
        Воспроизведение боевой музыки.
        
        Аргументы:
            is_boss: True если бой с боссом
        """
        self.current_state = 'battle'
        self.is_boss_battle = is_boss
        
        if is_boss:
            self._play_music(MUSIC_BOSS)
        else:
            # Случайный выбор между fight1 и fight2
            track = random.choice([MUSIC_FIGHT_1, MUSIC_FIGHT_2])
            self._play_music(track)
    
    # ========================================================================
    # МУЗЫКА GAME OVER
    # ========================================================================
    
    def play_game_over_music(self) -> None:
        """Воспроизведение музыки Game Over (один раз, без зацикливания)."""
        self.current_state = 'game_over'
        self._play_music(MUSIC_GAME_OVER, loops=0)
    
    # ========================================================================
    # ВОЗВРАТ К ПРЕДЫДУЩЕЙ МУЗЫКЕ
    # ========================================================================
    
    def resume_location_music(self) -> None:
        """Возобновление музыки локации после боя."""
        if self.current_location:
            self.play_location_music(self.current_location)
        else:
            self.play_location_music(1)
    
    def is_music_playing(self) -> bool:
        """Проверка, играет ли музыка."""
        try:
            return pygame.mixer.music.get_busy()
        except pygame.error:
            return False
    
    def get_current_state(self) -> str:
        """Получение текущего состояния аудио."""
        return self.current_state
