"""Экран паузы."""

import arcade

from src.constants import SCREEN_HEIGHT, SCREEN_WIDTH


class PauseView(arcade.View):
    """Вид паузы — отображается поверх игрового экрана."""

    def __init__(self, game_view):
        super().__init__()
        self.game_view = game_view

    def on_draw(self):
        """Отрисовка."""
        self.game_view.on_draw()

        # Полупрозрачный оверлей
        arcade.draw_lbwh_rectangle_filled(
            0, 0, SCREEN_WIDTH, SCREEN_HEIGHT,
            arcade.make_transparent_color(arcade.color.BLACK, 150),
        )

        arcade.draw_text(
            "ПАУЗА",
            SCREEN_WIDTH / 2,
            SCREEN_HEIGHT / 2 + 30,
            arcade.color.WHITE,
            font_size=40,
            anchor_x="center",
        )

        arcade.draw_text(
            "Нажмите ESC для продолжения",
            SCREEN_WIDTH / 2,
            SCREEN_HEIGHT / 2 - 30,
            arcade.color.LIGHT_GRAY,
            font_size=20,
            anchor_x="center",
        )

    def on_key_press(self, key: int, modifiers: int):
        """Обработка нажатий."""
        if key == arcade.key.ESCAPE:
            self.window.show_view(self.game_view)
