"""Отдельное окно для панели разработчика."""

import arcade
import arcade.gui


class DevWindow(arcade.Window):
    """Отдельное окно с GUI для настройки параметров."""

    def __init__(self, game_view, *args, **kwargs):
        super().__init__(
            width=300,
            height=600,
            title="Dev Panel",
            resizable=False,
            *args,
            **kwargs
        )
        
        self.game_view = game_view
        self.manager = arcade.gui.UIManager()
        
        # Текущие значения параметров
        self.gravity = game_view.current_gravity
        self.jump_speed = game_view.current_jump_speed
        self.move_speed = game_view.current_move_speed
        self.player_scaling = game_view.current_player_scaling
        
        self._setup_ui()

    def _setup_ui(self):
        """Создание UI элементов."""
        v_box = arcade.gui.UIBoxLayout(vertical=True, space_between=10)
        
        # Заголовок
        title = arcade.gui.UILabel(
            text="DEV PANEL",
            font_size=16,
            bold=True,
            text_color=arcade.color.YELLOW,
        )
        v_box.add(title)
        
        # GRAVITY
        self.gravity_label = arcade.gui.UILabel(
            text=f"Gravity: {self.gravity:.1f}",
            font_size=12,
        )
        v_box.add(self.gravity_label)
        
        self.gravity_slider = arcade.gui.UISlider(
            value=self.gravity,
            min_value=20,
            max_value=200,
            width=250,
            height=20,
        )
        v_box.add(self.gravity_slider)
        
        @self.gravity_slider.event("on_change")
        def on_gravity_change(event):
            self.gravity = event.new_value
            self.gravity_label.text = f"Gravity: {self.gravity:.1f}"
            self.game_view.apply_dev_settings(
                gravity=self.gravity,
                jump_speed=self.jump_speed,
                move_speed=self.move_speed,
                player_scaling=self.player_scaling,
            )
        
        # JUMP SPEED
        self.jump_label = arcade.gui.UILabel(
            text=f"Jump Speed: {self.jump_speed:.1f}",
            font_size=12,
        )
        v_box.add(self.jump_label)
        
        self.jump_slider = arcade.gui.UISlider(
            value=self.jump_speed,
            min_value=5,
            max_value=50,
            width=250,
            height=20,
        )
        v_box.add(self.jump_slider)
        
        @self.jump_slider.event("on_change")
        def on_jump_change(event):
            self.jump_speed = event.new_value
            self.jump_label.text = f"Jump Speed: {self.jump_speed:.1f}"
            self.game_view.apply_dev_settings(
                gravity=self.gravity,
                jump_speed=self.jump_speed,
                move_speed=self.move_speed,
                player_scaling=self.player_scaling,
            )
        
        # MOVE SPEED
        self.move_label = arcade.gui.UILabel(
            text=f"Move Speed: {self.move_speed:.1f}",
            font_size=12,
        )
        v_box.add(self.move_label)
        
        self.move_slider = arcade.gui.UISlider(
            value=self.move_speed,
            min_value=2,
            max_value=30,
            width=250,
            height=20,
        )
        v_box.add(self.move_slider)
        
        @self.move_slider.event("on_change")
        def on_move_change(event):
            self.move_speed = event.new_value
            self.move_label.text = f"Move Speed: {self.move_speed:.1f}"
            self.game_view.apply_dev_settings(
                gravity=self.gravity,
                jump_speed=self.jump_speed,
                move_speed=self.move_speed,
                player_scaling=self.player_scaling,
            )
        
        # PLAYER SCALING
        self.scaling_label = arcade.gui.UILabel(
            text=f"Player Scale: {self.player_scaling:.2f}",
            font_size=12,
        )
        v_box.add(self.scaling_label)
        
        self.scaling_slider = arcade.gui.UISlider(
            value=self.player_scaling,
            min_value=0.2,
            max_value=2.0,
            width=250,
            height=20,
        )
        v_box.add(self.scaling_slider)
        
        @self.scaling_slider.event("on_change")
        def on_scaling_change(event):
            self.player_scaling = event.new_value
            self.scaling_label.text = f"Player Scale: {self.player_scaling:.2f}"
            self.game_view.apply_dev_settings(
                gravity=self.gravity,
                jump_speed=self.jump_speed,
                move_speed=self.move_speed,
                player_scaling=self.player_scaling,
            )
        
        # Кнопка перезагрузки уровня
        reload_button = arcade.gui.UIFlatButton(
            text="Reload Level",
            width=250,
        )
        v_box.add(reload_button)
        
        @reload_button.event("on_click")
        def on_reload(_event):
            self.game_view.reload_level()
        
        # Кнопка сохранения в файл
        save_button = arcade.gui.UIFlatButton(
            text="Save to constants.py",
            width=250,
        )
        v_box.add(save_button)
        
        @save_button.event("on_click")
        def on_save(_event):
            self.game_view.save_constants_to_file()
        
        v_box.with_padding(all=20)
        
        self.manager.add(v_box)
        self.manager.enable()

    def on_draw(self):
        """Отрисовка окна."""
        self.clear()
        self.manager.draw()

    def on_close(self):
        """Закрытие окна."""
        self.manager.disable()
        super().on_close()
