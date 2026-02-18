"""
Модуль боевого интерфейса.
Содержит классы для кнопок меню боя и подменю действий.

Меню боя включает 4 кнопки:
- FIGHT: Атака врага
- ACT: Действия (Check, Talk и т.д.)
- ITEM: Использование предметов
- MERCY: Пощада врага (если is_sparable = True)
"""

import pygame
from core.settings import (
    BUTTON_FIGHT, BUTTON_ACT, BUTTON_ITEM, BUTTON_MERCY,
    BUTTON_COLOR_NORMAL, BUTTON_COLOR_SELECTED, BUTTON_COLOR_MERCY_SPARE,
    BUTTON_WIDTH, BUTTON_HEIGHT, BUTTON_SPACING,
    BATTLE_BOX_WIDTH, BATTLE_BOX_HEIGHT,
    COLOR_WHITE, COLOR_YELLOW, COLOR_BLACK
)


class Button:
    """
    Класс кнопки боевого меню.
    """
    
    def __init__(self, text: str, x: int, y: int):
        """
        Инициализация кнопки.
        
        Аргументы:
            text: Текст на кнопке
            x: Позиция X
            y: Позиция Y
        """
        self.text = text
        self.x = x
        self.y = y
        self.width = BUTTON_WIDTH
        self.height = BUTTON_HEIGHT
        self.selected = False
        self.mercy_spare = False  # Для кнопки MERCY (можно пощадить)
    
    def get_rect(self) -> pygame.Rect:
        """Получение прямоугольника кнопки."""
        return pygame.Rect(self.x, self.y, self.width, self.height)
    
    def draw(self, surface: pygame.Surface, font: pygame.font.Font) -> None:
        """
        Отрисовка кнопки.
        
        Аргументы:
            surface: Поверхность для отрисовки
            font: Шрифт для текста
        """
        # Определение цвета
        if self.selected:
            color = BUTTON_COLOR_SELECTED
        elif self.mercy_spare and self.text == BUTTON_MERCY:
            color = BUTTON_COLOR_MERCY_SPARE
        else:
            color = BUTTON_COLOR_NORMAL
        
        # Отрисовка текста (как в Undertale - просто текст)
        text_surface = font.render(self.text, True, color)
        
        # Если выбрана - рисуем указатель (сердечко)
        if self.selected:
            heart_x = self.x - 20
            heart_y = self.y + (self.height - 10) // 2
            pygame.draw.circle(surface, COLOR_YELLOW, (heart_x + 5, heart_y + 5), 5)
        
        surface.blit(text_surface, (self.x, self.y))


class BattleUI:
    """
    Класс боевого интерфейса.
    Управляет кнопками меню и подменю действий.
    """
    
    # Список кнопок в порядке отображения
    BUTTON_NAMES = [BUTTON_FIGHT, BUTTON_ACT, BUTTON_ITEM, BUTTON_MERCY]
    
    def __init__(self, screen_width: int, screen_height: int, box_y: int):
        """
        Инициализация боевого интерфейса.
        
        Аргументы:
            screen_width: Ширина экрана
            screen_height: Высота экрана
            box_y: Y-координата нижней части рамки боя
        """
        self.screen_width = screen_width
        self.screen_height = screen_height
        
        # Создание кнопок (под рамкой боя)
        self.buttons = []
        self._create_buttons(box_y + BATTLE_BOX_HEIGHT + 30)
        
        # Текущая выбранная кнопка
        self.selected_index = 0
        self.buttons[0].selected = True
        
        # Состояние подменю
        self.submenu_active = False
        self.submenu_items = []
        self.submenu_selected = 0
        
        # Шрифт
        self.font = pygame.font.Font(None, 28)
        self.small_font = pygame.font.Font(None, 24)
    
    def _create_buttons(self, y: int) -> None:
        """
        Создание кнопок меню.
        
        Аргументы:
            y: Y-координата для кнопок
        """
        total_width = len(self.BUTTON_NAMES) * BUTTON_WIDTH + (len(self.BUTTON_NAMES) - 1) * BUTTON_SPACING
        start_x = (self.screen_width - total_width) // 2
        
        for i, name in enumerate(self.BUTTON_NAMES):
            x = start_x + i * (BUTTON_WIDTH + BUTTON_SPACING)
            button = Button(name, x, y)
            self.buttons.append(button)
    
    def handle_input(self, key: int) -> str:
        """
        Обработка ввода в меню.
        
        Аргументы:
            key: Нажатая клавиша
            
        Возвращает:
            str: Название действия или None
        """
        if self.submenu_active:
            return self._handle_submenu_input(key)
        else:
            return self._handle_main_menu_input(key)
    
    def _handle_main_menu_input(self, key: int) -> str:
        """
        Обработка ввода в главном меню.
        
        Аргументы:
            key: Нажатая клавиша
            
        Возвращает:
            str: Название действия или None
        """
        # Переключение кнопок стрелками
        if key == pygame.K_LEFT:
            self.buttons[self.selected_index].selected = False
            self.selected_index = (self.selected_index - 1) % len(self.buttons)
            self.buttons[self.selected_index].selected = True
        
        elif key == pygame.K_RIGHT:
            self.buttons[self.selected_index].selected = False
            self.selected_index = (self.selected_index + 1) % len(self.buttons)
            self.buttons[self.selected_index].selected = True
        
        # Выбор кнопки (Z)
        elif key == pygame.K_z:
            return self.BUTTON_NAMES[self.selected_index]
        
        return None
    
    def _handle_submenu_input(self, key: int) -> str:
        """
        Обработка ввода в подменю.
        
        Аргументы:
            key: Нажатая клавиша
            
        Возвращает:
            str: Выбранный пункт подменю или 'back' или None
        """
        if not self.submenu_items:
            if key == pygame.K_x or key == pygame.K_z:
                self.close_submenu()
                return 'back'
            return None
        
        if key == pygame.K_UP:
            self.submenu_selected = (self.submenu_selected - 1) % len(self.submenu_items)
        
        elif key == pygame.K_DOWN:
            self.submenu_selected = (self.submenu_selected + 1) % len(self.submenu_items)
        
        elif key == pygame.K_z:
            # Сохраняем индекс и выбранный элемент ДО закрытия
            selected_idx = self.submenu_selected
            selected_item = self.submenu_items[selected_idx]
            self.close_submenu()
            
            # Если это предмет (dict), возвращаем специальный формат
            if isinstance(selected_item, dict):
                return f'item:{selected_idx}'
            return selected_item
        
        elif key == pygame.K_x:
            self.close_submenu()
            return 'back'
        
        return None
    
    def open_submenu(self, items: list) -> None:
        """
        Открытие подменю с пунктами.
        
        Аргументы:
            items: Список пунктов подменю
        """
        self.submenu_active = True
        self.submenu_items = items
        self.submenu_selected = 0
    
    def open_item_menu(self, inventory: list) -> None:
        """
        Открытие меню предметов с инвентарём.
        
        Аргументы:
            inventory: Список предметов игрока
        """
        self.submenu_active = True
        self.submenu_items = inventory.copy() if inventory else []
        self.submenu_selected = 0
    
    def get_selected_item_index(self) -> int:
        """Получение индекса выбранного предмета."""
        return self.submenu_selected
    
    def close_submenu(self) -> None:
        """Закрытие подменю."""
        self.submenu_active = False
        self.submenu_items = []
        self.submenu_selected = 0
    
    def set_mercy_spare(self, value: bool) -> None:
        """
        Установка возможности пощады для кнопки MERCY.
        
        Аргументы:
            value: True если врага можно пощадить
        """
        for button in self.buttons:
            if button.text == BUTTON_MERCY:
                button.mercy_spare = value
    
    def get_selected_button(self) -> str:
        """Получение названия выбранной кнопки."""
        return self.BUTTON_NAMES[self.selected_index]
    
    def draw(self, surface: pygame.Surface) -> None:
        """
        Отрисовка боевого интерфейса.
        
        Аргументы:
            surface: Поверхность для отрисовки
        """
        # Отрисовка кнопок
        for button in self.buttons:
            button.draw(surface, self.font)
        
        # Отрисовка подменю
        if self.submenu_active:
            self._draw_submenu(surface)
    
    def _draw_submenu(self, surface: pygame.Surface) -> None:
        """Отрисовка подменю."""
        # Фон подменю
        menu_width = 250
        menu_height = max(len(self.submenu_items) * 30 + 20, 50)
        menu_x = 50
        menu_y = 150
        
        # Рамка подменю
        menu_rect = pygame.Rect(menu_x, menu_y, menu_width, menu_height)
        pygame.draw.rect(surface, COLOR_BLACK, menu_rect)
        pygame.draw.rect(surface, COLOR_WHITE, menu_rect, 2)
        
        # Если список пуст
        if not self.submenu_items:
            text = self.small_font.render("- Пусто -", True, (150, 150, 150))
            surface.blit(text, (menu_x + 20, menu_y + 15))
            return
        
        # Пункты подменю
        for i, item in enumerate(self.submenu_items):
            y = menu_y + 10 + i * 30
            
            # Указатель для выбранного пункта
            if i == self.submenu_selected:
                pygame.draw.circle(surface, COLOR_YELLOW, (menu_x + 15, y + 10), 5)
            
            # Текст пункта (может быть строкой или dict)
            if isinstance(item, dict):
                item_name = item.get('name', '???')
                heal_value = item.get('heal_value', 0)
                text_str = f"{item_name} (+{heal_value} HP)"
            else:
                text_str = str(item)
            
            text = self.small_font.render(text_str, True, COLOR_WHITE)
            surface.blit(text, (menu_x + 30, y))
    
    def is_submenu_active(self) -> bool:
        """Проверка, открыто ли подменю."""
        return self.submenu_active
