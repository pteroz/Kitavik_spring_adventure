"""Класс игрока."""

import arcade

from src.constants import (
    PLAYER_JUMP_SPEED,
    PLAYER_MOVE_SPEED,
    PLAYER_SCALING,
)

# Константы для направления взгляда
RIGHT_FACING = 0
LEFT_FACING = 1

class Player(arcade.Sprite):
    """Спрайт игрока."""

    def __init__(self):
        super().__init__(
            # ":resources:images/animated_characters/female_adventurer/femaleAdventurer_idle.png",
            "assets/images/player/kitavik.png",
            scale=PLAYER_SCALING,
        )

        
        main_path = "assets/images/player/"
        self.facing_direction = RIGHT_FACING
        idle_texture = arcade.load_texture(f"{main_path}kitavik.png")
        self.idle_texture_pair = idle_texture, idle_texture.flip_left_right()

        self.can_jump = False
        self.is_jumping = False
        
        # Динамические параметры (могут изменяться из DevPanel)
        self.jump_speed = PLAYER_JUMP_SPEED
        self.move_speed = PLAYER_MOVE_SPEED
        
        # Базовый масштаб для отражения
        self.base_scale = PLAYER_SCALING
    

    def update(self, delta_time: float = 1 / 60, *args, **kwargs):
        """Обновление состояния игрока."""
        if self.change_x > 0 and self.facing_direction == RIGHT_FACING:
            self.facing_direction = LEFT_FACING
            self.texture = self.idle_texture_pair[0]
        elif self.change_x < 0 and self.facing_direction == LEFT_FACING:
            self.facing_direction = RIGHT_FACING
            self.texture = self.idle_texture_pair[1]

    def jump(self):
        """Прыжок."""
        if self.can_jump:
            self.change_y = self.jump_speed
            self.can_jump = False
            self.is_jumping = True
    
    def release_jump(self):
        """Отпускание клавиши прыжка - уменьшает высоту прыжка."""
        if self.is_jumping and self.change_y > 0:
            self.change_y *= 0.3
        self.is_jumping = False

    def move_left(self):
        """Движение влево."""
        self.change_x = -self.move_speed

    def move_right(self):
        """Движение вправо."""
        self.change_x = self.move_speed

    def stop(self):
        """Остановка горизонтального движения."""
        self.change_x = 0
