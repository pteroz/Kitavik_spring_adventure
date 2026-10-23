class_name RatEnemy
extends CharacterBody2D
## Враг-крыса: патрулирует вокруг точки старта, проигрывает 3-кадровую
## походку из rat_enemy.png, Area2D-детектор возвращает игрока на спавн.

@export var patrol_range := GameConfig.ENEMY_PATROL_RANGE
@export var speed := GameConfig.ENEMY_SPEED

@onready var sprite: Sprite2D = $Sprite
@onready var hurtbox: Area2D = $HurtBox

var _start_x := 0.0
var _dir := 1.0
var _frames: Array[AtlasTexture] = []
var _frame_idx := 0
var _anim_t := 0.0
var _frame_dur := 0.1


func _ready() -> void:
	_start_x = global_position.x
	_build_frames()
	if is_instance_valid(hurtbox):
		hurtbox.body_entered.connect(_on_hurtbox)


func _build_frames() -> void:
	var tex := sprite.texture
	if tex == null:
		return
	var fw := int(tex.get_width() / 3.0)  # 96 / 3 = 32
	for i in range(3):
		var a := AtlasTexture.new()
		a.atlas = tex
		a.region = Rect2(i * fw, 0, fw, tex.get_height())
		_frames.append(a)
	if not _frames.is_empty():
		sprite.texture = _frames[0]


func _physics_process(delta: float) -> void:
	if not is_on_floor():
		velocity.y += GameConfig.GRAVITY * delta
		velocity.y = minf(velocity.y, GameConfig.MAX_FALL_SPEED)

	velocity.x = _dir * speed
	move_and_slide()

	# разворот по границе патруля
	if global_position.x > _start_x + patrol_range:
		_dir = -1.0
	elif global_position.x < _start_x - patrol_range:
		_dir = 1.0

	# упёрся в стену на земле — подпрыгнуть, чтобы продолжить путь
	if is_on_floor() and absf(velocity.x) < 10.0:
		velocity.y = -GameConfig.ENEMY_HOP_VELOCITY

	_animate(delta)


func _animate(delta: float) -> void:
	if _frames.is_empty():
		return
	sprite.flip_h = _dir < 0.0
	if absf(velocity.x) < 5.0:
		return
	_anim_t += delta
	if _anim_t >= _frame_dur:
		_anim_t = 0.0
		_frame_idx = (_frame_idx + 1) % _frames.size()
		sprite.texture = _frames[_frame_idx]


func _on_hurtbox(body: Node2D) -> void:
	if body.has_method("die"):
		body.die()
