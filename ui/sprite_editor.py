from __future__ import annotations

from PySide6.QtWidgets import (
    QLabel,
    QPlainTextEdit,
    QVBoxLayout,
    QWidget,
)


class SpriteEditorWidget(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        title = QLabel("Neo Geo Sprite Workspace")
        description = QPlainTextEdit()
        description.setReadOnly(True)
        description.setPlainText(
            "C-ROM decoding is intentionally not enabled yet.\n\n"
            "KOF 2003 uses protected/scrambled graphics. The first milestone "
            "for this workspace is to validate the correct decode pipeline "
            "before rendering or importing tiles.\n\n"
            "Planned:\n"
            "• C-ROM selection\n"
            "• tile address/index navigation\n"
            "• palette selection\n"
            "• decoded tile preview\n"
            "• PNG export/import\n"
            "• animation linkage once KOF 2003 animation tables are mapped"
        )

        layout = QVBoxLayout(self)
        layout.addWidget(title)
        layout.addWidget(description)
