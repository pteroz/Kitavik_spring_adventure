extends SceneTree

var _frames := 0
var _level: Node


func _initialize() -> void:
	var packed: PackedScene = load("res://scenes/level1.tscn")
	_level = packed.instantiate()
	root.add_child(_level)


func _process(_delta: float) -> bool:
	_frames += 1
	if _frames == 5:
		var player: CharacterBody2D = _level.get_node("Player")
		var cam: Camera2D = player.get_node("Camera2D")
		print("camera limits=", cam.limit_left, ",", cam.limit_top, " -> ", cam.limit_right, ",", cam.limit_bottom)
		var enemies := 0
		var statics := 0
		var shapes := 0
		for child in _level.get_children():
			if child.scene_file_path == "res://scenes/enemy_rat.tscn":
				enemies += 1
			if child is StaticBody2D:
				statics += 1
				shapes += child.get_child_count()
		print("enemies=", enemies, " static_bodies=", statics, " shapes=", shapes)
		var platforms: TileMapLayer = _level.find_child("Platforms", true, false)
		print("platform cells=", platforms.get_used_cells().size() if platforms else "none")
	if _frames == 180:
		var player: CharacterBody2D = _level.get_node("Player")
		print("player pos=", player.global_position, " floor=", player.is_on_floor(), " vy=", player.velocity.y)
		var first_enemy: CharacterBody2D = null
		for child in _level.get_children():
			if child.scene_file_path == "res://scenes/enemy_rat.tscn":
				first_enemy = child
				break
		if first_enemy:
			print("enemy pos=", first_enemy.global_position, " floor=", first_enemy.is_on_floor())
	return _frames > 200
