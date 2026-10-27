extends SceneTree
## Headless-проверка поверхности под игроком: разметка тайлов, соломинки,
## снежные следы и скольжение по льду на реальной карте level1.

var _ok := true


func _initialize() -> void:
	_run.call_deferred()


func _check(cond: bool, label: String) -> void:
	print(("OK   " if cond else "FAIL "), label)
	_ok = _ok and cond


func _teleport(player: CharacterBody2D, at: Vector2) -> void:
	player.velocity = Vector2.ZERO
	player.global_position = at


func _run() -> void:
	var level := (load("res://scenes/level1.tscn") as PackedScene).instantiate()
	root.add_child(level)
	await process_frame
	await physics_frame

	var platforms := level.find_child("Platforms", true, false) as TileMapLayer
	var player := level.get_node("Player") as CharacterBody2D
	var fx := player.get_node("GroundFx")

	var counts := {"ice": 0, "snow": 0, "straw": 0}
	for cell in platforms.get_used_cells():
		var data := platforms.get_cell_tile_data(cell)
		if data == null:
			continue
		var surface := String(data.get_meta("surface", ""))
		if counts.has(surface):
			counts[surface] = int(counts[surface]) + 1
	_check(counts["ice"] > 0 and counts["snow"] > 0 and counts["straw"] > 0,
		"карта: поверхности ice=%d snow=%d straw=%d" % [
			counts["ice"], counts["snow"], counts["straw"]])

	var slippery_bodies := 0
	for child in level.get_children():
		if child is StaticBody2D and (child.collision_layer & GameConfig.LAYER_SLIPPERY) != 0:
			slippery_bodies += 1
	_check(slippery_bodies > 0, "лёд: тело с LAYER_SLIPPERY найдено (%d)" % slippery_bodies)

	# --- Солома: прутки при ходьбе ---
	_teleport(player, Vector2(880.0, 1298.0))
	for i in 10:
		await physics_frame
	_check(player.is_on_floor(), "солома: игрок стоит на платформе")
	_check(player.get_floor_surface() == "straw",
		"солома: поверхность определена (%s)" % player.get_floor_surface())
	Input.action_press("move_right")
	for i in 30:
		await physics_frame
	var straws: int = fx.straw_count()
	var straw_speed := absf(player.velocity.x)
	Input.action_release("move_right")
	_check(straws > 0, "солома: прутки вылетают при ходьбе (%d)" % straws)
	var straw_cap := GameConfig.WALK_SPEED * GameConfig.STRAW_SPEED_MULTIPLIER
	_check(straw_speed > straw_cap * 0.8 and straw_speed <= straw_cap + 2.0,
		"солома: ходьба замедлена в 1.5 раза (%.1f px/s, предел %.1f)" % [straw_speed, straw_cap])

	# --- Снег: следы под лапами ---
	fx.clear()
	_teleport(player, Vector2(2608.0, 1330.0))
	for i in 10:
		await physics_frame
	_check(player.get_floor_surface() == "snow",
		"снег: поверхность определена (%s)" % player.get_floor_surface())
	Input.action_press("move_right")
	for i in 30:
		await physics_frame
	var prints: int = fx.print_count()
	Input.action_release("move_right")
	_check(prints > 0, "снег: остаются следы (%d)" % prints)

	# --- Лёд: скольжение ---
	fx.clear()
	_teleport(player, Vector2(1776.0, 1202.0))
	for i in 10:
		await physics_frame
	_check(player.get_floor_surface() == "ice",
		"лёд: поверхность определена (%s)" % player.get_floor_surface())
	_check(player.get("_floor_slippery") == true, "лёд: пол скользкий")
	Input.action_press("run")
	Input.action_press("move_right")
	for i in 18:
		await physics_frame
	var ice_speed: float = player.velocity.x
	Input.action_release("move_right")
	Input.action_release("run")
	for i in 18:
		await physics_frame
	var coast: float = player.velocity.x
	_check(ice_speed < 150.0, "лёд: медленный разгон (%.1f < 150)" % ice_speed)
	_check(coast > 60.0, "лёд: долгое торможение (%.1f > 60)" % coast)
	_check(fx.straw_count() == 0 and fx.print_count() == 0,
		"лёд: эффектов соломы и снега нет")

	print("RESULT: ", "PASS" if _ok else "FAIL")
	quit(0 if _ok else 1)
