from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from formats.neogeo.romset import NeoGeoRomSet, classify_rom


class RomManagerWidget(QWidget):
    rom_set_loaded = Signal(object)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.romset: NeoGeoRomSet | None = None

        self.path_label = QLabel("No ROM folder loaded.")
        self.open_button = QPushButton("Open ROM Folder…")
        self.open_button.clicked.connect(self.choose_folder)

        top = QHBoxLayout()
        top.addWidget(self.path_label, 1)
        top.addWidget(self.open_button)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(
            ["File", "Role", "Size", "CRC32", "SHA-256"]
        )
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.horizontalHeader().setStretchLastSection(True)

        layout = QVBoxLayout(self)
        layout.addLayout(top)
        layout.addWidget(self.table)

    def choose_folder(self) -> None:
        directory = QFileDialog.getExistingDirectory(
            self,
            "Open Neo Geo ROM Folder",
            "",
        )
        if directory:
            self.load_folder(directory)

    def load_folder(self, directory: str | Path) -> None:
        try:
            self.romset = NeoGeoRomSet.load_directory(directory)
        except Exception as exc:
            QMessageBox.critical(self, "ROM load failed", str(exc))
            return

        self.path_label.setText(str(self.romset.directory))
        self.table.setRowCount(len(self.romset.roms))

        for row, rom in enumerate(self.romset.roms):
            hashes = rom.hashes()
            values = [
                rom.name,
                classify_rom(rom.name),
                f"{rom.size:,} bytes",
                hashes["crc32"],
                hashes["sha256"],
            ]
            for column, value in enumerate(values):
                self.table.setItem(row, column, QTableWidgetItem(value))

        self.table.resizeColumnsToContents()
        self.rom_set_loaded.emit(self.romset)
