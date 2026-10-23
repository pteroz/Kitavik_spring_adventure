class_name GameHud
extends CanvasLayer
## Мини-отладочный HUD: режим движения, скорость, контакт с полом, счёт.
## Управление — легенда внизу. F1 скрывает/показывает, R — рестарт.

@onready var info: Label = $Info
@onready var fps: Label = $Fps
@onready var score_label: Label = $Score

var score := 0
var _show := true
var _player: CharacterBody2D

const LEGEND := "← → / A D — движение · даблтап в сторону — бег · Shift — бег\nПробел/W/↑ — прыжок · S/↓ — соскочить вниз · R — рестарт · ESC — меню · F1 — HUD"


func _ready() -> void:
	info.text = ""
	score_label.text = "Очки: %d" % score
	_player = get_tree().get_first_node_in_group("player")


func add_score(amount: int = 1) -> void:
	score += amount
	score_label.text = "Очки: %d" % score


func _process(_dt: float) -> void:
	fps.text = "%d FPS" % Engine.get_frames_per_second()
	if Input.is_action_just_pressed("toggle_debug"):
		_show = not _show
	info.visible = _show
	if not _show or _player == null:
		return
	_refresh()


func _refresh() -> void:
	var v := _player.velocity
	var grounded := _player.is_on_floor()
	var mode := "WALK"
	if not grounded:
		mode = "AIR"
	elif _player.get("velocity") != null and absf(v.x) > GameConfig.WALK_SPEED + 20.0:
		mode = "RUN"
	info.text = "mode=%s  vx=%.0f  vy=%.0f  ground=%s\n%s" % [
		mode, v.x, v.y, grounded, LEGEND
	]
