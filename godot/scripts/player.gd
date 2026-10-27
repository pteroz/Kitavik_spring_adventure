extends CharacterBody2D
## Контроллер игрока на CharacterBody2D.
## Скоростная модель (ходьба/бег/воздух) и прыжок (буфер, койот, гашение)
## портированы из импульсной схемы Arcade и вынесены в GameConfig.

signal died
signal floor_started(body: Node2D)
signal breakable_hit(body: Node2D)

const RUN_ANIM_SPEED := 171.5  # 320 / 1.8667
const AIR_APEX_SPEED := 117.8  # 220 / 1.8667
const LAND_SQUASH_TIME := 0.10
const LAND_SQUASH_MIN_SPEED := 160.7  # 300 / 1.8667
const SHADOW_GROUND_ALPHA := 0.45
const SHADOW_FADE_SPEED := 3.0

@onready var sprite: AnimatedSprite2D = $Sprite
@onready var shadow: Node2D = $Shadow

var _facing := 1.0
var _run_side := 0.0
var _last_tap := {-1.0: -999.0, 1.0: -999.0}
var _hold_left := 0.0
var _hold_right := 0.0
var _t := 0.0
var _land_squash := 0.0
var _turning := false
var _turn_target := 1.0

var _coyote := 0.0
var _jump_buffer := 0.0
var _jumping := false
var _jump_start := 0.0
var _drop_timer := 0.0

var _floor_bodies: Array[Node2D] = []
var _floor_slippery := false
var _floor_surface := ""
var _platform_layer: TileMapLayer
var _broke_this_jump := false


func _ready() -> void:
	sprite.animation_finished.connect(_on_sprite_animation_finished)
	sprite.frame_changed.connect(_on_sprite_frame_changed)


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
	_update_shadow(delta)
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
	var gravity := GameConfig.PLAYER_FALL_GRAVITY if velocity.y > 0.0 else GameConfig.PLAYER_GRAVITY
	velocity.y += gravity * delta
	velocity.y = minf(velocity.y, GameConfig.PLAYER_MAX_FALL_SPEED)


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
			if _floor_surface == "straw":
				cap *= GameConfig.STRAW_SPEED_MULTIPLIER
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
		_cancel_turn()

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
	if absf(dir) <= 0.01 or _turning:
		return
	var new_facing := signf(dir)
	if new_facing == _facing:
		return
	_facing = new_facing
	if not is_on_floor():
		if sprite:
			sprite.flip_h = _facing < 0.0
		return
	_start_turn(_facing)


func _start_turn(target: float) -> void:
	_turning = true
	_turn_target = target
	sprite.speed_scale = 1.0
	# Полный клип turn сохранён в ресурсе; в игре видны только начало и конец.
	sprite.play(&"turn_short")


func _finish_turn() -> void:
	_turning = false
	_facing = _turn_target
	sprite.flip_h = _facing < 0.0
	_update_animation()


func _cancel_turn() -> void:
	if not _turning:
		return
	_turning = false
	_facing = _turn_target
	sprite.flip_h = _facing < 0.0


func _on_sprite_frame_changed() -> void:
	if not _turning:
		return
	if sprite.animation != &"turn" and sprite.animation != &"turn_short":
		return
	var flip_at := sprite.sprite_frames.get_frame_count(sprite.animation) / 2
	if sprite.frame >= flip_at:
		sprite.flip_h = _turn_target < 0.0


func _on_sprite_animation_finished() -> void:
	if sprite.animation == &"turn" or sprite.animation == &"turn_short":
		_finish_turn()


func _update_animation() -> void:
	if _turning:
		return
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
	sprite.speed_scale = clampf(absf(velocity.x) / ref_speed, 0.8, 1.0)


## Кадры прыжка выбираются по фазе: 1 — подъём, 2 — вершина, 3 — падение.
## Кадр 0 (присед) показывается при жёстком приземлении.
func _show_jump_frame(index: int) -> void:
	if sprite.animation != &"jump":
		sprite.speed_scale = 1.0
		sprite.play(&"jump")
		sprite.pause()
	if sprite.frame != index:
		sprite.frame = index


func _update_shadow(delta: float) -> void:
	var target := SHADOW_GROUND_ALPHA if is_on_floor() else 0.0
	shadow.modulate.a = move_toward(shadow.modulate.a, target, SHADOW_FADE_SPEED * delta)


func _update_floor_contact() -> void:
	if not is_on_floor():
		_floor_bodies.clear()
		_floor_slippery = false
		_floor_surface = ""
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
	_floor_surface = _surface_under_feet()


func setup_platform_layer(layer: TileMapLayer) -> void:
	_platform_layer = layer
	_floor_surface = ""


func get_floor_surface() -> String:
	return _floor_surface if is_on_floor() else ""


## Тип поверхности берётся из свойства surface тайла прямо под лапами.
func _surface_under_feet() -> String:
	if _platform_layer == null:
		return ""
	var feet := global_position + Vector2(0.0, GameConfig.PLAYER_SIZE.y / 2.0 + 4.0)
	var cell := _platform_layer.local_to_map(_platform_layer.to_local(feet))
	var data := _platform_layer.get_cell_tile_data(cell)
	if data == null:
		return ""
	return String(data.get_meta("surface", ""))


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
	_cancel_turn()
	_floor_bodies.clear()
	_floor_slippery = false
	_floor_surface = ""
	_broke_this_jump = false
	var fx := get_node_or_null("GroundFx")
	if fx != null:
		fx.clear()


func die() -> void:
	emit_signal("died")
