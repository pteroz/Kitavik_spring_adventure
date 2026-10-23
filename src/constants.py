"""Константы игры."""

import sys
import os
from pathlib import Path

def resource_path(relative_path):
    """Получить абсолютный путь к ресурсу, работает для dev и для PyInstaller"""
    try:
        # PyInstaller создает временную папку и сохраняет путь в _MEIPASS
        base_path = Path(sys._MEIPASS)
    except Exception:
        # Если запущено из исходников
        base_path = Path(__file__).resolve().parent.parent
    
    return base_path / relative_path

# Режим разработки (для production поставить False)
DEV_MODE = True

# Корень проекта
if getattr(sys, 'frozen', False):
    # Если запущено из PyInstaller
    PROJECT_ROOT = Path(sys._MEIPASS)
else:
    # Если запущено из исходников
    PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Окно
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
SCREEN_TITLE = "Kitavik Spring Adventure"

# Тайлы
TILE_SIZE = 32
TILE_SCALING = 1.0

# Игрок (ширина ~1 блок, высота ~1.5 блока)
PLAYER_WIDTH = 32
PLAYER_HEIGHT = 48
PLAYER_SCALING = 1.40

# Враги
ENEMY_SCALING = 1.80

# Физика Pymunk
GRAVITY = 1500

# Damping - потеря скорости в секунду (1.0 = нет потерь, 0.0 = свободное падение)
DEFAULT_DAMPING = 1.0
PLAYER_DAMPING = 0.4

# Friction - трение между объектами (0.0 = лед, 1.0 = резина)
PLAYER_FRICTION = 1.0
WALL_FRICTION = 0.7
DYNAMIC_ITEM_FRICTION = 0.6

# Масса (по умолчанию 1, игрок тяжелее чтобы толкать предметы)
PLAYER_MASS = 2.0

# Силы движения - три режима
PLAYER_MOVE_FORCE_SLOW = 400
PLAYER_MOVE_FORCE_NORMAL = 1900
PLAYER_MOVE_FORCE_RUN = 9000
PLAYER_MOVE_FORCE_IN_AIR = 900      # Сила движения в воздухе

# Старые константы для обратной совместимости
PLAYER_MOVE_FORCE_ON_GROUND = 2250

# Таймеры для режимов движения
MOVE_SLOW_THRESHOLD = 0.15
DOUBLE_TAP_THRESHOLD = 0.15
RUN_MODE_DURATION = 2.0             # Время (сек) сохранения режима бега

# Прыжок
PLAYER_JUMP_IMPULSE = 1400
PLAYER_JUMP_IMPULSE_WALK = 1600
PLAYER_JUMP_IMPULSE_RUN = 1800
JUMP_CUTOFF_TIME = 0.15             # Время (сек), в течение которого можно прервать прыжок
JUMP_CUTOFF_MULTIPLIER = 0.4        # Во сколько раз уменьшить скорость при прерывании

# Максимальная скорость игрока
PLAYER_MAX_HORIZONTAL_SPEED = 450
PLAYER_MAX_VERTICAL_SPEED = 1600

# Обратная совместимость (для старого кода в player.py)
PLAYER_JUMP_SPEED = 20
PLAYER_MOVE_SPEED = 10

# Хрупкие платформы
FRAGILE_BREAK_DELAY = 0.4

# Скользкие платформы
ICE_ACCELERATION = 0.3
ICE_DECELERATION = 0.05

# Камера
CAMERA_ZOOM = 1.70
VIEWPORT_MARGIN_LEFT = 250
VIEWPORT_MARGIN_RIGHT = 250
VIEWPORT_MARGIN_TOP = 150
VIEWPORT_MARGIN_BOTTOM = 150

# Слои карты (Tiled)
LAYER_PLATFORMS = "Platforms"
LAYER_MOVING_PLATFORMS = "MovingPlatforms"
LAYER_ONE_WAY_PLATFORMS = "OneWayPlatforms"
LAYER_PLATFORM_PATHS = "PlatformPaths"
LAYER_BACKGROUND = "Background"
LAYER_FOREGROUND = "Foreground"
LAYER_COINS = "Coins"
LAYER_ENEMIES = "Enemies"
LAYER_PLAYER_SPAWN = "PlayerSpawn"

# Пути к ресурсам
ASSETS_PATH = PROJECT_ROOT / "assets"
IMAGES_PATH = ASSETS_PATH / "images"
SOUNDS_PATH = ASSETS_PATH / "sounds"
MUSIC_PATH = ASSETS_PATH / "music"
MAPS_PATH = ASSETS_PATH / "maps"
STORY_PATH = ASSETS_PATH / "story"
