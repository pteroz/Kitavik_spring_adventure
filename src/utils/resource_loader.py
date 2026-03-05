"""Утилиты загрузки ресурсов."""

import os
from pathlib import Path


def get_project_root() -> Path:
    """Вернуть корневую директорию проекта."""
    return Path(__file__).resolve().parent.parent.parent


def get_asset_path(*parts: str) -> str:
    """Получить абсолютный путь к ресурсу в папке assets."""
    return str(get_project_root() / "assets" / os.path.join(*parts))


def get_map_path(filename: str) -> str:
    """Получить путь к карте уровня."""
    return get_asset_path("maps", filename)
