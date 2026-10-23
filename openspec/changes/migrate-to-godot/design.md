# Design: migrate-to-godot

Технические решения переноса. Living-спеки (`specs/*`) задают **что** должно работать; этот документ — **как** это воспроизвести в Godot 4.7.

## 1. Расположение проекта (решено)

**Решение (2026-10-23): подпапка `godot/` в `Kitavik_spring_adventure`.**

Один репозиторий: спеки, ассеты и Godot-код рядом, история общая. Python-код остаётся в `src/` до подтверждения parity. Бывший `godot-probe` перенесён в `godot/` (без кэша `.godot/`), импорт и headless-прогон в новом месте проходят чисто.

## 2. Соответствие движков и физики

| Python/Arcade + pymunk | Godot 4.7 |
|---|---|
| `arcade.View` (Menu/Story/Game/Pause) | `Node`-сцены + `get_tree().change_scene_to_file()` |
| `arcade.Sprite` | `Sprite2D` / `AnimatedSprite2D` |
| `arcade.SpriteList` | `Node2D`-контейнеры, группы |
| `PymunkPhysicsEngine`, `space.gravity` | встроенная 2D-физика, `project.godot → physics/2d/default_gravity` |
| игрок: pymunk dynamic body (mass 2, impulse/force) | `CharacterBody2D` + `move_and_slide()` (скоростная модель) |
| стены/платформы: static body | `StaticBody2D` + `CollisionShape2D` |
| движущиеся платформы: kinematic body | `AnimatableBody2D` (переносит игрока автоматически) |
| one-way: collision handler (возврат False) | `CollisionShape2D.one_way_collision = true` |
| collision handlers (fragile/breakable/enemy) | сигналы `Area2D` (`body_entered`) / `move_and_slide` + проверка пола |
| `arcade.load_tilemap` + `Scene.from_tilemap` | `TileMapLayer` + `TileSet` (импорт из TMX, см. §6) |
| `arcade.Camera2D` (zoom, lerp, bounds) | `Camera2D` (zoom, `position_smoothing`, `limit_*`) |
| parallax (смещение камеры на слой) | `ParallaxBackground` + `ParallaxLayer` (или `Parallax2D`) |
| `arcade.Text` / HUD | `CanvasLayer` + `Label` |
| dev-панели tkinter/DPG | редактор Godot + `@export`-поля, `GameConfig` autoload |
| PyInstaller / cx_Freeze | Godot export templates (Windows/Linux/macOS, Web, Android) |

## 3. Модель движения: сила/масса → скорость

Оригинал управляет **силами** pymunk (`apply_force` каждый кадр, масса 2, трение 0 в движении / 1 в покое, `max_horizontal_velocity = 450`). Godot-порт — **скоростная модель** (`velocity.x` через `move_toward` к целевой скорости с ускорением/трением).

Соответствие режимов (наблюдаемое поведение важнее чисел):

| Режим оригинала | Условие | Поведение | Скоростная модель Godot |
|---|---|---|---|
| Тап | удержание < 0.15 c | минимальный рывок (~2 px) | низкая целевая скорость на первые 0.15 c удержания |
| Ходьба | удержание ≥ 0.15 c, без даблтапа | средняя скорость | `WALK_SPEED` |
| Бег | даблтап (≤0.15 c) + удержание ≥ 0.15 c | максимальная скорость | `RUN_SPEED` (= 450, предел оригинала) |
| Воздух | не на земле | слабее | `AIR_SPEED` + пониженное ускорение |

- Предел горизонтальной скорости 450 px/с = `RUN_SPEED` (дальше не разгоняемся).
- Трение/остановка: при отсутствии ввода — `move_toward(velocity.x, 0, friction*delta)`.
- **Пробел прототипа:** в `godot-probe/scripts/player.gd` режим «тап» (короткое удержание = крошечный рывок) явно не реализован — есть только ходьба/бег/воздух. Нужно добавить отслеживание времени удержания стороны и пониженную целевую скорость первые 0.15 c (см. tasks).
- Даблтап-бег: в прототипе уже есть (`_read_run_input`, окно `DOUBLE_TAP_WINDOW`). Окно в оригинале 0.15 c, в прототипе расширено до 0.25 c — оставить 0.25 c как намеренное улучшение удобства (зафиксировано в `GameConfig`).

## 4. Прыжок

Импульс pymunk ÷ масса 2 = стартовая скорость Godot (уже перенесено в `GameConfig`):

| Режим | Импульс | Скорость `velocity.y` |
|---|---|---|
| Стоя | 1400 | 700 |
| Ходьба | 1600 | 800 |
| Бег | 1800 | 900 |

- Гашение: отпускание в пределах `JUMP_CUTOFF_TIME = 0.15 c` → `velocity.y *= 0.4` (уже в прототипе).
- Уровень выбирается в момент прыжка по текущему режиму (`_jump_velocity(dir)` в `player.gd`).
- Койот + буфер — намеренное добавление (дельта спеки), в прототипе есть.

## 5. Специальные платформы

- **One-way:** `CollisionShape2D.one_way_collision = true` на статическом теле; игрок проходит снизу, приземляется сверху. Соскакивание (S/↓) — временно снимает one-way-слой из маски игрока (`DROP_THROUGH_TIME`), уже в прототипе.
- **Хрупкие:** при контакте игрока с полом-хрупкой платформой (через `is_on_floor()` + группу/метаданные коллайдера, либо `Area2D`) запускается таймер 0.4 c → платформа удаляется (`queue_free` / отключение коллизии).
- **Разбиваемые:** детект удара головой — при движении вверх и контакте «потолка» (`move_and_slide` возвращает столкновение снизу-вверх, либо отдельный `Area2D`-«голова») блок удаляется, `velocity.y` гасится, один блок за прыжок (флаг сбрасывается когда `velocity.y <= 0`).
- **Скользкие:** в Godot `CharacterBody2D` не применяет трение пола автоматически — реализуем явно: если пол помечен «скользким» (группа/физматериал), снижаем `GROUND_FRICTION`/ускорение. Явная ледяная логика оригинала была отключена, поэтому переносим только наблюдаемое «скольжение».
- **Движущиеся:** `AnimatableBody2D`, движение заданием `position` (не `move_and_collide` — конфликтует с sync-to-physics; уже исправлено в прототипе). Маршрут — из данных карты (см. §6) или дефолт ±100 px. Игрок переносится автоматически.

## 6. Уровни из Tiled (самый трудоёмкий этап)

Godot 4.7 **не импортирует TMX нативно**. Варианты:

- **A. Аддон YATI (Yet Another Tiled Importer).** Импортирует `.tmx`/`.tsx` в сцены Godot, поддерживает слои, объекты, тайловые свойства, анимации. Лицензия MIT (указать автора в credits по правилу ассетов). Рекомендуемый вариант.
- **B. Собственный конвертер** (GDScript/Python): парсит TMX XML → строит `TileMapLayer` + размещает объекты (спавн, враги, пути платформ) как сцены/маркеры. Полный контроль, больше работы.
- **C. Пересобрать уровни нативно** в редакторе Godot. Просто для пары уровней, но теряется связь с Tiled (а уровни — это данные).

**Решение (2026-10-23): A (YATI)**, с fallback на B, если аддон не покроет свойства тайлов (is_fragile/is_slippery/is_broken) и объектные слои.

Карта `level1.tmx`: 200×100 тайлов (6400×3200 px), тайл 32 px, 3 тайлсета (floortileset 64 тайла с анимацией воды и свойствами, spring_village 42, grass_ground 60), слои: Platforms, OneWayPlatforms, MovingPlatforms, Coins, Foreground (parallax 1.2, opacity 0.79), Background (скрыт), image layer BackImage; объектные слои: Enemies (19 шт., x/y + свойства move_force/patrol_range), PlayerSpawn (1), PlatformPaths (пуст → дефолтное движение).

Маппинг свойств тайлов → поведение: `is_slippery` → скользкая, `is_fragile` → хрупкая, `is_broken` → разбиваемая, иначе обычная. В Godot — через тайловые данные (custom data layers) или имена тайлов/группы.

## 7. Камера и параллакс

- `Camera2D`: `zoom` = **1.70** (привести к оригиналу; в прототипе сейчас 3.0 — поменять), `limit_*` = границы карты, `position_smoothing_enabled = true`, `position_smoothing_speed ≈ 8` (аналог lerp 0.1).
- `ParallaxBackground` + `ParallaxLayer` (или `Parallax2D`): факторы из Tiled (`parallaxx/parallaxy`, custom `parallax_x/y`). BackImage и Foreground — параллакс-слои.

## 8. Экраны и сюжет

- Меню/Story/Level — отдельные сцены; переходы `change_scene_to_file`.
- Сюжет: `assets/story/level{N}.json` (массив слайдов {image?, text}) → `FileAccess` + `JSON.parse_string`; слайд = `Control` с `TextureRect`/`RichTextLabel`; ENTER/SPACE/→ далее, ← назад, ESC пропустить → уровень.
- ESC в уровне → меню (пауза в оригинале не подключена; решать отдельно — см. «Открытые вопросы»).

## 9. Структура Godot-проекта (предлагаемая)

```
godot/
├── project.godot            # main scene, autoload GameConfig, gravity, pixel snap
├── scripts/
│   ├── game_config.gd       # autoload: константы + InputMap (уже есть)
│   ├── player.gd            # CharacterBody2D (уже есть, доработать тап-режим)
│   ├── enemy_rat.gd         # враг (уже есть; обобщить до типов)
│   ├── moving_platform.gd   # AnimatableBody2D (уже есть)
│   ├── level.gd             # контроллер синтетического тест-уровня
│   ├── tiled_level.gd       # контроллер уровня из Tiled (коллизии/спавн/враги) — новый
│   ├── hud.gd               # HUD + FPS (уже есть)
│   ├── coin.gd, fragile_platform.gd, breakable_block.gd  # новые
│   └── story_view.gd, menu.gd  # новые экраны
├── scenes/                  # level1.tscn (Tiled), level_test.tscn, player.tscn, enemy_*.tscn, ui_*.tscn
├── assets/                  # перенесённые PNG/TMX/JSON
└── addons/YATI/             # импортёр Tiled (2.2.9, MIT)
```

## 10. Соответствие констант (constants.py → GameConfig)

Уже перенесено: GRAVITY 1500, MAX_FALL/MAX_VERTICAL 1500/1600, WALK/RUN/AIR скорости, GROUND/AIR accel, friction, JUMP_* (700/800/900), JUMP_CUTOFF_TIME 0.15, JUMP_CUT_MULTIPLIER 0.4, COYOTE 0.10, JUMP_BUFFER 0.10, DROP_THROUGH 0.18, PLAYER_SIZE, ENEMY_*, CAMERA_ZOOM (→ заменить 3.0 на 1.70), LEVEL_W/H, KILL_Y.

Нужно добавить/уточнить: MOVE_SLOW_THRESHOLD 0.15 (тап-режим), DOUBLE_TAP_THRESHOLD 0.15 (в прототипе 0.25 — намеренно), RUN_MODE_DURATION 2.0, FRAGILE_BREAK_DELAY 0.4, ENEMY move_force 300 / patrol_range 96 / hop impulse 400, PLAYER_MAX_HORIZONTAL 450 (= RUN_SPEED).

## 11. Риски и смягчение

- **«Ощущение» разойдётся** (сила/масса → скорость). Смягчение: подбор констант в `GameConfig` + живой прогон; HUD показывает vx/vy/mode для сверки. Начать с совпадения предела скорости (450) и высот прыжка (700/800/900), затем подстроить ускорения.
- **Импорт Tiled** — самый рискованный этап. Смягчение: сначала один уровень через YATI, проверить свойства тайлов и объектные слои; при проблемах — конвертер-скрипт.
- **Скользкие платформы** в Godot не «из коробки». Смягчение: явная проверка пола на «скользкость» и снижение трения.
- **Разбиваемые/хрупкие** требуют аккуратного детекта контакта. Смягчение: `Area2D`-датчики + `move_and_slide` collision info.
- **Множественные типы врагов** не реализованы даже в оригинале. Смягчение: переносим только крысу (активное поведение), остальные типы — отдельным изменением после миграции.

## 12. Открытые вопросы (к пользователю)

Решено 2026-10-23:

1. ~~Расположение Godot-проекта~~ → подпапка `godot/` в этом репозитории (§1).
2. ~~Удалять ли Python-код~~ → держать `src/` до подтверждения parity, затем решить отдельно (§1, tasks 1.9).
4. ~~Импорт Tiled~~ → аддон YATI (MIT), fallback — свой конвертер (§6, tasks 1.6).

Остаются открытыми:

3. Пауза: в оригинале не подключена — добавить в Godot (ESC → пауза, отдельная клавиша → меню) или сохранить «ESC → меню»?
5. Приоритет контента после parity ядра: монеты/очки, специальные платформы, несколько уровней, сюжет, или типы врагов?
