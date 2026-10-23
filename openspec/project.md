# Kitavik Spring Adventure — контекст проекта

2D-аркада-платформер с упором на физику и сюжет. Герой Китавик идёт через весенний мир, чтобы вернуть весну. Уровни собираются в Tiled, физика платформерная (бег/прыжок/специальные платформы), есть враги, монеты и сюжетные слайды перед уровнем.

Проект **мигрирует** с Python/Arcade на Godot 4.7. Текущий Python-код — источник правды о поведении (описан в `specs/`); Godot-порт обязан воспроизвести это поведение. Целевая причина миграции — кроссплатформенный десктоп + в перспективе браузер/мобильные без больших затрат (Arcade веб/мобильные не поддерживает).

## Жёсткие ограничения

- **Основная цель — кроссплатформенный десктоп** (Windows/Linux/macOS). Браузер и мобильные — «без больших затрат», как вторичный вектор; в Godot это достижимо экспортом, но веб требует COOP/COEP (SharedArrayBuffer), iOS — macOS+Xcode. Эти шероховатости не блокируют десктоп.
- **Поведение сохраняется.** Living-спеки (`specs/`) описывают текущую игру; порт не должен молча менять «ощущение» (скорости, импульсы прыжка, таймеры). Любое намеренное изменение — через change proposal.
- **Русский язык** всех текстов игры и спеков; структурные ключевые слова OpenSpec — английские.
- **Окно игры не запускать без спроса** — оно открывается на экране пользователя.
- **Не коммитить без явной команды** (репозиторий под git; агент показывает дифф, коммит/пуш — только по просьбе).
- Сторонние ассеты — с указанием автора и лицензии в credits (сейчас все ассеты свои/местные, credits не заведены; появятся при добавлении стороннего).

## Стек

### Текущий (источник правды поведения)

- Python 3.14, `arcade==3.3.3`, `pymunk==6.9.0`, `pytiled_parser==2.2.9`, `pillow`, `pyglet`
- Физика: `arcade.PymunkPhysicsEngine` (импульсы/силы, масса, трение, collision handlers)
- Карты: Tiled `.tmx` (ортогональные, тайл 32px)
- Сборка: PyInstaller (`KitavikAdventure.spec`) и cx_Freeze (`build_config/setup_cx.py`)
- **Проект сейчас не запускается как есть:** `DEV_MODE = True` в `constants.py`, а `src/views/dev_window_tk.py` импортирует `psutil`, которого нет в `requirements.txt` → ImportError на старте. Плюс сломан venv. Это одна из мотиваций миграции.

### Целевой (Godot)

- Godot 4.7.x (Flatpak `org.godotengine.Godot`), GDScript
- Физика 2D: встроенный движок Godot (`CharacterBody2D` + `move_and_slide`), гравитация в `project.godot`
- Карты: TileMap/TileSet Godot; импорт из Tiled `.tmx` (через плагин/конвертер или ручной перенос слоёв)
- Прототип перенесён в `godot/` (подпапка этого репозитория, решение 2026-10-23): autoload `GameConfig`, `player.gd`, `enemy_rat.gd`, `moving_platform.gd`, `hud.gd`, `menu.gd`, `story.gd`; сцены собираются headless-генератором `scripts/_scaffold.gd`. Python-код остаётся в `src/` до подтверждения parity.
- Игровой поток портирован: меню → сюжетные слайды (3 шт. из `assets/story/level1.json`) → уровень; ESC в уровне возвращает в меню. Headless-проверка `scripts/_check_flow.gd` проходит (меню, 3 слайда, навигация ←/→, старт уровня, ESC → меню).
- Импорт Tiled — аддон **YATI 2.2.9** (MIT, Roland Helmerichs; `godot/addons/YATI`, credits — `godot/CREDITS.md`). `level1.tmx` импортируется в `TileMapLayer`-слои и объекты; контроллер `tiled_level.gd` строит коллизии по ячейкам Platforms, ставит игрока на PlayerSpawn и размещает 19 врагов. Headless-проверка: игрок на земле, камера 0..6400×0..3200.
- Специальные платформы: свойства тайлов (`is_slippery`/`is_fragile`/`is_broken`) из metadata YATI делят ячейки Platforms на группы с приоритетом slippery → fragile → breakable → normal. Хрупкие (0.4 c) и разбиваемые (удар головой) — отдельные тела на ячейку с удалением тайла; скользкие — отдельный бит слоя, игрок снижает ускорение/трение; `MovingPlatforms` превращается в `AnimatableBody2D` с ходом ±100 px (120 px/s). В `level1` спецтайлов и движущихся платформ нет — логика проверена синтетикой в `scripts/_check_platforms.gd`.
- Лёд: явная логика `ICE_ACCELERATION`/`ICE_DECELERATION` в Python была отключена; в Godot она восстановлена осознанно по задаче 1.3 change-а (не «молчаливое» изменение — зафиксировано в `changes/migrate-to-godot/`).
- Запасной уровень: если `.tmx` не найден, `tiled_level.gd` строит площадку 1280×720 (земля, 2 платформы, 3 монеты) — проверено `_check_fallback.gd`.
- Детали и задачи — `changes/migrate-to-godot/`.

## Структура кода (Godot, `godot/`)

- `project.godot` — main scene `scenes/menu.tscn`, autoload `GameConfig`, gravity 1500, viewport 1280×720, pixel snap, nearest filter, YATI включён
- `scripts/game_config.gd` — все константы «ощущения» + InputMap
- `scripts/player.gd` — CharacterBody2D: тап/ходьба/бег/воздух, даблтап-бег, трёхуровневый прыжок, койот, буфер, соскакивание, скользкий пол, удар головой в разбиваемый блок
- `scripts/tiled_level.gd` — уровень из Tiled: коллизии из ячеек (слитые горизонтальные полосы), классификация спецтайлов по metadata, хрупкие/разбиваемые/скользкие платформы, движущиеся платформы, спавн, враги, границы камеры, респавн/рестарт, ESC → меню
- `scripts/menu.gd` — главное меню (ENTER → история, ESC → выход)
- `scripts/story.gd` — слайды истории из `assets/story/level{N}.json` (ENTER/SPACE/→ далее, ← назад, ESC пропустить → уровень)
- `scripts/enemy_rat.gd` — крыса: патруль, 3-кадровая походка, HurtBox
- `scripts/moving_platform.gd` — AnimatableBody2D для движущихся платформ
- `scripts/coin.gd` — монета-`Area2D`; ячейки слоя Coins становятся монетами с текстурой тайла
- `scripts/hud.gd` — отладочный HUD + FPS (F1) + счёт «Очки: N»
- `scenes/menu.tscn` — главное меню; `scenes/story.tscn` — экран истории; `scenes/coin.tscn` — монета
- `scenes/level1.tscn` — основной уровень (Tiled + Player + HUD); `scenes/level_test.tscn` — синтетический тест-уровень
- `scripts/_check_*.gd` — headless-проверки: уровень, поток, монеты, враг, специальные платформы
- `assets/images|maps|story` — ассеты оригинала; `addons/YATI` — импортёр Tiled

## Структура кода (Python)

- `src/main.py` — точка входа (`create_window()` → `arcade.run()`)
- `src/game_window.py` — создание окна 1280×720, показ `MenuView`
- `src/constants.py` — все константы (окно, игрок, физика, прыжок, режимы движения, специальные платформы, камера, слои Tiled, пути)
- `src/entities/player.py` — спрайт игрока (легаси: методы `jump()`/`release_jump()` **не используются**, реальный прыжок — импульсом в `game_view.py`)
- `src/entities/enemy.py` — враг-крыса: патруль, 3-кадровая походка из `rat_enemy.png`, смена направления по границам
- `src/views/menu_view.py` — главное меню (ENTER → история, ESC → выход)
- `src/views/story_view.py` — сюжетные слайды из `assets/story/level{N}.json` (ENTER/SPACE/→ далее, ← назад, ESC пропустить → игра)
- `src/views/game_view.py` — **ядро геймплея** (~1350 строк): загрузка карты, физика pymunk, движение, прыжок, collision handlers (one-way/fragile/breakable/enemy), движущиеся платформы, монеты/очки, камера, parallax, респавн
- `src/views/pause_view.py` — оверлей паузы (ESC → назад в игру)
- `src/views/dev_window_tk.py`, `dev_window_dpg.py`, `dev_panel*.py` — dev-панели (tkinter/DPG) для живой настройки констант; **не поставляются в релиз**, в Godot заменяются редактором + `@export`
- `src/utils/resource_loader.py` — пути к ассетам
- `assets/` — `images/` (player, enemies, tiles, backgrounds), `maps/level1.tmx`, `story/level1.json` + `story.json`

## Конвенции разработки

- Любое содержательное изменение поведения = change proposal в `openspec/changes/` до кода (правила — в `openspec/AGENTS.md`).
- Константы «ощущения» живут в одном месте (`constants.py` → в Godot `GameConfig` autoload) и не дублируются по коду.
- Уровни — данные (Tiled), не код: новое содержание уровня не требует правки исходников.
- Поведение, помеченное в коде как отключённое, либо реализуется, либо удаляется — не оставляется «на потом» без пометки в спеке (см. «Известные расхождения»).

## Известные расхождения «код ↔ спека» (Python)

Обнаружены при инвентаризации; важны для честной миграции (в Godot-порте воспроизводить только **активное** поведение, отключённое — переносить осознанно или не переносить):

- **Скользкие/лёд:** явная логика `ICE_ACCELERATION`/`ICE_DECELERATION` отключена (`game_view.py:697-712`, вызов `_process_special_platforms` закомментирован). Активно только то, что скользкие тайлы добавлены как статические тела с низким трением (friction 0.1) — т.е. «скользкость» частично есть через физику, но не через явный ледяной разгон.
- **One-way платформы:** ручная коррекция в `on_update` отключена (`if False`, `game_view.py:593-611`); активен pymunk collision handler (`game_view.py:897-949`) — он и реализует проход снизу / приземление сверху.
- **Разбиваемые блоки (is_broken):** ручной блок в `on_update` отключён (`if False`, `game_view.py:613-641`); активен collision handler (`game_view.py:979-1019`).
- **Хрупкие платформы (is_fragile):** активны (handler `game_view.py:951-977` ставит таймер, `on_update:570-586` удаляет платформу через `FRAGILE_BREAK_DELAY`).
- **Легаси `player.py`:** методы `jump()`/`release_jump()` и `PLAYER_JUMP_SPEED`/`PLAYER_MOVE_SPEED` не используются реальным геймплеем.
- **Мёртвый код паузы:** `src/views/pause_view.py` (`PauseView`) определён, но нигде не подключается; ESC из уровня ведёт сразу в `MenuView` (`game_view.py:1201-1204`), пауза недостижима.
- **Дублирование:** проверка падения/респавна выполнена дважды (`game_view.py:662` и `730`).
- **Типы врагов:** в коде реализован только «rat»; ассеты птиц (`sparrow_enemy.png`, `bird_3_sparrow.png`) и мышей (`mouse*.png`, `mmouse*.png`) есть, но не используются (неизвестный тип → крыса с предупреждением).
- **Камера:** `_scroll_camera` использует `viewport_width/3` и `viewport_height/2` как поля, хотя в `constants.py` заданы `VIEWPORT_MARGIN_*` — константы полей фактически не применяются.
