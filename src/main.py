"""Точка входа в игру."""

import arcade

from src.game_window import create_window


def main():
    """Запуск игры."""
    create_window()
    arcade.run()


if __name__ == "__main__":
    main()
