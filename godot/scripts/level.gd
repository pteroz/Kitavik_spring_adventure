extends Node2D
## Контроллер тестового уровня: респавн при падении/смерти и рестарт.

@onready var player: CharacterBody2D = $Player
@onready var spawn: Marker2D = $SpawnPoint

var _invuln := 0.0


func _ready() -> void:
	if not player.died.is_connected(_on_death):
		player.died.connect(_on_death)
	_respawn()


func _physics_process(delta: float) -> void:
	if _invuln > 0.0:
		_invuln -= delta
	if player.global_position.y > GameConfig.KILL_Y:
		_respawn()


func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("restart"):
		get_tree().reload_current_scene()


func _on_death() -> void:
	if _invuln <= 0.0:
		_respawn()


func _respawn() -> void:
	_invuln = 0.5
	player.respawn(spawn.position)
