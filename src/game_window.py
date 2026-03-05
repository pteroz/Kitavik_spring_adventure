"""Главное окно игры."""

import arcade

from src.constants import SCREEN_HEIGHT, SCREEN_TITLE, SCREEN_WIDTH
from src.views.menu_view import MenuView


def create_window() -> arcade.Window:
    """Создать и настроить главное окно."""
    window = arcade.Window(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE, resizable=False)
    menu = MenuView()
    window.show_view(menu)
    return window
