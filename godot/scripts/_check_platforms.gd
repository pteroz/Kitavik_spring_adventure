extends SceneTree
## Headless-проверка 1.3: классификация тайлов, хрупкие/разбиваемые/скользкие
## платформы, сигналы игрока и движущиеся платформы.

var _ok := true


func _initialize() -> void:
	_run.call_deferred()


func _check(cond: bool, label: String) -> void:
	print(("OK   " if cond else "FAIL "), label)
	_ok = _ok and cond


func _make_layer(kinds: Array) -> TileMapLayer:
	var img := Image.create(32 * kinds.size(), 32, false, Image.FORMAT_RGBA8)
	img.fill(Color.WHITE)
	var tex := ImageTexture.create_from_image(img)
	var source := TileSetAtlasSource.new()
	source.texture = tex
	for i in kinds.size():
		source.create_tile(Vector2i(i, 0))

	var tile_set := TileSet.new()
	tile_set.tile_size = Vector2i(GameConfig.TILE, GameConfig.TILE)
	var source_id := tile_set.add_source(source)

	var layer := TileMapLayer.new()
	layer.tile_set = tile_set
	for i in kinds.size():
		var cell := Vector2i(i, 0)
		layer.set_cell(cell, source_id, Vector2i(i, 0))
		var data := layer.get_cell_tile_data(cell)
		for key in kinds[i]:
			data.set_meta(key, kinds[i][key])
	return layer


func _static_rect(parent: Node2D, center: Vector2, size: Vector2, layer: int) -> StaticBody2D:
	var body := StaticBody2D.new()
	body.collision_layer = layer
	body.collision_mask = 0
	body.position = center
	var shape := CollisionShape2D.new()
	var rect := RectangleShape2D.new()
	rect.size = size
	shape.shape = rect
	body.add_child(shape)
	parent.add_child(body)
	return body


func _run() -> void:
	# --- Классификация тайлов по metadata ---
	var layer := _make_layer([
		{},
		{"is_slippery": true},
		{"is_fragile": true},
		{"is_broken": true},
		{"is_slippery": true, "is_fragile": true},
	])
	var probe_level: Node = load("res://scripts/tiled_level.gd").new()
	var groups: Dictionary = probe_level._classify_platform_cells(layer)
	_check(groups["normal"].size() == 1, "классификация: normal = 1")
	_check(groups["slippery"].size() == 2, "классификация: slippery = 2 (приоритет над fragile)")
	_check(groups["fragile"].size() == 1, "классификация: fragile = 1")
	_check(groups["breakable"].size() == 1, "классификация: breakable = 1")
	probe_level.free()
	layer.free()

	# --- Реальная карта и подписка уровня на сигналы игрока ---
	var level := (load("res://scenes/level1.tscn") as PackedScene).instantiate()
	root.add_child(level)
	await process_frame
	await physics_frame

	var platforms := level.find_child("Platforms", true, false) as TileMapLayer
	var total := platforms.get_used_cells().size()
	var real_groups: Dictionary = level._classify_platform_cells(platforms)
	_check(real_groups["normal"].size() == total,
		"level1: все %d ячеек Platforms — обычные" % total)
	_check(real_groups["slippery"].is_empty()
		and real_groups["fragile"].is_empty()
		and real_groups["breakable"].is_empty(),
		"level1: специальных тайлов нет")

	var player := level.get_node("Player") as CharacterBody2D
	_check(player.floor_started.is_connected(Callable(level, "_on_player_floor")),
		"level подписан на floor_started")
	_check(player.breakable_hit.is_connected(Callable(level, "_on_breakable_hit")),
		"level подписан на breakable_hit")

	# --- Хрупкая платформа: таймер 0.4 c и удаление тайла ---
	var sample := platforms.get_used_cells()[0]
	var source_id := platforms.get_cell_source_id(sample)
	var atlas_coords := platforms.get_cell_atlas_coords(sample)

	var frag_cell := Vector2i(0, 90)
	platforms.set_cell(frag_cell, source_id, atlas_coords)
	var frag_bodies: Array = level._build_cells(
		[frag_cell], GameConfig.LAYER_FRAGILE, "fragile")
	var fragile: StaticBody2D = frag_bodies[0]
	level._on_player_floor(fragile)
	_check(level._fragile_timers.has(fragile), "хрупкая: таймер запущен")

	var break_frame := -1
	for i in range(60):
		await physics_frame
		if not is_instance_valid(fragile):
			break_frame = i + 1
			break
	_check(break_frame >= 20 and break_frame <= 30,
		"хрупкая: разрушение за 0.4 c (%d кадров)" % break_frame)
	_check(platforms.get_cell_source_id(frag_cell) == -1,
		"хрупкая: тайл убран из карты")

	# --- Разбиваемый блок: удаление по сигналу игрока ---
	var br_cell := Vector2i(0, 91)
	platforms.set_cell(br_cell, source_id, atlas_coords)
	var br_bodies: Array = level._build_cells(
		[br_cell], GameConfig.LAYER_BREAKABLE, "breakable")
	var breakable: StaticBody2D = br_bodies[0]
	level._on_breakable_hit(breakable)
	await physics_frame
	await process_frame
	_check(not is_instance_valid(breakable), "разбиваемый: удалён по удару")
	_check(platforms.get_cell_source_id(br_cell) == -1,
		"разбиваемый: тайл убран из карты")

	level.queue_free()
	await process_frame

	# --- Игрок: сигнал пола, лёд, удар головой ---
	var world := Node2D.new()
	root.add_child(world)
	var floor_body := _static_rect(world, Vector2(0, 28), Vector2(600, 20),
		GameConfig.LAYER_SOLID | GameConfig.LAYER_FRAGILE)
	var player_scene := load("res://scenes/player.tscn") as PackedScene
	var test_player := player_scene.instantiate() as CharacterBody2D
	test_player.position = Vector2(0, 0)
	world.add_child(test_player)

	var floors: Array = []
	test_player.floor_started.connect(func(b): floors.append(b))
	for i in range(10):
		await physics_frame
	_check(test_player.is_on_floor(), "игрок: стоит на платформе")
	_check(floors.has(floor_body), "игрок: floor_started от тела пола")

	floor_body.collision_layer = GameConfig.LAYER_SOLID | GameConfig.LAYER_SLIPPERY
	for i in range(3):
		await physics_frame
	_check(test_player.get("_floor_slippery") == true, "лёд: пол распознан скользким")

	Input.action_press("move_right")
	for i in range(18):
		await physics_frame
	var slippery_speed: float = test_player.velocity.x
	Input.action_release("move_right")
	for i in range(10):
		await physics_frame
	var coast_speed: float = test_player.velocity.x
	_check(slippery_speed < 200.0,
		"лёд: медленный разгон (%.1f < 200)" % slippery_speed)
	_check(coast_speed > 30.0,
		"лёд: долгое торможение (%.1f > 30)" % coast_speed)

	var block := _static_rect(world,
		Vector2(test_player.position.x, test_player.position.y - 40.0),
		Vector2(32, 32), GameConfig.LAYER_SOLID | GameConfig.LAYER_BREAKABLE)
	var hits: Array = []
	var hit_vy: Array = []
	test_player.breakable_hit.connect(func(b):
		hits.append(b)
		hit_vy.append(test_player.velocity.y))
	test_player.velocity.y = -700.0
	for i in range(30):
		await physics_frame
		if not hits.is_empty():
			break
	_check(hits.has(block), "разбиваемый: игрок ударил блок головой")
	var vy_ok := not hit_vy.is_empty() and absf(float(hit_vy[0])) < 0.001
	_check(vy_ok, "разбиваемый: vy погашен при ударе")

	# --- Движущаяся платформа: слияние ячеек и дефолтный ход ---
	var map := Node2D.new()
	var moving_layer := _make_layer([{}, {}])
	moving_layer.name = "MovingPlatforms"
	map.add_child(moving_layer)
	var spawner: Node = load("res://scripts/tiled_level.gd").new()
	spawner._spawn_moving_platforms(map)

	var movers: Array = []
	for child in spawner.get_children():
		if child is AnimatableBody2D:
			movers.append(child)
	_check(movers.size() == 1, "движущаяся: две ячейки слиты в одну платформу")
	if movers.size() == 1:
		var body: AnimatableBody2D = movers[0]
		var shape_node := body.get_child(0) as CollisionShape2D
		var shape_size := (shape_node.shape as RectangleShape2D).size
		_check(is_equal_approx(float(body.get("speed")), GameConfig.MOVING_PLATFORM_SPEED),
			"движущаяся: скорость %.0f" % float(body.get("speed")))
		_check(is_equal_approx(float(body.get("travel").x), GameConfig.MOVING_PLATFORM_TRAVEL),
			"движущаяся: размах %.0f" % float(body.get("travel").x))
		_check(shape_size == Vector2(64, 32),
			"движущаяся: коллизия %s" % shape_size)
		_check(body.get_child_count() == 3, "движущаяся: 1 коллизия + 2 спрайта")
	_check(moving_layer.get_used_cells().is_empty(),
		"движущаяся: ячейки слоя погашены")
	spawner.free()
	map.free()

	var mover_script: GDScript = load("res://scripts/moving_platform.gd")
	var mover := mover_script.new() as AnimatableBody2D
	mover.set("travel", Vector2(200, 0))
	mover.set("speed", 120.0)
	mover.position = Vector2(1000, 1000)
	world.add_child(mover)
	var start_x: float = mover.position.x
	for i in range(30):
		await physics_frame
	var dx: float = mover.position.x - start_x
	_check(dx > 45.0 and dx < 75.0,
		"движущаяся: смещение ~60 px за 0.5 c (%.1f)" % dx)

	# --- Платформа переносит стоящего игрока ---
	var carrier := mover_script.new() as AnimatableBody2D
	carrier.set("travel", Vector2(200, 0))
	carrier.set("speed", 120.0)
	carrier.position = Vector2(0, -300)
	carrier.collision_layer = GameConfig.LAYER_SOLID
	carrier.collision_mask = 0
	var carrier_shape := CollisionShape2D.new()
	var carrier_rect := RectangleShape2D.new()
	carrier_rect.size = Vector2(200, 16)
	carrier_shape.shape = carrier_rect
	carrier.add_child(carrier_shape)
	world.add_child(carrier)
	await physics_frame

	test_player.velocity = Vector2.ZERO
	test_player.global_position = Vector2(carrier.position.x, carrier.position.y - 8.0 - 14.0)
	for i in range(5):
		await physics_frame
	_check(test_player.is_on_floor(), "движущаяся: игрок стоит на платформе")

	var platform_x0: float = carrier.position.x
	var player_x0: float = test_player.global_position.x
	for i in range(30):
		await physics_frame
	var platform_dx: float = carrier.position.x - platform_x0
	var player_dx: float = test_player.global_position.x - player_x0
	_check(platform_dx > 40.0 and absf(platform_dx - player_dx) < 6.0,
		"движущаяся: переносит игрока (платформа %.1f, игрок %.1f)" % [platform_dx, player_dx])

	print("RESULT: ", "PASS" if _ok else "FAIL")
	quit(0 if _ok else 1)
