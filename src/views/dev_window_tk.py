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
        
        # Текущие значения
        self.gravity = game_view.current_gravity
        self.jump_speed = game_view.current_jump_speed
        self.move_speed = game_view.current_move_speed
        self.player_scaling = game_view.current_player_scaling
        
        # Процесс для мониторинга
        self.process = psutil.Process()
        self.last_update_time = 0
        self.gpu_available = self._check_amd_gpu()
        
        self._create_window()

    def _create_window(self):
        """Создание окна tkinter."""
        self.window = tk.Tk()
        self.window.title("Dev Panel")
        self.window.geometry("400x750")
        self.window.resizable(False, False)
        
        # Заголовок
        title = tk.Label(self.window, text="DEV PANEL", font=("Arial", 16, "bold"), fg="orange")
        title.pack(pady=10)
        
        # Системная информация
        sys_frame = tk.LabelFrame(self.window, text="System Info", font=("Arial", 10, "bold"), fg="blue")
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
        
        tk.Frame(self.window, height=2, bg="gray").pack(fill=tk.X, pady=10)
        
        # GRAVITY
        self._create_param("Gravity", self.gravity, 20, 200, "gravity")
        
        # JUMP SPEED
        self._create_param("Jump Speed", self.jump_speed, 5, 50, "jump_speed")
        
        # MOVE SPEED
        self._create_param("Move Speed", self.move_speed, 2, 30, "move_speed")
        
        # PLAYER SCALING
        self._create_param("Player Scale", self.player_scaling, 0.2, 2.0, "player_scaling")
        
        # Кнопки
        btn_frame = tk.Frame(self.window)
        btn_frame.pack(pady=20)
        
        reload_btn = tk.Button(btn_frame, text="Restart Level", command=self._reload_level, width=15)
        reload_btn.pack(pady=5)
        
        save_btn = tk.Button(btn_frame, text="Save Params", command=self._save_constants, width=15)
        save_btn.pack(pady=5)

    def _create_param(self, label_text, initial_value, min_val, max_val, attr_name):
        """Создание секции параметра с полем ввода и слайдером."""
        frame = tk.Frame(self.window)
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
        
        # Применение значения из поля ввода
        def apply_entry_value(event=None):
            try:
                current_min = float(min_var.get())
                current_max = float(max_var.get())
                val = float(entry_var.get())
                
                if current_min <= val <= current_max:
                    slider.set(val)
                    setattr(self, attr_name, val)
                    self._apply_settings()
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
