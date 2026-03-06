"""Окно разработчика на tkinter."""

import tkinter as tk
from tkinter import ttk
import threading


class DevWindowTk:
    """Отдельное окно на tkinter для настройки параметров."""

    def __init__(self, game_view):
        self.game_view = game_view
        self.window = None
        self.thread = None
        
        # Текущие значения
        self.gravity = game_view.current_gravity
        self.jump_speed = game_view.current_jump_speed
        self.move_speed = game_view.current_move_speed
        self.player_scaling = game_view.current_player_scaling
        
        self._create_window()

    def _create_window(self):
        """Создание окна в отдельном потоке."""
        self.thread = threading.Thread(target=self._run_tk, daemon=True)
        self.thread.start()

    def _run_tk(self):
        """Запуск tkinter в отдельном потоке."""
        self.window = tk.Tk()
        self.window.title("Dev Panel")
        self.window.geometry("350x500")
        self.window.resizable(False, False)
        
        # Заголовок
        title = tk.Label(self.window, text="DEV PANEL", font=("Arial", 16, "bold"), fg="orange")
        title.pack(pady=10)
        
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
        
        reload_btn = tk.Button(btn_frame, text="Reload Level", command=self._reload_level, width=15)
        reload_btn.pack(pady=5)
        
        save_btn = tk.Button(btn_frame, text="Save to constants.py", command=self._save_constants, width=15)
        save_btn.pack(pady=5)
        
        self.window.mainloop()

    def _create_param(self, label_text, initial_value, min_val, max_val, attr_name):
        """Создание секции параметра с полем ввода и слайдером."""
        frame = tk.Frame(self.window)
        frame.pack(pady=5, padx=20, fill=tk.X)
        
        # Заголовок
        label = tk.Label(frame, text=label_text, font=("Arial", 10))
        label.pack(anchor=tk.W)
        
        # Поле ввода
        entry_var = tk.StringVar(value=f"{initial_value:.2f}")
        entry = tk.Entry(frame, textvariable=entry_var, width=10)
        entry.pack(anchor=tk.W, pady=2)
        
        # Слайдер
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
        
        # Синхронизация поля ввода и слайдера
        def on_entry_change(*args):
            try:
                val = float(entry_var.get())
                if min_val <= val <= max_val:
                    slider.set(val)
                    setattr(self, attr_name, val)
                    self._apply_settings()
            except ValueError:
                pass
        
        def on_slider_change(val):
            entry_var.set(f"{float(val):.2f}")
            setattr(self, attr_name, float(val))
            self._apply_settings()
        
        entry_var.trace_add("write", on_entry_change)
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

    def close(self):
        """Закрыть окно."""
        if self.window:
            self.window.quit()
