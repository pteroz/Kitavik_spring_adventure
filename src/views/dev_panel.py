"""Панель разработчика для настройки параметров игры."""

import arcade
import arcade.gui


class DevPanel:
    """GUI панель для настройки параметров в режиме разработки."""

    def __init__(self, game_view):
        self.game_view = game_view
        self.manager = arcade.gui.UIManager()
        
        # Импортируем текущие значения из констант
        from src.constants import (
            GRAVITY,
            PLAYER_MOVE_FORCE_SLOW,
            PLAYER_MOVE_FORCE_NORMAL,
            PLAYER_MOVE_FORCE_RUN,
            PLAYER_JUMP_IMPULSE,
            PLAYER_JUMP_IMPULSE_WALK,
            PLAYER_JUMP_IMPULSE_RUN,
            MOVE_SLOW_THRESHOLD,
            DOUBLE_TAP_THRESHOLD,
        )
        
        # Текущие значения параметров
        self.gravity = GRAVITY
        self.force_tap = PLAYER_MOVE_FORCE_SLOW
        self.force_walk = PLAYER_MOVE_FORCE_NORMAL
        self.force_run = PLAYER_MOVE_FORCE_RUN
        self.jump_stand = PLAYER_JUMP_IMPULSE
        self.jump_walk = PLAYER_JUMP_IMPULSE_WALK
        self.jump_run = PLAYER_JUMP_IMPULSE_RUN
        self.tap_threshold = MOVE_SLOW_THRESHOLD * 1000  # в мс
        self.doubletap_threshold = DOUBLE_TAP_THRESHOLD * 1000  # в мс
        
        self._setup_ui()

    def _setup_ui(self):
        """Создание UI элементов."""
        # Вертикальный контейнер
        v_box = arcade.gui.UIBoxLayout(vertical=True, space_between=3)
        
        # Заголовок
        title = arcade.gui.UILabel(
            text="PYMUNK DEV PANEL",
            font_size=14,
            bold=True,
            text_color=arcade.color.YELLOW,
        )
        v_box.add(title)
        
        # === ГРАВИТАЦИЯ ===
        v_box.add(arcade.gui.UILabel(text="=== GRAVITY ===", font_size=11, bold=True))
        self.gravity_label = arcade.gui.UILabel(
            text=f"Gravity: {self.gravity:.0f}",
            font_size=10,
        )
        v_box.add(self.gravity_label)
        
        
        # === PYMUNK ПАРАМЕТРЫ ===
        v_box.add(arcade.gui.UILabel(text="", font_size=8))  # Разделитель
        v_box.add(arcade.gui.UILabel(text="=== PYMUNK PARAMS ===", font_size=11, bold=True, text_color=arcade.color.CYAN))
        
        # Силы движения
        v_box.add(arcade.gui.UILabel(text=f"Force Tap: {self.force_tap:.0f}", font_size=9))
        v_box.add(arcade.gui.UILabel(text=f"Force Walk: {self.force_walk:.0f}", font_size=9))
        v_box.add(arcade.gui.UILabel(text=f"Force Run: {self.force_run:.0f}", font_size=9))
        
        # Импульсы прыжка
        v_box.add(arcade.gui.UILabel(text="", font_size=4))  # Разделитель
        v_box.add(arcade.gui.UILabel(text=f"Jump Stand: {self.jump_stand:.0f}", font_size=9))
        v_box.add(arcade.gui.UILabel(text=f"Jump Walk: {self.jump_walk:.0f}", font_size=9))
        v_box.add(arcade.gui.UILabel(text=f"Jump Run: {self.jump_run:.0f}", font_size=9))
        
        # Таймеры
        v_box.add(arcade.gui.UILabel(text="", font_size=4))  # Разделитель
        v_box.add(arcade.gui.UILabel(text=f"Tap Threshold: {self.tap_threshold:.0f}ms", font_size=9))
        v_box.add(arcade.gui.UILabel(text=f"DoubleTap: {self.doubletap_threshold:.0f}ms", font_size=9))
        
        # Кнопка перезагрузки уровня
        v_box.add(arcade.gui.UILabel(text="", font_size=8))  # Разделитель
        reload_button = arcade.gui.UIFlatButton(
            text="Reload Level",
            width=200,
        )
        v_box.add(reload_button)
        
        @reload_button.event("on_click")
        def on_reload(_event):
            self.game_view.reload_level()
        
        # Кнопка сохранения в файл
        save_button = arcade.gui.UIFlatButton(
            text="Save to constants.py",
            width=200,
        )
        v_box.add(save_button)
        
        @save_button.event("on_click")
        def on_save(_event):
            self.game_view.save_constants_to_file()
        
        # Добавляем отступ через padding в v_box
        v_box.with_padding(all=10)
        
        # Якорь для размещения панели в правом верхнем углу
        anchor = arcade.gui.UIAnchorLayout()
        anchor.add(
            child=v_box,
            anchor_x="right",
            anchor_y="top",
        )
        
        self.manager.add(anchor)

    def enable(self):
        """Включить панель."""
        self.manager.enable()

    def disable(self):
        """Отключить панель."""
        self.manager.disable()

    def draw(self):
        """Отрисовка панели."""
        self.manager.draw()
