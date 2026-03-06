"""Панель разработчика для настройки параметров игры."""

import arcade
import arcade.gui


class DevPanel:
    """GUI панель для настройки параметров в режиме разработки."""

    def __init__(self, game_view):
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
        # Вертикальный контейнер
        v_box = arcade.gui.UIBoxLayout(vertical=True, space_between=5)
        
        # Заголовок
        title = arcade.gui.UILabel(
            text="DEV PANEL",
            font_size=16,
            bold=True,
            text_color=arcade.color.YELLOW,
        )
        v_box.add(title)
        
        # GRAVITY
        gravity_title = arcade.gui.UILabel(text="Gravity:", font_size=12)
        v_box.add(gravity_title)
        
        self.gravity_input = arcade.gui.UIInputText(
            text=f"{self.gravity:.1f}",
            width=200,
            height=30,
        )
        v_box.add(self.gravity_input)
        
        @self.gravity_input.event("on_change")
        def on_gravity_input(event):
            try:
                val = float(event.text)
                if 20 <= val <= 200:
                    self.gravity = val
                    self.gravity_slider.value = val
                    self.game_view.apply_dev_settings(
                        gravity=self.gravity,
                        jump_speed=self.jump_speed,
                        move_speed=self.move_speed,
                        player_scaling=self.player_scaling,
                    )
            except ValueError:
                pass
        
        self.gravity_slider = arcade.gui.UISlider(
            value=self.gravity,
            min_value=20,
            max_value=200,
            width=200,
            height=20,
        )
        v_box.add(self.gravity_slider)
        
        @self.gravity_slider.event("on_change")
        def on_gravity_change(event):
            self.gravity = event.new_value
            self.gravity_input.text = f"{self.gravity:.1f}"
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
            width=200,
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
            width=200,
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
            width=200,
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
            width=200,
        )
        v_box.add(reload_button)
        
        @reload_button.event("on_click")
        def on_reload(_event):
            self.game_view.reload_level()
        
        # Кнопка сохранения в файл
        save_button = arcade.gui.UIFlatButton(
            text="Save to constants.py",
            width=200,
        )
        v_box.add(save_button)
        
        @save_button.event("on_click")
        def on_save(_event):
            self.game_view.save_constants_to_file()
        
        # Добавляем отступ через padding в v_box
        v_box.with_padding(all=10)
        
        # Якорь для размещения панели в правом верхнем углу
        anchor = arcade.gui.UIAnchorLayout()
        anchor.add(
            child=v_box,
            anchor_x="right",
            anchor_y="top",
        )
        
        self.manager.add(anchor)

    def enable(self):
        """Включить панель."""
        self.manager.enable()

    def disable(self):
        """Отключить панель."""
        self.manager.disable()

    def draw(self):
        """Отрисовка панели."""
        self.manager.draw()
