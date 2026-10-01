from __future__ import annotations


from PySide6.QtCore import (
    Qt,
)

from PySide6.QtWidgets import (
    QFormLayout,
    QGroupBox,
    QLabel,
    QPushButton,
    QPlainTextEdit,
    QVBoxLayout,
    QWidget,
)


from core.runtime_manager import (
    MameRuntimeManager,
    RuntimeErrorBase,
)


class RuntimeWidget(
    QWidget
):

    def __init__(
        self,
        parent=None,
    ) -> None:

        super().__init__(
            parent
        )


        self.runtime = (
            MameRuntimeManager()
        )


        self.status_value = QLabel(
            "Checking..."
        )


        self.version_value = QLabel(
            "-"
        )


        self.platform_value = QLabel(
            "-"
        )


        self.path_value = QLabel(
            str(
                self.runtime.runtime_dir
            )
        )


        self.path_value.setWordWrap(
            True
        )


        self.path_value.setTextInteractionFlags(
            Qt.TextSelectableByMouse
        )


        form = QFormLayout()


        form.addRow(
            "Status:",
            self.status_value,
        )


        form.addRow(
            "Version:",
            self.version_value,
        )


        form.addRow(
            "Platform:",
            self.platform_value,
        )


        form.addRow(
            "Runtime folder:",
            self.path_value,
        )


        group = QGroupBox(
            "Bundled MAME Runtime"
        )


        group.setLayout(
            form
        )


        self.test_button = QPushButton(
            "Test Runtime"
        )


        self.test_button.clicked.connect(
            self.refresh_status
        )


        self.instructions = (
            QPlainTextEdit()
        )


        self.instructions.setReadOnly(
            True
        )


        self.instructions.setPlainText(
            """
WINDOWS

Put MAME inside:

runtime/mame/

Required executable:

runtime/mame/mame.exe


LINUX

Put the Linux MAME binary inside:

runtime/mame/mame

Then:

chmod +x runtime/mame/mame


IMPORTANT

Do not place your KOF 2003 ROM files inside runtime/mame.

Use ROM Manager to select your own KOF 2003 ROM folder.

KOF Studio will create a temporary MAME ROM directory automatically when
Extract Game Data is pressed.
""".strip()
        )


        layout = QVBoxLayout(
            self
        )


        layout.addWidget(
            group
        )


        layout.addWidget(
            self.test_button
        )


        layout.addWidget(
            self.instructions,
            1,
        )


        self.refresh_status()


    def refresh_status(
        self,
    ) -> None:

        try:

            info = (
                self.runtime.probe()
            )

        except RuntimeErrorBase as exc:

            self.status_value.setText(
                "MISSING / NOT READY"
            )

            self.version_value.setText(
                "-"
            )

            self.platform_value.setText(
                "-"
            )

            self.status_value.setStyleSheet(
                "font-weight: bold;"
            )

            self.instructions.appendPlainText(
                "\n\nRuntime test failed:\n"
                + str(exc)
            )

            return


        version_line = (
            info.version
            .splitlines()[0]
            if info.version
            else "Unknown"
        )


        self.status_value.setText(
            "READY"
        )


        self.version_value.setText(
            version_line
        )


        self.platform_value.setText(
            info.system
        )


        self.status_value.setStyleSheet(
            "font-weight: bold;"
        )