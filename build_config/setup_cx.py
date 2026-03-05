"""Скрипт сборки через cx_Freeze."""

import sys
import os
from cx_Freeze import setup, Executable

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

build_exe_options = {
    "packages": ["arcade", "pyglet", "pymunk", "PIL"],
    "include_files": [
        (os.path.join(PROJECT_ROOT, "assets"), "assets"),
    ],
    "excludes": ["tkinter", "unittest"],
}

# Базовый объект: "Win32GUI" скроет консоль на Windows
base = "Win32GUI" if sys.platform == "win32" else None

setup(
    name="KitavikSpringAdventure",
    version="0.1.0",
    description="Kitavik Spring Adventure — 2D платформер",
    options={"build_exe": build_exe_options},
    executables=[
        Executable(
            os.path.join(PROJECT_ROOT, "src", "main.py"),
            base=base,
            target_name="KitavikSpringAdventure",
        )
    ],
)
