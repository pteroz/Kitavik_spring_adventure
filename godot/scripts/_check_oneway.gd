extends SceneTree
## Headless-проверка one-way: проход снизу, приземление сверху, соскакивание вниз.

var _ok := true


func _initialize() -> void:
	_run.call_deferred()


func _check(cond: bool, label: String) -> void:
	print(("OK   " if cond else "FAIL "), label)
	_ok = _ok and cond


func _static_rect(parent: Node2D, center: Vector2, size: Vector2,
		layer: int, oneway := false) -> StaticBody2D:
	var body := StaticBody2D.new()
	body.collision_layer = layer
	body.collision_mask = 0
	body.position = center
	var shape := CollisionShape2D.new()
	var rect := RectangleShape2D.new()
	rect.size = size
	shape.shape = rect
	shape.one_way_collision = oneway
	body.add_child(shape)
	parent.add_child(body)
	return body


func _run() -> void:
	var world := Node2D.new()
	root.add_child(world)
	_static_rect(world, Vector2(0, 210), Vector2(400, 20), GameConfig.LAYER_SOLID)
	var oneway := _static_rect(world, Vector2(0, 100), Vector2(200, 16),
		GameConfig.LAYER_ONEWAY, true)

	var player := (load("res://scenes/player.tscn") as PackedScene).instantiate() as CharacterBody2D
	player.position = Vector2(0, 180)
	world.add_child(player)

	for i in range(10):
		await physics_frame
	_check(player.is_on_floor(), "one-way: игрок на твёрдом полу (y=%.1f)" % player.global_position.y)

	player.velocity.y = -900.0
	var passed_through := false
	var landed_y := 0.0
	for i in range(120):
		await physics_frame
		if player.velocity.y < 0.0 and player.global_position.y < 70.0:
			passed_through = true
		if player.is_on_floor() and player.global_position.y < 90.0:
			landed_y = player.global_position.y
			break
	_check(passed_through, "one-way: игрок прошёл снизу вверх")
	_check(landed_y > 74.0 and landed_y < 82.0,
		"one-way: приземление сверху (y=%.1f, ожидали ~78)" % landed_y)

	Input.action_press("drop_through")
	await physics_frame
	await physics_frame
	Input.action_release("drop_through")

	var fell_to_floor := false
	var floor_y := 0.0
	for i in range(140):
		await physics_frame
		if player.is_on_floor() and player.global_position.y > 160.0:
			fell_to_floor = true
			floor_y = player.global_position.y
			break
	_check(fell_to_floor, "one-way: соскакивание вниз, приземление на пол (y=%.1f)" % floor_y)

	print("RESULT: ", "PASS" if _ok else "FAIL")
	quit(0 if _ok else 1)
