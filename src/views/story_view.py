"""Экран показа слайдов истории перед началом уровня."""

import json
from pathlib import Path

import arcade

from src.constants import SCREEN_HEIGHT, SCREEN_WIDTH, STORY_PATH


class StoryView(arcade.View):
    """Показ слайдов с вступительной историей.

    Слайды загружаются из assets/story/story.json.
    Каждый слайд может содержать:
      - "image": имя файла картинки в assets/story/
      - "text": текст, отображаемый поверх/под картинкой
    """

    def __init__(self, level: int = 1):
        super().__init__()
        self.level = level
        self.slides: list[dict] = []
        self.current_slide = 0

        self.slide_image: arcade.Texture | None = None
        self.slide_sprite: arcade.Sprite | None = None
        self.sprite_list = arcade.SpriteList()

        self.text_top: arcade.Text | None = None
        self.text_bottom: arcade.Text | None = None
        self.hint_text = arcade.Text(
            "ENTER — далее   |   ESC — пропустить",
            SCREEN_WIDTH / 2,
            20,
            arcade.color.GRAY,
            font_size=14,
            anchor_x="center",
        )

        self._load_slides()

    def _load_slides(self):
        """Загрузка данных слайдов из JSON."""
        story_file = STORY_PATH / f"level{self.level}.json"
        if not story_file.exists():
            story_file = STORY_PATH / "story.json"

        if story_file.exists():
            with open(story_file, "r", encoding="utf-8") as f:
                self.slides = json.load(f)
        else:
            self.slides = [
                {"text": "История ещё не написана...\nНажмите ENTER, чтобы начать игру."}
            ]

        if self.slides:
            self._apply_slide(0)

    def _apply_slide(self, index: int):
        """Применить данные слайда по индексу."""
        self.current_slide = index
        slide = self.slides[index]

        self.sprite_list = arcade.SpriteList()
        self.slide_sprite = None

        # Картинка слайда
        image_name = slide.get("image")
        if image_name:
            image_path = STORY_PATH / image_name
            if image_path.exists():
                tex = arcade.load_texture(str(image_path))
                self.slide_sprite = arcade.Sprite(tex)
                # Масштабируем чтобы влезло в экран с полями
                max_w = SCREEN_WIDTH - 80
                max_h = SCREEN_HEIGHT - 160
                scale = min(max_w / tex.width, max_h / tex.height, 1.0)
                self.slide_sprite.scale = scale
                self.slide_sprite.center_x = SCREEN_WIDTH / 2
                self.slide_sprite.center_y = SCREEN_HEIGHT / 2 + 20
                self.sprite_list.append(self.slide_sprite)

        # Текст слайда
        text = slide.get("text", "")
        if self.slide_sprite:
            # Текст под картинкой
            self.text_top = None
            self.text_bottom = arcade.Text(
                text,
                SCREEN_WIDTH / 2,
                60,
                arcade.color.WHITE,
                font_size=18,
                anchor_x="center",
                multiline=True,
                width=SCREEN_WIDTH - 100,
                align="center",
            )
        else:
            # Нет картинки — текст по центру
            self.text_bottom = None
            self.text_top = arcade.Text(
                text,
                SCREEN_WIDTH / 2,
                SCREEN_HEIGHT / 2,
                arcade.color.WHITE,
                font_size=22,
                anchor_x="center",
                anchor_y="center",
                multiline=True,
                width=SCREEN_WIDTH - 100,
                align="center",
            )

    def on_show_view(self):
        """Вызывается при показе вида."""
        self.background_color = arcade.color.BLACK

    def on_draw(self):
        """Отрисовка слайда."""
        self.clear()

        self.sprite_list.draw()

        if self.text_top:
            self.text_top.draw()
        if self.text_bottom:
            self.text_bottom.draw()

        self.hint_text.draw()

    def _next_slide(self):
        """Перейти к следующему слайду или начать игру."""
        if self.current_slide + 1 < len(self.slides):
            self._apply_slide(self.current_slide + 1)
        else:
            self._start_game()

    def _start_game(self):
        """Запустить игровой уровень."""
        from src.views.game_view import GameView
        game = GameView(level=self.level)
        game.setup()
        self.window.show_view(game)

    def on_key_press(self, key: int, modifiers: int):
        """Обработка нажатий."""
        if key in (arcade.key.RETURN, arcade.key.SPACE, arcade.key.RIGHT):
            self._next_slide()
        elif key == arcade.key.LEFT and self.current_slide > 0:
            self._apply_slide(self.current_slide - 1)
        elif key == arcade.key.ESCAPE:
            self._start_game()
