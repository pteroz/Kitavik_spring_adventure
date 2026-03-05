"""Константы игры."""

from pathlib import Path

# Корень проекта
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
PLAYER_SCALING = 0.5

# Враги
ENEMY_SCALING = 1.0

# Физика
GRAVITY = 60
PLAYER_MOVE_SPEED = 10
PLAYER_JUMP_SPEED = 20
PLAYER_MAX_HORIZONTAL_SPEED = 10
PLAYER_MAX_VERTICAL_SPEED = 10
PLAYER_FRICTION = 1.0
WALL_FRICTION = 0.7

# Камера
VIEWPORT_MARGIN_LEFT = 250
VIEWPORT_MARGIN_RIGHT = 250
VIEWPORT_MARGIN_TOP = 150
VIEWPORT_MARGIN_BOTTOM = 150

# Слои карты (Tiled)
LAYER_PLATFORMS = "Platforms"
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
