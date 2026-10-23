extends SceneTree
## Headless-проверка «ощущения»: тап, ходьба, бег (Shift и даблтап),
## скорости прыжков стоя/ходьба/бег и гашение короткого прыжка.

var _ok := true
var _player: CharacterBody2D


func _initialize() -> void:
	_run.call_deferred()


func _check(cond: bool, label: String) -> void:
	print(("OK   " if cond else "FAIL "), label)
	_ok = _ok and cond


func _wait(frames: int) -> void:
	for i in range(frames):
		await physics_frame


func _release_all() -> void:
	for action in ["move_left", "move_right", "run", "jump", "drop_through"]:
		Input.action_release(action)


func _jump_initial(press_move: bool, press_run: bool) -> float:
	if press_move:
		Input.action_press("move_right")
	if press_run:
		Input.action_press("run")
	await _wait(30)

	Input.action_press("jump")
	await physics_frame
	await physics_frame
	var vy: float = _player.velocity.y
	Input.action_release("jump")
	await _wait(70)
	_release_all()
	await _wait(20)
	return vy


func _measure_apex(short_press: bool) -> float:
	await _wait(20)
	var start_y: float = _player.global_position.y
	var min_y := start_y

	Input.action_press("jump")
	var hold := 5 if short_press else 20
	for i in range(hold):
		await physics_frame
		min_y = minf(min_y, _player.global_position.y)
	Input.action_release("jump")

	for i in range(120):
		await physics_frame
		min_y = minf(min_y, _player.global_position.y)
		if i > 5 and _player.is_on_floor():
			break
	await _wait(10)
	return start_y - min_y


func _run() -> void:
	var world := Node2D.new()
	root.add_child(world)
	var floor_body := StaticBody2D.new()
	floor_body.collision_layer = GameConfig.LAYER_SOLID
	floor_body.collision_mask = 0
	floor_body.position = Vector2(0, 28)
	var shape := CollisionShape2D.new()
	var rect := RectangleShape2D.new()
	rect.size = Vector2(4000, 20)
	shape.shape = rect
	floor_body.add_child(shape)
	world.add_child(floor_body)

	_player = (load("res://scenes/player.tscn") as PackedScene).instantiate() as CharacterBody2D
	_player.position = Vector2(0, 0)
	world.add_child(_player)
	await _wait(10)
	_check(_player.is_on_floor(), "движение: игрок на полу")

	# Тап: короткое нажатие — минимальный рывок ≤ TAP_SPEED
	Input.action_press("move_right")
	await _wait(3)
	var tap_speed: float = _player.velocity.x
	Input.action_release("move_right")
	await _wait(30)
	_check(tap_speed > 0.0 and tap_speed <= GameConfig.TAP_SPEED + 5.0,
		"тап: рывок %.1f ≤ %.0f" % [tap_speed, GameConfig.TAP_SPEED])

	# Ходьба
	Input.action_press("move_right")
	await _wait(40)
	var walk_speed: float = _player.velocity.x
	Input.action_release("move_right")
	await _wait(30)
	_check(absf(walk_speed - GameConfig.WALK_SPEED) < 1.0,
		"ходьба: %.1f == %.0f" % [walk_speed, GameConfig.WALK_SPEED])

	# Бег с Shift
	Input.action_press("move_right")
	Input.action_press("run")
	await _wait(40)
	var run_speed: float = _player.velocity.x
	Input.action_release("run")
	Input.action_release("move_right")
	await _wait(30)
	_check(absf(run_speed - GameConfig.RUN_SPEED) < 1.0,
		"бег (Shift): %.1f == %.0f" % [run_speed, GameConfig.RUN_SPEED])

	# Бег даблтапом
	Input.action_press("move_right")
	await _wait(2)
	Input.action_release("move_right")
	await _wait(2)
	Input.action_press("move_right")
	await _wait(40)
	var double_tap_speed: float = _player.velocity.x
	Input.action_release("move_right")
	await _wait(30)
	_check(absf(double_tap_speed - GameConfig.RUN_SPEED) < 1.0,
		"бег (даблтап): %.1f == %.0f" % [double_tap_speed, GameConfig.RUN_SPEED])

	# Стартовые скорости трёх уровней прыжка
	var vy_stand: float = await _jump_initial(false, false)
	_check(absf(vy_stand + GameConfig.JUMP_VELOCITY_STAND) < 1.0,
		"прыжок стоя: %.1f == -%.0f" % [vy_stand, GameConfig.JUMP_VELOCITY_STAND])

	var vy_walk: float = await _jump_initial(true, false)
	_check(absf(vy_walk + GameConfig.JUMP_VELOCITY_WALK) < 1.0,
		"прыжок на ходу: %.1f == -%.0f" % [vy_walk, GameConfig.JUMP_VELOCITY_WALK])

	var vy_run: float = await _jump_initial(true, true)
	_check(absf(vy_run + GameConfig.JUMP_VELOCITY_RUN) < 1.0,
		"прыжок с разбега: %.1f == -%.0f" % [vy_run, GameConfig.JUMP_VELOCITY_RUN])

	# Короткое нажатие < удержание
	_release_all()
	var short_apex: float = await _measure_apex(true)
	var full_apex: float = await _measure_apex(false)
	_check(short_apex > 40.0 and short_apex < 110.0,
		"короткий прыжок: высота %.1f px" % short_apex)
	_check(full_apex > GameConfig.JUMP_VELOCITY_STAND * GameConfig.JUMP_VELOCITY_STAND
		/ (2.0 * GameConfig.GRAVITY) - 20.0,
		"полный прыжок: высота %.1f px" % full_apex)
	_check(full_apex > short_apex + 50.0,
		"гашение: короткий ниже полного (%.1f < %.1f)" % [short_apex, full_apex])

	print("RESULT: ", "PASS" if _ok else "FAIL")
	quit(0 if _ok else 1)
