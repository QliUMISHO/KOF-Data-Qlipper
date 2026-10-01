from __future__ import annotations

from pathlib import Path

from PySide6.QtGui import QAction
from PySide6.QtWidgets import QFileDialog, QMainWindow, QMessageBox, QTabWidget

from app.project import KofProject
from app.settings import AppSettings
from ui.character_editor import CharacterEditorWidget
from ui.hex_viewer import HexViewerWidget
from ui.rom_manager import RomManagerWidget
from ui.sprite_editor import SpriteEditorWidget


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()

        self.settings = AppSettings()
        self.project = KofProject()

        self.setWindowTitle("KOF Studio")
        self.resize(1320, 840)

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        self.rom_manager = RomManagerWidget()
        self.hex_viewer = HexViewerWidget()
        self.character_editor = CharacterEditorWidget()
        self.sprite_editor = SpriteEditorWidget()

        self.tabs.addTab(self.rom_manager, "ROM Manager")
        self.tabs.addTab(self.hex_viewer, "Hex Inspector")
        self.tabs.addTab(self.character_editor, "Characters")
        self.tabs.addTab(self.sprite_editor, "Sprites")

        self.character_editor.set_project(self.project)
        self.rom_manager.rom_set_loaded.connect(self._on_romset_loaded)

        self._create_actions()
        self._create_menus()
        self.statusBar().showMessage("Ready")

    def _create_actions(self) -> None:
        self.open_rom_action = QAction("Open ROM Folder…", self)
        self.open_rom_action.setShortcut("Ctrl+O")
        self.open_rom_action.triggered.connect(self.open_rom_folder)

        self.open_project_action = QAction("Open Project…", self)
        self.open_project_action.setShortcut("Ctrl+Shift+O")
        self.open_project_action.triggered.connect(self.open_project)

        self.save_project_action = QAction("Save Project", self)
        self.save_project_action.setShortcut("Ctrl+S")
        self.save_project_action.triggered.connect(self.save_project)

        self.save_project_as_action = QAction("Save Project As…", self)
        self.save_project_as_action.setShortcut("Ctrl+Shift+S")
        self.save_project_as_action.triggered.connect(self.save_project_as)

        self.exit_action = QAction("Exit", self)
        self.exit_action.triggered.connect(self.close)

    def _create_menus(self) -> None:
        file_menu = self.menuBar().addMenu("&File")
        file_menu.addAction(self.open_rom_action)
        file_menu.addSeparator()
        file_menu.addAction(self.open_project_action)
        file_menu.addAction(self.save_project_action)
        file_menu.addAction(self.save_project_as_action)
        file_menu.addSeparator()
        file_menu.addAction(self.exit_action)

    def open_rom_folder(self) -> None:
        initial = self.settings.last_rom_dir()
        directory = QFileDialog.getExistingDirectory(
            self,
            "Open Neo Geo ROM Folder",
            str(initial) if initial else "",
        )

        if directory:
            self.rom_manager.load_folder(directory)
            self.settings.set_last_rom_dir(directory)

    def _on_romset_loaded(self, romset) -> None:
        self.project.romset = romset
        self.project.rom_directory = romset.directory
        self.hex_viewer.set_romset(romset)
        self.statusBar().showMessage(
            f"Loaded {len(romset.roms)} file(s) from {romset.directory}"
        )

    def open_project(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Open KOF Studio Project",
            "",
            "KOF Studio Project (*.kofproj.json);;JSON (*.json)",
        )
        if not path:
            return

        try:
            self.project = KofProject.load(path)
        except Exception as exc:
            QMessageBox.critical(self, "Project load failed", str(exc))
            return

        self.character_editor.set_project(self.project)

        if self.project.romset:
            self.rom_manager.load_folder(self.project.romset.directory)

        self.settings.set_last_project(path)
        self.setWindowTitle(f"KOF Studio — {self.project.name}")
        self.statusBar().showMessage(f"Opened project {Path(path).name}")

    def save_project(self) -> None:
        if self.project.project_file is None:
            self.save_project_as()
            return

        try:
            self.project.save()
        except Exception as exc:
            QMessageBox.critical(self, "Project save failed", str(exc))
            return

        self.character_editor.set_project(self.project)
        self.statusBar().showMessage(f"Saved {self.project.project_file.name}")

    def save_project_as(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save KOF Studio Project",
            "my_mod.kofproj.json",
            "KOF Studio Project (*.kofproj.json);;JSON (*.json)",
        )
        if not path:
            return

        if not path.lower().endswith(".json"):
            path += ".kofproj.json"

        try:
            self.project.save(path)
        except Exception as exc:
            QMessageBox.critical(self, "Project save failed", str(exc))
            return

        self.character_editor.set_project(self.project)
        self.settings.set_last_project(path)
        self.setWindowTitle(f"KOF Studio — {self.project.name}")
        self.statusBar().showMessage(f"Saved {Path(path).name}")
