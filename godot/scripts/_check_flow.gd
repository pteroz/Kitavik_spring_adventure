extends SceneTree
## Headless-проверка потока: меню → история → уровень → меню.

var _failures := 0


func _initialize() -> void:
	_run.call_deferred()


func _key(code: int) -> InputEventKey:
	var event := InputEventKey.new()
	event.keycode = code
	event.pressed = true
	return event


func _check(condition: bool, message: String) -> void:
	if condition:
		print("OK   ", message)
	else:
		_failures += 1
		print("FAIL ", message)


func _gap() -> void:
	await process_frame
	await process_frame


func _run() -> void:
	var menu = (load("res://scenes/menu.tscn") as PackedScene).instantiate()
	root.add_child(menu)
	await process_frame

	_check(menu.name == "Menu" and menu.scene_file_path == "res://scenes/menu.tscn", "menu scene loads")
	var title := menu.get_node("Center/Title") as Label
	var start_hint := menu.get_node("Center/StartHint") as Label
	var exit_hint := menu.get_node("Center/ExitHint") as Label
	var background := menu.get_node("Background") as ColorRect
	_check(title.text == "Kitavik Spring Adventure", "menu title")
	_check(start_hint.text == "Нажмите ENTER для начала игры", "menu start hint")
	_check(exit_hint.text == "ESC — выход", "menu exit hint")
	_check(background.color == Color(0.4, 0.4, 0.6, 1.0), "menu background")

	menu.call("_unhandled_input", _key(KEY_ENTER))
	await _gap()

	var story = current_scene
	_check(story != null and story.name == "Story", "ENTER opens story")
	if story == null:
		print("RESULT: FAIL")
		quit(1)
		return

	var slides: Array = story.get("slides")
	var slide_label := story.get_node("SlideText") as Label
	var hint := story.get_node("Hint") as Label
	_check(slides.size() == 3, "story has 3 slides")
	_check(slide_label.text.begins_with("Давным-давно"), "first slide text")
	_check(hint.text == "ENTER — далее   |   ESC — пропустить", "story hint")

	story.call("_unhandled_input", _key(KEY_RIGHT))
	await process_frame
	_check(int(story.get("index")) == 1, "RIGHT advances slide")
	story.call("_unhandled_input", _key(KEY_LEFT))
	await process_frame
	_check(int(story.get("index")) == 0, "LEFT goes back")
	for i in range(3):
		story.call("_unhandled_input", _key(KEY_ENTER))
		await process_frame
	await _gap()

	var level = current_scene
	_check(level != null and level.name == "Level1", "last slide starts level")
	if level != null:
		level.call("_unhandled_input", _key(KEY_ESCAPE))
		await _gap()
		var back = current_scene
		_check(back != null and back.scene_file_path == "res://scenes/menu.tscn",
			"ESC returns to menu")

	print("RESULT: ", "PASS" if _failures == 0 else "%d FAIL" % _failures)
	quit(0 if _failures == 0 else 1)
