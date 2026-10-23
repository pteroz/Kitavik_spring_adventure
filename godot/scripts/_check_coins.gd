extends SceneTree
## Headless-проверка: ячейка слоя Coins → монета → подбор → счёт.


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var level = (load("res://scenes/level1.tscn") as PackedScene).instantiate()
	root.add_child(level)
	await process_frame
	await physics_frame

	var hud: GameHud = level.get_node("HUD")
	var score_label := hud.get_node("Score") as Label
	var player := level.get_node("Player") as CharacterBody2D
	print("HUD initial=", score_label.text)
	var ok := score_label.text == "Очки: 0" and hud.score == 0

	var map: Node2D = level.get_child(0)
	var layer := map.find_child("Coins", true, false) as TileMapLayer
	var cell := layer.local_to_map(layer.to_local(player.global_position))
	var source := layer.tile_set.get_source(0) as TileSetAtlasSource
	layer.set_cell(cell, 0, source.get_tile_id(0))
	print("cells before spawn=", layer.get_used_cells().size())
	ok = ok and layer.get_used_cells().size() == 1

	level.call("_spawn_coins", map)

	var coin: Coin = null
	for child in level.get_children():
		if child is Coin:
			coin = child
			break
	var has_texture := coin != null and (coin.get_node("Sprite") as Sprite2D).texture != null
	print("coin spawned=", coin != null, " texture=", has_texture,
		" cells after spawn=", layer.get_used_cells().size())
	ok = ok and coin != null and has_texture and layer.get_used_cells().is_empty()

	for i in range(5):
		await physics_frame

	print("HUD after=", score_label.text, " score=", hud.score,
		" coin_freed=", not is_instance_valid(coin))
	ok = ok and score_label.text == "Очки: 1" and hud.score == 1 and not is_instance_valid(coin)
	print("RESULT: ", "PASS" if ok else "FAIL")
	quit(0 if ok else 1)
