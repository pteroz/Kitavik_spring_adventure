extends Control
## Слайды истории из assets/story/level{N}.json (запасной — story.json).
## ENTER/SPACE/RIGHT — далее, LEFT — назад, ESC — пропустить.

const STORY_DIR := "res://assets/story"
const LEVEL_SCENE := "res://scenes/level1.tscn"
const FALLBACK_TEXT := "История ещё не написана...\nНажмите ENTER, чтобы начать игру."

var level := 1
var slides: Array = []
var index := 0

@onready var image_rect: TextureRect = $Image
@onready var slide_text: Label = $SlideText


func _ready() -> void:
	_load_slides()
	_apply(0)


func _load_slides() -> void:
	var path := "%s/level%d.json" % [STORY_DIR, level]
	if not FileAccess.file_exists(path):
		path = STORY_DIR + "/story.json"

	if FileAccess.file_exists(path):
		var data: Variant = JSON.parse_string(FileAccess.get_file_as_string(path))
		if data is Array:
			for slide in data:
				if slide is Dictionary:
					slides.append(slide)

	if slides.is_empty():
		slides.append({"text": FALLBACK_TEXT})


func _apply(slide_index: int) -> void:
	index = clampi(slide_index, 0, slides.size() - 1)
	var slide: Dictionary = slides[index]

	var image_name: String = str(slide.get("image", ""))
	var image_path := "%s/%s" % [STORY_DIR, image_name]
	var tex: Texture2D = null
	if image_name != "" and ResourceLoader.exists(image_path):
		tex = load(image_path) as Texture2D

	image_rect.texture = tex
	image_rect.visible = tex != null

	slide_text.text = str(slide.get("text", ""))
	if tex != null:
		slide_text.anchor_top = 1.0
		slide_text.anchor_bottom = 1.0
		slide_text.offset_top = -150.0
		slide_text.offset_bottom = -55.0
		slide_text.add_theme_font_size_override("font_size", 18)
	else:
		slide_text.anchor_top = 0.0
		slide_text.anchor_bottom = 1.0
		slide_text.offset_top = 0.0
		slide_text.offset_bottom = 0.0
		slide_text.add_theme_font_size_override("font_size", 22)


func _unhandled_input(event: InputEvent) -> void:
	if not (event is InputEventKey) or not event.pressed or event.echo:
		return
	match event.keycode:
		KEY_ENTER, KEY_KP_ENTER, KEY_SPACE, KEY_RIGHT:
			_next()
		KEY_LEFT:
			if index > 0:
				_apply(index - 1)
		KEY_ESCAPE:
			_finish()


func _next() -> void:
	if index + 1 < slides.size():
		_apply(index + 1)
	else:
		_finish()


func _finish() -> void:
	get_tree().change_scene_to_file(LEVEL_SCENE)
