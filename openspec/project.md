# Kitavik Spring Adventure — контекст проекта

2D-аркада-платформер с упором на физику и сюжет. Герой Китавик идёт через весенний мир, чтобы вернуть весну. Уровни собираются в Tiled, физика платформерная (бег/прыжок/специальные платформы), есть враги, монеты и сюжетные слайды перед уровнем.

Основная реализация — **Godot 4.7** (`godot/`). Python/Arcade-версия (`src/`) оставлена как референс поведения до отдельного решения об удалении; актуальное поведение описано в living-спеках `specs/`. Причина миграции — кроссплатформенный десктоп + в перспективе браузер/мобильные без больших затрат (Arcade веб/мобильные не поддерживает).

## Жёсткие ограничения

- **Основная цель — кроссплатформенный десктоп** (Windows/Linux/macOS). Браузер и мобильные — «без больших затрат», как вторичный вектор; в Godot это достижимо экспортом, но веб требует COOP/COEP (SharedArrayBuffer), iOS — macOS+Xcode. Эти шероховатости не блокируют десктоп.
- **Поведение сохраняется.** Living-спеки (`specs/`) описывают текущую игру; реализация не должна молча менять «ощущение» (скорости, импульсы прыжка, таймеры). Любое намеренное изменение — через change proposal.
- **Русский язык** всех текстов игры и спеков; структурные ключевые слова OpenSpec — английские.
- **Окно игры не запускать без спроса** — оно открывается на экране пользователя.
- **Не коммитить без явной команды** (репозиторий под git; агент показывает дифф, коммит/пуш — только по просьбе).
- Сторонние компоненты и ассеты — с указанием автора и лицензии в `godot/CREDITS.md` (сейчас: YATI 2.2.9, MIT; ассеты свои).

## Стек

### Основной (Godot)

- Godot 4.7.2 (Flatpak `org.godotengine.Godot`), GDScript; рендер Forward Mobile, Vulkan
- Физика 2D: встроенный движок Godot (`CharacterBody2D` + `move_and_slide`), гравитация 1500
- Карты: Tiled `.tmx` через аддон **YATI 2.2.9** (MIT, Roland Helmerichs; `godot/addons/YATI`), `TileMapLayer` + объектные слои; контроллер `tiled_level.gd`
- Уровень `level1.tmx`: 6219 ячеек, точка `PlayerSpawn`, 19 врагов, камера 0..6400×0..3200; запасной уровень при отсутствии карты
- Игровой поток: меню → 3 сюжетных слайда → уровень; ESC → меню; R — рестарт; F1 — отладочный HUD и FPS
- Специальные платформы: one-way, хрупкие (0.4 c), разбиваемые (удар головой), скользкие (явные `ICE_ACCELERATION`/`ICE_DECELERATION`), движущиеся (`AnimatableBody2D`, ±100 px по умолчанию)
- Монеты/счёт, камера с зумом 1.70 и лимитами карты, параллакс из Tiled-слоёв
- Сборка: `godot/export_presets.cfg` — Linux x86_64, Windows x86_64, macOS universal (unsigned); PCK встраивается в бинарник. Артефакты — `godot/build/` (gitignored). Шаблоны экспорта 4.7.2 установлены в Flatpak-профиль (`~/.var/app/org.godotengine.Godot/data/godot/export_templates/4.7.2.stable/`, 2 ГБ)
- Проверки: `godot/scripts/_check_*.gd` — headless и оконный прогон, все PASS; визуальное «ощущение» подтверждено пользователем 2026-10-24
- Детали миграции — `changes/archive/migrate-to-godot/`

### Python/Arcade (референс, не поставляется)

- Python 3.14, `arcade==3.3.3`, `pymunk==6.9.0`, `pytiled_parser==2.2.9`, `pillow`, `pyglet`
- Оставлен как референс поведения до отдельного решения об удалении; сборка и dev-панели больше не используются, артефакты (`build/`, `dist/`, `build_config/`, `KitavikAdventure.spec`) удалены 2026-10-24
- В исходном виде не запускался: `DEV_MODE = True` и импорт `psutil`, отсутствующего в `requirements.txt`, плюс сломанный venv

## Структура кода (Godot, `godot/`)

- `project.godot` — `config/name="Kitavik Spring Adventure"`, main scene `scenes/menu.tscn`, autoload `GameConfig`, gravity 1500, viewport 1280×720, pixel snap, nearest filter, ETC2/ASTC для macOS, YATI включён
- `export_presets.cfg` — пресеты Linux / Windows / macOS (PCK встроен); сборка в `build/` (gitignored)
- `scripts/game_config.gd` — все константы «ощущения» + InputMap
- `scripts/player.gd` — CharacterBody2D: тап/ходьба/бег/воздух, даблтап-бег, трёхуровневый прыжок, койот, буфер, соскакивание, скользкий пол, определение поверхности под лапами, замедление на соломе (×1.5), удар головой в разбиваемый блок
- `scripts/player_ground_fx.gd` — эффекты поверхности в мировых координатах: соломинки на сене, затухающие следы на снегу
- `scripts/tiled_level.gd` — уровень из Tiled: коллизии из ячеек (слитые горизонтальные полосы), классификация спецтайлов и поверхностей по metadata, хрупкие/разбиваемые/скользкие платформы, движущиеся платформы, спавн, враги, границы камеры, респавн/рестарт, ESC → меню
- `scripts/menu.gd` — главное меню (ENTER → история, ESC → выход)
- `scripts/story.gd` — слайды истории из `assets/story/level{N}.json` (ENTER/SPACE/→ далее, ← назад, ESC пропустить → уровень)
- `scripts/enemy_rat.gd` — крыса: патруль, 3-кадровая походка, HurtBox
- `scripts/moving_platform.gd` — AnimatableBody2D для движущихся платформ
- `scripts/coin.gd` — монета-`Area2D`; ячейки слоя Coins становятся монетами с текстурой тайла
- `scripts/hud.gd` — отладочный HUD + FPS (F1) + счёт «Очки: N»
- `scenes/menu.tscn` — главное меню; `scenes/story.tscn` — экран истории; `scenes/coin.tscn` — монета
- `scenes/level1.tscn` — основной уровень (Tiled + Player + HUD); `scenes/level_test.tscn` — синтетический тест-уровень
- `scripts/_check_*.gd` — headless/оконные проверки: `_check_level`, `_check_flow`, `_check_coins`, `_check_enemy`, `_check_platforms`, `_check_oneway`, `_check_movement`, `_check_fallback`, `_check_ground_fx`
- `scripts/_scaffold.gd` — headless-генератор сцен прототипа
- `assets/images|maps|story` — ассеты оригинала; `addons/YATI` — импортёр Tiled

## Структура кода (Python, референс)

Оставлен как референс поведения; сборка и dev-панели больше не используются, артефакты и конфиги сборки удалены 2026-10-24.

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
- Поведение, помеченное в коде как отключённое, либо реализуется, либо удаляется — не оставляется «на потом» без пометки в спеке (см. «Исторические расхождения Python-версии»).

## Исторические расхождения Python-версии (референс)

Обнаружены при инвентаризации перед миграцией. В Godot воспроизведено активное поведение; отключённое либо восстановлено осознанно (лёд), либо не переносилось (пауза, dev-панели). Список сохранён как история решений:

- **Скользкие/лёд:** явная логика `ICE_ACCELERATION`/`ICE_DECELERATION` отключена (`game_view.py:697-712`, вызов `_process_special_platforms` закомментирован). Активно только то, что скользкие тайлы добавлены как статические тела с низким трением (friction 0.1) — т.е. «скользкость» частично есть через физику, но не через явный ледяной разгон.
- **One-way платформы:** ручная коррекция в `on_update` отключена (`if False`, `game_view.py:593-611`); активен pymunk collision handler (`game_view.py:897-949`) — он и реализует проход снизу / приземление сверху.
- **Разбиваемые блоки (is_broken):** ручной блок в `on_update` отключён (`if False`, `game_view.py:613-641`); активен collision handler (`game_view.py:979-1019`).
- **Хрупкие платформы (is_fragile):** активны (handler `game_view.py:951-977` ставит таймер, `on_update:570-586` удаляет платформу через `FRAGILE_BREAK_DELAY`).
- **Легаси `player.py`:** методы `jump()`/`release_jump()` и `PLAYER_JUMP_SPEED`/`PLAYER_MOVE_SPEED` не используются реальным геймплеем.
- **Мёртвый код паузы:** `src/views/pause_view.py` (`PauseView`) определён, но нигде не подключается; ESC из уровня ведёт сразу в `MenuView` (`game_view.py:1201-1204`), пауза недостижима.
- **Дублирование:** проверка падения/респавна выполнена дважды (`game_view.py:662` и `730`).
- **Типы врагов:** в коде реализован только «rat»; ассеты птиц (`sparrow_enemy.png`, `bird_3_sparrow.png`) и мышей (`mouse*.png`, `mmouse*.png`) есть, но не используются (неизвестный тип → крыса с предупреждением).
- **Камера:** `_scroll_camera` использует `viewport_width/3` и `viewport_height/2` как поля, хотя в `constants.py` заданы `VIEWPORT_MARGIN_*` — константы полей фактически не применяются.
