# Kitavik Spring Adventure

2D-платформер про Китавика. Основная реализация — Godot 4.7 (`godot/`); Python/Arcade-версия (`src/`) оставлена как референс поведения.

## Запуск (Godot)

Требуется Godot 4.7.2. В системе установлен Flatpak `org.godotengine.Godot`.

```bash
flatpak run org.godotengine.Godot --path godot
```

Главная сцена — `godot/scenes/menu.tscn`.

Управление: ENTER — начать, ESC — выход/меню, ←/→ — слайды, A/D или стрелки — движение, Shift — бег, Space — прыжок, S/↓ — соскочить с one-way, R — рестарт, F1 — HUD и FPS.

## Сборка (Godot)

Пресеты — `godot/export_presets.cfg`: Linux x86_64, Windows x86_64, macOS universal. Шаблоны экспорта 4.7.2 установлены в профиль Flatpak.

```bash
cd godot
flatpak run org.godotengine.Godot --headless --path . --export-release "Linux" build/linux/Kitavik.x86_64
flatpak run org.godotengine.Godot --headless --path . --export-release "Windows" build/windows/Kitavik.exe
flatpak run org.godotengine.Godot --headless --path . --export-release "macOS" build/macos/Kitavik.zip
```

Артефакты лежат в `godot/build/` и не коммитятся. macOS-сборка без подписи и нотаризации.

## Проверки

```bash
cd godot
for s in _check_level _check_flow _check_coins _check_enemy _check_platforms _check_oneway _check_movement _check_fallback; do
  flatpak run org.godotengine.Godot --headless --path . -s "scripts/$s.gd" || break
done
```

## Структура

- `godot/` — основная игра: сцены, GDScript, Tiled-карта, аддон YATI, export presets
- `openspec/` — living-спеки поведения и архив миграции
- `assets/` — исходные спрайты, карты и сюжетные данные
- `src/`, `requirements.txt`, `venv/` — Python/Arcade-версия (референс, не поставляется)

## Python/Arcade (референс)

Python-код сохранён для сверки поведения. В исходном виде не запускался: `DEV_MODE = True`, импорт `psutil` отсутствует в `requirements.txt`, venv сломан. Артефакты и конфиги сборки удалены; при необходимости их можно достать из git-истории.

## Лицензии

Сторонние компоненты — в `godot/CREDITS.md` (YATI 2.2.9, MIT). Ассеты игры — собственные материалы проекта.
