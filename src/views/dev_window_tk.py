"""Окно разработчика на tkinter."""

import tkinter as tk
from tkinter import ttk
import psutil
import time
import glob
import os


class DevWindowTk:
    """Отдельное окно на tkinter для настройки параметров."""

    def __init__(self, game_view):
        self.game_view = game_view
        
        # Импортируем константы pymunk
        from src.constants import (
            CAMERA_ZOOM,
            GRAVITY,
            PLAYER_MOVE_FORCE_SLOW,
            PLAYER_MOVE_FORCE_NORMAL,
            PLAYER_MOVE_FORCE_RUN,
            PLAYER_JUMP_IMPULSE,
            PLAYER_JUMP_IMPULSE_WALK,
            PLAYER_JUMP_IMPULSE_RUN,
            MOVE_SLOW_THRESHOLD,
            DOUBLE_TAP_THRESHOLD,
            ENEMY_SCALING,
        )
        
        # Текущие значения параметров pymunk
        self.gravity = GRAVITY
        self.force_tap = PLAYER_MOVE_FORCE_SLOW
        self.force_walk = PLAYER_MOVE_FORCE_NORMAL
        self.force_run = PLAYER_MOVE_FORCE_RUN
        self.jump_stand = PLAYER_JUMP_IMPULSE
        self.jump_walk = PLAYER_JUMP_IMPULSE_WALK
        self.jump_run = PLAYER_JUMP_IMPULSE_RUN
        self.tap_threshold = MOVE_SLOW_THRESHOLD * 1000  # мс
        self.doubletap_threshold = DOUBLE_TAP_THRESHOLD * 1000  # мс
        
        # Параметры камеры
        self.camera_zoom = CAMERA_ZOOM
        
        # Параметры врагов
        self.enemy_scale = ENEMY_SCALING
        
        # Процесс для мониторинга
        self.process = psutil.Process()
        self.last_update_time = 0
        self.gpu_available = self._check_amd_gpu()
        
        self._create_window()

    def _create_window(self):
        """Создание окна tkinter."""
        self.window = tk.Tk()
        self.window.title("Dev Panel")
        self.window.geometry("420x750")
        self.window.resizable(False, False)
        
        # Заголовок (фиксированный)
        title = tk.Label(self.window, text="DEV PANEL", font=("Arial", 16, "bold"), fg="orange")
        title.pack(pady=10)
        
        # Создаем Canvas с прокруткой для остального содержимого
        canvas = tk.Canvas(self.window, highlightthickness=0)
        scrollbar = tk.Scrollbar(self.window, orient="vertical", command=canvas.yview)
        self.scrollable_frame = tk.Frame(canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Прокрутка колесиком мыши
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        canvas.bind_all("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))
        canvas.bind_all("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Системная информация
        sys_frame = tk.LabelFrame(self.scrollable_frame, text="System Info", font=("Arial", 10, "bold"), fg="blue")
        sys_frame.pack(pady=5, padx=20, fill=tk.X)
        
        self.cpu_label = tk.Label(sys_frame, text="CPU: ---%", font=("Arial", 9), anchor=tk.W)
        self.cpu_label.pack(anchor=tk.W, padx=10, pady=2)
        
        self.ram_label = tk.Label(sys_frame, text="RAM: --- MB", font=("Arial", 9), anchor=tk.W)
        self.ram_label.pack(anchor=tk.W, padx=10, pady=2)
        
        if self.gpu_available:
            self.gpu_label = tk.Label(sys_frame, text="GPU: ---%", font=("Arial", 9), anchor=tk.W)
            self.gpu_label.pack(anchor=tk.W, padx=10, pady=2)
            
            self.vram_label = tk.Label(sys_frame, text="VRAM: --- MB", font=("Arial", 9), anchor=tk.W)
            self.vram_label.pack(anchor=tk.W, padx=10, pady=2)
        
        tk.Frame(self.scrollable_frame, height=2, bg="gray").pack(fill=tk.X, pady=10)
        
        # === PYMUNK ПАРАМЕТРЫ ===
        pymunk_label = tk.Label(self.scrollable_frame, text="PYMUNK PARAMS", font=("Arial", 12, "bold"), fg="cyan")
        pymunk_label.pack(pady=5)
        
        # Силы движения
        self._create_param("Force Tap", self.force_tap, 100, 2000, "force_tap")
        self._create_param("Force Walk", self.force_walk, 500, 5000, "force_walk")
        self._create_param("Force Run", self.force_run, 3000, 15000, "force_run")
        
        # Импульсы прыжка
        self._create_param("Jump Stand", self.jump_stand, 500, 3000, "jump_stand")
        self._create_param("Jump Walk", self.jump_walk, 500, 3000, "jump_walk")
        self._create_param("Jump Run", self.jump_run, 500, 3000, "jump_run")
        
        # Таймеры (мс)
        self._create_param("Tap Threshold (ms)", self.tap_threshold, 50, 500, "tap_threshold")
        self._create_param("DoubleTap (ms)", self.doubletap_threshold, 50, 500, "doubletap_threshold")
        
        # Гравитация
        self._create_param("Gravity", self.gravity, 500, 3000, "gravity")
        
        # Разделитель
        tk.Frame(self.scrollable_frame, height=2, bg="gray").pack(fill=tk.X, pady=10)
        
        # === CAMERA ПАРАМЕТРЫ ===
        camera_label = tk.Label(self.scrollable_frame, text="CAMERA PARAMS", font=("Arial", 12, "bold"), fg="blue")
        camera_label.pack(pady=5)
        
        # Zoom камеры
        self._create_param("Camera Zoom", self.camera_zoom, 0.5, 3.0, "camera_zoom")
        
        # Разделитель
        tk.Frame(self.scrollable_frame, height=2, bg="gray").pack(fill=tk.X, pady=10)
        
        # === ENEMIES ПАРАМЕТРЫ ===
        enemies_label = tk.Label(self.scrollable_frame, text="ENEMIES PARAMS", font=("Arial", 12, "bold"), fg="red")
        enemies_label.pack(pady=5)
        
        # Масштаб врагов
        self._create_param("Enemy Scale", self.enemy_scale, 0.5, 3.0, "enemy_scale")
        
        # Кнопки
        btn_frame = tk.Frame(self.scrollable_frame)
        btn_frame.pack(pady=20)
        
        # Кнопка применения параметров
        apply_btn = tk.Button(
            btn_frame, 
            text="Apply Params", 
            command=self._apply_settings, 
            width=15,
            bg="#4CAF50",
            fg="white",
            font=("Arial", 10, "bold")
        )
        apply_btn.pack(pady=5)
        
        reload_btn = tk.Button(btn_frame, text="Restart Level", command=self._reload_level, width=15)
        reload_btn.pack(pady=5)
        
        save_btn = tk.Button(btn_frame, text="Save Params", command=self._save_constants, width=15)
        save_btn.pack(pady=5)

    def _create_param(self, label_text, initial_value, min_val, max_val, attr_name):
        """Создание секции параметра с полем ввода и слайдером."""
        frame = tk.Frame(self.scrollable_frame)
        frame.pack(pady=5, padx=20, fill=tk.X)
        
        # Заголовок
        label = tk.Label(frame, text=label_text, font=("Arial", 10))
        label.pack(anchor=tk.W)
        
        # Фрейм для min, value, max
        values_frame = tk.Frame(frame)
        values_frame.pack(anchor=tk.W, pady=2)
        
        # Min поле
        tk.Label(values_frame, text="Min:", font=("Arial", 8)).pack(side=tk.LEFT)
        min_var = tk.StringVar(value=f"{min_val:.1f}")
        min_entry = tk.Entry(values_frame, textvariable=min_var, width=6, font=("Arial", 9))
        min_entry.pack(side=tk.LEFT, padx=2)
        
        # Value поле (основной источник значений)
        tk.Label(values_frame, text="Value:", font=("Arial", 8)).pack(side=tk.LEFT, padx=(10, 0))
        entry_var = tk.StringVar(value=f"{initial_value:.2f}")
        entry = tk.Entry(values_frame, textvariable=entry_var, width=8, font=("Arial", 11, "bold"))
        entry.pack(side=tk.LEFT, padx=2)
        
        # Max поле
        tk.Label(values_frame, text="Max:", font=("Arial", 8)).pack(side=tk.LEFT, padx=(10, 0))
        max_var = tk.StringVar(value=f"{max_val:.1f}")
        max_entry = tk.Entry(values_frame, textvariable=max_var, width=6, font=("Arial", 9))
        max_entry.pack(side=tk.LEFT, padx=2)
        
        # Слайдер (вспомогательный инструмент)
        slider = tk.Scale(
            frame,
            from_=min_val,
            to=max_val,
            orient=tk.HORIZONTAL,
            resolution=0.1,
            length=300,
        )
        slider.set(initial_value)
        slider.pack(fill=tk.X)
        
        # Применение значения из поля ввода (только локально, без применения к игре)
        def apply_entry_value(event=None):
            try:
                current_min = float(min_var.get())
                current_max = float(max_var.get())
                val = float(entry_var.get())
                
                if current_min <= val <= current_max:
                    slider.set(val)
                    setattr(self, attr_name, val)
                    entry.config(bg="white")
                else:
                    entry.config(bg="#ffcccc")  # Красный фон если вне диапазона
            except ValueError:
                entry.config(bg="#ffcccc")  # Красный фон если не число
        
        # Обновление границ слайдера
        def update_slider_range(event=None):
            try:
                new_min = float(min_var.get())
                new_max = float(max_var.get())
                
                if new_min < new_max:
                    slider.config(from_=new_min, to=new_max)
                    min_entry.config(bg="white")
                    max_entry.config(bg="white")
                else:
                    min_entry.config(bg="#ffcccc")
                    max_entry.config(bg="#ffcccc")
            except ValueError:
                min_entry.config(bg="#ffcccc")
                max_entry.config(bg="#ffcccc")
        
        # Слайдер только обновляет поле ввода
        def on_slider_change(val):
            entry_var.set(f"{float(val):.2f}")
            setattr(self, attr_name, float(val))
        
        # Привязки событий
        entry.bind("<Return>", apply_entry_value)
        entry.bind("<FocusOut>", apply_entry_value)
        min_entry.bind("<Return>", update_slider_range)
        min_entry.bind("<FocusOut>", update_slider_range)
        max_entry.bind("<Return>", update_slider_range)
        max_entry.bind("<FocusOut>", update_slider_range)
        slider.config(command=on_slider_change)

    def _apply_settings(self):
        """Применить настройки pymunk к игре через метод GameView."""
        # Вызываем метод GameView для применения параметров pymunk
        self.game_view.apply_pymunk_settings(
            force_tap=self.force_tap,
            force_walk=self.force_walk,
            force_run=self.force_run,
            jump_stand=self.jump_stand,
            jump_walk=self.jump_walk,
            jump_run=self.jump_run,
            tap_threshold=self.tap_threshold / 1000.0,  
            doubletap_threshold=self.doubletap_threshold / 1000.0,  
            gravity=self.gravity
        )
        
        # Применяем настройки камеры
        self.game_view.apply_camera_settings(
            camera_zoom=self.camera_zoom
        )
        
        # Применяем настройки врагов
        self.game_view.apply_enemy_settings(
            enemy_scale=self.enemy_scale
        )

    def _reload_level(self):
        """Перезагрузить уровень."""
        self.game_view.reload_level()

    def _save_constants(self):
        """Сохранить константы в файл."""
        self.game_view.save_constants_to_file()

    def update(self):
        """Обновление окна tkinter (вызывается из основного потока arcade)."""
        if self.window:
            try:
                self.window.update()
                
                # Обновляем системную информацию раз в 5 секунд
                current_time = time.time()
                if current_time - self.last_update_time >= 5.0:
                    self._update_system_info()
                    self.last_update_time = current_time
            except tk.TclError:
                pass
    
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
            # CPU usage процесса игры
            cpu_percent = self.process.cpu_percent(interval=0)
            self.cpu_label.config(text=f"CPU: {cpu_percent:.1f}%")
            
            # RAM usage процесса игры
            mem_info = self.process.memory_info()
            ram_used_mb = mem_info.rss / (1024 ** 2)
            self.ram_label.config(text=f"RAM: {ram_used_mb:.1f} MB")
            
            # GPU и VRAM (если доступно)
            if self.gpu_available:
                gpu_percent, vram_used_mb = self._get_amd_gpu_stats()
                if gpu_percent is not None:
                    self.gpu_label.config(text=f"GPU: {gpu_percent}%")
                if vram_used_mb is not None:
                    self.vram_label.config(text=f"VRAM: {vram_used_mb:.0f} MB")
        except Exception:
            self.cpu_label.config(text="CPU: Error")
            self.ram_label.config(text="RAM: Error")

    def close(self):
        """Закрыть окно."""
        if self.window:
            try:
                self.window.destroy()
            except tk.TclError:
                pass
