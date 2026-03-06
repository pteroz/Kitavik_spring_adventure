"""Базовый класс врага."""

import arcade

from src.constants import ENEMY_SCALING


class Enemy(arcade.Sprite):
    """Враг, патрулирующий платформу влево-вправо."""

    def __init__(
        self,
        x: float,
        y: float,
        speed: float = 1.5,
        patrol_range: float = 96,
    ):
        super().__init__(
            ":resources:images/enemies/slimeBlue.png",
            scale=ENEMY_SCALING,
        )
        self.center_x = x
        self.center_y = y

        self.speed = speed
        self.patrol_range = patrol_range
        self.start_x = x
        self.change_x = speed

    def update(self, delta_time: float = 1 / 60, *args, **kwargs):
        """Движение патрулирования."""
        self.center_x += self.change_x

        # Разворот при достижении границ патруля
        if self.center_x > self.start_x + self.patrol_range:
            self.change_x = -self.speed
        elif self.center_x < self.start_x - self.patrol_range:
            self.change_x = self.speed
