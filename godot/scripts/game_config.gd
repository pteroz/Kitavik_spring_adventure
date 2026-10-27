extends Node
## Порт констант из Kitavik `src/constants.py` в единый источник настройки
## физики/управления и построение карты ввода в рантайме.
## Здесь намеренно только то, что участвует в "ощущении" аркады.

# --- Слои коллизий (битовые маски) ---
const LAYER_SOLID := 1 << 0      # 1: земля/платформы
const LAYER_ONEWAY := 1 << 1     # 2: one-way платформы
const LAYER_PLAYER := 1 << 2     # 4: игрок (для детекта врагами)
const LAYER_SLIPPERY := 1 << 3   # 8: скользкая платформа (дополнительно к SOLID)
const LAYER_FRAGILE := 1 << 4    # 16: хрупкая платформа (дополнительно к SOLID)
const LAYER_BREAKABLE := 1 << 5  # 32: разбиваемый блок (дополнительно к SOLID)
const WORLD_MASK := LAYER_SOLID | LAYER_ONEWAY

# --- Камера / отрисовка ---
const VIEWPORT_W := 1280
const VIEWPORT_H := 720
const TILE := 32
const CAMERA_ZOOM := 1.7         # == CAMERA_ZOOM оригинала

# --- Игрок (пересчитано из импульсов pymunk в скорости Godot) ---
# В Arcade прыжок делался импульсом к телу массой PLAYER_MASS=2.0,
# т.е. стартовая скорость ~ impulse/2. Здесь фиксируем эти скорости.
# Темп 2026-10-27: движение и прыжки сначала замедлены в 1.4 раза, затем
# до 3/4 текущей скорости (суммарно ×1.8667 от исходной). Скорости и
# ускорения игрока умножены на 0.75, его гравитация — на 0.75², поэтому
# высота прыжка сохраняется, а время в воздухе растёт ещё в 1.333 раза.
# GRAVITY/MAX_FALL_SPEED ниже остаются общими для врагов.
const GRAVITY := 1500.0
const MAX_FALL_SPEED := 1500.0
const PLAYER_GRAVITY := 430.5        # 1500 / 1.8667²
const PLAYER_FALL_GRAVITY := PLAYER_GRAVITY * 1.5  # падение в 1.5 раза быстрее, подъём не меняется
const PLAYER_MAX_FALL_SPEED := 803.6  # 1500 / 1.8667

const WALK_SPEED := 139.3        # 260 / 1.8667
const RUN_SPEED := 241.1         # 450 / 1.8667 == PLAYER_MAX_HORIZONTAL_SPEED
const AIR_SPEED := 203.6         # 380 / 1.8667: управление в воздухе чуть слабее земли

const GROUND_ACCEL := 1285.7     # 2400 / 1.8667
const AIR_ACCEL := 482.2         # 900 / 1.8667
const GROUND_FRICTION := 1500.0  # 2800 / 1.8667: торможение при отпускании
const RUN_HOLD_THRESHOLD := 0.15 # == MOVE_SLOW_THRESHOLD: тап короче — минимальный рывок
const TAP_ACCEL := 107.2         # 200 / 1.8667 == PLAYER_MOVE_FORCE_SLOW 400 / масса 2
const TAP_SPEED := 16.1          # 30 / 1.8667: пик скорости за окно тапа
const DOUBLE_TAP_WINDOW := 0.25  # окно даблтапа (расширено с 0.15 для тач/клавиатуры)

# Три уровня прыжка из оригинала (импульс / масса 2.0):
# stand 1400/2, walk 1600/2, run 1800/2 — режим выбирается в момент прыжка.
const JUMP_VELOCITY_STAND := 375.0  # 700 / 1.8667
const JUMP_VELOCITY_WALK := 428.6   # 800 / 1.8667
const JUMP_VELOCITY_RUN := 482.2    # 900 / 1.8667
const JUMP_CUTOFF_TIME := 0.28   # 0.15 × 1.8667: окно, в котором отпускание гасит прыжок
const JUMP_CUT_MULTIPLIER := 0.4 # == JUMP_CUTOFF_MULTIPLIER
const COYOTE_TIME := 0.10        # прощение: прыжок сразу после схода с края
const JUMP_BUFFER_TIME := 0.10   # прощение: нажатие чуть раньше приземления
const DROP_THROUGH_TIME := 0.34  # 0.18 × 1.8667: при медленном падении нужно дольше

const PLAYER_SIZE := Vector2(20, 28)  # хитбокс (чуть уже спрайта 32x32)

# --- Враги ---
const ENEMY_PATROL_RANGE := 96.0
const ENEMY_SPEED := 60.0
const ENEMY_SIZE := Vector2(26, 20)
const ENEMY_MOVE_FORCE := 300.0  # значение по умолчанию из оригинала/Tiled
const ENEMY_FORCE_TO_SPEED := 0.2 # 300 силы → 60 px/s: калибровка порта
const ENEMY_HOP_VELOCITY := 800.0 # импульс 400 при массе 0.5 → Δv 800

# --- Специальные платформы (== constants.py) ---
const FRAGILE_BREAK_DELAY := 0.4   # таймер хрупкой платформы после наступания
const ICE_ACCELERATION := 0.3      # множитель ускорения на скользком полу
const ICE_DECELERATION := 0.05     # множитель трения на скользком полу
const STRAW_SPEED_MULTIPLIER := 1.0 / 1.5  # ходьба и бег по соломе медленнее в 1.5 раза
const MOVING_PLATFORM_SPEED := 120.0   # 2 px/кадр при 60 FPS
const MOVING_PLATFORM_TRAVEL := 200.0  # размах ±100 px от центра (как boundary оригинала)

# --- Границы уровня (для камеры) ---
const LEVEL_W := 2048
const LEVEL_H := 480
const KILL_Y := 600.0            # ниже — падение, респавн


func _ready() -> void:
	_build_input_map()


func _build_input_map() -> void:
	_action("move_left", [KEY_A, KEY_LEFT])
	_action("move_right", [KEY_D, KEY_RIGHT])
	_action("jump", [KEY_SPACE, KEY_W, KEY_UP])
	_action("drop_through", [KEY_S, KEY_DOWN])
	_action("run", [KEY_SHIFT])   # альтернатива даблтапу (доступность)
	_action("restart", [KEY_R])
	_action("toggle_debug", [KEY_F1])


func _action(name: String, keys: Array) -> void:
	if not InputMap.has_action(name):
		InputMap.add_action(name)
	for k in keys:
		var ev := InputEventKey.new()
		ev.physical_keycode = k
		ev.echo = (name == "jump")  # удержание прыжка не спамит буфер
		InputMap.action_add_event(name, ev)


func has_action(name: String) -> bool:
	return InputMap.has_action(name)
