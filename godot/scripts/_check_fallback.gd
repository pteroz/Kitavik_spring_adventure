extends SceneTree
## Headless-проверка запасного уровня: карта не найдена → площадка, монеты, лимиты.

var _ok := true


func _initialize() -> void:
	_run.call_deferred()


func _check(cond: bool, label: String) -> void:
	print(("OK   " if cond else "FAIL "), label)
	_ok = _ok and cond


func _run() -> void:
	var level := (load("res://scenes/level1.tscn") as PackedScene).instantiate()
	level.map_path = "res://assets/maps/does_not_exist.tmx"
	root.add_child(level)
	await process_frame

	for i in range(30):
		await physics_frame

	var player := level.get_node("Player") as CharacterBody2D
	_check(player.is_on_floor(), "запасной: игрок приземлился")
	_check(absf(player.global_position.x - 120.0) < 2.0,
		"запасной: спавн x=120 (%.1f)" % player.global_position.x)
	_check(player.global_position.y > 360.0 and player.global_position.y < 400.0,
		"запасной: стоит на земле (y=%.1f)" % player.global_position.y)

	var coins := 0
	var textured := 0
	for child in level.get_children():
		if child is Coin:
			coins += 1
			if (child.get_node("Sprite") as Sprite2D).texture != null:
				textured += 1
	_check(coins == 3, "запасной: 3 монеты (найдено %d)" % coins)
	_check(textured == 3, "запасной: у монет есть текстуры (%d)" % textured)

	var cam := player.get_node("Camera2D") as Camera2D
	_check(cam.limit_right == 1280 and cam.limit_bottom == 720,
		"запасной: лимиты камеры 1280x720")

	print("RESULT: ", "PASS" if _ok else "FAIL")
	quit(0 if _ok else 1)
