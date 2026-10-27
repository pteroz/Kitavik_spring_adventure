extends Node2D
## Эффекты поверхности под лапами: соломинки на сене и следы на снегу.
## Узел работает в мировых координатах (top_level), поэтому следы остаются
## на месте, когда игрок уходит, а соломинки не «прилипают» к телу.

const STRAW_LIGHT := Color(1.0, 0.9, 0.45)
const STRAW_DARK := Color(0.72, 0.5, 0.12)
const SNOW_PRINT := Color(0.38, 0.47, 0.62)

const STRAW_INTERVAL := 0.05
const STRAW_MIN_SPEED := 24.0
const STRAW_GRAVITY := 720.0

const STEP_DISTANCE := 26.0
const STEP_MIN_SPEED := 18.0
const PRINT_LIFE := 4.5

var _straws: Array = []
var _prints: Array = []
var _straw_timer := 0.0
var _straw_side := 1.0
var _step_accum := 0.0
var _step_side := 1.0

@onready var _player: CharacterBody2D = get_parent() as CharacterBody2D


func _physics_process(delta: float) -> void:
	if _player == null:
		return
	var surface: String = _player.get_floor_surface()
	var speed := absf(_player.velocity.x)

	if surface == "straw" and speed > STRAW_MIN_SPEED:
		_straw_timer -= delta
		while _straw_timer <= 0.0:
			_straw_timer += STRAW_INTERVAL
			_emit_straw(speed)
	else:
		_straw_timer = 0.0

	if surface == "snow" and speed > STEP_MIN_SPEED:
		_step_accum += speed * delta
		while _step_accum >= STEP_DISTANCE:
			_step_accum -= STEP_DISTANCE
			_emit_print()
	else:
		_step_accum = 0.0

	_advance(delta)
	queue_redraw()


func _advance(delta: float) -> void:
	for s in _straws:
		s["life"] -= delta
		s["vel"].y += STRAW_GRAVITY * delta
		s["pos"] += s["vel"] * delta
		s["rot"] += s["spin"] * delta
	_straws = _straws.filter(func(s): return s["life"] > 0.0)
	for p in _prints:
		p["life"] -= delta
	_prints = _prints.filter(func(p): return p["life"] > 0.0)


func _emit_straw(speed: float) -> void:
	var feet := _player.global_position + Vector2(0.0, GameConfig.PLAYER_SIZE.y / 2.0)
	var back := -signf(_player.velocity.x)
	_straw_side = -_straw_side
	var vx := back * randf_range(15.0, 105.0) + randf_range(-45.0, 45.0)
	var vy := -randf_range(45.0, 145.0) - speed * 0.12
	var life := randf_range(0.3, 0.55)
	_straws.append({
		"pos": feet + Vector2(_straw_side * randf_range(3.0, 7.0), randf_range(-2.0, 1.0)),
		"vel": Vector2(vx, vy),
		"rot": randf_range(-PI, PI),
		"spin": randf_range(-12.0, 12.0),
		"len": randf_range(5.0, 10.0),
		"life": life,
		"max_life": life,
		"color": STRAW_LIGHT.lerp(STRAW_DARK, randf()),
	})


func _emit_print() -> void:
	var feet := _player.global_position + Vector2(0.0, GameConfig.PLAYER_SIZE.y / 2.0 + 1.0)
	_step_side = -_step_side
	_prints.append({
		"pos": feet + Vector2(_step_side * 3.5, 0.0 if _step_side > 0.0 else 2.0),
		"rot": randf_range(-0.3, 0.3),
		"life": PRINT_LIFE,
		"max_life": PRINT_LIFE,
	})


func _draw() -> void:
	for s in _prints:
		var fade: float = clampf(s["life"] / s["max_life"] * 1.8, 0.0, 1.0)
		var col := SNOW_PRINT
		col.a = 0.6 * fade
		draw_set_transform(s["pos"], s["rot"], Vector2(1.0, 0.45))
		draw_circle(Vector2.ZERO, 5.0, col)
	draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)

	for s in _straws:
		var fade: float = clampf(s["life"] / s["max_life"] * 1.6, 0.0, 1.0)
		var col: Color = s["color"]
		col.a = fade
		var axis := Vector2.RIGHT.rotated(s["rot"])
		var half: Vector2 = axis * (s["len"] * 0.5)
		draw_line(s["pos"] - half, s["pos"] + half, col, 1.8, true)


func clear() -> void:
	_straws.clear()
	_prints.clear()
	_straw_timer = 0.0
	_straw_side = 1.0
	_step_accum = 0.0
	queue_redraw()


func straw_count() -> int:
	return _straws.size()


func print_count() -> int:
	return _prints.size()
