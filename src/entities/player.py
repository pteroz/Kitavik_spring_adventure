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

    def update(self):
        """Обновление состояния игрока."""
        if self.change_x > 0:
            self.facing_right = True
        elif self.change_x < 0:
            self.facing_right = False

    def jump(self):
        """Прыжок."""
        if self.can_jump:
            self.change_y = PLAYER_JUMP_SPEED
            self.can_jump = False

    def move_left(self):
        """Движение влево."""
        self.change_x = -PLAYER_MOVE_SPEED

    def move_right(self):
        """Движение вправо."""
        self.change_x = PLAYER_MOVE_SPEED

    def stop(self):
        """Остановка горизонтального движения."""
        self.change_x = 0
