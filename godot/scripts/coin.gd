class_name Coin
extends Area2D
## Монета: исчезает при касании игроком и сообщает об этом уровню.

signal collected

var _taken := false


func _ready() -> void:
	body_entered.connect(_on_body_entered)


func _on_body_entered(body: Node2D) -> void:
	if _taken or not body.is_in_group("player"):
		return
	_taken = true
	collected.emit()
	queue_free()
