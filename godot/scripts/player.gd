extends CharacterBody2D
## Контроллер игрока на CharacterBody2D.
## Скоростная модель (ходьба/бег/воздух) и прыжок (буфер, койот, гашение)
## портированы из импульсной схемы Arcade и вынесены в GameConfig.

signal died
signal floor_started(body: Node2D)
signal breakable_hit(body: Node2D)

const RUN_ANIM_SPEED := 320.0
const AIR_APEX_SPEED := 220.0
const LAND_SQUASH_TIME := 0.10
const LAND_SQUASH_MIN_SPEED := 300.0

@onready var sprite: AnimatedSprite2D = $Sprite

var _facing := 1.0
var _run_side := 0.0
var _last_tap := {-1.0: -999.0, 1.0: -999.0}
var _hold_left := 0.0
var _hold_right := 0.0
var _t := 0.0
var _land_squash := 0.0

var _coyote := 0.0
var _jump_buffer := 0.0
var _jumping := false
var _jump_start := 0.0
var _drop_timer := 0.0

var _floor_bodies: Array[Node2D] = []
var _floor_slippery := false
var _broke_this_jump := false


func _physics_process(delta: float) -> void:
	_t += delta
	_land_squash = maxf(0.0, _land_squash - delta)
	if velocity.y >= 0.0:
		_broke_this_jump = false

	var was_on_floor := is_on_floor()
	var dir := Input.get_axis("move_left", "move_right")
	_read_run_input(delta, dir)
	_update_facing(dir)

	var on_floor := is_on_floor()
	_apply_gravity(delta, on_floor)
	_apply_horizontal(delta, dir, on_floor)
	_handle_jump(delta, on_floor, dir)
	_handle_drop_through(delta)

	var rising := velocity.y < 0.0
	var fall_speed := velocity.y
	move_and_slide()
	_update_floor_contact()
	if rising:
		_check_breakable_ceiling()
	if not was_on_floor and is_on_floor() and fall_speed > LAND_SQUASH_MIN_SPEED:
		_land_squash = LAND_SQUASH_TIME
	_update_animation()


func _read_run_input(delta: float, dir: float) -> void:
	_hold_left = _hold_left + delta if Input.is_action_pressed("move_left") else 0.0
	_hold_right = _hold_right + delta if Input.is_action_pressed("move_right") else 0.0
	for side in [-1.0, 1.0]:
		var act := "move_left" if side < 0.0 else "move_right"
		if Input.is_action_just_pressed(act):
			if _t - _last_tap[side] < GameConfig.DOUBLE_TAP_WINDOW:
				_run_side = side
			_last_tap[side] = _t
	# даблтап живёт, пока держим ту же сторону; иначе гаснет
	if _run_side != 0.0 and (dir == 0.0 or signf(dir) != _run_side):
		_run_side = 0.0


func _want_run(dir: float) -> bool:
	return Input.is_action_pressed("run") or (_run_side != 0.0 and signf(dir) == _run_side)


func _apply_gravity(delta: float, on_floor: bool) -> void:
	if on_floor:
		return
	velocity.y += GameConfig.GRAVITY * delta
	velocity.y = minf(velocity.y, GameConfig.MAX_FALL_SPEED)


func _apply_horizontal(delta: float, dir: float, on_floor: bool) -> void:
	var ground_accel := GameConfig.GROUND_ACCEL
	var ground_friction := GameConfig.GROUND_FRICTION
	if on_floor and _floor_slippery:
		ground_accel *= GameConfig.ICE_ACCELERATION
		ground_friction *= GameConfig.ICE_DECELERATION

	if absf(dir) > 0.01:
		var side := signf(dir)
		var hold := _hold_left if side < 0.0 else _hold_right
		# тап короче 0.15 c — минимальный рывок (как SLOW-сила оригинала)
		var tapping := on_floor and not _want_run(dir) and hold < GameConfig.RUN_HOLD_THRESHOLD
		var cap := GameConfig.AIR_SPEED
		if on_floor:
			cap = GameConfig.TAP_SPEED if tapping else (GameConfig.RUN_SPEED if _want_run(dir) else GameConfig.WALK_SPEED)
		var accel := GameConfig.TAP_ACCEL if tapping else (ground_accel if on_floor else GameConfig.AIR_ACCEL)
		velocity.x = move_toward(velocity.x, side * cap, accel * delta)
	else:
		var fr := ground_friction if on_floor else GameConfig.AIR_ACCEL * 0.4
		velocity.x = move_toward(velocity.x, 0.0, fr * delta)


func _handle_jump(delta: float, on_floor: bool, dir: float) -> void:
	if Input.is_action_just_pressed("jump"):
		_jump_buffer = GameConfig.JUMP_BUFFER_TIME
	else:
		_jump_buffer = maxf(0.0, _jump_buffer - delta)

	_coyote = GameConfig.COYOTE_TIME if on_floor else maxf(0.0, _coyote - delta)

	if _jump_buffer > 0.0 and (on_floor or _coyote > 0.0):
		velocity.y = -_jump_velocity(dir)
		_jump_buffer = 0.0
		_coyote = 0.0
		_jumping = true
		_jump_start = _t

	# переменная высота: гасим подъём, только если отпустили в пределах окна
	# (короткое нажатие = маленький прыжок, удержание дольше окна = полный)
	if _jumping and Input.is_action_just_released("jump") and velocity.y < 0.0:
		if _t - _jump_start < GameConfig.JUMP_CUTOFF_TIME:
			velocity.y *= GameConfig.JUMP_CUT_MULTIPLIER
		_jumping = false


func _jump_velocity(dir: float) -> float:
	# три уровня из оригинала: с разбега > на ходу > стоя
	if _want_run(dir):
		return GameConfig.JUMP_VELOCITY_RUN
	if absf(dir) > 0.01:
		return GameConfig.JUMP_VELOCITY_WALK
	return GameConfig.JUMP_VELOCITY_STAND


func _handle_drop_through(delta: float) -> void:
	if Input.is_action_just_pressed("drop_through") and is_on_floor():
		_drop_timer = GameConfig.DROP_THROUGH_TIME
	if _drop_timer > 0.0:
		collision_mask &= ~GameConfig.LAYER_ONEWAY
		_drop_timer -= delta
	else:
		collision_mask |= GameConfig.LAYER_ONEWAY


func _update_facing(dir: float) -> void:
	if absf(dir) > 0.01:
		_facing = signf(dir)
	if sprite:
		sprite.flip_h = _facing < 0.0


func _update_animation() -> void:
	if not is_on_floor():
		if velocity.y < -AIR_APEX_SPEED:
			_show_jump_frame(1)
		elif velocity.y <= AIR_APEX_SPEED:
			_show_jump_frame(2)
		else:
			_show_jump_frame(3)
	elif _land_squash > 0.0:
		_show_jump_frame(0)
	else:
		var speed := absf(velocity.x)
		if speed < 8.0:
			_play_loop(&"idle")
		elif speed > RUN_ANIM_SPEED:
			_play_loop(&"run")
		else:
			_play_loop(&"walk")


func _play_loop(anim: StringName) -> void:
	if sprite.animation != anim or not sprite.is_playing():
		sprite.play(anim)
	if anim == &"idle":
		sprite.speed_scale = 1.0
		return
	var ref_speed := GameConfig.RUN_SPEED if anim == &"run" else GameConfig.WALK_SPEED
	sprite.speed_scale = clampf(absf(velocity.x) / ref_speed, 0.7, 1.3)


## Кадры прыжка выбираются по фазе: 1 — подъём, 2 — вершина, 3 — падение.
## Кадр 0 (присед) показывается при жёстком приземлении.
func _show_jump_frame(index: int) -> void:
	if sprite.animation != &"jump":
		sprite.speed_scale = 1.0
		sprite.play(&"jump")
		sprite.pause()
	if sprite.frame != index:
		sprite.frame = index


func _update_floor_contact() -> void:
	if not is_on_floor():
		_floor_bodies.clear()
		_floor_slippery = false
		return

	var bodies := _find_floor_bodies()
	if bodies.is_empty():
		return

	_floor_slippery = false
	for body in bodies:
		if body is CollisionObject2D and ((body as CollisionObject2D).collision_layer & GameConfig.LAYER_SLIPPERY) != 0:
			_floor_slippery = true
		if not _floor_bodies.has(body):
			floor_started.emit(body)
	_floor_bodies = bodies


func _find_floor_bodies() -> Array[Node2D]:
	var bodies: Array[Node2D] = []
	for i in get_slide_collision_count():
		var c := get_slide_collision(i)
		if c.get_normal().y >= -0.5:
			continue
		var body := c.get_collider() as Node2D
		if body != null and not bodies.has(body):
			bodies.append(body)
	if bodies.is_empty():
		bodies = _probe_floor_bodies()
	return bodies


## Запасной зонд под ногами: при стоянии на месте slide-коллизий может не быть.
func _probe_floor_bodies() -> Array[Node2D]:
	var bodies: Array[Node2D] = []
	var shape := RectangleShape2D.new()
	shape.size = Vector2(12.0, 4.0)
	var params := PhysicsShapeQueryParameters2D.new()
	params.shape = shape
	params.transform = Transform2D(0.0, global_position + Vector2(0.0, GameConfig.PLAYER_SIZE.y / 2.0 + 2.0))
	params.collision_mask = GameConfig.WORLD_MASK
	params.exclude = [get_rid()]
	for hit in get_world_2d().direct_space_state.intersect_shape(params, 8):
		var body := hit.get("collider") as Node2D
		if body != null and not bodies.has(body):
			bodies.append(body)
	return bodies


func _check_breakable_ceiling() -> void:
	if _broke_this_jump:
		return
	for i in get_slide_collision_count():
		var c := get_slide_collision(i)
		if c.get_normal().y < 0.5:
			continue
		var body := c.get_collider() as CollisionObject2D
		if body == null or (body.collision_layer & GameConfig.LAYER_BREAKABLE) == 0:
			continue
		_broke_this_jump = true
		velocity.y = 0.0
		breakable_hit.emit(body)
		return


func respawn(at: Vector2) -> void:
	global_position = at
	velocity = Vector2.ZERO
	_jumping = false
	_run_side = 0.0
	_land_squash = 0.0
	_floor_bodies.clear()
	_floor_slippery = false
	_broke_this_jump = false


func die() -> void:
	emit_signal("died")
