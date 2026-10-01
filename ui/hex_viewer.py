from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QPlainTextEdit,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from formats.neogeo.romset import NeoGeoRomSet


class HexViewerWidget(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.romset: NeoGeoRomSet | None = None

        self.file_combo = QComboBox()
        self.file_combo.currentIndexChanged.connect(self.refresh)

        self.offset_edit = QLineEdit("0x0")
        self.offset_edit.setPlaceholderText("0x000000")

        self.length_spin = QSpinBox()
        self.length_spin.setRange(16, 64 * 1024)
        self.length_spin.setSingleStep(16)
        self.length_spin.setValue(512)

        self.go_button = QPushButton("Go")
        self.go_button.clicked.connect(self.refresh)

        top = QHBoxLayout()
        top.addWidget(QLabel("ROM:"))
        top.addWidget(self.file_combo, 1)
        top.addWidget(QLabel("Offset:"))
        top.addWidget(self.offset_edit)
        top.addWidget(QLabel("Bytes:"))
        top.addWidget(self.length_spin)
        top.addWidget(self.go_button)

        self.output = QPlainTextEdit()
        self.output.setReadOnly(True)
        self.output.setLineWrapMode(QPlainTextEdit.NoWrap)

        layout = QVBoxLayout(self)
        layout.addLayout(top)
        layout.addWidget(self.output)

    def set_romset(self, romset: NeoGeoRomSet) -> None:
        self.romset = romset
        self.file_combo.blockSignals(True)
        self.file_combo.clear()
        self.file_combo.addItems([rom.name for rom in romset.roms])
        self.file_combo.blockSignals(False)
        self.refresh()

    def _selected_rom(self):
        if not self.romset or self.file_combo.currentIndex() < 0:
            return None
        return self.romset.roms[self.file_combo.currentIndex()]

    @staticmethod
    def _format_hex(data: bytes | bytearray, base_offset: int) -> str:
        lines: list[str] = []
        width = 16

        for local in range(0, len(data), width):
            chunk = bytes(data[local:local + width])
            hex_part = " ".join(f"{byte:02X}" for byte in chunk)
            hex_part = hex_part.ljust(width * 3 - 1)
            ascii_part = "".join(
                chr(byte) if 32 <= byte < 127 else "."
                for byte in chunk
            )
            lines.append(
                f"{base_offset + local:08X}  {hex_part}  |{ascii_part}|"
            )

        return "\n".join(lines)

    def refresh(self) -> None:
        rom = self._selected_rom()
        if rom is None:
            self.output.setPlainText("Load a ROM set first.")
            return

        try:
            offset = int(self.offset_edit.text().strip(), 0)
        except ValueError:
            QMessageBox.warning(self, "Invalid offset", "Use 0x1234 or decimal.")
            return

        if offset < 0 or offset >= rom.size:
            self.output.setPlainText(
                f"Offset 0x{offset:X} is outside {rom.name} "
                f"(size 0x{rom.size:X})."
            )
            return

        length = min(self.length_spin.value(), rom.size - offset)
        chunk = rom.data[offset:offset + length]
        self.output.setPlainText(self._format_hex(chunk, offset))
