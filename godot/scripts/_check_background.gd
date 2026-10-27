extends SceneTree
## Headless-проверка фона-сарая: параллакс по X и Y, бесшовный горизонтальный
## цикл, плотность 1 тексель на экранный пиксель, покрытие экрана при любом
## положении камеры.


var _ok := true


func _initialize() -> void:
	_run.call_deferred()


func _check(cond: bool, label: String) -> void:
	print(("OK   " if cond else "FAIL "), label)
	_ok = _ok and cond


func _run() -> void:
	# В headless окно 64x64, и вьюпорт растягивается до 1280x1280 — задаём
	# размер как у игры, чтобы проверять те же экранные координаты.
	root.size = Vector2i(GameConfig.VIEWPORT_W, GameConfig.VIEWPORT_H)
	await process_frame

	var level := (load("res://scenes/level1.tscn") as PackedScene).instantiate()
	root.add_child(level)
	await process_frame
	await physics_frame

	var backdrop := level.find_child("Backdrop", true, false) as Parallax2D
	_check(backdrop != null, "фон: узел Backdrop (Parallax2D) создан")
	if backdrop == null:
		print("RESULT: FAIL")
		quit(1)
		return

	_check(level.find_child("BackImage", true, false) == null,
		"фон: исходный BackImage из Tiled убран")

	var color := level.find_child("Background Color", true, false) as ColorRect
	_check(color == null or color.z_index < backdrop.z_index,
		"фон: подложка под параллаксом (z %d < %d)" % [
			color.z_index if color else -999, backdrop.z_index])

	var factor_x := backdrop.scroll_scale.x
	var factor_y := backdrop.scroll_scale.y
	_check(factor_x > 0.0 and factor_x < 1.0,
		"фон: параллакс по X относительно блоков (%.2f)" % factor_x)
	_check(factor_y > 0.0 and factor_y < 1.0,
		"фон: параллакс по Y (%.2f)" % factor_y)

	var rects: Array[TextureRect] = []
	for child in backdrop.get_children():
		if child is TextureRect:
			rects.append(child)
	_check(rects.size() == 2, "фон: две копии для бесшовного стыка (%d)" % rects.size())
	if rects.size() != 2:
		print("RESULT: FAIL")
		quit(1)
		return

	var tex := rects[0].texture
	var player := level.get_node("Player") as CharacterBody2D
	var cam := player.get_node("Camera2D") as Camera2D
	var art := Vector2(tex.get_width(), tex.get_height()) / cam.zoom.y
	_check(rects[0].flip_h != rects[1].flip_h, "фон: вторая копия отражена по X")
	_check(is_equal_approx(rects[0].position.x, 0.0)
		and is_equal_approx(rects[1].position.x, art.x),
		"фон: копии стыкуются по шагу картинки")
	_check(backdrop.repeat_size.x >= art.x * 2.0 - 1.0,
		"фон: шаг повтора равен паре копий (%.0f px)" % backdrop.repeat_size.x)
	_check(absf(rects[0].size.y - art.y) < 0.01
		and absf(rects[0].size.x - art.x) <= 2.5 / cam.zoom.y,
		"фон: 1 тексель = 1 экранный пиксель (%s при zoom %.2f)"
		% [rects[0].size, cam.zoom.y])
	_check(rects[1].position.x + rects[1].size.x > backdrop.repeat_size.x,
		"фон: копии перекрываются на стыке повтора")

	# --- Средний слой между дальним фоном и блоками ---
	var mid := level.find_child("Midground", true, false) as Parallax2D
	_check(mid != null, "средний слой: Midground (Parallax2D) создан")
	if mid == null:
		print("RESULT: FAIL")
		quit(1)
		return
	_check(mid.z_index > backdrop.z_index and mid.z_index < 0,
		"средний слой: между фоном (z %d) и блоками (z 0) — z %d"
		% [backdrop.z_index, mid.z_index])
	_check(mid.modulate.v < 0.8,
		"средний слой: приглушён (modulate %s), чтобы не читался как платформы"
		% mid.modulate)
	_check(mid.scroll_scale.x > factor_x and mid.scroll_scale.x < 1.0,
		"средний слой: движется быстрее дальнего фона по X (%.2f > %.2f)"
		% [mid.scroll_scale.x, factor_x])
	_check(is_equal_approx(mid.scroll_scale.y, factor_y),
		"средний слой: по высоте выровнен с дальним фоном (%.2f)" % mid.scroll_scale.y)

	var mid_rects: Array[TextureRect] = []
	for child in mid.get_children():
		if child is TextureRect:
			mid_rects.append(child)
	_check(mid_rects.size() == 2, "средний слой: две копии для стыка (%d)" % mid_rects.size())
	if mid_rects.size() != 2:
		print("RESULT: FAIL")
		quit(1)
		return
	var mid_tex := mid_rects[0].texture
	var mid_art := Vector2(mid_tex.get_width(), mid_tex.get_height()) / cam.zoom.y
	_check(mid_rects[0].flip_h != mid_rects[1].flip_h, "средний слой: вторая копия отражена по X")
	_check(is_equal_approx(mid_rects[0].position.x, 0.0)
		and is_equal_approx(mid_rects[1].position.x, mid_art.x),
		"средний слой: копии стыкуются по шагу картинки")
	_check(absf(mid_rects[0].size.y - mid_art.y) < 0.01
		and absf(mid_rects[0].size.x - mid_art.x) <= 2.5 / cam.zoom.y,
		"средний слой: 1 тексель = 1 экранный пиксель (%s)" % mid_rects[0].size)
	_check(mid_rects[1].position.x + mid_rects[1].size.x > mid.repeat_size.x,
		"средний слой: копии перекрываются на стыке повтора")

	# --- Покрытие экрана на всём ходу камеры (реальные экранные координаты) ---
	var smoothing := cam.position_smoothing_enabled
	cam.position_smoothing_enabled = false
	var vis := root.get_visible_rect().size
	var mid_spawn := _screen_rect(mid_rects[0])
	_check(mid_spawn.position.y < vis.y and mid_spawn.end.y > 0.0,
		"средний слой: виден в кадре спавна (%.0f..%.0f из %.0f)"
		% [mid_spawn.position.y, mid_spawn.end.y, vis.y])

	for spot in [Vector2(0.0, 0.0), Vector2(6400.0, 0.0),
			Vector2(0.0, 3200.0), Vector2(6400.0, 3200.0)]:
		player.global_position = spot
		player.velocity = Vector2.ZERO
		cam.reset_smoothing()
		for i in range(4):
			await process_frame
			await physics_frame
		var r := _screen_rect(rects[0])
		_check(r.position.y <= 0.5 and r.end.y >= vis.y - 0.5,
			"фон: экран покрыт по высоте у камеры %s (%.0f..%.0f из %.0f)"
			% [spot, r.position.y, r.end.y, vis.y])
		_check(_horizontal_covered(rects, backdrop.repeat_size.x * cam.zoom.x,
				backdrop.repeat_times, vis.x),
			"фон: экран покрыт по ширине у камеры %s" % spot)

	# --- Сдвиг фона при перемещении камеры по X ---
	player.global_position = Vector2(3200.0, 1874.0)
	cam.reset_smoothing()
	for i in range(4):
		await process_frame
		await physics_frame
	var cam_x0 := cam.get_screen_center_position().x
	var bg_x0 := backdrop.get_global_transform_with_canvas().origin.x
	var mid_x0 := mid.get_global_transform_with_canvas().origin.x
	player.global_position.x = 4200.0
	cam.reset_smoothing()
	for i in range(4):
		await process_frame
		await physics_frame
	var cam_x1 := cam.get_screen_center_position().x
	var bg_x1 := backdrop.get_global_transform_with_canvas().origin.x
	var mid_x1 := mid.get_global_transform_with_canvas().origin.x
	var cam_shift := cam_x1 - cam_x0
	var zoom := cam.zoom.x
	var screen_world_shift := -cam_shift * zoom
	# Зацикленный слой прыгает на repeat_size (в экранных px) — снимаем оборот.
	var period := backdrop.repeat_size.x * zoom
	var bg_shift := fposmod(bg_x1 - bg_x0 + period / 2.0, period) - period / 2.0
	var mid_period := mid.repeat_size.x * zoom
	var mid_shift := fposmod(mid_x1 - mid_x0 + mid_period / 2.0, mid_period) - mid_period / 2.0
	_check(absf(cam_x1 - player.global_position.x) < 1.0,
		"камера: центр сошёлся с игроком (%.1f)" % cam_x1)
	_check(absf(bg_shift - screen_world_shift * factor_x) < 2.0,
		"фон X: экранный сдвиг %.1f ≈ %.2f × %.1f (блоки)"
		% [bg_shift, factor_x, screen_world_shift])
	_check(absf(bg_shift) < absf(screen_world_shift),
		"фон X: движется медленнее блоков (%.1f < %.1f)"
		% [absf(bg_shift), absf(screen_world_shift)])
	_check(absf(mid_shift - screen_world_shift * mid.scroll_scale.x) < 2.0,
		"средний слой X: экранный сдвиг %.1f ≈ %.2f × %.1f"
		% [mid_shift, mid.scroll_scale.x, screen_world_shift])
	_check(absf(mid_shift) > absf(bg_shift),
		"средний слой X: движется быстрее дальнего фона (%.1f > %.1f)"
		% [absf(mid_shift), absf(bg_shift)])

	# --- Сдвиг фона при перемещении камеры по Y ---
	var cam_y0 := cam.get_screen_center_position().y
	var bg_y0 := backdrop.get_global_transform_with_canvas().origin.y
	player.global_position.y = 2400.0
	cam.reset_smoothing()
	for i in range(4):
		await process_frame
		await physics_frame
	var cam_y1 := cam.get_screen_center_position().y
	var bg_y1 := backdrop.get_global_transform_with_canvas().origin.y
	cam.position_smoothing_enabled = smoothing
	var cam_shift_y := cam_y1 - cam_y0
	var screen_shift_y := -cam_shift_y * zoom
	var bg_shift_y := bg_y1 - bg_y0
	_check(absf(cam_y1 - player.global_position.y) < 1.0,
		"камера Y: центр сошёлся с игроком (%.1f)" % cam_y1)
	_check(absf(bg_shift_y - screen_shift_y * factor_y) < 2.0,
		"фон Y: экранный сдвиг %.1f ≈ %.2f × %.1f (блоки)"
		% [bg_shift_y, factor_y, screen_shift_y])

	level.queue_free()
	await process_frame

	print("RESULT: ", "PASS" if _ok else "FAIL")
	quit(0 if _ok else 1)


## Прямоугольник копии фона в экранных пикселях.
func _screen_rect(rect: TextureRect) -> Rect2:
	var xf := rect.get_global_transform_with_canvas()
	return Rect2(xf.origin, rect.size * xf.get_scale())


## Копии вместе накрывают экран по горизонтали (стык без дыр).
## repeat_times рисует копии параллакса влево/вправо от узлов — учитываем их.
func _horizontal_covered(rects: Array[TextureRect], period_px: float,
		times: int, vis_w: float) -> bool:
	var spans: Array[Vector2] = []
	for r in rects:
		var sr := _screen_rect(r)
		for k in range(-times, times + 1):
			var shift := k * period_px
			spans.append(Vector2(sr.position.x + shift, sr.end.x + shift))
	spans.sort_custom(func(a: Vector2, b: Vector2) -> bool: return a.x < b.x)
	var covered := 0.0
	for span in spans:
		if span.x > covered + 1.0:
			return false
		covered = maxf(covered, span.y)
		if covered >= vis_w - 1.0:
			return true
	return covered >= vis_w - 1.0
