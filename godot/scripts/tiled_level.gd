extends Node2D
## Уровень из Tiled (YATI): коллизии строятся по занятым ячейкам Platforms,
## игрок ставится на PlayerSpawn, враги — по маркерам Enemies.

const MAP_PATH := "res://assets/maps/level1.tmx"
const ENEMY_SCENE := preload("res://scenes/enemy_rat.tscn")
const COIN_SCENE := preload("res://scenes/coin.tscn")
const MOVING_PLATFORM_SCRIPT := preload("res://scripts/moving_platform.gd")

@export var map_path := MAP_PATH

@onready var player: CharacterBody2D = $Player
@onready var hud: GameHud = $HUD

var _spawn := Vector2.ZERO
var _kill_y := 99999.0
var _invuln := 0.0
var _platforms_layer: TileMapLayer
var _fragile_timers := {}


func _ready() -> void:
	_build_map()
	player.setup_platform_layer(_platforms_layer)
	player.floor_started.connect(_on_player_floor)
	player.breakable_hit.connect(_on_breakable_hit)
	player.died.connect(_on_death)
	_respawn()


func _physics_process(delta: float) -> void:
	if _invuln > 0.0:
		_invuln -= delta
	_process_fragile(delta)
	if player.global_position.y > _kill_y:
		_respawn()


func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("restart"):
		get_tree().reload_current_scene()
	elif event is InputEventKey and event.pressed and not event.echo and event.keycode == KEY_ESCAPE:
		get_tree().change_scene_to_file("res://scenes/menu.tscn")


func _build_map() -> void:
	if not ResourceLoader.exists(map_path):
		_build_fallback()
		return

	var map: Node2D = (load(map_path) as PackedScene).instantiate()
	add_child(map)
	move_child(map, 0)

	var platforms := map.find_child("Platforms", true, false) as TileMapLayer
	var oneway := map.find_child("OneWayPlatforms", true, false) as TileMapLayer
	_platforms_layer = platforms
	if platforms:
		var groups := _classify_platform_cells(platforms)
		_build_static(groups["normal"], false)
		_build_static(groups["slippery"], false, GameConfig.LAYER_SLIPPERY)
		_build_cells(groups["fragile"], GameConfig.LAYER_FRAGILE, "fragile")
		_build_cells(groups["breakable"], GameConfig.LAYER_BREAKABLE, "breakable")
	if oneway:
		_build_static(oneway.get_used_cells(), true)

	var size := _map_size(map, platforms)
	_kill_y = size.y + 200.0
	_place_camera(size)

	var spawn_parent := map.find_child("PlayerSpawn", true, false)
	if spawn_parent:
		var marker := spawn_parent.find_child("PlayerSpawn", true, false) as Marker2D
		if marker:
			_spawn = marker.global_position
	_spawn_enemies(map)
	_spawn_moving_platforms(map)
	_spawn_coins(map)


## Запасной уровень без Tiled: земля, две платформы и три монеты.
func _build_fallback() -> void:
	_spawn = Vector2(120, 300)
	_kill_y = 800.0
	_place_camera(Vector2(GameConfig.VIEWPORT_W, GameConfig.VIEWPORT_H))

	_add_fallback_solid(Vector2(640, 420), Vector2(1280, 40), Color(0.3, 0.45, 0.3))
	_add_fallback_solid(Vector2(420, 320), Vector2(240, 24), Color(0.45, 0.35, 0.25))
	_add_fallback_solid(Vector2(820, 260), Vector2(200, 24), Color(0.45, 0.35, 0.25))

	var coin_texture := _fallback_coin_texture()
	var coin_positions: Array[Vector2] = [
		Vector2(360, 280), Vector2(420, 280), Vector2(480, 280)]
	for pos in coin_positions:
		_add_coin(pos, coin_texture)


func _add_fallback_solid(center: Vector2, size: Vector2, color: Color) -> void:
	var body := StaticBody2D.new()
	body.collision_layer = GameConfig.LAYER_SOLID
	body.collision_mask = 0
	body.position = center

	var shape := RectangleShape2D.new()
	shape.size = size
	var cs := CollisionShape2D.new()
	cs.shape = shape
	body.add_child(cs)

	var visual := ColorRect.new()
	visual.color = color
	visual.size = size
	visual.position = -size / 2.0
	visual.mouse_filter = Control.MOUSE_FILTER_IGNORE
	body.add_child(visual)
	add_child(body)


func _fallback_coin_texture() -> Texture2D:
	var img := Image.create(12, 12, false, Image.FORMAT_RGBA8)
	img.fill(Color(1.0, 0.84, 0.2))
	return ImageTexture.create_from_image(img)


func _map_size(map: Node2D, platforms: TileMapLayer) -> Vector2:
	var bg := map.find_child("Background Color", true, false) as ColorRect
	if bg:
		return Vector2(bg.offset_right, bg.offset_bottom)
	if platforms:
		var r := platforms.get_used_rect()
		return Vector2(r.size) * GameConfig.TILE
	return Vector2(GameConfig.LEVEL_W, GameConfig.LEVEL_H)


func _place_camera(size: Vector2) -> void:
	var cam := player.get_node("Camera2D") as Camera2D
	if cam == null:
		return
	cam.limit_left = 0
	cam.limit_top = 0
	cam.limit_right = int(size.x)
	cam.limit_bottom = int(size.y)


func _spawn_enemies(map: Node2D) -> void:
	var markers := map.find_child("Enemies", true, false)
	if markers == null:
		return
	for marker in markers.get_children():
		if marker is Marker2D:
			var enemy := ENEMY_SCENE.instantiate() as RatEnemy
			enemy.position = marker.global_position
			enemy.patrol_range = float(marker.get_meta(
				"patrol_range", GameConfig.ENEMY_PATROL_RANGE))
			var force := float(marker.get_meta(
				"move_force", GameConfig.ENEMY_MOVE_FORCE))
			enemy.speed = force * GameConfig.ENEMY_FORCE_TO_SPEED
			add_child(enemy)


func _spawn_coins(map: Node2D) -> void:
	var layer := map.find_child("Coins", true, false) as TileMapLayer
	if layer == null:
		return
	for cell in layer.get_used_cells():
		var texture := _cell_texture(layer, cell)
		_add_coin(layer.to_global(layer.map_to_local(cell)), texture)
		layer.erase_cell(cell)


func _cell_texture(layer: TileMapLayer, cell: Vector2i) -> Texture2D:
	var source_id := layer.get_cell_source_id(cell)
	if source_id < 0 or layer.tile_set == null:
		return null
	var source := layer.tile_set.get_source(source_id) as TileSetAtlasSource
	if source == null or source.texture == null:
		return null
	var coords := layer.get_cell_atlas_coords(cell)
	if not source.has_tile(coords):
		return null
	var atlas := AtlasTexture.new()
	atlas.atlas = source.texture
	atlas.region = Rect2(source.get_tile_texture_region(coords))
	return atlas


func _add_coin(world_position: Vector2, texture: Texture2D) -> Coin:
	var coin := COIN_SCENE.instantiate() as Coin
	add_child(coin)
	coin.global_position = world_position
	if texture != null:
		(coin.get_node("Sprite") as Sprite2D).texture = texture
	coin.collected.connect(_on_coin_collected)
	return coin


func _on_coin_collected() -> void:
	hud.add_score(1)


## Делит ячейки Platforms по свойствам тайла; приоритет как в оригинале:
## slippery → fragile → breakable → normal.
func _classify_platform_cells(layer: TileMapLayer) -> Dictionary:
	var groups := {}
	for kind in ["normal", "slippery", "fragile", "breakable"]:
		groups[kind] = []
	for cell in layer.get_used_cells():
		var data := layer.get_cell_tile_data(cell)
		var kind := "normal"
		if data != null:
			if bool(data.get_meta("is_slippery", false)):
				kind = "slippery"
			elif bool(data.get_meta("is_fragile", false)):
				kind = "fragile"
			elif bool(data.get_meta("is_broken", false)):
				kind = "breakable"
		groups[kind].append(cell)
	return groups


## Специальные тайлы — отдельные тела на ячейку: их можно убрать точечно.
func _build_cells(cells: Array, extra_layer: int, kind: String) -> Array:
	var bodies: Array = []
	for cell in cells:
		var body := StaticBody2D.new()
		body.collision_layer = GameConfig.LAYER_SOLID | extra_layer
		body.collision_mask = 0
		body.set_meta("kind", kind)
		body.set_meta("cell", cell)

		var shape := RectangleShape2D.new()
		shape.size = Vector2(GameConfig.TILE, GameConfig.TILE)
		var cs := CollisionShape2D.new()
		cs.shape = shape
		cs.position = Vector2(
			cell.x * GameConfig.TILE + GameConfig.TILE / 2.0,
			cell.y * GameConfig.TILE + GameConfig.TILE / 2.0)
		body.add_child(cs)
		add_child(body)
		bodies.append(body)
	return bodies


func _on_player_floor(body: Node2D) -> void:
	if body.get_meta("kind", "") != "fragile":
		return
	if not _fragile_timers.has(body):
		_fragile_timers[body] = GameConfig.FRAGILE_BREAK_DELAY


func _process_fragile(delta: float) -> void:
	for body in _fragile_timers.keys():
		if not is_instance_valid(body):
			_fragile_timers.erase(body)
			continue
		_fragile_timers[body] -= delta
		if _fragile_timers[body] <= 0.0:
			_fragile_timers.erase(body)
			_remove_platform(body)


func _on_breakable_hit(body: Node2D) -> void:
	if body.get_meta("kind", "") == "breakable":
		_remove_platform(body)


func _remove_platform(body: Node2D) -> void:
	if _platforms_layer != null and body.has_meta("cell"):
		_platforms_layer.erase_cell(body.get_meta("cell"))
	body.queue_free()


## Ячейки MovingPlatforms превращаются в AnimatableBody2D с дефолтным
## горизонтальным ходом ±100 px (PlatformPaths в текущих картах пуст).
func _spawn_moving_platforms(map: Node2D) -> void:
	var layer := map.find_child("MovingPlatforms", true, false) as TileMapLayer
	if layer == null:
		return
	var cells := layer.get_used_cells()
	if cells.is_empty():
		return

	var rows := {}
	for c in cells:
		if not rows.has(c.y):
			rows[c.y] = []
		rows[c.y].append(c.x)

	for y in rows:
		var xs: Array = rows[y]
		xs.sort()
		var run_start: int = xs[0]
		var run_end: int = xs[0]
		for i in range(1, xs.size()):
			if xs[i] == run_end + 1:
				run_end = xs[i]
			else:
				_make_moving_platform(layer, run_start, run_end, y)
				run_start = xs[i]
				run_end = xs[i]
		_make_moving_platform(layer, run_start, run_end, y)

	for c in cells:
		layer.erase_cell(c)


func _make_moving_platform(layer: TileMapLayer, x0: int, x1: int, y: int) -> void:
	var body := MOVING_PLATFORM_SCRIPT.new() as AnimatableBody2D
	body.collision_layer = GameConfig.LAYER_SOLID
	body.collision_mask = 0
	body.set("travel", Vector2(GameConfig.MOVING_PLATFORM_TRAVEL, 0.0))
	body.set("speed", GameConfig.MOVING_PLATFORM_SPEED)

	var w := (x1 - x0 + 1) * GameConfig.TILE
	var center := Vector2(
		x0 * GameConfig.TILE + w / 2.0,
		y * GameConfig.TILE + GameConfig.TILE / 2.0)
	body.position = center

	var shape := RectangleShape2D.new()
	shape.size = Vector2(w, GameConfig.TILE)
	var cs := CollisionShape2D.new()
	cs.shape = shape
	body.add_child(cs)

	for x in range(x0, x1 + 1):
		var sprite := Sprite2D.new()
		sprite.texture = _cell_texture(layer, Vector2i(x, y))
		sprite.position = Vector2(
			x * GameConfig.TILE + GameConfig.TILE / 2.0 - center.x, 0.0)
		body.add_child(sprite)

	add_child(body)


## Сливает занятые ячейки в горизонтальные полосы: меньше тел, нет швов по полу.
func _build_static(cells: Array, oneway: bool, extra_layer: int = 0) -> void:
	if cells.is_empty():
		return
	var rows := {}
	for c in cells:
		if not rows.has(c.y):
			rows[c.y] = []
		rows[c.y].append(c.x)

	var body := StaticBody2D.new()
	body.collision_layer = (GameConfig.LAYER_ONEWAY if oneway else GameConfig.LAYER_SOLID) | extra_layer
	body.collision_mask = 0
	add_child(body)

	for y in rows:
		var xs: Array = rows[y]
		xs.sort()
		var run_start: int = xs[0]
		var run_end: int = xs[0]
		for i in range(1, xs.size()):
			if xs[i] == run_end + 1:
				run_end = xs[i]
			else:
				_add_run(body, run_start, run_end, y, oneway)
				run_start = xs[i]
				run_end = xs[i]
		_add_run(body, run_start, run_end, y, oneway)


func _add_run(body: StaticBody2D, x0: int, x1: int, y: int, oneway: bool) -> void:
	var w := (x1 - x0 + 1) * GameConfig.TILE
	var shape := RectangleShape2D.new()
	shape.size = Vector2(w, GameConfig.TILE)
	var cs := CollisionShape2D.new()
	cs.shape = shape
	cs.one_way_collision = oneway
	cs.position = Vector2(x0 * GameConfig.TILE + w / 2.0, y * GameConfig.TILE + GameConfig.TILE / 2.0)
	body.add_child(cs)


func _on_death() -> void:
	if _invuln <= 0.0:
		_respawn()


func _respawn() -> void:
	_invuln = 0.5
	player.respawn(_spawn)
