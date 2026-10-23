"""Основной игровой экран."""

import time
import arcade

from src.constants import (
    CAMERA_ZOOM,
    DEV_MODE,
    DEFAULT_DAMPING,
    DOUBLE_TAP_THRESHOLD,
    ENEMY_SCALING,
    FRAGILE_BREAK_DELAY,
    GRAVITY,
    ICE_ACCELERATION,
    ICE_DECELERATION,
    JUMP_CUTOFF_MULTIPLIER,
    JUMP_CUTOFF_TIME,
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
    MOVE_SLOW_THRESHOLD,
    PLAYER_DAMPING,
    PLAYER_FRICTION,
    PLAYER_JUMP_IMPULSE,
    PLAYER_JUMP_IMPULSE_RUN,
    PLAYER_JUMP_IMPULSE_WALK,
    PLAYER_JUMP_SPEED,
    PLAYER_MASS,
    PLAYER_MAX_HORIZONTAL_SPEED,
    PLAYER_MAX_VERTICAL_SPEED,
    PLAYER_MOVE_FORCE_IN_AIR,
    PLAYER_MOVE_FORCE_NORMAL,
    PLAYER_MOVE_FORCE_ON_GROUND,
    PLAYER_MOVE_FORCE_RUN,
    PLAYER_MOVE_FORCE_SLOW,
    PLAYER_MOVE_SPEED,
    PLAYER_SCALING,
    PROJECT_ROOT,
    RUN_MODE_DURATION,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    TILE_SCALING,
    WALL_FRICTION,
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

        self.score = 0
        self.spawn_x = 96
        self.spawn_y = 128
        self.score_text: arcade.Text | None = None

        self.fragile_timers: dict[arcade.Sprite, float] = {}
        self.on_ice = False
        self.left_pressed = False
        self.right_pressed = False
        
        # Переменные для улучшенной механики прыжка
        self.is_jumping = False
        self.jump_release_time = 0
        
        # Система трех режимов движения
        self.left_press_time = 0.0       # Время удержания левой кнопки
        self.right_press_time = 0.0      # Время удержания правой кнопки
        self.last_left_tap_time = 0.0    # Время последнего тапа влево
        self.last_right_tap_time = 0.0   # Время последнего тапа вправо
        self.run_mode_left = False       # Режим бега влево
        self.run_mode_right = False      # Режим бега вправо
        self.run_mode_timer = 0.0        # Таймер для сброса режима бега

        # Текущие значения параметров (для DevPanel)
        self.current_gravity = GRAVITY
        self.current_jump_speed = PLAYER_JUMP_SPEED
        self.current_move_speed = PLAYER_MOVE_SPEED
        self.current_player_scaling = PLAYER_SCALING
        self.current_enemy_scale = ENEMY_SCALING
        self.current_camera_zoom = CAMERA_ZOOM
        
        # Текущие pymunk параметры
        self.current_force_tap = PLAYER_MOVE_FORCE_SLOW
        self.current_force_walk = PLAYER_MOVE_FORCE_NORMAL
        self.current_force_run = PLAYER_MOVE_FORCE_RUN
        self.current_jump_stand = PLAYER_JUMP_IMPULSE
        self.current_jump_walk = PLAYER_JUMP_IMPULSE_WALK
        self.current_jump_run = PLAYER_JUMP_IMPULSE_RUN
        self.current_tap_threshold = MOVE_SLOW_THRESHOLD
        self.current_doubletap_threshold = DOUBLE_TAP_THRESHOLD

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
        self.camera.zoom = CAMERA_ZOOM  # Применяем zoom из константы
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
            
            # Удаляем автоматически загруженные image layers (они будут перезагружены с правильными настройками)
            layers_to_remove = []
            for layer_name in list(self.scene._name_mapping.keys()):
                # Проверяем является ли это image layer из Tiled
                if self.tile_map.tiled_map:
                    for tiled_layer in self.tile_map.tiled_map.layers:
                        if hasattr(tiled_layer, 'image') and tiled_layer.image and tiled_layer.name == layer_name:
                            layers_to_remove.append(layer_name)
                            break
            
            for layer_name in layers_to_remove:
                del self.scene._name_mapping[layer_name]
            
            # Загрузка image layers (фоновые изображения) с нашими настройками
            self._load_image_layers()
            
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
        
        # walls - обычные платформы
        walls = self.scene.get_sprite_list(LAYER_PLATFORMS) if LAYER_PLATFORMS in self.scene else arcade.SpriteList()

        if self.tile_map and LAYER_ENEMIES in self.tile_map.object_lists:
            for obj in self.tile_map.object_lists[LAYER_ENEMIES]:
                ex, ey = obj.shape
                move_force = float(obj.properties.get("move_force", 300))
                patrol = float(obj.properties.get("patrol_range", 96))
                
                # Проверяем имя объекта для определения типа врага
                enemy_type = obj.name.lower() if obj.name else "rat"
                
                # Создаем врага в зависимости от типа
                if enemy_type == "rat" or enemy_type == "":
                    # Мышь - базовый тип врага
                    enemy = Enemy(ex, ey, move_force=move_force, patrol_range=patrol)
                    self.enemy_list.append(enemy)
                # Здесь можно добавить другие типы врагов
                # elif enemy_type == "bat":
                #     enemy = BatEnemy(ex, ey, ...)
                #     self.enemy_list.append(enemy)
                else:
                    # Неизвестный тип - создаем обычную мышь
                    print(f"[WARNING] Неизвестный тип врага: {enemy_type}, создаем мышь")
                    enemy = Enemy(ex, ey, move_force=move_force, patrol_range=patrol)
                    self.enemy_list.append(enemy)
        self.scene.add_sprite_list(LAYER_ENEMIES, sprite_list=self.enemy_list)

        # --- Pymunk Physics Engine ---
        # Damping - потеря скорости для платформера должна быть 1.0
        damping = DEFAULT_DAMPING
        
        # Гравитация (0, -GRAVITY) - вниз
        gravity = (0, -GRAVITY)
        
        # Создаем физический движок Pymunk
        self.physics_engine = arcade.PymunkPhysicsEngine(damping=damping, gravity=gravity)
        
        # Настройка pymunk space для уменьшения подпрыгивания на стыках тайлов
        # collision_slop - допуск проникновения объектов
        # collision_bias - насколько быстро разрешаются проникновения
        self.physics_engine.space.collision_slop = 0.02  # Минимальный допуск
        self.physics_engine.space.collision_bias = pow(1.0 - 0.5, 60.0)  # Быстрое разрешение
        
        # Добавляем игрока
        # - friction: трение с другими объектами
        # - mass: масса (игрок тяжелее для толкания предметов)
        # - moment_of_inertia: MOMENT_INF предотвращает вращение
        # - max_horizontal_velocity: ограничение горизонтальной скорости
        # - max_vertical_velocity: ограничение вертикальной скорости
        self.physics_engine.add_sprite(
            self.player,
            friction=PLAYER_FRICTION,
            mass=PLAYER_MASS,
            moment_of_inertia=arcade.PymunkPhysicsEngine.MOMENT_INF,
            damping=PLAYER_DAMPING,
            collision_type="player",
            max_horizontal_velocity=PLAYER_MAX_HORIZONTAL_SPEED,
            max_vertical_velocity=PLAYER_MAX_VERTICAL_SPEED,
            elasticity=0.0,  # Убираем упругость для предотвращения подпрыгивания
        )
        
        # Добавляем стены (статические тела - не двигаются)
        # Разделяем на обычные, скользкие, хрупкие и разбиваемые
        normal_walls = arcade.SpriteList()
        slippery_walls = arcade.SpriteList()
        fragile_walls = arcade.SpriteList()
        breakable_walls = arcade.SpriteList()
        
        for wall in walls:
            # Проверяем свойства платформы
            is_slippery = wall.properties.get("is_slippery", False) if hasattr(wall, 'properties') else False
            is_fragile = wall.properties.get("is_fragile", False) if hasattr(wall, 'properties') else False
            is_broken = wall.properties.get("is_broken", False) if hasattr(wall, 'properties') else False
            
            if is_slippery:
                slippery_walls.append(wall)
            elif is_fragile:
                fragile_walls.append(wall)
            elif is_broken:
                breakable_walls.append(wall)
            else:
                normal_walls.append(wall)
        
        # Добавляем обычные стены
        if len(normal_walls) > 0:
            self.physics_engine.add_sprite_list(
                normal_walls,
                friction=WALL_FRICTION,
                collision_type="wall",
                body_type=arcade.PymunkPhysicsEngine.STATIC,
                elasticity=0.0,
            )
        
        # Добавляем скользкие платформы (низкое трение)
        if len(slippery_walls) > 0:
            self.physics_engine.add_sprite_list(
                slippery_walls,
                friction=0.1,  # Очень низкое трение
                collision_type="slippery",
                body_type=arcade.PymunkPhysicsEngine.STATIC,
                elasticity=0.0,
            )
        
        # Добавляем хрупкие платформы
        if len(fragile_walls) > 0:
            self.physics_engine.add_sprite_list(
                fragile_walls,
                friction=WALL_FRICTION,
                collision_type="fragile",
                body_type=arcade.PymunkPhysicsEngine.STATIC,
                elasticity=0.0,
            )
        
        # Добавляем разбиваемые блоки
        if len(breakable_walls) > 0:
            self.physics_engine.add_sprite_list(
                breakable_walls,
                friction=WALL_FRICTION,
                collision_type="breakable",
                body_type=arcade.PymunkPhysicsEngine.STATIC,
                elasticity=0.0,
            )
        
        # Добавляем движущиеся платформы (kinematic bodies - двигаются, но не реагируют на силы)
        if LAYER_MOVING_PLATFORMS in self.scene:
            moving_platforms = self.scene.get_sprite_list(LAYER_MOVING_PLATFORMS)
            self.physics_engine.add_sprite_list(
                moving_platforms,
                friction=WALL_FRICTION,
                collision_type="moving_platform",
                body_type=arcade.PymunkPhysicsEngine.KINEMATIC,
                elasticity=0.0,
            )
        
        # Добавляем one-way платформы (статические, но с особой логикой коллизий)
        if LAYER_ONE_WAY_PLATFORMS in self.scene:
            oneway_platforms = self.scene.get_sprite_list(LAYER_ONE_WAY_PLATFORMS)
            self.physics_engine.add_sprite_list(
                oneway_platforms,
                friction=WALL_FRICTION,
                collision_type="oneway",
                body_type=arcade.PymunkPhysicsEngine.STATIC,
                elasticity=0.0,
            )
        
        # Добавляем врагов в pymunk (динамические тела с небольшой массой)
        if len(self.enemy_list) > 0:
            self.physics_engine.add_sprite_list(
                self.enemy_list,
                friction=0.1,
                mass=0.5,
                moment_of_inertia=arcade.PymunkPhysicsEngine.MOMENT_INF,
                collision_type="enemy",
                elasticity=0.0,
            )
        
        # Настройка collision handlers
        self._setup_oneway_collision_handler()
        self._setup_fragile_collision_handler()
        self._setup_breakable_collision_handler()
        self._setup_enemy_collision_handler()
        
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

        # Определяем порядок отрисовки слоев (от заднего к переднему)
        # BackImage должен быть первым (задний фон)
        layer_order = []
        
        # Сначала фоновые слои
        if "BackImage" in self.scene._name_mapping:
            layer_order.append("BackImage")
        if LAYER_BACKGROUND in self.scene._name_mapping:
            layer_order.append(LAYER_BACKGROUND)
        
        # Затем все остальные слои в порядке их добавления
        for layer_name in self.scene._name_mapping:
            if layer_name not in layer_order:
                layer_order.append(layer_name)
        
        # Рисуем каждый слой с учетом parallax в правильном порядке
        for layer_name in layer_order:
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
        # Обновление подвижных платформ (pymunk kinematic)
        if LAYER_MOVING_PLATFORMS in self.scene:
            for platform in self.scene.get_sprite_list(LAYER_MOVING_PLATFORMS):
                # Проверяем границы и разворачиваем направление
                if hasattr(platform, 'boundary_right') and platform.boundary_right:
                    if platform.change_x > 0 and platform.right > platform.boundary_right:
                        platform.change_x *= -1
                
                if hasattr(platform, 'boundary_left') and platform.boundary_left:
                    if platform.change_x < 0 and platform.left < platform.boundary_left:
                        platform.change_x *= -1
                
                if hasattr(platform, 'boundary_top') and platform.boundary_top:
                    if platform.change_y > 0 and platform.top > platform.boundary_top:
                        platform.change_y *= -1
                
                if hasattr(platform, 'boundary_bottom') and platform.boundary_bottom:
                    if platform.change_y < 0 and platform.bottom < platform.boundary_bottom:
                        platform.change_y *= -1
                
                # Устанавливаем velocity через pymunk body
                # change_x/change_y в пикселях/кадр, velocity в пикселях/секунду
                # Предполагаем 60 FPS, но используем delta_time для точности
                velocity_x = platform.change_x / delta_time if delta_time > 0 else 0
                velocity_y = platform.change_y / delta_time if delta_time > 0 else 0
                
                # Получаем pymunk объект и устанавливаем velocity
                physics_obj = self.physics_engine.get_physics_object(platform)
                if physics_obj:
                    physics_obj.body.velocity = (velocity_x, velocity_y)
        
        # --- Система трех режимов движения ---
        # Обновляем таймеры удержания клавиш
        if self.left_pressed:
            self.left_press_time += delta_time
        if self.right_pressed:
            self.right_press_time += delta_time
        
        # Обновляем таймер режима бега
        if self.run_mode_timer > 0:
            self.run_mode_timer -= delta_time
            if self.run_mode_timer <= 0:
                self.run_mode_left = False
                self.run_mode_right = False
        
        # --- Управление движением через pymunk ---
        is_on_ground = self.physics_engine.is_on_ground(self.player)
        
        # Применяем силы движения влево/вправо
        if self.left_pressed and not self.right_pressed:
            # Определяем силу движения влево на основе режима
            if is_on_ground:
                if self.run_mode_left and self.left_press_time >= MOVE_SLOW_THRESHOLD:
                    # Бег (двойное нажатие + длинное зажатие)
                    move_force = PLAYER_MOVE_FORCE_RUN
                elif self.left_press_time < MOVE_SLOW_THRESHOLD:
                    # Тап (короткое нажатие <150мс) - 2 пикселя
                    move_force = PLAYER_MOVE_FORCE_SLOW
                else:
                    # Ходьба (долгое нажатие без двойного тапа)
                    move_force = PLAYER_MOVE_FORCE_NORMAL
                force = (-move_force, 0)
            else:
                force = (-PLAYER_MOVE_FORCE_IN_AIR, 0)
            self.physics_engine.apply_force(self.player, force)
            # Убираем трение при движении
            self.physics_engine.set_friction(self.player, 0)
        elif self.right_pressed and not self.left_pressed:
            # Определяем силу движения вправо на основе режима
            if is_on_ground:
                if self.run_mode_right and self.right_press_time >= MOVE_SLOW_THRESHOLD:
                    # Бег (двойное нажатие + длинное зажатие)
                    move_force = PLAYER_MOVE_FORCE_RUN
                elif self.right_press_time < MOVE_SLOW_THRESHOLD:
                    # Тап (короткое нажатие <150мс) - 2 пикселя
                    move_force = PLAYER_MOVE_FORCE_SLOW
                else:
                    # Ходьба (долгое нажатие без двойного тапа)
                    move_force = PLAYER_MOVE_FORCE_NORMAL
                force = (move_force, 0)
            else:
                force = (PLAYER_MOVE_FORCE_IN_AIR, 0)
            self.physics_engine.apply_force(self.player, force)
            # Убираем трение при движении
            self.physics_engine.set_friction(self.player, 0)
        else:
            # Игрок не движется - добавляем трение для остановки
            self.physics_engine.set_friction(self.player, 1.0)
        
        # Сохраняем состояние игрока ДО physics update (для старых механик)
        player_velocity_before = self.player.change_y
        player_bottom_before = self.player.bottom
        player_falling = self.player.change_y < 0
        
        # Физический движок (ОДИН раз!)
        self.physics_engine.step()
        
        # Проверка: может ли игрок прыгать (pymunk использует is_on_ground)
        self.player.can_jump = self.physics_engine.is_on_ground(self.player)
        
        # Обработка хрупких платформ
        fragile_to_remove = []
        for fragile_platform, timer in self.fragile_timers.items():
            # Увеличиваем таймер
            self.fragile_timers[fragile_platform] += delta_time
            
            # Если прошло достаточно времени, удаляем платформу
            if self.fragile_timers[fragile_platform] >= FRAGILE_BREAK_DELAY:
                fragile_platform.remove_from_sprite_lists()
                # Проверяем, что спрайт еще в physics_engine перед удалением
                if fragile_platform in self.physics_engine.sprites:
                    self.physics_engine.remove_sprite(fragile_platform)
                fragile_to_remove.append(fragile_platform)
        
        # Удаляем из словаря таймеров
        for platform in fragile_to_remove:
            del self.fragile_timers[platform]
        
        # Сброс флага разбитого блока когда игрок не прыгает вверх
        player_physics_obj = self.physics_engine.get_physics_object(self.player)
        if player_physics_obj and player_physics_obj.body.velocity.y <= 0:
            self.block_broken_this_jump = False
        
        # ВРЕМЕННО ОТКЛЮЧЕНО: One-way платформы
        # TODO: Портировать на pymunk
        if False and LAYER_ONE_WAY_PLATFORMS in self.scene:
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
        
        # ВРЕМЕННО ОТКЛЮЧЕНО: Разбиваемые блоки
        # TODO: Портировать на pymunk
        if False:
            # Сбрасываем флаг разбитого блока когда игрок не прыгает вверх
            if self.player.change_y <= 0:
                self.block_broken_this_jump = False
        
        # Разбиваемые блоки: если игрок прыгал вверх, но скорость стала ≤0 - ударился головой
        if False and LAYER_PLATFORMS in self.scene and player_velocity_before > 0 and self.player.change_y <= 0:
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
        
        # Проверка падения за пределы карты
        if self.player.center_y < -100:
            # Игрок упал за пределы карты - респавн на стартовой позиции
            player_physics = self.physics_engine.get_physics_object(self.player)
            if player_physics:
                player_physics.body.position = (self.spawn_x, self.spawn_y)
                player_physics.body.velocity = (0, 0)
            self.player.center_x = self.spawn_x
            self.player.center_y = self.spawn_y
        
        # Обновление врагов - патрулирование и анимация
        
        for i, enemy in enumerate(self.enemy_list):
            # Проверяем границы патрулирования и меняем направление при необходимости
            enemy.check_patrol_bounds()
            
            # Применяем силу движения к врагу через pymunk
            force = (enemy.direction * enemy.move_force, 0)
            self.physics_engine.apply_force(enemy, force)
            
            # Проверяем упирается ли враг в препятствие и подпрыгиваем
            enemy_physics = self.physics_engine.get_physics_object(enemy)
            if enemy_physics and self.physics_engine.is_on_ground(enemy):
                # Если горизонтальная скорость < 10, враг упирается в стену
                if abs(enemy_physics.body.velocity.x) < 10:
                    enemy_physics.body.apply_impulse_at_local_point((0, 400))
            
            # Обновляем анимацию ходьбы
            enemy.update_animation(delta_time)
        
        self.scene.update_animation(delta_time)
        
        # Обновление DevPanel (tkinter)
        if DEV_MODE and self.dev_panel:
            self.dev_panel.update()

        # ВРЕМЕННО ОТКЛЮЧЕНО: Специальные платформы (лед, хрупкие)
        # TODO: Портировать на pymunk
        # self._process_special_platforms(delta_time)

        # ВРЕМЕННО ОТКЛЮЧЕНО: Логика льда
        # TODO: Портировать на pymunk через изменение friction
        # if self.on_ice and self.player.can_jump:
        #     if self.left_pressed:
        #         self.player.change_x = max(-PLAYER_MOVE_SPEED, self.player.change_x - ICE_ACCELERATION)
        #     elif self.right_pressed:
        #         self.player.change_x = min(PLAYER_MOVE_SPEED, self.player.change_x + ICE_ACCELERATION)
        #     else:
        #         if self.player.change_x > 0:
        #             self.player.change_x = max(0, self.player.change_x - ICE_DECELERATION)
        #         elif self.player.change_x < 0:
        #             self.player.change_x = min(0, self.player.change_x + ICE_DECELERATION)

        # Коллизии с врагами обрабатываются через pymunk collision handler

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

    def _load_image_layers(self):
        """Загрузка image layers (фоновые изображения) из Tiled карты."""
        if not self.tile_map or not self.tile_map.tiled_map:
            return
        
        # Получаем размеры карты
        map_width = self.tile_map.width * self.tile_map.tile_width
        map_height = self.tile_map.height * self.tile_map.tile_height
        
        # Проходим по всем слоям в Tiled карте
        for layer in self.tile_map.tiled_map.layers:
            # Проверяем, является ли слой ImageLayer
            if hasattr(layer, 'image') and layer.image:
                layer_name = layer.name
                
                # Получаем путь к изображению (layer.image уже PosixPath)
                image_path = layer.image
                full_image_path = (MAPS_PATH / image_path).resolve()
                
                # Получаем параметры повторения из Tiled (repeat_x, repeat_y)
                repeatx = bool(getattr(layer, 'repeat_x', False))
                repeaty = bool(getattr(layer, 'repeat_y', False))
                
                # Получаем parallax из Tiled
                # parallax=1.0 означает что фон движется синхронно с камерой (как часть мира)
                parallax_factor = getattr(layer, 'parallax_factor', None)
                if parallax_factor:
                    parallax_x = parallax_factor.x if hasattr(parallax_factor, 'x') else 1.0
                    parallax_y = parallax_factor.y if hasattr(parallax_factor, 'y') else 1.0
                else:
                    parallax_x = 1.0
                    parallax_y = 1.0
                
                # Создаем SpriteList для фона
                background_list = arcade.SpriteList()
                
                # Загружаем базовый спрайт чтобы узнать размеры
                base_sprite = arcade.Sprite(str(full_image_path))
                img_width = base_sprite.width
                img_height = base_sprite.height
                
                if repeatx or repeaty:
                    # Если нужно повторение, создаем несколько копий
                    # Покрываем область включая левую сторону (отрицательные координаты)
                    
                    # Определяем диапазон для X (включая левую сторону)
                    if repeatx:
                        # Начинаем с -2 копий слева от 0, покрываем карту и добавляем 2 копии справа
                        start_x = -2
                        tiles_x = int(map_width / img_width) + 5
                    else:
                        start_x = 0
                        tiles_x = 1
                    
                    # Определяем диапазон для Y - всегда покрываем всю высоту карты
                    if repeaty:
                        start_y = -2
                        tiles_y = int(map_height / img_height) + 5
                    else:
                        # Даже если repeat_y=False, повторяем чтобы покрыть всю высоту карты
                        start_y = 0
                        tiles_y = int(map_height / img_height) + 2
                    
                    # Создаем сетку из спрайтов
                    for ty in range(start_y, start_y + tiles_y):
                        for tx in range(start_x, start_x + tiles_x):
                            bg_sprite = arcade.Sprite(str(full_image_path))
                            
                            # Позиционируем с учетом отрицательных индексов
                            bg_sprite.left = tx * img_width
                            bg_sprite.bottom = ty * img_height
                            
                            background_list.append(bg_sprite)
                else:
                    # Одиночный фон без повторения - масштабируем на всю высоту карты
                    background_sprite = arcade.Sprite(str(full_image_path))
                    
                    # Масштабируем чтобы покрыть всю высоту карты
                    scale_y = map_height / background_sprite.height
                    background_sprite.scale = scale_y
                    
                    # Позиционируем снизу слева
                    background_sprite.left = 0
                    background_sprite.bottom = 0
                    
                    background_list.append(background_sprite)
                
                # Добавляем в scene
                self.scene.add_sprite_list(layer_name, sprite_list=background_list)
                
                # Устанавливаем parallax из настроек Tiled
                self.parallax_factors[layer_name] = (parallax_x, parallax_y)
    
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
    
    def _setup_oneway_collision_handler(self):
        """Настроить collision handler для one-way платформ."""
        
        def oneway_collision_handler(sprite_a, sprite_b, arbiter, space, data):
            """
            Callback для проверки коллизии с one-way платформой.
            Разрешает коллизию только если игрок падает сверху.
            
            Args:
                sprite_a: Спрайт игрока
                sprite_b: Спрайт платформы
                arbiter: Объект коллизии pymunk
                space: Pymunk space
                data: Дополнительные данные
            
            Returns:
                True - разрешить коллизию (игрок приземляется)
                False - игнорировать коллизию (игрок проходит сквозь)
            """
            # Получаем pymunk объект игрока
            player_physics_obj = self.physics_engine.get_physics_object(sprite_a)
            if not player_physics_obj:
                return True  # Если нет объекта, разрешаем коллизию по умолчанию
            
            player_body = player_physics_obj.body
            
            # Проверяем вертикальную скорость игрока
            player_velocity_y = player_body.velocity.y
            
            # Проверяем позицию игрока относительно платформы
            player_bottom = sprite_a.bottom
            platform_top = sprite_b.top
            
            # Если игрок движется вверх (прыгает) → игнорировать коллизию
            # (позволяет прыгать сквозь платформу снизу)
            if player_velocity_y > 10:  # Явно прыгает вверх
                return False
            
            # Если игрок НАД платформой (или почти касается сверху) → разрешить коллизию
            # Это работает как при падении, так и при стоянии/движении по платформе
            if player_bottom >= platform_top - 5:
                return True
            
            # Игрок под платформой или внутри неё → игнорировать коллизию
            return False
        
        # Создаем handler для коллизий между игроком ("player") и one-way платформами ("oneway")
        # PymunkPhysicsEngine.add_collision_handler принимает строковые collision_type
        self.physics_engine.add_collision_handler(
            "player",
            "oneway",
            begin_handler=oneway_collision_handler
        )
    
    def _setup_fragile_collision_handler(self):
        """Настроить collision handler для хрупких платформ."""
        
        def fragile_collision_handler(sprite_a, sprite_b, arbiter, space, data):
            """
            Callback для хрупких платформ.
            Запускает таймер при наступании на платформу.
            """
            # sprite_a - игрок, sprite_b - хрупкая платформа
            
            # Проверяем, что игрок падает сверху (аналогично one-way)
            player_physics_obj = self.physics_engine.get_physics_object(sprite_a)
            if not player_physics_obj:
                return True
            
            # Если игрок уже на платформе и она еще не в таймерах, добавляем таймер
            if sprite_b not in self.fragile_timers:
                self.fragile_timers[sprite_b] = 0.0
            
            return True  # Разрешаем коллизию
        
        # Регистрируем handler
        self.physics_engine.add_collision_handler(
            "player",
            "fragile",
            begin_handler=fragile_collision_handler
        )
    
    def _setup_breakable_collision_handler(self):
        """Настроить collision handler для разбиваемых блоков."""
        
        def breakable_collision_handler(sprite_a, sprite_b, arbiter, space, data):
            """
            Callback для разбиваемых блоков.
            Разбивает блок при ударе головой снизу.
            """
            # sprite_a - игрок, sprite_b - разбиваемый блок
            
            # Получаем pymunk объект игрока
            player_physics_obj = self.physics_engine.get_physics_object(sprite_a)
            if not player_physics_obj:
                return True
            
            player_body = player_physics_obj.body
            
            # Проверяем, что игрок движется вверх (прыгает)
            if player_body.velocity.y > 0:
                # Проверяем, что игрок ударяется головой (снизу)
                if sprite_a.top < sprite_b.bottom + 10:
                    # Разбиваем блок только если не разбили в этом прыжке
                    if not self.block_broken_this_jump:
                        # Удаляем блок из scene и physics engine
                        sprite_b.remove_from_sprite_lists()
                        # Проверяем, что спрайт еще в physics_engine перед удалением
                        if sprite_b in self.physics_engine.sprites:
                            self.physics_engine.remove_sprite(sprite_b)
                        self.block_broken_this_jump = True
                        # Гасим вертикальную скорость игрока (эффект удара)
                        player_body.velocity = (player_body.velocity[0], 0)
                        return False  # Прерываем коллизию
            
            return True  # Обычная коллизия
        
        # Регистрируем handler
        self.physics_engine.add_collision_handler(
            "player",
            "breakable",
            begin_handler=breakable_collision_handler
        )
    
    def _setup_enemy_collision_handler(self):
        """Настроить collision handler для врагов."""
        
        def enemy_collision_handler(player_sprite, enemy_sprite, arbiter, space, data):
            """
            Callback для коллизий игрока с врагом.
            При столкновении игрок респавнится на стартовой позиции.
            """
            # Получаем pymunk объект игрока
            player_physics_obj = self.physics_engine.get_physics_object(player_sprite)
            if player_physics_obj:
                # Телепортируем через pymunk body (это правильный способ)
                player_physics_obj.body.position = (self.spawn_x, self.spawn_y)
                player_physics_obj.body.velocity = (0, 0)
            
            # Также обновляем позицию спрайта (для синхронизации)
            player_sprite.center_x = self.spawn_x
            player_sprite.center_y = self.spawn_y
            
            return True  # Продолжаем коллизию
        
        # Регистрируем handler
        self.physics_engine.add_collision_handler(
            "player",
            "enemy",
            begin_handler=enemy_collision_handler
        )
    
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
        """Плавное следование камеры за игроком с ограничением границами карты."""
        target_x = self.player.center_x
        target_y = self.player.center_y

        # Вычисляем новую позицию камеры с плавным следованием
        new_camera_x = arcade.math.lerp(self.camera.position[0], target_x, 0.1)
        new_camera_y = arcade.math.lerp(self.camera.position[1], target_y, 0.1)
        
        # Получаем размеры карты
        if self.tile_map:
            map_width = self.tile_map.width * self.tile_map.tile_width
            map_height = self.tile_map.height * self.tile_map.tile_height
        else:
            # Если нет карты, используем значения по умолчанию
            map_width = 2560
            map_height = 1600
        
        # Ограничиваем камеру границами карты
        # Камера не может выйти за пределы так, чтобы показать пустое пространство
        half_width = self.camera.viewport_width / 3
        half_height = self.camera.viewport_height / 2
        
        # Ограничение по X
        camera_left = half_width
        camera_right = map_width - half_width
        new_camera_x = max(camera_left, min(new_camera_x, camera_right))
        
        # Ограничение по Y
        camera_bottom = half_height
        camera_top = map_height - half_height
        new_camera_y = max(camera_bottom, min(new_camera_y, camera_top))
        
        self.camera.position = (new_camera_x, new_camera_y)

    def on_key_press(self, key: int, modifiers: int):
        """Нажатие клавиши."""
        if key in (arcade.key.UP, arcade.key.W, arcade.key.SPACE):
            # Прыжок через pymunk impulse с учетом режима движения
            if self.physics_engine.is_on_ground(self.player):
                # Определяем импульс на основе режима движения
                if self.run_mode_left or self.run_mode_right:
                    # Бег - больший импульс
                    jump_impulse = PLAYER_JUMP_IMPULSE_RUN
                elif self.left_pressed or self.right_pressed:
                    # Ходьба - средний импульс
                    jump_impulse = PLAYER_JUMP_IMPULSE_WALK
                else:
                    # Стоя - базовый импульс
                    jump_impulse = PLAYER_JUMP_IMPULSE
                
                impulse = (0, jump_impulse)
                self.physics_engine.apply_impulse(self.player, impulse)
                # Устанавливаем флаг прыжка и время начала
                self.is_jumping = True
                self.jump_release_time = time.time()
        elif key in (arcade.key.LEFT, arcade.key.A):
            current_time = time.time()
            
            # Проверяем двойное нажатие влево
            if current_time - self.last_left_tap_time < DOUBLE_TAP_THRESHOLD:
                self.run_mode_left = True
                self.run_mode_right = False
                self.run_mode_timer = RUN_MODE_DURATION
            
            self.last_left_tap_time = current_time
            self.left_pressed = True
            self.left_press_time = 0.0  # Сбрасываем таймер удержания
            
        elif key in (arcade.key.RIGHT, arcade.key.D):
            current_time = time.time()
            
            # Проверяем двойное нажатие вправо
            if current_time - self.last_right_tap_time < DOUBLE_TAP_THRESHOLD:
                self.run_mode_right = True
                self.run_mode_left = False
                self.run_mode_timer = RUN_MODE_DURATION
            
            self.last_right_tap_time = current_time
            self.right_pressed = True
            self.right_press_time = 0.0  # Сбрасываем таймер удержания
            
        elif key == arcade.key.ESCAPE:
            from src.views.menu_view import MenuView
            menu = MenuView()
            self.window.show_view(menu)

    def on_key_release(self, key: int, modifiers: int):
        """Отпускание клавиши."""
        if key in (arcade.key.UP, arcade.key.W, arcade.key.SPACE):
            # Переменная высота прыжка с временным окном
            if self.is_jumping:
                # Проверяем, быстро ли отпустили кнопку
                time_since_jump = time.time() - self.jump_release_time
                if time_since_jump < JUMP_CUTOFF_TIME:
                    # Гасим вертикальную скорость напрямую через pymunk body
                    physics_obj = self.physics_engine.get_physics_object(self.player)
                    current_velocity = physics_obj.body.velocity
                    new_velocity = (current_velocity[0], current_velocity[1] * JUMP_CUTOFF_MULTIPLIER)
                    physics_obj.body.velocity = new_velocity
                
                self.is_jumping = False
        elif key in (arcade.key.LEFT, arcade.key.A):
            self.left_pressed = False
            self.left_press_time = 0.0
        elif key in (arcade.key.RIGHT, arcade.key.D):
            self.right_pressed = False
            self.right_press_time = 0.0

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
    
    def apply_pymunk_settings(self, force_tap, force_walk, force_run, 
                             jump_stand, jump_walk, jump_run,
                             tap_threshold, doubletap_threshold, gravity):
        """Применить параметры pymunk к игре в реальном времени."""
        # Обновляем модуль constants для использования в коде
        import src.constants as constants
        constants.PLAYER_MOVE_FORCE_SLOW = force_tap
        constants.PLAYER_MOVE_FORCE_NORMAL = force_walk
        constants.PLAYER_MOVE_FORCE_RUN = force_run
        constants.PLAYER_JUMP_IMPULSE = jump_stand
        constants.PLAYER_JUMP_IMPULSE_WALK = jump_walk
        constants.PLAYER_JUMP_IMPULSE_RUN = jump_run
        constants.MOVE_SLOW_THRESHOLD = tap_threshold
        constants.DOUBLE_TAP_THRESHOLD = doubletap_threshold
        constants.GRAVITY = gravity
        
        # Обновляем гравитацию в physics engine
        if hasattr(self, 'physics_engine') and self.physics_engine:
            self.physics_engine.space.gravity = (0, -gravity)
        
        # Обновляем текущие значения для сохранения
        self.current_gravity = gravity
        self.current_force_tap = force_tap
        self.current_force_walk = force_walk
        self.current_force_run = force_run
        self.current_jump_stand = jump_stand
        self.current_jump_walk = jump_walk
        self.current_jump_run = jump_run
        self.current_tap_threshold = tap_threshold
        self.current_doubletap_threshold = doubletap_threshold
    
    def apply_camera_settings(self, camera_zoom):
        """Применить настройки камеры к игре в реальном времени."""
        import src.constants as constants
        constants.CAMERA_ZOOM = camera_zoom
        
        # Применяем zoom к камере
        if self.camera:
            self.camera.zoom = camera_zoom
        
        # Сохраняем текущее значение
        self.current_camera_zoom = camera_zoom
    
    def apply_enemy_settings(self, enemy_scale):
        """Применить настройки врагов к игре в реальном времени."""
        import src.constants as constants
        constants.ENEMY_SCALING = enemy_scale

        # Обновляем масштаб всех врагов
        for enemy in self.enemy_list:
            enemy.scale = enemy_scale

        # Сохраняем текущее значение
        self.current_enemy_scale = enemy_scale

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
                elif line.startswith("PLAYER_MOVE_FORCE_SLOW = "):
                    lines[i] = f"PLAYER_MOVE_FORCE_SLOW = {int(self.current_force_tap)}\n"
                elif line.startswith("PLAYER_MOVE_FORCE_NORMAL = "):
                    lines[i] = f"PLAYER_MOVE_FORCE_NORMAL = {int(self.current_force_walk)}\n"
                elif line.startswith("PLAYER_MOVE_FORCE_RUN = "):
                    lines[i] = f"PLAYER_MOVE_FORCE_RUN = {int(self.current_force_run)}\n"
                elif line.startswith("PLAYER_JUMP_IMPULSE = "):
                    lines[i] = f"PLAYER_JUMP_IMPULSE = {int(self.current_jump_stand)}\n"
                elif line.startswith("PLAYER_JUMP_IMPULSE_WALK = "):
                    lines[i] = f"PLAYER_JUMP_IMPULSE_WALK = {int(self.current_jump_walk)}\n"
                elif line.startswith("PLAYER_JUMP_IMPULSE_RUN = "):
                    lines[i] = f"PLAYER_JUMP_IMPULSE_RUN = {int(self.current_jump_run)}\n"
                elif line.startswith("MOVE_SLOW_THRESHOLD = "):
                    lines[i] = f"MOVE_SLOW_THRESHOLD = {self.current_tap_threshold:.2f}\n"
                elif line.startswith("DOUBLE_TAP_THRESHOLD = "):
                    lines[i] = f"DOUBLE_TAP_THRESHOLD = {self.current_doubletap_threshold:.2f}\n"
                elif line.startswith("PLAYER_MOVE_SPEED = "):
                    lines[i] = f"PLAYER_MOVE_SPEED = {int(self.current_move_speed)}\n"
                elif line.startswith("PLAYER_JUMP_SPEED = "):
                    lines[i] = f"PLAYER_JUMP_SPEED = {int(self.current_jump_speed)}\n"
                elif line.startswith("PLAYER_SCALING = "):
                    lines[i] = f"PLAYER_SCALING = {self.current_player_scaling:.2f}\n"
                elif line.startswith("CAMERA_ZOOM = "):
                    lines[i] = f"CAMERA_ZOOM = {self.current_camera_zoom:.2f}\n"
                elif line.startswith("ENEMY_SCALING = "):
                    lines[i] = f"ENEMY_SCALING = {self.current_enemy_scale:.2f}\n"
            
            with open(constants_path, "w", encoding="utf-8") as f:
                f.writelines(lines)
            
            print(f"Параметры сохранены в {constants_path}")
        except Exception as e:
            print(f"Ошибка сохранения: {e}")
