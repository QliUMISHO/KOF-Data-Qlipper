from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QProcess, Signal
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QPlainTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.settings import AppSettings
from formats.neogeo.mame_dump import create_mame_dump_job


class MameSpriteDumpDialog(QDialog):
    dump_completed = Signal(str)

    def __init__(self, output_path: str | Path, parent=None) -> None:
        super().__init__(parent)

        self.settings = AppSettings()
        self.output_path = Path(output_path)
        self.process: QProcess | None = None
        self.job = None

        self.setWindowTitle("Dump Decrypted Sprite Region with MAME")
        self.resize(760, 480)

        self.mame_edit = QLineEdit(str(self.settings.mame_exe() or ""))
        self.mame_button = QPushButton("Browse…")
        self.mame_button.clicked.connect(self.choose_mame)

        self.rompath_edit = QLineEdit(str(self.settings.mame_rompath() or ""))
        self.rompath_button = QPushButton("Browse…")
        self.rompath_button.clicked.connect(self.choose_rompath)

        self.output_edit = QLineEdit(str(self.output_path))
        self.output_edit.setReadOnly(True)

        form = QFormLayout()
        form.addRow("MAME executable:", self._row(self.mame_edit, self.mame_button))
        form.addRow("MAME ROM path:", self._row(self.rompath_edit, self.rompath_button))
        form.addRow("Output:", self.output_edit)

        note = QLabel(
            "KOF Studio launches your local MAME and asks it to dump the "
            "already-decrypted Neo Geo ':sprites' region. It does not download "
            "or include game ROM data."
        )
        note.setWordWrap(True)

        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)

        self.run_button = QPushButton("Start Dump")
        self.run_button.clicked.connect(self.start_dump)

        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(note)
        layout.addLayout(form)
        layout.addWidget(self.log, 1)
        layout.addWidget(self.run_button)
        layout.addWidget(buttons)

    @staticmethod
    def _row(edit: QLineEdit, button: QPushButton) -> QWidget:
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(edit, 1)
        layout.addWidget(button)
        return widget

    def choose_mame(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select MAME executable",
            "",
            "Executables (*.exe);;All files (*)",
        )
        if path:
            self.mame_edit.setText(path)

    def choose_rompath(self) -> None:
        path = QFileDialog.getExistingDirectory(
            self,
            "Select MAME ROM root",
            self.rompath_edit.text(),
        )
        if path:
            self.rompath_edit.setText(path)

    def start_dump(self) -> None:
        if self.process and self.process.state() != QProcess.NotRunning:
            return

        try:
            self.job = create_mame_dump_job(
                self.mame_edit.text().strip(),
                self.rompath_edit.text().strip(),
                self.output_edit.text().strip(),
            )
        except Exception as exc:
            QMessageBox.critical(self, "Unable to start MAME", str(exc))
            return

        self.settings.set_mame_exe(self.job.program)
        self.settings.set_mame_rompath(self.rompath_edit.text().strip())

        self.log.clear()
        self.log.appendPlainText(f"Program: {self.job.program}")
        self.log.appendPlainText("Arguments:")
        for arg in self.job.arguments:
            self.log.appendPlainText(f"  {arg}")
        self.log.appendPlainText("")

        self.process = QProcess(self)
        self.process.setProgram(str(self.job.program))
        self.process.setArguments(self.job.arguments)
        self.process.setProcessChannelMode(QProcess.MergedChannels)
        self.process.readyReadStandardOutput.connect(self._read_output)
        self.process.finished.connect(self._finished)

        self.run_button.setEnabled(False)
        self.process.start()

    def _read_output(self) -> None:
        if not self.process:
            return
        data = bytes(self.process.readAllStandardOutput()).decode(errors="replace")
        if data:
            self.log.appendPlainText(data.rstrip())

    def _finished(self, exit_code: int, exit_status) -> None:
        self.run_button.setEnabled(True)
        output = Path(self.output_edit.text())

        if exit_code == 0 and output.is_file() and output.stat().st_size:
            self.log.appendPlainText(
                f"\nDump complete: {output} ({output.stat().st_size:,} bytes)"
            )
            self.dump_completed.emit(str(output))
        else:
            self.log.appendPlainText(
                f"\nMAME exited with code {exit_code}. "
                "No valid sprite dump was detected."
            )
