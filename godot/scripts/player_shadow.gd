extends Node2D
## Мягкая тень под игроком: рисуется только над опорными блоками.
## Каждая вертикальная полоса проверяется коротким лучом вниз, поэтому
## на краю платформы тень обрезается, а не свисает на фон.

const TEXTURE := preload("res://assets/images/player/shadow.png")
const COLUMNS := 16
const HALF_WIDTH := 16.0
const HEIGHT := 8.0

var _player: CharacterBody2D


func _ready() -> void:
	_player = get_parent() as CharacterBody2D


func _physics_process(_delta: float) -> void:
	queue_redraw()


func _draw() -> void:
	if _player == null or modulate.a <= 0.001:
		return
	var space := get_world_2d().direct_space_state
	var exclude := [_player.get_rid()]
	var y0 := _player.global_position.y + 10.0
	var y1 := _player.global_position.y + 26.0
	var slice_w := HALF_WIDTH * 2.0 / COLUMNS
	var src_w := TEXTURE.get_width() / float(COLUMNS)
	for i in COLUMNS:
		var x := global_position.x - HALF_WIDTH + (i + 0.5) * slice_w
		var params := PhysicsRayQueryParameters2D.create(
			Vector2(x, y0), Vector2(x, y1), GameConfig.WORLD_MASK, exclude)
		var hit: Dictionary = space.intersect_ray(params)
		if hit.is_empty() or hit.normal.y > -0.5:
			continue
		draw_texture_rect_region(
			TEXTURE,
			Rect2(-HALF_WIDTH + i * slice_w, -HEIGHT * 0.5, slice_w, HEIGHT),
			Rect2(i * src_w, 0.0, src_w, TEXTURE.get_height()))
