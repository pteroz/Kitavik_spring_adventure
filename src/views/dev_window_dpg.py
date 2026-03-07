"""Окно разработчика на DearPyGui."""

import dearpygui.dearpygui as dpg
import threading
import psutil
import glob
import os


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
        
        # Системная информация
        self.cpu_text = None
        self.ram_text = None
        self.gpu_text = None
        self.vram_text = None
        self.process = psutil.Process()
        self.gpu_available = self._check_amd_gpu()
        
        # Запуск в отдельном потоке
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def _run(self):
        """Запуск DearPyGui окна."""
        dpg.create_context()
        
        # Основное окно
        with dpg.window(label="Dev Panel", width=400, height=700, pos=(50, 50), 
                       no_resize=True, no_close=True):
            
            dpg.add_text("DEV PANEL", color=(255, 165, 0))
            dpg.add_separator()
            dpg.add_spacer(height=10)
            
            # СИСТЕМНАЯ ИНФОРМАЦИЯ
            dpg.add_text("System Info:", color=(100, 200, 255))
            self.cpu_text = dpg.add_text("CPU: ---%")
            self.ram_text = dpg.add_text("RAM: --- MB")
            if self.gpu_available:
                self.gpu_text = dpg.add_text("GPU: ---%")
                self.vram_text = dpg.add_text("VRAM: --- MB")
            dpg.add_spacer(height=10)
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
        
        dpg.create_viewport(title="Dev Panel", width=420, height=730)
        dpg.setup_dearpygui()
        dpg.show_viewport()
        
        self.running = True
        frame_count = 0
        while dpg.is_dearpygui_running() and self.running:
            dpg.render_dearpygui_frame()
            
            # Обновляем системную информацию каждые 300 фреймов (~5 сек)
            frame_count += 1
            if frame_count >= 300:
                self._update_system_info()
                frame_count = 0
        
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
    
    def _check_amd_gpu(self):
        """Проверить доступность AMD GPU."""
        try:
            cards = glob.glob('/sys/class/drm/card*/device/gpu_busy_percent')
            return len(cards) > 0
        except:
            return False
    
    def _get_amd_gpu_stats(self):
        """Получить статистику AMD GPU."""
        try:
            cards = glob.glob('/sys/class/drm/card*/device')
            if not cards:
                return None, None
            
            card = cards[0]
            
            # GPU usage
            gpu_percent = 0
            gpu_file = os.path.join(card, 'gpu_busy_percent')
            if os.path.exists(gpu_file):
                with open(gpu_file, 'r') as f:
                    gpu_percent = int(f.read().strip())
            
            # VRAM usage
            vram_used_mb = 0
            vram_used_file = os.path.join(card, 'mem_info_vram_used')
            if os.path.exists(vram_used_file):
                with open(vram_used_file, 'r') as f:
                    vram_used_mb = int(f.read().strip()) / (1024 ** 2)
            
            return gpu_percent, vram_used_mb
        except:
            return None, None
    
    def _update_system_info(self):
        """Обновить информацию о ресурсах процесса игры."""
        try:
            # CPU usage процесса игры (% от одного ядра)
            cpu_percent = self.process.cpu_percent(interval=0)
            dpg.set_value(self.cpu_text, f"CPU: {cpu_percent:.1f}%")
            
            # RAM usage процесса игры
            mem_info = self.process.memory_info()
            ram_used_mb = mem_info.rss / (1024 ** 2)  # RSS = Resident Set Size
            dpg.set_value(self.ram_text, f"RAM: {ram_used_mb:.1f} MB")
            
            # GPU и VRAM (если доступно)
            if self.gpu_available:
                gpu_percent, vram_used_mb = self._get_amd_gpu_stats()
                if gpu_percent is not None:
                    dpg.set_value(self.gpu_text, f"GPU: {gpu_percent}%")
                if vram_used_mb is not None:
                    dpg.set_value(self.vram_text, f"VRAM: {vram_used_mb:.0f} MB")
        except Exception as e:
            dpg.set_value(self.cpu_text, f"CPU: Error")
            dpg.set_value(self.ram_text, f"RAM: Error")

    def close(self):
        """Закрыть окно."""
        self.running = False
