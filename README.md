# Kitavik Spring Adventure

2D платформер на Python Arcade.

## Требования

- Python 3.14+
- Зависимости из `requirements.txt`

## Установка

```bash
python3.14 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Запуск

```bash
source venv/bin/activate
python -m src.main
```

## Сборка

### PyInstaller
```bash
pyinstaller build_config/game.spec
```

### cx_Freeze
```bash
python build_config/setup_cx.py build
```

## Структура проекта

```
├── src/                    # Исходный код
│   ├── main.py             # Точка входа
│   ├── constants.py        # Константы игры
│   ├── game_window.py      # Главное окно
│   ├── views/              # Экраны (меню, игра, пауза)
│   ├── entities/           # Игровые сущности (игрок, враги)
│   └── utils/              # Утилиты
├── assets/                 # Ресурсы
│   ├── images/             # Спрайты и фоны
│   ├── sounds/             # Звуковые эффекты
│   ├── music/              # Музыка
│   └── maps/               # Карты уровней (Tiled)
├── build_config/           # Конфигурации сборки
├── requirements.txt        # Зависимости
└── README.md
```
