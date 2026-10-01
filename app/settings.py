from __future__ import annotations

from pathlib import Path
from PySide6.QtCore import QSettings


class AppSettings:
    KEY_LAST_ROM_DIR = "paths/last_rom_dir"
    KEY_LAST_PROJECT = "paths/last_project"
    KEY_MAME_EXE = "paths/mame_exe"
    KEY_MAME_ROMPATH = "paths/mame_rompath"

    def __init__(self) -> None:
        self._settings = QSettings()

    def _get_path(self, key: str) -> Path | None:
        value = self._settings.value(key, "")
        return Path(value) if value else None

    def _set_path(self, key: str, value: str | Path | None) -> None:
        self._settings.setValue(key, "" if value is None else str(value))

    def last_rom_dir(self) -> Path | None:
        return self._get_path(self.KEY_LAST_ROM_DIR)

    def set_last_rom_dir(self, path: str | Path) -> None:
        self._set_path(self.KEY_LAST_ROM_DIR, path)

    def last_project(self) -> Path | None:
        return self._get_path(self.KEY_LAST_PROJECT)

    def set_last_project(self, path: str | Path) -> None:
        self._set_path(self.KEY_LAST_PROJECT, path)

    def mame_exe(self) -> Path | None:
        return self._get_path(self.KEY_MAME_EXE)

    def set_mame_exe(self, path: str | Path) -> None:
        self._set_path(self.KEY_MAME_EXE, path)

    def mame_rompath(self) -> Path | None:
        return self._get_path(self.KEY_MAME_ROMPATH)

    def set_mame_rompath(self, path: str | Path) -> None:
        self._set_path(self.KEY_MAME_ROMPATH, path)
