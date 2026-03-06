"""Окно разработчика на DearPyGui."""

import dearpygui.dearpygui as dpg
import threading


class DevWindowDPG:
    """Отдельное окно на DearPyGui для настройки параметров."""

    def __init__(self, game_view):
        self.game_view = game_view
        self.running = False
        
        # Текущие значения
        self.gravity = game_view.current_gravity
        self.jump_speed = game_view.current_jump_speed
        self.move_speed = game_view.current_move_speed
        self.player_scaling = game_view.current_player_scaling
        
        # Запуск в отдельном потоке
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def _run(self):
        """Запуск DearPyGui окна."""
        dpg.create_context()
        
        # Основное окно
        with dpg.window(label="Dev Panel", width=400, height=550, pos=(50, 50), 
                       no_resize=True, no_close=True):
            
            dpg.add_text("DEV PANEL", color=(255, 165, 0))
            dpg.add_separator()
            dpg.add_spacer(height=10)
            
            # GRAVITY
            dpg.add_text("Gravity:")
            self.gravity_input = dpg.add_input_float(
                default_value=self.gravity,
                width=200,
                callback=lambda s, v: self._on_gravity_input(v)
            )
            self.gravity_slider = dpg.add_slider_float(
                default_value=self.gravity,
                min_value=20.0,
                max_value=200.0,
                width=350,
                callback=lambda s, v: self._on_gravity_slider(v)
            )
            dpg.add_spacer(height=10)
            
            # JUMP SPEED
            dpg.add_text("Jump Speed:")
            self.jump_input = dpg.add_input_float(
                default_value=self.jump_speed,
                width=200,
                callback=lambda s, v: self._on_jump_input(v)
            )
            self.jump_slider = dpg.add_slider_float(
                default_value=self.jump_speed,
                min_value=5.0,
                max_value=50.0,
                width=350,
                callback=lambda s, v: self._on_jump_slider(v)
            )
            dpg.add_spacer(height=10)
            
            # MOVE SPEED
            dpg.add_text("Move Speed:")
            self.move_input = dpg.add_input_float(
                default_value=self.move_speed,
                width=200,
                callback=lambda s, v: self._on_move_input(v)
            )
            self.move_slider = dpg.add_slider_float(
                default_value=self.move_speed,
                min_value=2.0,
                max_value=30.0,
                width=350,
                callback=lambda s, v: self._on_move_slider(v)
            )
            dpg.add_spacer(height=10)
            
            # PLAYER SCALING
            dpg.add_text("Player Scale:")
            self.scaling_input = dpg.add_input_float(
                default_value=self.player_scaling,
                width=200,
                format="%.2f",
                callback=lambda s, v: self._on_scaling_input(v)
            )
            self.scaling_slider = dpg.add_slider_float(
                default_value=self.player_scaling,
                min_value=0.2,
                max_value=2.0,
                width=350,
                format="%.2f",
                callback=lambda s, v: self._on_scaling_slider(v)
            )
            dpg.add_spacer(height=20)
            dpg.add_separator()
            dpg.add_spacer(height=10)
            
            # Кнопки
            dpg.add_button(label="Reload Level", width=350, callback=self._reload_level)
            dpg.add_spacer(height=5)
            dpg.add_button(label="Save to constants.py", width=350, callback=self._save_constants)
        
        dpg.create_viewport(title="Dev Panel", width=420, height=580)
        dpg.setup_dearpygui()
        dpg.show_viewport()
        
        self.running = True
        while dpg.is_dearpygui_running() and self.running:
            dpg.render_dearpygui_frame()
        
        dpg.destroy_context()

    def _on_gravity_input(self, value):
        """Обработка ввода gravity."""
        if 20 <= value <= 200:
            self.gravity = value
            dpg.set_value(self.gravity_slider, value)
            self._apply_settings()

    def _on_gravity_slider(self, value):
        """Обработка слайдера gravity."""
        self.gravity = value
        dpg.set_value(self.gravity_input, value)
        self._apply_settings()

    def _on_jump_input(self, value):
        """Обработка ввода jump speed."""
        if 5 <= value <= 50:
            self.jump_speed = value
            dpg.set_value(self.jump_slider, value)
            self._apply_settings()

    def _on_jump_slider(self, value):
        """Обработка слайдера jump speed."""
        self.jump_speed = value
        dpg.set_value(self.jump_input, value)
        self._apply_settings()

    def _on_move_input(self, value):
        """Обработка ввода move speed."""
        if 2 <= value <= 30:
            self.move_speed = value
            dpg.set_value(self.move_slider, value)
            self._apply_settings()

    def _on_move_slider(self, value):
        """Обработка слайдера move speed."""
        self.move_speed = value
        dpg.set_value(self.move_input, value)
        self._apply_settings()

    def _on_scaling_input(self, value):
        """Обработка ввода player scaling."""
        if 0.2 <= value <= 2.0:
            self.player_scaling = value
            dpg.set_value(self.scaling_slider, value)
            self._apply_settings()

    def _on_scaling_slider(self, value):
        """Обработка слайдера player scaling."""
        self.player_scaling = value
        dpg.set_value(self.scaling_input, value)
        self._apply_settings()

    def _apply_settings(self):
        """Применить настройки к игре."""
        self.game_view.apply_dev_settings(
            gravity=self.gravity,
            jump_speed=self.jump_speed,
            move_speed=self.move_speed,
            player_scaling=self.player_scaling,
        )

    def _reload_level(self):
        """Перезагрузить уровень."""
        self.game_view.reload_level()

    def _save_constants(self):
        """Сохранить константы в файл."""
        self.game_view.save_constants_to_file()

    def close(self):
        """Закрыть окно."""
        self.running = False
