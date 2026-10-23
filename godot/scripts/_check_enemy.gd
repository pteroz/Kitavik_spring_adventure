extends SceneTree
## Headless-проверка врага: патруль, прыжок у стены, параметры из metadata.


func _initialize() -> void:
	_run.call_deferred()


func _static_rect(parent: Node2D, center: Vector2, size: Vector2) -> StaticBody2D:
	var body := StaticBody2D.new()
	body.collision_layer = GameConfig.LAYER_SOLID
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
	var ok := true

	var world := Node2D.new()
	root.add_child(world)
	_static_rect(world, Vector2(0, 100), Vector2(400, 20))
	_static_rect(world, Vector2(40, 40), Vector2(20, 100))

	var enemy := (load("res://scenes/enemy_rat.tscn") as PackedScene).instantiate() as RatEnemy
	enemy.position = Vector2(0, 80)
	world.add_child(enemy)

	for i in range(10):
		await physics_frame
	print("enemy floor=", enemy.is_on_floor(), " x=", enemy.global_position.x,
		" vx=", enemy.velocity.x, " patrol=", enemy.patrol_range, " speed=", enemy.speed)
	ok = ok and enemy.is_on_floor()
	ok = ok and enemy.patrol_range == GameConfig.ENEMY_PATROL_RANGE
	ok = ok and enemy.speed == GameConfig.ENEMY_SPEED

	var hopped := false
	for i in range(90):
		await physics_frame
		if enemy.velocity.y < -100.0:
			hopped = true
			break
	print("hopped=", hopped, " x=", enemy.global_position.x, " vy=", enemy.velocity.y)
	ok = ok and hopped

	var level = (load("res://scenes/level1.tscn") as PackedScene).instantiate()
	root.add_child(level)
	await process_frame

	var map := Node2D.new()
	var layer := Node2D.new()
	layer.name = "Enemies"
	var marker := Marker2D.new()
	marker.position = Vector2(500, 500)
	marker.set_meta("patrol_range", 200.0)
	marker.set_meta("move_force", 500.0)
	layer.add_child(marker)
	map.add_child(layer)
	level.add_child(map)
	level.call("_spawn_enemies", map)

	var configured: RatEnemy = null
	for child in level.get_children():
		if child is RatEnemy and is_equal_approx(child.patrol_range, 200.0):
			configured = child
			break
	var meta_ok := configured != null and is_equal_approx(configured.speed, 100.0)
	print("meta enemy=", configured != null,
		" patrol=", configured.patrol_range if configured else -1.0,
		" speed=", configured.speed if configured else -1.0)
	ok = ok and meta_ok

	print("RESULT: ", "PASS" if ok else "FAIL")
	quit(0 if ok else 1)
