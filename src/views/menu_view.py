"""Экран главного меню."""

import arcade

from src.constants import SCREEN_HEIGHT, SCREEN_WIDTH


class MenuView(arcade.View):
    """Главное меню."""

    def __init__(self):
        super().__init__()

        cx = SCREEN_WIDTH / 2
        cy = SCREEN_HEIGHT / 2

        self.title_text = arcade.Text(
            "Kitavik Spring Adventure",
            cx, cy + 50,
            arcade.color.WHITE,
            font_size=40,
            anchor_x="center",
        )
        self.start_text = arcade.Text(
            "Нажмите ENTER для начала игры",
            cx, cy - 30,
            arcade.color.LIGHT_GRAY,
            font_size=20,
            anchor_x="center",
        )
        self.exit_text = arcade.Text(
            "ESC — выход",
            cx, cy - 80,
            arcade.color.LIGHT_GRAY,
            font_size=16,
            anchor_x="center",
        )

    def on_show_view(self):
        """Вызывается при показе вида."""
        self.background_color = arcade.color.DARK_BLUE_GRAY

    def on_draw(self):
        """Отрисовка меню."""
        self.clear()
        self.title_text.draw()
        self.start_text.draw()
        self.exit_text.draw()

    def on_key_press(self, key: int, modifiers: int):
        """Обработка нажатий."""
        if key == arcade.key.RETURN:
            from src.views.story_view import StoryView
            story = StoryView()
            self.window.show_view(story)
        elif key == arcade.key.ESCAPE:
            arcade.exit()
