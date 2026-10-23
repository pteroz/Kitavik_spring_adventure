extends Control
## Главное меню: ENTER — экран истории, ESC — выход.


func _unhandled_input(event: InputEvent) -> void:
	if not (event is InputEventKey) or not event.pressed or event.echo:
		return
	match event.keycode:
		KEY_ENTER, KEY_KP_ENTER:
			get_tree().change_scene_to_file("res://scenes/story.tscn")
		KEY_ESCAPE:
			get_tree().quit()
