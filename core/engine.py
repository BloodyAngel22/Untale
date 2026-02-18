"""
Модуль игрового движка.
Содержит класс GameManager, управляющий сменой состояний игры.

Менеджер состояний координирует работу всех модулей:
1. При состоянии MAIN_MENU: главное меню с выбором New Game/Continue/Quit
2. При состоянии OVERWORLD: управляет картой и игроком в режиме исследования
3. При состоянии BATTLE: управляет боем, атаками, UI и игроком-душой
4. При состоянии GAME_OVER: показывает экран проигрыша

Передача данных между модулями:
- GameManager создаёт и хранит ссылки на все компоненты
- MapManager управляет тайловой картой и переходами
- BattleUI управляет кнопками меню боя
- При смене состояния передаётся информация о враге
"""

import pygame
import random
from core.settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT,
    STATE_MAIN_MENU, STATE_OVERWORLD, STATE_BATTLE, STATE_GAME_OVER, STATE_MENU,
    BATTLE_BOX_WIDTH, BATTLE_BOX_HEIGHT,
    PLAYER_DAMAGE, PLAYER_ATTACK_DAMAGE, TILE_SIZE,
    COLOR_BLACK, COLOR_WHITE, COLOR_YELLOW, COLOR_RED, BOX_COLOR,
    BUTTON_FIGHT, BUTTON_ACT, BUTTON_ITEM, BUTTON_MERCY,
    MENU_ITEM_CONTINUE, MENU_ITEM_FULLSCREEN, MENU_ITEM_QUIT, MENU_ITEM_LOAD_SAVE,
    TITLE_MENU_NEW_GAME, TITLE_MENU_CONTINUE, TITLE_MENU_QUIT,
    MOB_PATTERNS_PER_ROUND, PLAYER_MAX_HP,
    SAFETY_PAUSE_DURATION, SAFETY_PAUSE_MESSAGE, WARMUP_DURATION, WARMUP_MESSAGE
)
from entities.player import Player
from entities.pickup_item import PickupItem, ItemData
from entities.save_point import SavePoint
from combat.patterns import AttackManager
from combat.battle_ui import BattleUI
from scenes.map_manager import MapManager, Enemy
from core.audio import AudioManager
from core.save_manager import SaveManager


class MainMenu:
    """
    Главное меню игры в стиле Undertale.
    Чёрный фон, белый текст, логотип сверху.
    """
    
    def __init__(self, screen_width: int, screen_height: int):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.selected_index = 0
        self.has_save = False
        self.menu_items = [TITLE_MENU_NEW_GAME, TITLE_MENU_CONTINUE, TITLE_MENU_QUIT]
        
        # Анимация
        self.animation_timer = 0
        
    def check_save(self, save_manager: SaveManager) -> None:
        """Проверка наличия сохранения."""
        self.has_save = save_manager.has_saved_game()
        # Если нет сохранения, Continue неактивна
        if not self.has_save:
            # Пропускаем Continue при навигации
            pass
        
    def handle_input(self, key: int) -> str:
        """Обработка ввода в меню."""
        # Определяем доступные пункты
        available_items = self._get_available_items()
        
        if key == pygame.K_UP:
            # Переход к предыдущему доступному пункту
            current_item = available_items[self.selected_index] if self.selected_index < len(available_items) else available_items[0]
            current_idx = self.menu_items.index(current_item)
            
            # Ищем предыдущий доступный
            for i in range(len(self.menu_items) - 1, -1, -1):
                idx = (current_idx + i) % len(self.menu_items)
                if self._is_item_available(self.menu_items[idx]):
                    self.selected_index = self.menu_items.index(self.menu_items[idx])
                    break
                    
        elif key == pygame.K_DOWN:
            # Переход к следующему доступному пункту
            current_item = available_items[self.selected_index] if self.selected_index < len(available_items) else available_items[0]
            current_idx = self.menu_items.index(current_item)
            
            # Ищем следующий доступный
            for i in range(1, len(self.menu_items) + 1):
                idx = (current_idx + i) % len(self.menu_items)
                if self._is_item_available(self.menu_items[idx]):
                    self.selected_index = self.menu_items.index(self.menu_items[idx])
                    break
                    
        elif key == pygame.K_z or key == pygame.K_RETURN:
            selected_item = self.menu_items[self.selected_index]
            if self._is_item_available(selected_item):
                return selected_item
                
        return None
    
    def _get_available_items(self) -> list:
        """Получение списка доступных пунктов."""
        return [item for item in self.menu_items if self._is_item_available(item)]
    
    def _is_item_available(self, item: str) -> bool:
        """Проверка доступности пункта меню."""
        if item == TITLE_MENU_CONTINUE:
            return self.has_save
        return True

    def update(self) -> None:
        """Обновление анимации."""
        self.animation_timer += 1
    
    def draw(self, surface: pygame.Surface) -> None:
        """Отрисовка главного меню."""
        # Чёрный фон
        surface.fill(COLOR_BLACK)
        
        # Логотип/название игры
        title_font = pygame.font.Font(None, 72)
        title_text = "UNDERTALE"
        
        # Эффект мерцания для названия
        flicker = abs(pygame.math.Vector2(1, 0).rotate(self.animation_timer * 2).x)
        title_color = (
            int(255 * (0.8 + 0.2 * flicker)),
            int(255 * (0.8 + 0.2 * flicker)),
            int(255 * (0.8 + 0.2 * flicker))
        )
        
        title = title_font.render(title_text, True, title_color)
        title_x = (self.screen_width - title.get_width()) // 2
        title_y = 120
        surface.blit(title, (title_x, title_y))
        
        # Подзаголовок
        subtitle_font = pygame.font.Font(None, 28)
        subtitle = subtitle_font.render("- Style Game Demo -", True, (150, 150, 150))
        subtitle_x = (self.screen_width - subtitle.get_width()) // 2
        surface.blit(subtitle, (subtitle_x, title_y + 60))
        
        # Пункты меню
        item_font = pygame.font.Font(None, 40)
        menu_y = 280
        item_spacing = 60
        
        for i, item in enumerate(self.menu_items):
            # Проверяем доступность
            is_available = self._is_item_available(item)
            is_selected = (i == self.selected_index)
            
            # Цвет
            if not is_available:
                color = (80, 80, 80)  # Серый для недоступных
            elif is_selected:
                color = COLOR_YELLOW
            else:
                color = COLOR_WHITE
            
            # Текст
            text = item_font.render(item, True, color)
            text_x = (self.screen_width - text.get_width()) // 2
            text_y = menu_y + i * item_spacing
            surface.blit(text, (text_x, text_y))
            
            # Индикатор выбора (сердечко) для выбранного пункта
            if is_selected and is_available:
                heart_x = text_x - 30
                heart_y = text_y + 5
                self._draw_heart(surface, heart_x, heart_y, COLOR_RED)
        
        # Подсказка
        hint_font = pygame.font.Font(None, 24)
        hint = hint_font.render("↑↓ - выбор, Z - подтвердить", True, (100, 100, 100))
        hint_x = (self.screen_width - hint.get_width()) // 2
        surface.blit(hint, (hint_x, self.screen_height - 50))
        
        # Информация о сохранении
        if self.has_save:
            save_info_font = pygame.font.Font(None, 20)
            save_text = save_info_font.render("Найдено сохранение", True, (100, 200, 100))
            save_x = (self.screen_width - save_text.get_width()) // 2
            surface.blit(save_text, (save_x, self.screen_height - 80))
    
    def _draw_heart(self, surface: pygame.Surface, x: int, y: int, color):
        """Отрисовка сердечка."""
        pygame.draw.circle(surface, color, (x + 5, y + 5), 5)
        pygame.draw.circle(surface, color, (x + 15, y + 5), 5)
        pygame.draw.polygon(surface, color, [(x, y + 7), (x + 10, y + 20), (x + 20, y + 7)])
    
    def reset(self):
        """Сброс меню."""
        self.selected_index = 0


class PauseMenu:
    """Меню паузы игры."""
    
    MENU_ITEMS = [MENU_ITEM_CONTINUE, MENU_ITEM_LOAD_SAVE, MENU_ITEM_FULLSCREEN, MENU_ITEM_QUIT]
    
    def __init__(self, screen_width: int, screen_height: int):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.selected_index = 0
        self.is_fullscreen = False
        self.has_save = False
        
    def check_save(self, save_manager: SaveManager) -> None:
        """Проверка наличия сохранения."""
        self.has_save = save_manager.has_saved_game()
        
    def handle_input(self, key: int) -> str:
        """Обработка ввода в меню."""
        # Фильтруем недоступные пункты
        available_items = self._get_available_items()
        
        if key == pygame.K_UP:
            current_item = self.MENU_ITEMS[self.selected_index]
            if current_item in available_items:
                current_idx = available_items.index(current_item)
                new_idx = (current_idx - 1) % len(available_items)
                self.selected_index = self.MENU_ITEMS.index(available_items[new_idx])
            else:
                self.selected_index = self.MENU_ITEMS.index(available_items[0])
                
        elif key == pygame.K_DOWN:
            current_item = self.MENU_ITEMS[self.selected_index]
            if current_item in available_items:
                current_idx = available_items.index(current_item)
                new_idx = (current_idx + 1) % len(available_items)
                self.selected_index = self.MENU_ITEMS.index(available_items[new_idx])
            else:
                self.selected_index = self.MENU_ITEMS.index(available_items[0])
                
        elif key == pygame.K_z or key == pygame.K_RETURN:
            selected_item = self.MENU_ITEMS[self.selected_index]
            if selected_item in available_items:
                return selected_item
                
        elif key == pygame.K_ESCAPE or key == pygame.K_x:
            return MENU_ITEM_CONTINUE
        return None
    
    def _get_available_items(self) -> list:
        """Получение списка доступных пунктов."""
        items = [MENU_ITEM_CONTINUE]
        if self.has_save:
            items.append(MENU_ITEM_LOAD_SAVE)
        items.append(MENU_ITEM_FULLSCREEN)
        items.append(MENU_ITEM_QUIT)
        return items
    
    def set_fullscreen_state(self, is_fullscreen: bool):
        """Установка состояния полноэкранного режима."""
        self.is_fullscreen = is_fullscreen
    
    def draw(self, surface: pygame.Surface):
        """Отрисовка меню."""
        # Полупрозрачный фон
        overlay = pygame.Surface((self.screen_width, self.screen_height))
        overlay.fill(COLOR_BLACK)
        overlay.set_alpha(200)
        surface.blit(overlay, (0, 0))
        
        # Заголовок
        title_font = pygame.font.Font(None, 48)
        title = title_font.render("ПАУЗА", True, COLOR_WHITE)
        title_x = (self.screen_width - title.get_width()) // 2
        surface.blit(title, (title_x, 100))
        
        # Пункты меню
        item_font = pygame.font.Font(None, 32)
        available_items = self._get_available_items()
        menu_y = 180
        item_spacing = 50
        
        for i, item in enumerate(self.MENU_ITEMS):
            # Проверяем доступность
            is_available = item in available_items
            is_selected = (item == self.MENU_ITEMS[self.selected_index])
            
            # Модифицируем текст для полноэкранного режима
            display_text = item
            if item == MENU_ITEM_FULLSCREEN:
                status = "ВКЛ" if self.is_fullscreen else "ВЫКЛ"
                display_text = f"{item}: {status}"
            
            # Цвет
            if not is_available:
                color = (80, 80, 80)
            elif is_selected:
                color = COLOR_YELLOW
            else:
                color = COLOR_WHITE
            
            # Текст
            text = item_font.render(display_text, True, color)
            text_x = (self.screen_width - text.get_width()) // 2
            surface.blit(text, (text_x, menu_y + i * item_spacing))
            
            # Индикатор выбора (сердечко)
            if is_selected and is_available:
                heart_x = text_x - 25
                heart_y = menu_y + i * item_spacing + 5
                self._draw_heart(surface, heart_x, heart_y, COLOR_RED)
        
        # Подсказка
        hint_font = pygame.font.Font(None, 24)
        hint = hint_font.render("↑↓ - выбор, Z - подтвердить, ESC/X - закрыть", True, (150, 150, 150))
        hint_x = (self.screen_width - hint.get_width()) // 2
        surface.blit(hint, (hint_x, self.screen_height - 50))
    
    def _draw_heart(self, surface: pygame.Surface, x: int, y: int, color):
        """Отрисовка сердечка."""
        pygame.draw.circle(surface, color, (x + 5, y + 5), 5)
        pygame.draw.circle(surface, color, (x + 15, y + 5), 5)
        pygame.draw.polygon(surface, color, [(x, y + 7), (x + 10, y + 20), (x + 20, y + 7)])
    
    def reset(self):
        """Сброс меню."""
        self.selected_index = 0


class Battle:
    """
    Класс боя (Battle).
    Управляет рамкой боя, атаками, UI и проверкой столкновений.
    """
    
    def __init__(self, screen_width: int, screen_height: int):
        """
        Инициализация боя.
        
        Аргументы:
            screen_width: Ширина экрана
            screen_height: Высота экрана
        """
        self.screen_width = screen_width
        self.screen_height = screen_height
        
        # Рамка боя (по центру экрана)
        self.box_x = (screen_width - BATTLE_BOX_WIDTH) // 2
        self.box_y = (screen_height - BATTLE_BOX_HEIGHT) // 2 - 40
        self.box_rect = pygame.Rect(
            self.box_x, self.box_y,
            BATTLE_BOX_WIDTH, BATTLE_BOX_HEIGHT
        )
        
        # Группа спрайтов для снарядов
        self.bullets = pygame.sprite.Group()
        
        # Менеджер атак
        self.attack_manager = AttackManager(self.box_rect, self.bullets)
    
        # Боевой UI
        self.ui = BattleUI(screen_width, screen_height, self.box_y)
        
        # Текущий враг
        self.current_enemy = None
        
        # Режим боя ('menu' - меню, 'dodge' - уклонение, 'fight_attack' - атака игрока)
        self.battle_mode = 'menu'
        
        # Система мини-игры FIGHT
        self.fight_bar_active = False
        self.fight_bar_position = 0.0  # Позиция бегунка (0.0 - 1.0)
        self.fight_bar_direction = 1   # Направление движения (1 или -1)
        self.fight_bar_speed = 0.03    # Скорость бегунка
        
        # Флаг для показа сообщения о переходе во вторую фазу босса
        self.show_phase2_message = False
        self.phase2_message_timer = 0
    
        # Safety Pause - пауза перед атакой врага
        self.safety_pause_active = False
        self.safety_pause_timer = 0
        self.safety_pause_message = SAFETY_PAUSE_MESSAGE
    
        # Warmup - время для перемещения перед атакой
        self.warmup_active = False
        self.warmup_timer = 0
        self.warmup_message = WARMUP_MESSAGE
    
    def can_player_move(self) -> bool:
        """Проверка, может ли игрок двигаться в текущем режиме."""
        return self.battle_mode in ('dodge', 'warmup')
    
    def set_enemy(self, enemy: Enemy) -> None:
        """
        Установка текущего врага для боя.
        
        Аргументы:
            enemy: Объект врага
        """
        self.current_enemy = enemy
        # Обновляем UI в зависимости от врага
        self.ui.set_mercy_spare(enemy.is_sparable)
    
        # Сбрасываем флаги фаз босса
        self.show_phase2_message = False
        self.phase2_message_timer = 0
    
    def handle_input(self, key: int) -> str:
        """
        Обработка ввода в бою.
        
        Аргументы:
            key: Нажатая клавиша
            
        Возвращает:
            str: Результат действия или None
        """
        # Обработка мини-игры FIGHT
        if self.battle_mode == 'fight_attack':
            if key == pygame.K_z:
                return self._process_fight_attack()
            elif key == pygame.K_x:
                # Отмена атаки
                self.battle_mode = 'menu'
                self.fight_bar_active = False
                return 'fight_cancel'
            return None
        
        if self.battle_mode == 'menu':
            action = self.ui.handle_input(key)
            
            if action:
                return self._process_menu_action(action)
        
        return None
    
    def _process_menu_action(self, action) -> str:
        """
        Обработка действия из меню.
        
        Аргументы:
            action: Название действия или данные предмета (dict)
            
        Возвращает:
            str: Результат действия
        """
        if action is None:
            return None
        
        # Обработка выбора предмета (приходит как строка 'item:index')
        if isinstance(action, str) and action.startswith('item:'):
            return action
        
        if action == BUTTON_FIGHT:
            # Запуск мини-игры FIGHT
            self._start_fight_minigame()
            return None
        
        elif action == BUTTON_ACT:
            # Открытие подменю ACT
            self.ui.open_submenu(['Check', 'Talk'])
            return 'act_menu'
        
        elif action == 'Check':
            # Проверка врага
            return self._get_enemy_check_info()
        
        elif action == 'Talk':
            # Разговор с врагом - делает его пощадным
            if self.current_enemy:
                self.current_enemy.is_sparable = True
                self.ui.set_mercy_spare(True)
            return 'talk'
        
        elif action == BUTTON_MERCY:
            if self.current_enemy and self.current_enemy.is_sparable:
                return 'spare'  # Пощада - конец боя
            return 'mercy_fail'
        
        elif action == BUTTON_ITEM:
            # Открытие меню предметов
            return 'item_menu'
        
        # Обработка возврата из подменю
        elif action == 'back':
            return 'back'
        
        return None
    
    def _get_enemy_check_info(self) -> str:
        """Получение информации о враге для команды Check."""
        if not self.current_enemy:
            return 'check:???'
        
        enemy = self.current_enemy
        if enemy.is_boss:
            info = f"{enemy.name} - БОСС\nHP: {enemy.hp}/{enemy.max_hp}\nATK: {enemy.attack_damage}\nФаза: {enemy.phase}"
        else:
            info = f"{enemy.name}\nHP: {enemy.hp}/{enemy.max_hp}\nATK: {enemy.attack_damage}"
        
        return f'check:{info}'
    
    def _start_fight_minigame(self) -> None:
        """Запуск мини-игры для атаки FIGHT."""
        self.battle_mode = 'fight_attack'
        self.fight_bar_active = True
        self.fight_bar_position = 0.0
        self.fight_bar_direction = 1
    
    def update(self, player_x: float, player_y: float) -> None:
        """
        Обновление состояния боя.
        
        Аргументы:
            player_x: Позиция игрока X
            player_y: Позиция игрока Y
        """
        # Обновление таймера сообщения о фазе 2
        if self.phase2_message_timer > 0:
            self.phase2_message_timer -= 1
            if self.phase2_message_timer <= 0:
                self.show_phase2_message = False
        
        # Обновление Safety Pause
        if self.safety_pause_active:
            self.safety_pause_timer -= 1
            if self.safety_pause_timer <= 0:
                self.safety_pause_active = False
                self._start_warmup()  # Переходим к warmup
            return
        
        # Обновление Warmup (время для перемещения)
        if self.warmup_active:
            self.warmup_timer -= 1
            if self.warmup_timer <= 0:
                self.warmup_active = False
                self._start_enemy_attack_after_warmup()  # Запускаем атаку
            return
        
        # Обновление мини-игры FIGHT
        if self.battle_mode == 'fight_attack' and self.fight_bar_active:
            self.fight_bar_position += self.fight_bar_speed * self.fight_bar_direction
            
            # Отскок от краёв
            if self.fight_bar_position >= 1.0:
                self.fight_bar_position = 1.0
                self.fight_bar_direction = -1
            elif self.fight_bar_position <= 0.0:
                self.fight_bar_position = 0.0
                self.fight_bar_direction = 1
            return
        
        if self.battle_mode == 'dodge':
            # Обновление снарядов
            self.bullets.update()
            
            # Обновление менеджера атак
            round_active = self.attack_manager.update(player_x, player_y)
            
            # Проверка завершения раунда атак
            if not round_active:
                self._end_dodge_phase()
    
    def start_safety_pause(self) -> None:
        """Запуск паузы перед атакой врага."""
        self.safety_pause_active = True
        self.safety_pause_timer = SAFETY_PAUSE_DURATION
        self.battle_mode = 'safety_pause'
    
    def _start_warmup(self) -> None:
        """Запуск фазы разминки (игрок может двигаться)."""
        self.warmup_active = True
        self.warmup_timer = WARMUP_DURATION
        self.battle_mode = 'warmup'
    
    def _start_enemy_attack_after_warmup(self) -> None:
        """Запуск атаки врага после разминки."""
        if not self.current_enemy:
            self.battle_mode = 'menu'
            return
        
        if self.current_enemy.is_boss:
            if self.current_enemy.phase == 1:
                self.attack_manager.start_round_with_pattern_count(1)
            else:
                patterns_count = random.randint(2, 4)
                self.attack_manager.start_round_with_pattern_count(patterns_count)
                self.attack_manager.set_difficulty(1.3)
        else:
            self.attack_manager.start_round_with_pattern_count(MOB_PATTERNS_PER_ROUND)
        
        self.battle_mode = 'dodge'
    
    def _process_fight_attack(self) -> str:
        """
        Обработка атаки FIGHT после мини-игры.
        
        Возвращает:
            str: Результат атаки
        """
        if not self.current_enemy:
            self.battle_mode = 'menu'
            self.fight_bar_active = False
            return None
        
        # Расчёт урона на основе позиции бегунка
        # Центр (0.5) = максимальный урон, края = минимальный
        distance_from_center = abs(self.fight_bar_position - 0.5)
        
        # Максимальный урон в центре, минимум 50% урона по краям
        damage_multiplier = 1.0 - (distance_from_center * 0.8)
        damage = int(PLAYER_ATTACK_DAMAGE * damage_multiplier)
        
        # Наносим урон врагу
        enemy_dead = self.current_enemy.take_damage(damage)
        
        # Сбрасываем мини-игру
        self.battle_mode = 'menu'
        self.fight_bar_active = False
        
        # Проверяем, перешёл ли босс во вторую фазу
        if self.current_enemy.is_boss and self.current_enemy.phase == 2 and self.current_enemy.phase2_triggered:
            self.show_phase2_message = True
            self.phase2_message_timer = 120  # 2 секунды
            self.current_enemy.phase2_triggered = False  # Сбрасываем флаг
        
        if enemy_dead:
            return f'enemy_killed:{damage}'
        
        return f'fight_damage:{damage}'
    
    def _end_dodge_phase(self) -> None:
        """Завершение фазы уклонения."""
        self.battle_mode = 'menu'
        self.bullets.empty()
        self.attack_manager.reset()
    
    def start_enemy_attack_round(self) -> None:
        """Запуск раунда атак врага с учётом его типа и фазы."""
        if not self.current_enemy:
            return
        
        if self.current_enemy.is_boss:
            # Босс: количество атак зависит от фазы
            if self.current_enemy.phase == 1:
                # Фаза 1: 1 паттерн
                self.attack_manager.start_round_with_pattern_count(1)
            else:
                # Фаза 2: 2-4 паттерна случайно
                patterns_count = random.randint(2, 4)
                self.attack_manager.start_round_with_pattern_count(patterns_count)
                # Увеличиваем сложность во второй фазе
                self.attack_manager.set_difficulty(1.3)
        else:
            # Обычный моб: всегда 1 паттерн
            self.attack_manager.start_round_with_pattern_count(MOB_PATTERNS_PER_ROUND)
        
        self.battle_mode = 'dodge'
    
    def check_collisions(self, player_rect: pygame.Rect, player: Player) -> None:
        """
        Проверка столкновений игрока со снарядами и лазерами.
        
        Аргументы:
            player_rect: Прямоугольник коллизии игрока
            player: Объект игрока
        """
        if self.battle_mode != 'dodge':
            return
        
        if not self.current_enemy:
            return
        
        # Получаем урон врага
        enemy_damage = self.current_enemy.attack_damage
        
        # Проверка столкновений со снарядами
        for bullet in self.bullets:
            if bullet.rect.colliderect(player_rect):
                if player.take_damage(enemy_damage):
                    bullet.kill()
    
        # Проверка столкновений с лазерами
        if self.attack_manager.check_laser_collision(player_rect):
            player.take_damage(enemy_damage)
    
    def draw(self, surface: pygame.Surface, player: Player) -> None:
        """Отрисовка боя."""
        # Фон
        surface.fill(COLOR_BLACK)
        
        # HP бар врага (над рамкой боя)
        if self.current_enemy:
            self._draw_enemy_hp_bar(surface)
        
        # Имя врага
        if self.current_enemy:
            font = pygame.font.Font(None, 32)
            name_color = COLOR_YELLOW if self.current_enemy.is_boss else COLOR_WHITE
            name_text = font.render(self.current_enemy.name, True, name_color)
            surface.blit(name_text, (self.screen_width // 2 - name_text.get_width() // 2, 15))
            
            # Индикатор босса
            if self.current_enemy.is_boss:
                boss_font = pygame.font.Font(None, 20)
                phase_text = boss_font.render(f"Фаза {self.current_enemy.phase}", True, COLOR_YELLOW)
                surface.blit(phase_text, (self.screen_width // 2 - phase_text.get_width() // 2, 38))
        
        # Рамка боя
        pygame.draw.rect(surface, BOX_COLOR, self.box_rect, 3)
        
        # Мини-игра FIGHT
        if self.battle_mode == 'fight_attack' and self.fight_bar_active:
            self._draw_fight_minigame(surface)
        
        # Safety Pause - сообщение о подготовке врага
        if self.safety_pause_active:
            self._draw_safety_pause_message(surface)
        
        # Warmup - время для перемещения (игрок виден и может двигаться)
        if self.warmup_active:
            player.draw_battle(surface)
            self._draw_warmup_message(surface)
        
        # Снаряды и игрок (только в режиме уклонения)
        if self.battle_mode == 'dodge':
            self.bullets.draw(surface)
            # Отрисовка лазеров
            self.attack_manager.draw_lasers(surface)
            # Отрисовка гравитационных аномалий
            self.attack_manager.draw_gravity_wells(surface)
            player.draw_battle(surface)
        
            # Информация о текущем паттерне
            self._draw_pattern_info(surface)
        
        # HP бар игрока
        self._draw_hp_bar(surface, player)
        
        # Боевой UI (кнопки)
        self.ui.draw(surface)
        
        # Подсказки
        self._draw_hints(surface)
        
        # Сообщение о переходе во вторую фазу босса
        if self.show_phase2_message:
            self._draw_phase2_message(surface)
    
    def _draw_safety_pause_message(self, surface: pygame.Surface) -> None:
        """Отрисовка сообщения о подготовке врага к атаке."""
        font = pygame.font.Font(None, 32)
        
        text = font.render(self.safety_pause_message, True, (255, 255, 255))
        text_x = (self.screen_width - text.get_width()) // 2
        text_y = self.box_y + BATTLE_BOX_HEIGHT // 2 - 10
        
        # Фон для текста
        bg_rect = pygame.Rect(text_x - 20, text_y - 5, text.get_width() + 40, text.get_height() + 10)
        pygame.draw.rect(surface, COLOR_BLACK, bg_rect)
        pygame.draw.rect(surface, COLOR_YELLOW, bg_rect, 2)
        
        surface.blit(text, (text_x, text_y))
    
    def _draw_warmup_message(self, surface: pygame.Surface) -> None:
        """Отрисовка сообщения о разминке (можно двигаться)."""
        font = pygame.font.Font(None, 36)
        
        # Мигающий зелёный текст
        if pygame.time.get_ticks() % 500 < 250:
            text = font.render(self.warmup_message, True, (100, 255, 100))
        else:
            text = font.render(self.warmup_message, True, (200, 255, 200))
        
        text_x = (self.screen_width - text.get_width()) // 2
        text_y = self.box_y + BATTLE_BOX_HEIGHT // 2 - 10
        
        # Фон для текста
        bg_rect = pygame.Rect(text_x - 20, text_y - 5, text.get_width() + 40, text.get_height() + 10)
        pygame.draw.rect(surface, COLOR_BLACK, bg_rect)
        pygame.draw.rect(surface, (100, 255, 100), bg_rect, 2)
        
        surface.blit(text, (text_x, text_y))
    
        # Показываем таймер
        timer_font = pygame.font.Font(None, 24)
        seconds = (self.warmup_timer // 60) + 1
        timer_text = timer_font.render(f"Атака через: {seconds}с", True, (150, 255, 150))
        timer_x = (self.screen_width - timer_text.get_width()) // 2
        surface.blit(timer_text, (timer_x, text_y + 30))
    
    def _draw_enemy_hp_bar(self, surface: pygame.Surface) -> None:
        """Отрисовка полоски здоровья врага."""
        enemy = self.current_enemy
        if not enemy:
            return
        
        bar_width = 300
        bar_height = 15
        bar_x = (self.screen_width - bar_width) // 2
        bar_y = self.box_y - 25
        
        # Фон
        pygame.draw.rect(surface, (40, 40, 40), (bar_x, bar_y, bar_width, bar_height))
        
        # Текущее HP
        hp_percent = enemy.get_hp_percent()
        hp_width = int(bar_width * hp_percent)
        
        # Цвет зависит от типа врага и HP
        if enemy.is_boss:
            if hp_percent > 0.5:
                hp_color = (255, 100, 0)  # Оранжевый для босса фаза 1
            else:
                hp_color = (255, 0, 100)  # Красно-розовый для босса фаза 2
        else:
            hp_color = (100, 255, 100)  # Зелёный для обычных мобов
        
        pygame.draw.rect(surface, hp_color, (bar_x, bar_y, hp_width, bar_height))
        
        # Рамка
        pygame.draw.rect(surface, COLOR_WHITE, (bar_x, bar_y, bar_width, bar_height), 2)
        
        # Текст HP
        font = pygame.font.Font(None, 18)
        hp_text = font.render(f"{enemy.hp}/{enemy.max_hp}", True, COLOR_WHITE)
        text_x = bar_x + (bar_width - hp_text.get_width()) // 2
        surface.blit(hp_text, (text_x, bar_y - 2))
    
    def _draw_fight_minigame(self, surface: pygame.Surface) -> None:
        """Отрисовка мини-игры для атаки FIGHT."""
        bar_width = 250
        bar_height = 30
        bar_x = (self.screen_width - bar_width) // 2
        bar_y = self.box_y + BATTLE_BOX_HEIGHT // 2 - bar_height // 2
        
        # Фон полосы
        pygame.draw.rect(surface, (30, 30, 30), (bar_x, bar_y, bar_width, bar_height))
        
        # Зона максимального урона (центр)
        zone_width = 40
        zone_x = bar_x + (bar_width - zone_width) // 2
        pygame.draw.rect(surface, (100, 100, 100), (zone_x, bar_y, zone_width, bar_height))
        
        # Бегунок
        runner_x = bar_x + int(self.fight_bar_position * (bar_width - 10))
        pygame.draw.rect(surface, COLOR_YELLOW, (runner_x, bar_y - 5, 10, bar_height + 10))
        
        # Рамка
        pygame.draw.rect(surface, COLOR_WHITE, (bar_x, bar_y, bar_width, bar_height), 2)
        
        # Текст подсказки
        font = pygame.font.Font(None, 24)
        hint = font.render("Z - атаковать!  X - отмена", True, COLOR_WHITE)
        surface.blit(hint, (bar_x + (bar_width - hint.get_width()) // 2, bar_y + bar_height + 10))
    
    def _draw_phase2_message(self, surface: pygame.Surface) -> None:
        """Отрисовка сообщения о переходе босса во вторую фазу."""
        font = pygame.font.Font(None, 36)
        
        # Мигающий текст
        if pygame.time.get_ticks() % 500 < 250:
            text = font.render("БОСС В ЯРОСТИ!", True, COLOR_RED)
        else:
            text = font.render("БОСС В ЯРОСТИ!", True, COLOR_YELLOW)
        
        text_x = (self.screen_width - text.get_width()) // 2
        text_y = self.box_y + BATTLE_BOX_HEIGHT // 2 - 50
        
        # Фон для текста
        bg_rect = pygame.Rect(text_x - 20, text_y - 5, text.get_width() + 40, text.get_height() + 10)
        pygame.draw.rect(surface, COLOR_BLACK, bg_rect)
        pygame.draw.rect(surface, COLOR_RED, bg_rect, 2)
        
        surface.blit(text, (text_x, text_y))
    
    def _draw_hp_bar(self, surface: pygame.Surface, player: Player) -> None:
        """Отрисовка полоски здоровья игрока."""
        bar_x, bar_y = 20, self.screen_height - 80
        bar_width, bar_height = 200, 20
        
        # Фон
        pygame.draw.rect(surface, (50, 50, 50), (bar_x, bar_y, bar_width, bar_height))
        
        # Текущее HP
        hp_width = int(bar_width * (player.hp / player.max_hp))
        hp_color = COLOR_YELLOW if player.hp > 30 else COLOR_RED
        pygame.draw.rect(surface, hp_color, (bar_x, bar_y, hp_width, bar_height))
        
        # Рамка
        pygame.draw.rect(surface, COLOR_WHITE, (bar_x, bar_y, bar_width, bar_height), 2)
        
        # Текст
        font = pygame.font.Font(None, 24)
        hp_text = font.render(f"HP: {player.hp}/{player.max_hp}", True, COLOR_WHITE)
        surface.blit(hp_text, (bar_x + bar_width + 10, bar_y + 2))
    
    def _draw_hints(self, surface: pygame.Surface) -> None:
        """Отрисовка подсказок."""
        font = pygame.font.Font(None, 24)
        
        if self.battle_mode == 'menu':
            if self.ui.is_submenu_active():
                hint = font.render("Z - выбрать, X - назад", True, (150, 150, 150))
            else:
                hint = font.render("←→ - выбор, Z - подтвердить", True, (150, 150, 150))
        elif self.battle_mode == 'fight_attack':
            hint = font.render("Z - атаковать в нужный момент!", True, COLOR_YELLOW)
        elif self.battle_mode == 'warmup':
            hint = font.render("Займите позицию! Используйте стрелки для движения", True, (100, 255, 100))
        else:
            hint = font.render("Уклоняйся от атак!", True, (150, 150, 150))
        
        surface.blit(hint, (10, self.screen_height - 25))
    
    def _draw_pattern_info(self, surface: pygame.Surface) -> None:
        """Отрисовка информации о текущем паттерне атаки."""
        font = pygame.font.Font(None, 20)
        
        # Название текущего паттерна
        pattern_name = self.attack_manager.get_current_pattern_name()
        remaining = self.attack_manager.get_remaining_attacks()
        
        # Текст
        info_text = f"Паттерн: {pattern_name}"
        remaining_text = f"Осталось атак: {remaining}"
        
        # Отрисовка
        text1 = font.render(info_text, True, COLOR_YELLOW)
        text2 = font.render(remaining_text, True, (150, 150, 150))
        
        surface.blit(text1, (self.box_x, self.box_y - 20))
        surface.blit(text2, (self.box_x + self.box_rect.width - text2.get_width(), self.box_y - 20))
    
    def reset(self) -> None:
        """Сброс состояния боя."""
        self.bullets.empty()
        self.attack_manager.reset()
        self.battle_mode = 'menu'
        self.ui.close_submenu()
        self.fight_bar_active = False
        self.show_phase2_message = False
        self.phase2_message_timer = 0
        self.safety_pause_active = False
        self.safety_pause_timer = 0
        self.warmup_active = False
        self.warmup_timer = 0
    
    def get_box_rect(self) -> pygame.Rect:
        """Получение прямоугольника рамки боя."""
        return self.box_rect

    def open_item_menu(self, inventory: list) -> None:
        """
        Открытие меню предметов.
        
        Аргументы:
            inventory: Список предметов игрока
        """
        self.ui.open_item_menu(inventory)
    
    def get_selected_item_index(self) -> int:
        """Получение индекса выбранного предмета."""
        return self.ui.get_selected_item_index()


class GameManager:
    """
    Менеджер состояний игры.
    Управляет переключением между режимами MAIN_MENU, OVERWORLD, BATTLE, MENU и GAME_OVER.
    """
    
    def __init__(self, screen_width: int = SCREEN_WIDTH, 
                 screen_height: int = SCREEN_HEIGHT):
        """
        Инициализация менеджера игры.
        
        Аргументы:
            screen_width: Ширина экрана
            screen_height: Высота экрана
        """
        self.screen_width = screen_width
        self.screen_height = screen_height
        
        # Текущее состояние - начинаем с главного меню
        self.state = STATE_MAIN_MENU
        
        # Предыдущее состояние (для возврата из меню)
        self.previous_state = None
        
        # Инициализация компонентов
        self.map_manager = MapManager()
        self.battle = Battle(screen_width, screen_height)
        
        # Главное меню
        self.main_menu = MainMenu(screen_width, screen_height)
        
        # Меню паузы
        self.pause_menu = PauseMenu(screen_width, screen_height)
        
        # Менеджер дисплея (устанавливается из main.py)
        self.display_manager = None
        
        # Аудио менеджер
        self.audio_manager = AudioManager()
        
        # Менеджер сохранений
        self.save_manager = SaveManager()
        
        # Игрок (начальная позиция в безопасном месте)
        self.player = Player(3 * TILE_SIZE, 3 * TILE_SIZE)
        
        # Предметы на карте
        self.pickup_items = []
        
        # Сообщение для отображения
        self.message = None
        self.message_timer = 0
        
        # Флаг: игра инициализирована
        self.game_initialized = False
        
        # Проверяем наличие сохранения для меню
        self.main_menu.check_save(self.save_manager)
        self.pause_menu.check_save(self.save_manager)
        
    def set_display_manager(self, display_manager):
        """Установка менеджера дисплея."""
        self.display_manager = display_manager

    def _create_pickup_items(self) -> None:
        """Создание предметов на карте в доступных местах."""
        # Получаем стены, врагов и переходы с текущей карты
        walls = self.map_manager.get_walls()
        enemies = self.map_manager.enemies
        transitions = self.map_manager.transitions
        
        # Размеры карты в тайлах
        map_width = 25  # тайлов
        map_height = 15  # тайлов
        
        # Функция проверки, свободна ли позиция
        def is_position_free(tile_x: int, tile_y: int) -> bool:
            item_rect = pygame.Rect(
                tile_x * TILE_SIZE,
                tile_y * TILE_SIZE,
                TILE_SIZE,
                TILE_SIZE
            )
            
            # Проверка столкновения со стенами
            for wall in walls:
                if item_rect.colliderect(wall):
                    return False
            
            # Проверка столкновения с врагами
            for enemy in enemies:
                if item_rect.colliderect(enemy.get_rect()):
                    return False
            
            # Проверка столкновения с переходами
            for trans_rect, _, _ in transitions:
                if item_rect.colliderect(trans_rect):
                    return False
            
            return True
        
        # Список предметов для размещения с предпочтительными позициями
        items_to_place = [
            ('healing_candy', 5, 2),
            ('bandage', 12, 5),
            ('healing_pie', 8, 6)
        ]
        
        # Размещаем предметы только в свободных местах
        for item_type, default_x, default_y in items_to_place:
            placed = False
            
            # Сначала проверяем дефолтную позицию
            if is_position_free(default_x, default_y):
                self.pickup_items.append(
                    PickupItem(default_x * TILE_SIZE, default_y * TILE_SIZE, item_type)
                )
                placed = True
            
            # Если дефолтная позиция занята, ищем свободное место
            if not placed:
                for y in range(1, map_height - 1):
                    for x in range(1, map_width - 1):
                        if is_position_free(x, y):
                            self.pickup_items.append(
                                PickupItem(x * TILE_SIZE, y * TILE_SIZE, item_type)
                            )
                            placed = True
                            break
                    if placed:
                        break
    
    def handle_event(self, event: pygame.event.Event) -> None:
        """
        Обработка событий.
        
        Аргументы:
            event: Событие Pygame
        """
        if event.type == pygame.KEYDOWN:
            # Обработка главного меню
            if self.state == STATE_MAIN_MENU:
                result = self.main_menu.handle_input(event.key)
                if result:
                    self._process_main_menu_result(result)
                return
            
            # Обработка состояния GAME_OVER
            if self.state == STATE_GAME_OVER:
                if event.key == pygame.K_r:
                    self.restart_game()  # Загрузка сохранения или начало заново
                elif event.key == pygame.K_n:
                    self._restart_from_beginning()  # Начать заново
                elif event.key == pygame.K_ESCAPE:
                    pygame.event.post(pygame.event.Event(pygame.QUIT))
                return

            # Обработка состояния MENU
            if self.state == STATE_MENU:
                result = self.pause_menu.handle_input(event.key)
                if result:
                    self._process_menu_result(result)
                return
        
            # Открытие меню паузы по ESC
            if event.key == pygame.K_ESCAPE:
                if self.state in (STATE_OVERWORLD, STATE_BATTLE):
                    self.switch_to_menu()
                return

            if self.state == STATE_BATTLE:
                # Если показывается сообщение, закрываем его по нажатию Z или X
                if self.message and self.message_timer > 0:
                    if event.key == pygame.K_z or event.key == pygame.K_x:
                        self.message = None
                        self.message_timer = 0
                    return
                
                # Обычная обработка ввода в бою
                result = self.battle.handle_input(event.key)
                if result:
                    self._process_battle_result(result)
    
    def _process_main_menu_result(self, result: str) -> None:
        """Обработка результата выбора в главном меню."""
        if result == TITLE_MENU_NEW_GAME:
            self._start_new_game()
        elif result == TITLE_MENU_CONTINUE:
            self._load_game_from_menu()
        elif result == TITLE_MENU_QUIT:
            pygame.event.post(pygame.event.Event(pygame.QUIT))
    
    def _start_new_game(self) -> None:
        """Начало новой игры."""
        # Инициализация игры
        self._initialize_game()
        
        # Переключение в режим мира
        self.state = STATE_OVERWORLD
        
        # Запуск музыки локации
        self.audio_manager.play_location_music(self.map_manager.get_location_id())
        
    def _load_game_from_menu(self) -> None:
        """Загрузка игры из главного меню."""
        if self.save_manager.has_saved_game():
            self._initialize_game()
            self._load_game()
        else:
            # Если сохранения нет, начинаем новую игру
            self._start_new_game()
    
    def _initialize_game(self) -> None:
        """Инициализация игровых компонентов."""
        if self.game_initialized:
            return
        
        # Создаём предметы на карте
        self._create_pickup_items()
        
        # Устанавливаем флаг
        self.game_initialized = True
    
    def _process_battle_result(self, result: str) -> None:
        """
        Обработка результата действия в бою.
        
        Аргументы:
            result: Строка результата
        """
        if result is None:
            return
        
        if result == 'spare':
            # Пощада - конец боя
            if self.battle.current_enemy:
                self.map_manager.remove_enemy(self.battle.current_enemy)
            # Сначала очищаем всё, потом переключаемся
            self.message = None
            self.message_timer = 0
            self.switch_to_overworld()
            return
        
        elif result == 'talk':
            self.show_message("Вы поговорили с врагом.\nТеперь его можно пощадить (MERCY)!")
        
        elif result == 'fight_cancel':
            # Отмена атаки FIGHT
            pass
        
        elif result and result.startswith('fight_damage:'):
            # Нанесение урона врагу
            try:
                damage = int(result.split(':', 1)[1])
                enemy = self.battle.current_enemy
                if enemy:
                    enemy_name = enemy.name
                    self.show_message(f"Вы нанесли {damage} урона!\n{enemy_name}: {enemy.hp}/{enemy.max_hp} HP")
                    # Запускаем safety pause перед атакой врага
                    self.battle.start_safety_pause()
            except ValueError:
                self.show_message("Атака!")
        
        elif result and result.startswith('enemy_killed:'):
            # Враг побеждён
            try:
                damage = int(result.split(':', 1)[1])
                enemy = self.battle.current_enemy
                if enemy:
                    enemy_name = enemy.name
                    self.show_message(f"Вы нанесли {damage} урона!\n{enemy_name} побеждён!", 90)
                    # Удаляем врага и возвращаемся в мир
                    self.map_manager.remove_enemy(enemy)
                    # Задержка перед возвратом в мир
                    self._victory_timer = 60
            except ValueError:
                self._handle_enemy_victory()
        
        elif result and result.startswith('check:'):
            info = result.split(':', 1)[1]
            self.show_message(f"* {info}")
        
        elif result == 'item_menu':
            # Открытие меню предметов
            if self.player.has_items():
                self.battle.open_item_menu(self.player.get_inventory_items())
            else:
                self.show_message("У вас нет предметов!")
        
        elif result and result.startswith('item:'):
            # Использование предмета по индексу
            try:
                index = int(result.split(':', 1)[1])
                used_item = self.player.use_item(index)
                if used_item:
                    item_name = used_item.get('name', '???')
                    heal_value = used_item.get('heal_value', 0)
                    self.show_message(f"Вы использовали {item_name}.\nВосстановлено {heal_value} HP!")
                    # Запускаем safety pause перед атакой врага
                    self.battle.start_safety_pause()
            except (ValueError, IndexError):
                self.show_message("Ошибка использования предмета!")
        
        elif result == 'back':
            # Возврат из подменю - ничего не делаем
            pass
        
        elif result == 'mercy_fail':
            self.show_message("Враг не хочет уходить.\nПопробуйте поговорить с ним (ACT -> Talk)")
    
    def _handle_enemy_victory(self) -> None:
        """Обработка победы над врагом."""
        if self.battle.current_enemy:
            self.map_manager.remove_enemy(self.battle.current_enemy)
        self.message = None
        self.message_timer = 0
        self.switch_to_overworld()
    
    def _process_menu_result(self, result: str) -> None:
        """Обработка результата выбора в меню паузы."""
        if result == MENU_ITEM_CONTINUE:
            self.close_menu()
        
        elif result == MENU_ITEM_LOAD_SAVE:
            if self.save_manager.has_saved_game():
                self._load_game()
                self.close_menu()
            else:
                # Если сохранения нет, просто закрываем меню
                self.close_menu()
        
        elif result == MENU_ITEM_FULLSCREEN:
            if self.display_manager:
                self.display_manager.toggle_fullscreen()
                self.pause_menu.set_fullscreen_state(self.display_manager.is_fullscreen)
        
        elif result == MENU_ITEM_QUIT:
            pygame.event.post(pygame.event.Event(pygame.QUIT))
    
    def show_message(self, text: str, duration: int = 120) -> None:
        """
        Показать сообщение на экране.
        
        Аргументы:
            text: Текст сообщения
            duration: Длительность в кадрах
        """
        self.message = text
        self.message_timer = duration
    
    def update(self, keys: pygame.key.ScancodeWrapper) -> None:
        """
        Обновление игры.
        
        Аргументы:
            keys: Состояние клавиш клавиатуры
        """
        # Обновление таймера сообщения
        if self.message_timer > 0:
            self.message_timer -= 1
            if self.message_timer == 0:
                self.message = None
        
        if self.state == STATE_MAIN_MENU:
            self.main_menu.update()
        elif self.state == STATE_OVERWORLD:
            self._update_overworld(keys)
        elif self.state == STATE_BATTLE:
            self._update_battle(keys)
        # GAME_OVER и MENU не требуют обновления
    
    def _update_overworld(self, keys: pygame.key.ScancodeWrapper) -> None:
        """Обновление в режиме мира."""
        # Перемещение игрока
        self.player.handle_overworld_input(keys, self.map_manager.get_walls())
        
        # Обновление предметов
        for item in self.pickup_items:
            item.update()
        
        # Обновление точек сохранения (анимация)
        self.map_manager.update_save_points()
        
        # Проверка столкновения с предметами (Z для подбора)
        player_rect = self.player.get_overworld_rect()
        for item in self.pickup_items:
            if item.check_collision(player_rect):
                # Проверяем нажатие Z
                if keys[pygame.K_z]:
                    item_data = item.collect()
                    if item_data:
                        self.player.add_item(item_data)
                        self.show_message(f"Вы подобрали {item_data['name']}!")
        
        # Проверка столкновения с точкой сохранения
        save_point = self.map_manager.check_save_point_collision(player_rect)
        if save_point and keys[pygame.K_z]:
            if save_point.can_interact():
                self._interact_with_save_point(save_point)
        
        # Проверка перехода на другую карту
        transition = self.map_manager.check_transition(self.player.get_overworld_rect())
        if transition:
            new_map, new_x, new_y = transition
            new_pos = self.map_manager.load_map(new_map, new_x, new_y)
            if new_pos:
                self.player.set_overworld_position(new_pos[0], new_pos[1])
                # Смена музыки локации
                self.audio_manager.play_location_music(self.map_manager.get_location_id())
        
        # Проверка столкновения с врагом
        enemy = self.map_manager.check_enemy_collision(self.player.get_overworld_rect())
        if enemy:
            self.switch_to_battle(enemy)
    
    def _interact_with_save_point(self, save_point: SavePoint) -> None:
        """
        Взаимодействие с точкой сохранения.
        
        Аргументы:
            save_point: Объект точки сохранения
        """
        # Восстанавливаем HP игрока
        self.player.hp = self.player.max_hp
        
        # Выполняем взаимодействие
        result = save_point.interact()
        
        if result:
            # Сохраняем игру
            self._save_game()
            
            # Показываем сообщение
            self.show_message(result['message'])
    
    def _update_battle(self, keys: pygame.key.ScancodeWrapper) -> None:
        """Обновление в режиме боя."""
        # Обновление неуязвимости
        self.player.update_invulnerability()
        
        # Проверка таймера победы
        if hasattr(self, '_victory_timer') and self._victory_timer > 0:
            self._victory_timer -= 1
            if self._victory_timer <= 0:
                self._handle_enemy_victory()
                return
        
        # Перемещение игрока в бою (в режиме уклонения или разминки)
        if self.battle.can_player_move():
            self.player.handle_battle_input(keys)
        
            # Применение гравитационной силы от аномалий (только в dodge)
            if self.battle.battle_mode == 'dodge' and self.battle.attack_manager.is_gravity_mode():
                player_x, player_y = self.player.get_battle_position()
                force_x, force_y = self.battle.attack_manager.get_gravity_force(player_x, player_y)
                self.player.apply_gravity_force(force_x, force_y)
        
        # Обновление боя
        player_x, player_y = self.player.get_battle_position()
        self.battle.update(player_x, player_y)
        
        # Проверка столкновений (только в режиме dodge)
        if self.battle.battle_mode == 'dodge':
            self.battle.check_collisions(self.player.get_battle_rect(), self.player)
    
        # Проверка смерти игрока
        if not self.player.is_alive():
            self.switch_to_game_over()
    
    def draw(self, surface: pygame.Surface) -> None:
        """Отрисовка игры."""
        if self.state == STATE_MAIN_MENU:
            self.main_menu.draw(surface)
        elif self.state == STATE_OVERWORLD:
            self._draw_overworld(surface)
        elif self.state == STATE_BATTLE:
            self._draw_battle(surface)
        elif self.state == STATE_GAME_OVER:
            self._draw_game_over(surface)
        elif self.state == STATE_MENU:
            # Отрисовка предыдущего состояния как фона
            if self.previous_state == STATE_OVERWORLD:
                self._draw_overworld(surface)
            elif self.previous_state == STATE_BATTLE:
                self._draw_battle(surface)
            # Отрисовка меню поверх
            self.pause_menu.draw(surface)
        
        # Отрисовка сообщения (не в game over, menu и main menu)
        if self.message and self.state not in (STATE_GAME_OVER, STATE_MENU, STATE_MAIN_MENU):
            self._draw_message(surface)
    
    def _draw_overworld(self, surface: pygame.Surface) -> None:
        """Отрисовка в режиме мира."""
        self.map_manager.draw(surface)
        
        # Отрисовка предметов
        for item in self.pickup_items:
            item.draw(surface)
        
        # Отрисовка точек сохранения
        self.map_manager.draw_save_points(surface)
        
        self.player.draw_overworld(surface)
        
        # Подсказка
        font = pygame.font.Font(None, 24)
        hint = font.render("Зелёные - переходы, синие - враги, золото - сохранение, Z - взаимодействовать, ESC - меню", True, (150, 150, 150))
        surface.blit(hint, (10, self.screen_height - 30))
    
    def _draw_battle(self, surface: pygame.Surface) -> None:
        """Отрисовка в режиме боя."""
        self.battle.draw(surface, self.player)
    
    def _draw_message(self, surface: pygame.Surface) -> None:
        """Отрисовка сообщения."""
        font = pygame.font.Font(None, 24)
        
        # Фон для сообщения
        lines = self.message.split('\n')
        max_width = max(font.size(line)[0] for line in lines)
        height = len(lines) * 25 + 20
        
        msg_x = (self.screen_width - max_width - 40) // 2
        msg_y = self.screen_height - 160
        
        # Рамка сообщения
        msg_rect = pygame.Rect(msg_x, msg_y, max_width + 40, height)
        pygame.draw.rect(surface, COLOR_BLACK, msg_rect)
        pygame.draw.rect(surface, COLOR_WHITE, msg_rect, 2)
        
        # Текст
        for i, line in enumerate(lines):
            text = font.render(line, True, COLOR_WHITE)
            surface.blit(text, (msg_x + 20, msg_y + 10 + i * 25))
    
    def switch_to_battle(self, enemy: Enemy) -> None:
        """
        Переключение в режим боя.
        
        Аргументы:
            enemy: Враг, с которым начинается бой
        """
        self.state = STATE_BATTLE
        
        # Установка рамки боя для игрока
        self.player.set_battle_box(self.battle.get_box_rect())
        
        # Установка врага
        self.battle.set_enemy(enemy)
        
        # Сброс состояния
        self.battle.reset()
        self.player.reset_battle_state()

        # Запуск боевой музыки
        self.audio_manager.play_battle_music(is_boss=enemy.is_boss)

    def switch_to_overworld(self) -> None:
        """Переключение в режим мира."""
        self.state = STATE_OVERWORLD
        # Очищаем сообщение
        self.message = None
        self.message_timer = 0
        # Сбрасываем состояние боя
        self.battle.reset()

        # Возвращаем музыку локации
        self.audio_manager.resume_location_music()

    def switch_to_game_over(self) -> None:
        """Переключение в режим Game Over."""
        self.state = STATE_GAME_OVER
        # Очищаем сообщение
        self.message = None
        self.message_timer = 0
    
        # Запуск музыки Game Over
        self.audio_manager.play_game_over_music()
    
    def switch_to_menu(self) -> None:
        """Переключение в меню паузы."""
        self.previous_state = self.state
        self.state = STATE_MENU
        self.pause_menu.reset()
        
        # Обновляем состояние полноэкранного режима
        if self.display_manager:
            self.pause_menu.set_fullscreen_state(self.display_manager.is_fullscreen)
    
    def close_menu(self) -> None:
        """Закрытие меню и возврат к предыдущему состоянию."""
        if self.previous_state:
            self.state = self.previous_state
        else:
            self.state = STATE_OVERWORLD
        self.previous_state = None
    
    def _draw_game_over(self, surface: pygame.Surface) -> None:
        """Отрисовка экрана Game Over."""
        # Чёрный фон
        surface.fill(COLOR_BLACK)
        
        # Большой шрифт для заголовка
        title_font = pygame.font.Font(None, 72)
        small_font = pygame.font.Font(None, 32)
        
        # Заголовок GAME OVER
        title = title_font.render("GAME OVER", True, COLOR_RED)
        title_x = (self.screen_width - title.get_width()) // 2
        title_y = self.screen_height // 2 - 80
        surface.blit(title, (title_x, title_y))
        
        # Подсказки
        if self.save_manager.has_saved_game():
            hint1 = small_font.render("Нажмите R - загрузить последнее сохранение", True, COLOR_WHITE)
            hint2 = small_font.render("Нажмите N - начать заново", True, (150, 150, 150))
        else:
            hint1 = small_font.render("Нажмите R для перезапуска", True, COLOR_WHITE)
            hint2 = small_font.render("Сохранение не найдено", True, (150, 150, 150))
        
        hint3 = small_font.render("Нажмите ESC для выхода", True, (150, 150, 150))
        
        hint1_x = (self.screen_width - hint1.get_width()) // 2
        hint2_x = (self.screen_width - hint2.get_width()) // 2
        hint3_x = (self.screen_width - hint3.get_width()) // 2
        
        surface.blit(hint1, (hint1_x, self.screen_height // 2 + 10))
        surface.blit(hint2, (hint2_x, self.screen_height // 2 + 45))
        surface.blit(hint3, (hint3_x, self.screen_height // 2 + 80))
    
    def restart_game(self) -> None:
        """Перезапуск игры после Game Over (загрузка последнего сохранения)."""
        # Проверяем наличие сохранения
        if self.save_manager.has_saved_game():
            self._load_game()
        else:
            # Если сохранения нет, начинаем сначала
            self._restart_from_beginning()
    
    def _restart_from_beginning(self) -> None:
        """Перезапуск игры с самого начала."""
        # Полный сброс игрока
        self.player.reset_for_restart()
        
        # Сброс предметов на карте
        self.pickup_items = []
        self._create_pickup_items()
        
        # Перезагрузка карты
        self.map_manager.load_map('start', 3, 3)
        self.player.set_overworld_position(3 * TILE_SIZE, 3 * TILE_SIZE)
        
        # Сброс состояния боя
        self.battle.reset()
        
        # Возврат в режим мира
        self.state = STATE_OVERWORLD
        self.message = None
        self.message_timer = 0

        # Запуск музыки начальной локации
        self.audio_manager.play_location_music(1)
    
    def _return_to_main_menu(self) -> None:
        """Возврат в главное меню."""
        self.state = STATE_MAIN_MENU
        self.message = None
        self.message_timer = 0
        self.battle.reset()
        self.main_menu.reset()
        self.main_menu.check_save(self.save_manager)
        
    def _save_game(self) -> bool:
        """
        Сохранение игры.
        
        Возвращает:
            bool: True если сохранение успешно
        """
        # Получаем позицию игрока в тайлах
        player_x = self.player.overworld_x // TILE_SIZE
        player_y = self.player.overworld_y // TILE_SIZE
        
        return self.save_manager.save_game(
            location_id=self.map_manager.get_location_id(),
            player_x=player_x,
            player_y=player_y,
            player_hp=self.player.hp,
            player_max_hp=self.player.max_hp,
            inventory=self.player.get_inventory_items(),
            defeated_enemies=[],  # TODO: добавить список побеждённых врагов
            current_map=self.map_manager.current_map_name
        )
    
    def _load_game(self) -> bool:
        """
        Загрузка игры из сохранения.
        
        Возвращает:
            bool: True если загрузка успешна
        """
        save_data = self.save_manager.load_game()
        
        if save_data is None:
            self._restart_from_beginning()
            return False
        
        # Инициализируем игру, если ещё не сделано
        if not self.game_initialized:
            self._initialize_game()
        
        # Загружаем карту
        self.map_manager.load_map(save_data.current_map)
        
        # Устанавливаем позицию игрока
        self.player.set_overworld_position(
            save_data.player_x * TILE_SIZE,
            save_data.player_y * TILE_SIZE
        )
        
        # Восстанавливаем HP
        self.player.hp = save_data.player_hp
        self.player.max_hp = save_data.player_max_hp
        
        # Восстанавливаем инвентарь
        self.player.inventory = []
        for item_data in save_data.inventory:
            self.player.add_item(item_data)
        
        # Сбрасываем состояние боя
        self.battle.reset()
        
        # Возврат в режим мира
        self.state = STATE_OVERWORLD
        self.message = None
        self.message_timer = 0
        
        # Запуск музыки локации
        self.audio_manager.play_location_music(self.map_manager.get_location_id())
        
        # Показываем сообщение о загрузке
        self.show_message("Игра загружена!")
        
        return True
