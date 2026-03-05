"""Скрипт сборки через PyInstaller."""

import PyInstaller.__main__
import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PyInstaller.__main__.run([
    os.path.join(PROJECT_ROOT, "src", "main.py"),
    "--name=KitavikSpringAdventure",
    "--onedir",
    "--windowed",
    f"--add-data={os.path.join(PROJECT_ROOT, 'assets')}:assets",
    f"--distpath={os.path.join(PROJECT_ROOT, 'dist')}",
    f"--workpath={os.path.join(PROJECT_ROOT, 'build')}",
    f"--specpath={os.path.join(PROJECT_ROOT, 'build_config')}",
    "--clean",
])
