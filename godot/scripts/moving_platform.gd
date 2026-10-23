extends AnimatableBody2D
## Плавная качающаяся платформа. Двигается прямым заданием position:
## AnimatableBody2D так корректно переносит CharacterBody2D-игрока сверху.

@export var travel := Vector2(220, 0)
@export var period := 3.0
@export var speed := 0.0   # > 0 — линейный ход с отскоком (платформы из карты)

var _t := 0.0
var _start := Vector2.ZERO


func _ready() -> void:
	_start = position


func _physics_process(delta: float) -> void:
	_t += delta
	if speed > 0.0 and travel.length() > 0.01:
		# треугольная волна: центр → +travel/2 → −travel/2 → центр
		var cycle := 2.0 * travel.length() / speed
		var phase := fposmod(0.25 + _t / cycle, 1.0)
		var tri := 1.0 - absf(2.0 * phase - 1.0)
		position = _start + travel * (tri - 0.5)
	else:
		var f := 0.5 - 0.5 * cos(TAU * _t / period)  # 0..1..0, гладко
		position = _start + travel * f
