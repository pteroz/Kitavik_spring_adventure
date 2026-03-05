"""Основной игровой экран."""

import arcade

from src.constants import (
    GRAVITY,
    LAYER_BACKGROUND,
    LAYER_COINS,
    LAYER_FOREGROUND,
    LAYER_PLATFORMS,
    LAYER_PLAYER_SPAWN,
    MAPS_PATH,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    TILE_SCALING,
)
from src.entities.player import Player


class GameView(arcade.View):
    """Основной игровой вид — геймплей."""

    def __init__(self, level: int = 1):
        super().__init__()
        self.level = level

        self.player: Player | None = None
        self.physics_engine: arcade.PhysicsEnginePlatformer | None = None
        self.camera: arcade.camera.Camera2D | None = None
        self.gui_camera: arcade.camera.Camera2D | None = None

        self.tile_map: arcade.TileMap | None = None
        self.scene: arcade.Scene | None = None
        self.player_list: arcade.SpriteList | None = None

        self.score = 0
        self.score_text: arcade.Text | None = None

    def setup(self):
        """Инициализация уровня."""
        self.camera = arcade.camera.Camera2D()
        self.gui_camera = arcade.camera.Camera2D()
        self.score = 0

        # Загрузка Tiled-карты
        map_file = MAPS_PATH / f"level{self.level}.tmx"

        layer_options = {
            LAYER_PLATFORMS: {"use_spatial_hash": True},
            LAYER_COINS: {"use_spatial_hash": True},
        }

        if map_file.exists():
            self.tile_map = arcade.load_tilemap(
                str(map_file),
                scaling=TILE_SCALING,
                layer_options=layer_options,
            )
            self.scene = arcade.Scene.from_tilemap(self.tile_map)
        else:
            self.scene = arcade.Scene()
            self._generate_fallback_level()

        # Создание игрока
        self.player = Player()
        self.player_list = arcade.SpriteList()

        # Поиск точки спавна на карте
        spawn_x, spawn_y = 96, 128
        if self.tile_map and LAYER_PLAYER_SPAWN in self.tile_map.sprite_lists:
            spawn_list = self.tile_map.sprite_lists[LAYER_PLAYER_SPAWN]
            if spawn_list:
                spawn_x = spawn_list[0].center_x
                spawn_y = spawn_list[0].center_y
                spawn_list[0].remove_from_sprite_lists()

        self.player.center_x = spawn_x
        self.player.center_y = spawn_y
        self.player_list.append(self.player)
        self.scene.add_sprite_list("Player", sprite_list=self.player_list)

        # Физический движок
        walls = self.scene.get_sprite_list(LAYER_PLATFORMS) if LAYER_PLATFORMS in self.scene else arcade.SpriteList()
        self.physics_engine = arcade.PhysicsEnginePlatformer(
            self.player,
            walls=walls,
            gravity_constant=GRAVITY / 60,
        )

        self.score_text = arcade.Text(
            f"Очки: {self.score}",
            10,
            SCREEN_HEIGHT - 40,
            arcade.color.WHITE,
            font_size=18,
        )

    def _generate_fallback_level(self):
        """Генерация простого уровня-заглушки (если .tmx не найден)."""
        platforms = arcade.SpriteList(use_spatial_hash=True)
        coins = arcade.SpriteList(use_spatial_hash=True)

        # Пол
        for x in range(0, 2560, 32):
            wall = arcade.Sprite(
                ":resources:images/tiles/grassMid.png",
                scale=0.45,
            )
            wall.center_x = x + 16
            wall.center_y = 16
            platforms.append(wall)

        # Платформы
        for x in range(256, 448, 32):
            wall = arcade.Sprite(
                ":resources:images/tiles/grassMid.png",
                scale=0.45,
            )
            wall.center_x = x + 16
            wall.center_y = 32 * 4
            platforms.append(wall)

        for x in range(640, 896, 32):
            wall = arcade.Sprite(
                ":resources:images/tiles/grassMid.png",
                scale=0.45,
            )
            wall.center_x = x + 16
            wall.center_y = 32 * 6
            platforms.append(wall)

        # Монетки
        for coord in [(320, 180), (700, 240), (768, 240), (836, 240)]:
            coin = arcade.Sprite(
                ":resources:images/items/coinGold.png",
                scale=0.4,
            )
            coin.center_x = coord[0]
            coin.center_y = coord[1]
            coins.append(coin)

        self.scene.add_sprite_list(LAYER_PLATFORMS, sprite_list=platforms)
        self.scene.add_sprite_list(LAYER_COINS, sprite_list=coins)

    def on_draw(self):
        """Отрисовка."""
        self.clear()

        with self.camera.activate():
            self.scene.draw()

        with self.gui_camera.activate():
            self.score_text.draw()

    def on_update(self, delta_time: float):
        """Обновление логики."""
        self.physics_engine.update()
        self.player.update()

        # Проверка: может ли игрок прыгать
        self.player.can_jump = self.physics_engine.can_jump()

        # Сбор монет
        if LAYER_COINS in self.scene:
            coins_hit = arcade.check_for_collision_with_list(
                self.player, self.scene.get_sprite_list(LAYER_COINS)
            )
            for coin in coins_hit:
                coin.remove_from_sprite_lists()
                self.score += 1
                self.score_text.text = f"Очки: {self.score}"

        # Камера следует за игроком
        self._scroll_camera()

        # Падение — респавн
        if self.player.center_y < -100:
            self.player.center_x = 96
            self.player.center_y = 128

    def _scroll_camera(self):
        """Плавное следование камеры за игроком."""
        target_x = self.player.center_x
        target_y = self.player.center_y

        self.camera.position = (
            arcade.math.lerp(self.camera.position[0], target_x, 0.1),
            arcade.math.lerp(self.camera.position[1], target_y, 0.1),
        )

    def on_key_press(self, key: int, modifiers: int):
        """Нажатие клавиши."""
        if key in (arcade.key.UP, arcade.key.W):
            self.player.jump()
        elif key in (arcade.key.LEFT, arcade.key.A):
            self.player.move_left()
        elif key in (arcade.key.RIGHT, arcade.key.D):
            self.player.move_right()
        elif key == arcade.key.ESCAPE:
            from src.views.menu_view import MenuView
            menu = MenuView()
            self.window.show_view(menu)

    def on_key_release(self, key: int, modifiers: int):
        """Отпускание клавиши."""
        if key in (arcade.key.LEFT, arcade.key.A) and self.player.change_x < 0:
            self.player.stop()
        elif key in (arcade.key.RIGHT, arcade.key.D) and self.player.change_x > 0:
            self.player.stop()
