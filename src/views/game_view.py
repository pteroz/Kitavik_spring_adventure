"""Основной игровой экран."""

import arcade

from src.constants import (
    DEV_MODE,
    FRAGILE_BREAK_DELAY,
    GRAVITY,
    ICE_ACCELERATION,
    ICE_DECELERATION,
    LAYER_BACKGROUND,
    LAYER_COINS,
    LAYER_ENEMIES,
    LAYER_FOREGROUND,
    LAYER_MOVING_PLATFORMS,
    LAYER_ONE_WAY_PLATFORMS,
    LAYER_PLATFORM_PATHS,
    LAYER_PLATFORMS,
    LAYER_PLAYER_SPAWN,
    MAPS_PATH,
    PLAYER_JUMP_SPEED,
    PLAYER_MOVE_SPEED,
    PLAYER_SCALING,
    PROJECT_ROOT,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    TILE_SCALING,
)
from src.entities.enemy import Enemy
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
        self.enemy_list: arcade.SpriteList | None = None
        self.enemy_engines: list[arcade.PhysicsEnginePlatformer] = []

        self.score = 0
        self.spawn_x = 96
        self.spawn_y = 128
        self.score_text: arcade.Text | None = None

        self.fragile_timers: dict[arcade.Sprite, float] = {}
        self.on_ice = False
        self.left_pressed = False
        self.right_pressed = False

        # Текущие значения параметров (для DevPanel)
        self.current_gravity = GRAVITY
        self.current_jump_speed = PLAYER_JUMP_SPEED
        self.current_move_speed = PLAYER_MOVE_SPEED
        self.current_player_scaling = PLAYER_SCALING

        self.dev_panel = None
        
        # Parallax факторы для слоев (слой: (x_factor, y_factor))
        self.parallax_factors: dict[str, tuple[float, float]] = {}
        
        # Отладка коллизий
        self.debug_collisions = True
        self.collision_blocks: list[arcade.Sprite] = []
        
        # One-way платформы: временно убранные при прыжке через них
        # {platform: y_position_when_removed}
        self.disabled_oneway_platforms: dict[arcade.Sprite, float] = {}
        
        # Разбиваемые блоки: флаг для ограничения - только 1 блок за прыжок
        self.block_broken_this_jump = False

    def setup(self):
        """Инициализация уровня."""
        self.camera = arcade.camera.Camera2D()
        self.gui_camera = arcade.camera.Camera2D()
        self.score = 0

        # Загрузка Tiled-карты
        map_file = MAPS_PATH / f"level{self.level}.tmx"

        layer_options = {
            LAYER_PLATFORMS: {"use_spatial_hash": True},
            LAYER_MOVING_PLATFORMS: {"use_spatial_hash": False},
            LAYER_ONE_WAY_PLATFORMS: {"use_spatial_hash": False},
            LAYER_COINS: {"use_spatial_hash": True},
        }

        if map_file.exists():
            self.tile_map = arcade.load_tilemap(
                str(map_file),
                scaling=TILE_SCALING,
                layer_options=layer_options,
            )
            self.scene = arcade.Scene.from_tilemap(self.tile_map)
            
            # Чтение parallax факторов из свойств слоев Tiled
            self._load_parallax_factors()
        else:
            self.scene = arcade.Scene()
            self._generate_fallback_level()

        # Создание игрока
        self.player = Player()
        self.player_list = arcade.SpriteList()

        # Поиск точки спавна на карте
        if self.tile_map and LAYER_PLAYER_SPAWN in self.tile_map.object_lists:
            objects = self.tile_map.object_lists[LAYER_PLAYER_SPAWN]
            if objects:
                self.spawn_x, self.spawn_y = objects[0].shape

        self.player.center_x = self.spawn_x
        self.player.center_y = self.spawn_y
        self.player_list.append(self.player)
        self.scene.add_sprite_list("Player", sprite_list=self.player_list)

        # Загрузка врагов
        self.enemy_list = arcade.SpriteList()
        self.enemy_engines = []
        
        # walls - обычные платформы
        walls = self.scene.get_sprite_list(LAYER_PLATFORMS) if LAYER_PLATFORMS in self.scene else arcade.SpriteList()

        if self.tile_map and LAYER_ENEMIES in self.tile_map.object_lists:
            for obj in self.tile_map.object_lists[LAYER_ENEMIES]:
                ex, ey = obj.shape
                speed = float(obj.properties.get("speed", 1.5))
                patrol = float(obj.properties.get("patrol_range", 96))
                enemy = Enemy(ex, ey, speed=speed, patrol_range=patrol)
                self.enemy_list.append(enemy)
                engine = arcade.PhysicsEnginePlatformer(
                    enemy,
                    walls=walls,
                    gravity_constant=GRAVITY / 60,
                )
                self.enemy_engines.append(engine)
        self.scene.add_sprite_list(LAYER_ENEMIES, sprite_list=self.enemy_list)

        # Физический движок игрока
        # platforms - подвижные платформы
        moving_platforms = None
        if LAYER_MOVING_PLATFORMS in self.scene:
            moving_platforms = self.scene.get_sprite_list(LAYER_MOVING_PLATFORMS)
        
        self.physics_engine = arcade.PhysicsEnginePlatformer(
            self.player,
            walls=walls,
            platforms=moving_platforms,
            gravity_constant=GRAVITY / 60,
        )
        
        # Настройка движения подвижных платформ
        self._setup_moving_platforms()

        self.score_text = arcade.Text(
            f"Очки: {self.score}",
            10,
            SCREEN_HEIGHT - 40,
            arcade.color.WHITE,
            font_size=18,
        )

        # Инициализация DevWindowTk (только если еще не создана)
        if DEV_MODE and not self.dev_panel:
            from src.views.dev_window_tk import DevWindowTk
            self.dev_panel = DevWindowTk(self)

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
        """Отрисовка с поддержкой parallax."""
        self.clear()

        # Сохраняем текущую позицию камеры
        camera_x, camera_y = self.camera.position

        # Рисуем каждый слой с учетом parallax
        for layer_name in self.scene._name_mapping:
            if layer_name in self.parallax_factors:
                parallax_x, parallax_y = self.parallax_factors[layer_name]
                
                # Вычисляем смещенную позицию камеры для parallax
                offset_camera_x = camera_x * parallax_x
                offset_camera_y = camera_y * parallax_y
                
                # Устанавливаем смещенную позицию и рисуем слой
                self.camera.position = (offset_camera_x, offset_camera_y)
                with self.camera.activate():
                    self.scene.get_sprite_list(layer_name).draw()
            else:
                # Рисуем слой без parallax - с нормальной позицией камеры
                self.camera.position = (camera_x, camera_y)
                with self.camera.activate():
                    self.scene.get_sprite_list(layer_name).draw()
        
        # Восстанавливаем нормальную позицию камеры
        self.camera.position = (camera_x, camera_y)

        with self.gui_camera.activate():
            self.score_text.draw()
        
    def on_update(self, delta_time: float):
        """Обновление логики."""
        # Обновление подвижных платформ
        if LAYER_MOVING_PLATFORMS in self.scene:
            for platform in self.scene.get_sprite_list(LAYER_MOVING_PLATFORMS):
                if hasattr(platform, 'direction'):
                    # Горизонтальное движение
                    if platform.direction == "horizontal":
                        platform.center_x += platform.change_x
                        
                        if platform.center_x >= platform.boundary_right:
                            platform.center_x = platform.boundary_right
                            platform.change_x = -abs(platform.change_x)
                        elif platform.center_x <= platform.boundary_left:
                            platform.center_x = platform.boundary_left
                            platform.change_x = abs(platform.change_x)
                    
                    # Вертикальное движение
                    elif platform.direction == "vertical":
                        platform.center_y += platform.change_y
                        
                        if platform.center_y >= platform.boundary_top:
                            platform.center_y = platform.boundary_top
                            platform.change_y = -abs(platform.change_y)
                        elif platform.center_y <= platform.boundary_bottom:
                            platform.center_y = platform.boundary_bottom
                            platform.change_y = abs(platform.change_y)
        
        # Сохраняем состояние игрока ДО physics update
        player_velocity_before = self.player.change_y
        player_bottom_before = self.player.bottom
        player_falling = self.player.change_y < 0
        
        # Физический движок (ОДИН раз!)
        self.physics_engine.update()
        for engine in self.enemy_engines:
            engine.update()
        
        # Проверка: может ли игрок прыгать
        self.player.can_jump = self.physics_engine.can_jump()
        
        # One-way платформы: обработка после physics update
        if LAYER_ONE_WAY_PLATFORMS in self.scene:
            oneway_platforms = self.scene.get_sprite_list(LAYER_ONE_WAY_PLATFORMS)
            for platform in oneway_platforms:
                if arcade.check_for_collision(self.player, platform):
                    # Игрок падал вниз И был над платформой (bottom был выше или на уровне top платформы)
                    if player_falling and player_bottom_before >= platform.top - 5:
                        # Приземление разрешено
                        self.player.bottom = platform.top
                        self.player.change_y = 0
                        # Разрешаем прыжок, так как игрок стоит на платформе
                        self.player.can_jump = True
                    # Игрок стоит на платформе (не падает, bottom близко к top)
                    elif abs(self.player.bottom - platform.top) < 5 and abs(self.player.change_y) < 1:
                        # Разрешаем прыжок каждый кадр
                        self.player.can_jump = True
                    # Иначе: игрок прыгает снизу или идет сбоку - проходит насквозь
                    # Physics engine уже обработал движение, не корректируем позицию
        
        # Сбрасываем флаг разбитого блока когда игрок не прыгает вверх
        if self.player.change_y <= 0:
            self.block_broken_this_jump = False
        
        # Разбиваемые блоки: если игрок прыгал вверх, но скорость стала ≤0 - ударился головой
        if LAYER_PLATFORMS in self.scene and player_velocity_before > 0 and self.player.change_y <= 0:
            # Удаляем только если ещё не разбили блок в этом прыжке
            if not self.block_broken_this_jump:
                platforms = self.scene.get_sprite_list(LAYER_PLATFORMS)
                
                # Ищем блоки близко над головой игрока (в пределах 10px)
                nearby_blocks = []
                for block in platforms:
                    # Проверяем: блок над игроком и близко (в зоне удара головой)
                    if (abs(block.center_x - self.player.center_x) < (block.width / 2 + self.player.width / 2) and
                        block.bottom <= self.player.top + 10 and
                        block.bottom >= self.player.top - 5):
                        nearby_blocks.append(block)
                
                # Удаляем ТОЛЬКО ПЕРВЫЙ блок с атрибутом is_broken
                for block in nearby_blocks:
                    props = getattr(block, "properties", {})
                    if props.get("is_broken"):
                        block.remove_from_sprite_lists()
                        self.block_broken_this_jump = True
                        break  # Выходим после первого удаления
        
        # Отладка коллизий - собираем все блоки, с которыми сталкивается игрок
        if self.debug_collisions:
            self.collision_blocks = []
            if LAYER_PLATFORMS in self.scene:
                self.collision_blocks.extend(
                    arcade.check_for_collision_with_list(self.player, self.scene.get_sprite_list(LAYER_PLATFORMS))
                )
            if LAYER_MOVING_PLATFORMS in self.scene:
                self.collision_blocks.extend(
                    arcade.check_for_collision_with_list(self.player, self.scene.get_sprite_list(LAYER_MOVING_PLATFORMS))
                )
            if LAYER_ONE_WAY_PLATFORMS in self.scene:
                self.collision_blocks.extend(
                    arcade.check_for_collision_with_list(self.player, self.scene.get_sprite_list(LAYER_ONE_WAY_PLATFORMS))
                )
        
        self.player.update()
        self.enemy_list.update()
        self.scene.update_animation(delta_time)
        
        # Обновление DevPanel (tkinter)
        if DEV_MODE and self.dev_panel:
            self.dev_panel.update()

        # Обработка специальных платформ
        self._process_special_platforms(delta_time)

        # Логика льда: плавное ускорение и торможение
        if self.on_ice and self.player.can_jump:
            if self.left_pressed:
                self.player.change_x = max(-PLAYER_MOVE_SPEED, self.player.change_x - ICE_ACCELERATION)
            elif self.right_pressed:
                self.player.change_x = min(PLAYER_MOVE_SPEED, self.player.change_x + ICE_ACCELERATION)
            else:
                if self.player.change_x > 0:
                    self.player.change_x = max(0, self.player.change_x - ICE_DECELERATION)
                elif self.player.change_x < 0:
                    self.player.change_x = min(0, self.player.change_x + ICE_DECELERATION)

        # Столкновение с врагами — респавн
        enemies_hit = arcade.check_for_collision_with_list(
            self.player, self.enemy_list
        )
        if enemies_hit:
            self.player.center_x = self.spawn_x
            self.player.center_y = self.spawn_y
            self.player.change_x = 0
            self.player.change_y = 0

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
            self.player.center_x = self.spawn_x
            self.player.center_y = self.spawn_y
            self.player.change_x = 0
            self.player.change_y = 0

    def _process_special_platforms(self, delta_time: float):
        """Обработка хрупких и скользких платформ."""
        self.on_ice = False

        if LAYER_PLATFORMS not in self.scene:
            return

        platforms = self.scene.get_sprite_list(LAYER_PLATFORMS)

        # Сдвигаем игрока вниз на 2px для обнаружения платформы под ногами
        self.player.center_y -= 2
        touching = arcade.check_for_collision_with_list(self.player, platforms)
        self.player.center_y += 2
        

        for platform in touching:
            props = getattr(platform, "properties", {})

            # Хрупкая платформа — начинаем отсчёт
            if props.get("fragile"):
                if platform not in self.fragile_timers:
                    self.fragile_timers[platform] = FRAGILE_BREAK_DELAY

            # Скользкая платформа
            if props.get("slippery"):
                self.on_ice = True

        # Обновление таймеров хрупких платформ
        to_remove = []
        for platform, timer in self.fragile_timers.items():
            timer -= delta_time
            self.fragile_timers[platform] = timer
            if timer <= 0:
                platform.remove_from_sprite_lists()
                to_remove.append(platform)
        for p in to_remove:
            del self.fragile_timers[p]

    def _load_parallax_factors(self):
        """Чтение parallax факторов из атрибутов и properties слоев Tiled."""
        if not self.tile_map:
            return
        
        # Перебираем все слои в tile_map
        for layer_name in self.tile_map.sprite_lists:
            # Получаем layer object из pytiled_parser
            tiled_layer = None
            for layer in self.tile_map.tiled_map.layers:
                if layer.name == layer_name:
                    tiled_layer = layer
                    break
            
            if tiled_layer:
                # Читаем parallax_factor (OrderedPair из pytiled_parser)
                parallax_factor = getattr(tiled_layer, 'parallax_factor', None)
                
                if parallax_factor and hasattr(parallax_factor, 'x') and hasattr(parallax_factor, 'y'):
                    parallax_x = float(parallax_factor.x)
                    parallax_y = float(parallax_factor.y)
                else:
                    # Если нет встроенного parallax_factor, проверяем custom properties
                    props = getattr(tiled_layer, 'properties', {}) or {}
                    parallax_x = float(props.get('parallax_x', 1.0))
                    parallax_y = float(props.get('parallax_y', 1.0))
                
                if parallax_x != 1.0 or parallax_y != 1.0:
                    self.parallax_factors[layer_name] = (parallax_x, parallax_y)
    
    def _setup_moving_platforms(self):
        """Настроить движение платформ из Object Layer PlatformPaths."""
        if not self.tile_map or LAYER_MOVING_PLATFORMS not in self.scene:
            return
        
        # Получаем все подвижные платформы
        moving_platforms = self.scene.get_sprite_list(LAYER_MOVING_PLATFORMS)
        if not moving_platforms:
            return
        
        # Ищем Object Layer с путями движения
        platform_paths = None
        if LAYER_PLATFORM_PATHS in self.tile_map.object_lists:
            platform_paths = self.tile_map.object_lists[LAYER_PLATFORM_PATHS]
        
        if not platform_paths:
            # Если нет определенных путей, устанавливаем дефолтное движение
            for platform in moving_platforms:
                platform.boundary_left = platform.center_x - 100
                platform.boundary_right = platform.center_x + 100
                platform.boundary_top = platform.center_y + 100
                platform.boundary_bottom = platform.center_y - 100
                platform.change_x = 2.0
                platform.change_y = 0
                platform.direction = "horizontal"
            return
        
        # Настраиваем каждую платформу по объектам из Tiled
        for obj in platform_paths:
            # obj.shape возвращает (x, y) для точек или (x, y, width, height) для прямоугольников
            if isinstance(obj.shape, tuple):
                if len(obj.shape) == 2:
                    obj_x, obj_y = obj.shape
                elif len(obj.shape) == 4:
                    obj_x, obj_y, _, _ = obj.shape
                else:
                    continue
            else:
                continue
            
            # Находим ближайшую платформу к этому объекту
            closest_platform = None
            min_distance = float('inf')
            
            for platform in moving_platforms:
                distance = ((platform.center_x - obj_x) ** 2 + (platform.center_y - obj_y) ** 2) ** 0.5
                if distance < min_distance and distance < 64:  # В пределах 64 пикселей
                    min_distance = distance
                    closest_platform = platform
            
            if closest_platform:
                # Читаем свойства из объекта
                props = obj.properties if obj.properties else {}
                
                closest_platform.boundary_left = float(props.get('boundary_left', obj_x - 100))
                closest_platform.boundary_right = float(props.get('boundary_right', obj_x + 100))
                closest_platform.boundary_top = float(props.get('boundary_top', obj_y + 100))
                closest_platform.boundary_bottom = float(props.get('boundary_bottom', obj_y - 100))
                
                speed = float(props.get('speed', 2.0))
                direction = props.get('direction', 'horizontal')
                
                closest_platform.direction = direction
                if direction == "horizontal":
                    closest_platform.change_x = speed
                    closest_platform.change_y = 0
                else:  # vertical
                    closest_platform.change_x = 0
                    closest_platform.change_y = speed
    
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
            self.left_pressed = True
            if not self.on_ice:
                self.player.move_left()
        elif key in (arcade.key.RIGHT, arcade.key.D):
            self.right_pressed = True
            if not self.on_ice:
                self.player.move_right()
        elif key == arcade.key.ESCAPE:
            from src.views.menu_view import MenuView
            menu = MenuView()
            self.window.show_view(menu)

    def on_key_release(self, key: int, modifiers: int):
        """Отпускание клавиши."""
        if key in (arcade.key.UP, arcade.key.W):
            self.player.release_jump()
        elif key in (arcade.key.LEFT, arcade.key.A):
            self.left_pressed = False
            if not self.on_ice and self.player.change_x < 0:
                self.player.stop()
        elif key in (arcade.key.RIGHT, arcade.key.D):
            self.right_pressed = False
            if not self.on_ice and self.player.change_x > 0:
                self.player.stop()

    def apply_dev_settings(self, gravity, jump_speed, move_speed, player_scaling):
        """Применить настройки из DevPanel в реальном времени."""
        self.current_gravity = gravity
        self.current_jump_speed = jump_speed
        self.current_move_speed = move_speed
        self.current_player_scaling = player_scaling

        # Обновляем физический движок игрока
        if self.physics_engine:
            self.physics_engine.gravity_constant = gravity / 60

        # Обновляем параметры игрока
        if self.player:
            self.player.scale = player_scaling
            self.player.jump_speed = jump_speed
            self.player.move_speed = move_speed

    def reload_level(self):
        """Перезагрузить уровень с текущими настройками."""
        self.setup()

    def save_constants_to_file(self):
        """Сохранить текущие параметры в constants.py."""
        constants_path = PROJECT_ROOT / "src" / "constants.py"
        
        try:
            with open(constants_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
            
            # Обновляем значения в файле
            for i, line in enumerate(lines):
                if line.startswith("GRAVITY = "):
                    lines[i] = f"GRAVITY = {int(self.current_gravity)}\n"
                elif line.startswith("PLAYER_MOVE_SPEED = "):
                    lines[i] = f"PLAYER_MOVE_SPEED = {int(self.current_move_speed)}\n"
                elif line.startswith("PLAYER_JUMP_SPEED = "):
                    lines[i] = f"PLAYER_JUMP_SPEED = {int(self.current_jump_speed)}\n"
                elif line.startswith("PLAYER_SCALING = "):
                    lines[i] = f"PLAYER_SCALING = {self.current_player_scaling:.2f}\n"
            
            with open(constants_path, "w", encoding="utf-8") as f:
                f.writelines(lines)
            
            print(f"Параметры сохранены в {constants_path}")
        except Exception as e:
            print(f"Ошибка сохранения: {e}")
