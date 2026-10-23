extends SceneTree
## Одноразовый headless-генератор сцен. Запуск:
##   godot --headless --path <proj> --script res://scripts/_scaffold.gd
## Godot сам сериализует валидные .tscn из кода, вместо ручного текста сцен.

const SK_PLAYER := preload("res://scripts/player.gd")
const SK_ENEMY := preload("res://scripts/enemy_rat.gd")
const SK_LEVEL := preload("res://scripts/level.gd")
const SK_HUD := preload("res://scripts/hud.gd")
const SK_PLATFORM := preload("res://scripts/moving_platform.gd")

const C := preload("res://scripts/game_config.gd")

const TEX_PLAYER := preload("res://assets/images/player/kitavik.png")
const TEX_RAT := preload("res://assets/images/enemies/rat_enemy.png")
const TEX_GRASS := preload("res://assets/images/tiles/grass_ground.png")

const SOIL := Color(0.36, 0.24, 0.14)


func _initialize() -> void:
	_save(_build_player(), "res://scenes/player.tscn")
	_save(_build_enemy(), "res://scenes/enemy_rat.tscn")
	_save(_build_level(), "res://scenes/level_test.tscn")
	print("SCAFFOLD_OK")
	quit()


func _save(root: Node, path: String) -> void:
	_own(root, root)
	var ps := PackedScene.new()
	var err := ps.pack(root)
	if err != OK:
		push_error("pack failed for " + path)
		return
	var rerr := ResourceSaver.save(ps, path)
	if rerr != OK:
		push_error("save failed (%d) for %s" % [rerr, path])
	root.free()


func _own(node: Node, owner: Node) -> void:
	for c in node.get_children():
		c.owner = owner
		_own(c, owner)


# -- Player -------------------------------------------------------------

func _build_player() -> Node:
	var body := CharacterBody2D.new()
	body.name = "Player"
	body.set_script(SK_PLAYER)
	body.collision_layer = C.LAYER_PLAYER
	body.collision_mask = C.WORLD_MASK
	body.add_to_group("player")
	body.position = Vector2(120, 360)

	var spr := Sprite2D.new()
	spr.name = "Sprite"
	spr.texture = TEX_PLAYER
	body.add_child(spr)

	var cs := CollisionShape2D.new()
	cs.name = "CollisionShape2D"
	var rect := RectangleShape2D.new()
	rect.size = C.PLAYER_SIZE
	cs.shape = rect
	body.add_child(cs)

	var cam := Camera2D.new()
	cam.name = "Camera2D"
	cam.zoom = Vector2(C.CAMERA_ZOOM, C.CAMERA_ZOOM)
	cam.limit_left = 0
	cam.limit_top = 0
	cam.limit_right = C.LEVEL_W
	cam.limit_bottom = C.LEVEL_H
	cam.position_smoothing_enabled = true
	cam.position_smoothing_speed = 8.0
	body.add_child(cam)

	return body


# -- Enemy --------------------------------------------------------------

func _build_enemy() -> Node:
	var body := CharacterBody2D.new()
	body.name = "EnemyRat"
	body.set_script(SK_ENEMY)
	body.collision_layer = 0
	body.collision_mask = C.WORLD_MASK

	var spr := Sprite2D.new()
	spr.name = "Sprite"
	spr.texture = TEX_RAT
	body.add_child(spr)

	var cs := CollisionShape2D.new()
	cs.name = "CollisionShape2D"
	var rect := RectangleShape2D.new()
	rect.size = C.ENEMY_SIZE
	cs.shape = rect
	body.add_child(cs)

	var hb := Area2D.new()
	hb.name = "HurtBox"
	hb.collision_layer = 0
	hb.collision_mask = C.LAYER_PLAYER
	var hcs := CollisionShape2D.new()
	hcs.name = "CollisionShape2D"
	var hrect := RectangleShape2D.new()
	hrect.size = C.ENEMY_SIZE
	hcs.shape = hrect
	hb.add_child(hcs)
	body.add_child(hb)

	return body


# -- Level --------------------------------------------------------------

func _build_level() -> Node:
	var level := Node2D.new()
	level.name = "LevelTest"
	level.set_script(SK_LEVEL)

	_sky(level)

	var spawn := Marker2D.new()
	spawn.name = "SpawnPoint"
	spawn.position = Vector2(120, 360)
	level.add_child(spawn)

	# курс: ground1 -> яма с плавающими/onestop-платформами -> движущаяся -> ground2
	_platform(level, Vector2(0, 400), Vector2(720, 80), false)
	_platform(level, Vector2(800, 320), Vector2(160, 32), false)
	_platform(level, Vector2(1000, 240), Vector2(140, 24), true)
	_platform(level, Vector2(1180, 160), Vector2(140, 24), true)
	_moving(level, Vector2(1400, 300), Vector2(140, 28), Vector2(0, -160), 3.5)
	_platform(level, Vector2(1500, 400), Vector2(548, 80), false)

	var player := _build_player()
	player.name = "Player"
	level.add_child(player)

	for epos in [Vector2(400, 380), Vector2(1700, 380), Vector2(1900, 380)]:
		var e := _build_enemy()
		e.name = "Enemy"
		e.position = epos
		level.add_child(e)

	_hud(level)
	return level


func _sky(parent: Node) -> void:
	var sky := ColorRect.new()
	sky.name = "Sky"
	sky.color = Color(0.04, 0.06, 0.12)
	sky.z_index = -100
	sky.offset_left = -400
	sky.offset_top = -400
	sky.offset_right = C.LEVEL_W + 400
	sky.offset_bottom = C.LEVEL_H + 400
	parent.add_child(sky)


func _platform(parent: Node, top_left: Vector2, size: Vector2, oneway: bool) -> void:
	var body := StaticBody2D.new()
	body.name = "Platform"
	body.collision_layer = C.LAYER_ONEWAY if oneway else C.LAYER_SOLID
	body.collision_mask = 0
	body.position = top_left + size * 0.5

	var cs := CollisionShape2D.new()
	cs.name = "CollisionShape2D"
	var rect := RectangleShape2D.new()
	rect.size = size
	cs.shape = rect
	cs.one_way_collision = oneway
	body.add_child(cs)

	var soil := ColorRect.new()
	soil.name = "Soil"
	soil.color = SOIL
	soil.offset_left = -size.x * 0.5
	soil.offset_top = -size.y * 0.5
	soil.offset_right = size.x * 0.5
	soil.offset_bottom = size.y * 0.5
	body.add_child(soil)

	var grass := _grass_band(size)
	body.add_child(grass)

	parent.add_child(body)


func _grass_band(size: Vector2) -> Control:
	var tx := TextureRect.new()
	tx.name = "Grass"
	tx.texture = TEX_GRASS
	tx.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	tx.stretch_mode = TextureRect.STRETCH_TILE
	tx.texture_repeat = CanvasItem.TEXTURE_REPEAT_ENABLED
	tx.offset_left = -size.x * 0.5
	tx.offset_top = -size.y * 0.5
	tx.offset_right = size.x * 0.5
	tx.offset_bottom = -size.y * 0.5 + minf(size.y, 32.0)
	return tx


func _moving(parent: Node, center: Vector2, size: Vector2, travel: Vector2, period: float) -> void:
	var body := AnimatableBody2D.new()
	body.name = "MovingPlatform"
	body.set_script(SK_PLATFORM)
	body.collision_layer = C.LAYER_SOLID
	body.collision_mask = 0
	body.position = center
	body.set("travel", travel)
	body.set("period", period)

	var cs := CollisionShape2D.new()
	cs.name = "CollisionShape2D"
	var rect := RectangleShape2D.new()
	rect.size = size
	cs.shape = rect
	body.add_child(cs)

	var soil := ColorRect.new()
	soil.name = "Soil"
	soil.color = Color(0.30, 0.30, 0.42)
	soil.offset_left = -size.x * 0.5
	soil.offset_top = -size.y * 0.5
	soil.offset_right = size.x * 0.5
	soil.offset_bottom = size.y * 0.5
	body.add_child(soil)

	var grass := _grass_band(size)
	body.add_child(grass)

	parent.add_child(body)


func _hud(parent: Node) -> void:
	var hud := CanvasLayer.new()
	hud.name = "HUD"
	hud.set_script(SK_HUD)

	var info := Label.new()
	info.name = "Info"
	info.position = Vector2(16, 12)
	info.add_theme_font_size_override("font_size", 16)
	info.add_theme_color_override("font_color", Color(0.85, 0.9, 1.0))
	hud.add_child(info)

	var fps := Label.new()
	fps.name = "Fps"
	fps.anchor_left = 1.0
	fps.anchor_right = 1.0
	fps.offset_left = -160.0
	fps.offset_top = 12.0
	fps.offset_right = -16.0
	fps.offset_bottom = 40.0
	fps.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	fps.add_theme_font_size_override("font_size", 16)
	fps.add_theme_color_override("font_color", Color(0.6, 0.95, 0.6))
	hud.add_child(fps)

	parent.add_child(hud)
