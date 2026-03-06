"""Класс игрока."""

import arcade

from src.constants import (
    PLAYER_JUMP_SPEED,
    PLAYER_MOVE_SPEED,
    PLAYER_SCALING,
)


class Player(arcade.Sprite):
    """Спрайт игрока."""

    def __init__(self):
        super().__init__(
            ":resources:images/animated_characters/female_adventurer/femaleAdventurer_idle.png",
            scale=PLAYER_SCALING,
        )

        self.can_jump = False
        self.facing_right = True
        
        # Динамические параметры (могут изменяться из DevPanel)
        self.jump_speed = PLAYER_JUMP_SPEED
        self.move_speed = PLAYER_MOVE_SPEED

    def update(self, delta_time: float = 1 / 60, *args, **kwargs):
        """Обновление состояния игрока."""
        if self.change_x > 0:
            self.facing_right = True
        elif self.change_x < 0:
            self.facing_right = False

    def jump(self):
        """Прыжок."""
        if self.can_jump:
            self.change_y = self.jump_speed
            self.can_jump = False

    def move_left(self):
        """Движение влево."""
        self.change_x = -self.move_speed

    def move_right(self):
        """Движение вправо."""
        self.change_x = self.move_speed

    def stop(self):
        """Остановка горизонтального движения."""
        self.change_x = 0
