"""Базовый класс врага."""

import arcade
from PIL import Image

from src.constants import ENEMY_SCALING

# Константы для направления врага
RIGHT_FACING = 0
LEFT_FACING = 1


class Enemy(arcade.Sprite):
    """Враг-мышь, патрулирующая вокруг точки респавна."""

    def __init__(
        self,
        x: float,
        y: float,
        move_force: float = 300,
        patrol_range: float = 96,
    ):
        super().__init__(scale=ENEMY_SCALING)
        
        self.center_x = x
        self.center_y = y

        # Параметры патрулирования
        self.move_force = move_force  # Сила движения для pymunk
        self.patrol_range = patrol_range
        self.start_x = x
        self.start_y = y
        
        # Направление движения
        self.facing_direction = RIGHT_FACING
        self.direction = 1  # 1 = вправо, -1 = влево
        
        # Загрузка текстур анимации мыши (3 кадра ходьбы)
        # Тайлсет: 32x96 (ширина 96, высота 32, 3 кадра по 32 пикселя)
        self.walk_textures_right = []
        self.walk_textures_left = []
        
        sprite_sheet_path = "assets/images/enemies/rat_enemy.png"
        sprite_sheet = Image.open(sprite_sheet_path)
        frame_width = 32
        frame_height = 32
        
        for i in range(3):
            # Вырезаем кадр из спрайт-листа
            left = i * frame_width
            frame = sprite_sheet.crop((left, 0, left + frame_width, frame_height))
            
            # Создаем текстуру для движения вправо
            texture_right = arcade.Texture(
                name=f"rat_walk_right_{i}",
                image=frame
            )
            self.walk_textures_right.append(texture_right)
            
            # Отзеркаливаем для движения влево
            frame_left = frame.transpose(Image.FLIP_LEFT_RIGHT)
            texture_left = arcade.Texture(
                name=f"rat_walk_left_{i}",
                image=frame_left
            )
            self.walk_textures_left.append(texture_left)
        
        # Устанавливаем начальную текстуру
        self.texture = self.walk_textures_right[0]
        
        # Счетчик для анимации
        self.cur_texture_index = 0
        self.animation_update_time = 0.1  # Обновление кадра каждые 0.1 сек
        self.time_since_last_update = 0

    def update_animation(self, delta_time: float = 1 / 60):
        """Обновление анимации ходьбы."""
        # Обновляем таймер анимации
        self.time_since_last_update += delta_time
        
        if self.time_since_last_update > self.animation_update_time:
            self.time_since_last_update = 0
            self.cur_texture_index += 1
            if self.cur_texture_index >= len(self.walk_textures_right):
                self.cur_texture_index = 0
            
            # Выбираем текстуру в зависимости от направления
            if self.facing_direction == RIGHT_FACING:
                self.texture = self.walk_textures_right[self.cur_texture_index]
            else:
                self.texture = self.walk_textures_left[self.cur_texture_index]
    
    def check_patrol_bounds(self):
        """Проверка границ патрулирования и смена направления."""
        if self.center_x > self.start_x + self.patrol_range:
            self.direction = -1  # Идем влево
            self.facing_direction = LEFT_FACING
        elif self.center_x < self.start_x - self.patrol_range:
            self.direction = 1  # Идем вправо
            self.facing_direction = RIGHT_FACING
