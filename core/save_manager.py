"""
Модуль системы сохранений.
Реализует сохранение и загрузку игрового прогресса в формате JSON.
"""

import json
import os
from core.settings import SAVE_FILE_NAME, PLAYER_MAX_HP


class SaveData:
    """
    Класс данных сохранения.
    Содержит всю информацию о состоянии игры.
    """
    
    def __init__(self):
        """Инициализация данных сохранения."""
        self.location_id = 1
        self.player_x = 0.0
        self.player_y = 0.0
        self.player_hp = PLAYER_MAX_HP
        self.player_max_hp = PLAYER_MAX_HP
        self.inventory = []
        self.defeated_enemies = []
        self.current_map = 'start'
    
    def to_dict(self) -> dict:
        """Конвертация данных в словарь для JSON."""
        return {
            'location_id': self.location_id,
            'player_x': self.player_x,
            'player_y': self.player_y,
            'player_hp': self.player_hp,
            'player_max_hp': self.player_max_hp,
            'inventory': self.inventory,
            'defeated_enemies': self.defeated_enemies,
            'current_map': self.current_map
        }
    
    def from_dict(self, data: dict) -> None:
        """Загрузка данных из словаря."""
        self.location_id = data.get('location_id', 1)
        self.player_x = data.get('player_x', 0.0)
        self.player_y = data.get('player_y', 0.0)
        self.player_hp = data.get('player_hp', PLAYER_MAX_HP)
        self.player_max_hp = data.get('player_max_hp', PLAYER_MAX_HP)
        self.inventory = data.get('inventory', [])
        self.defeated_enemies = data.get('defeated_enemies', [])
        self.current_map = data.get('current_map', 'start')


class SaveManager:
    """
    Менеджер сохранений.
    Управляет сохранением и загрузкой игрового прогресса.
    """
    
    def __init__(self):
        """Инициализация менеджера сохранений."""
        self.save_file = SAVE_FILE_NAME
        self.save_data = SaveData()
        self.has_save = False
    
    def save_game(self, location_id: int, player_x: float, player_y: float,
                  player_hp: int, player_max_hp: int, inventory: list,
                  defeated_enemies: list = None, current_map: str = 'start') -> bool:
        """
        Сохранение игры.
        
        Аргументы:
            location_id: Номер локации
            player_x: Позиция игрока X
            player_y: Позиция игрока Y
            player_hp: Текущее HP игрока
            player_max_hp: Максимальное HP игрока
            inventory: Инвентарь игрока
            defeated_enemies: Список побеждённых врагов
            current_map: Имя текущей карты
            
        Возвращает:
            bool: True если сохранение успешно
        """
        try:
            self.save_data.location_id = location_id
            self.save_data.player_x = player_x
            self.save_data.player_y = player_y
            self.save_data.player_hp = player_hp
            self.save_data.player_max_hp = player_max_hp
            self.save_data.inventory = inventory.copy() if inventory else []
            self.save_data.defeated_enemies = defeated_enemies.copy() if defeated_enemies else []
            self.save_data.current_map = current_map
            
            # Запись в файл
            with open(self.save_file, 'w', encoding='utf-8') as f:
                json.dump(self.save_data.to_dict(), f, indent=2, ensure_ascii=False)
            
            self.has_save = True
            return True
        except (IOError, json.JSONEncodeError):
            return False
    
    def load_game(self) -> SaveData:
        """
        Загрузка игры.
        
        Возвращает:
            SaveData: Данные сохранения или None
        """
        try:
            if not os.path.exists(self.save_file):
                return None
            
            with open(self.save_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.save_data.from_dict(data)
            self.has_save = True
            return self.save_data
        except (IOError, json.JSONDecodeError, KeyError):
            return None
    
    def has_saved_game(self) -> bool:
        """Проверка наличия сохранения."""
        return os.path.exists(self.save_file)
    
    def delete_save(self) -> bool:
        """Удаление сохранения."""
        try:
            if os.path.exists(self.save_file):
                os.remove(self.save_file)
            self.has_save = False
            self.save_data = SaveData()
            return True
        except IOError:
            return False
    
    def get_save_info(self) -> dict:
        """
        Получение информации о сохранении для отображения.
        
        Возвращает:
            dict: Информация о сохранении
        """
        if not self.has_saved_game():
            return None
        
        data = self.load_game()
        if data is None:
            return None
        
        return {
            'location': data.location_id,
            'map': data.current_map,
            'hp': data.player_hp,
            'items': len(data.inventory)
        }
