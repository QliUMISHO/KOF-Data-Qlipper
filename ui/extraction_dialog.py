from __future__ import annotations


from PySide6.QtCore import (
    QProcess,
    Signal,
)

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QMessageBox,
    QPlainTextEdit,
    QProgressBar,
    QVBoxLayout,
)


from core.extraction_manager import (
    ExtractionError,
    ExtractionJob,
    ExtractionManager,
)


class ExtractionDialog(
    QDialog
):

    extraction_completed = Signal(
        str
    )


    def __init__(
        self,
        manager: ExtractionManager,
        job: ExtractionJob,
        parent=None,
    ) -> None:

        super().__init__(
            parent
        )


        self.manager = manager

        self.job = job

        self.process: (
            QProcess
            | None
        ) = None


        self.setWindowTitle(
            "KOF Studio - Extract Game Data"
        )

        self.resize(
            800,
            500,
        )


        self.status_label = QLabel(
            "Preparing extraction..."
        )

        self.status_label.setWordWrap(
            True
        )


        self.progress = (
            QProgressBar()
        )

        # Infinite/indeterminate progress
        self.progress.setRange(
            0,
            0,
        )


        self.log = (
            QPlainTextEdit()
        )

        self.log.setReadOnly(
            True
        )


        self.buttons = (
            QDialogButtonBox(
                QDialogButtonBox.Close
            )
        )


        self.buttons.button(
            QDialogButtonBox.Close
        ).setEnabled(
            False
        )


        self.buttons.rejected.connect(
            self.reject
        )


        layout = QVBoxLayout(
            self
        )

        layout.addWidget(
            self.status_label
        )

        layout.addWidget(
            self.progress
        )

        layout.addWidget(
            self.log,
            1,
        )

        layout.addWidget(
            self.buttons
        )


    # --------------------------------------------------
    # Start
    # --------------------------------------------------

    def start(
        self,
    ) -> None:

        # ----------------------------------------------
        # Cache hit
        # ----------------------------------------------

        if self.job.cached:

            self.progress.setRange(
                0,
                1,
            )

            self.progress.setValue(
                1
            )

            self.status_label.setText(
                "Using cached decrypted sprite region."
            )

            self.log.appendPlainText(
                "No MAME extraction was needed."
            )

            self.log.appendPlainText(
                ""
            )

            self.log.appendPlainText(
                str(
                    self.job.output_path
                )
            )

            self.buttons.button(
                QDialogButtonBox.Close
            ).setEnabled(
                True
            )


            self.extraction_completed.emit(
                str(
                    self.job.output_path
                )
            )

            return


        # ----------------------------------------------
        # Launch bundled MAME
        # ----------------------------------------------

        self.status_label.setText(
            "Running bundled MAME "
            "as the KOF Studio extraction backend..."
        )


        self.log.appendPlainText(
            f"MAME:\n{self.job.program}"
        )

        self.log.appendPlainText(
            ""
        )

        self.log.appendPlainText(
            "Working directory:"
        )

        self.log.appendPlainText(
            str(
                self.job.working_directory
            )
        )

        self.log.appendPlainText(
            ""
        )

        self.log.appendPlainText(
            "Temporary ROM root:"
        )

        self.log.appendPlainText(
            str(
                self.job.rom_root
            )
        )

        self.log.appendPlainText(
            ""
        )

        self.log.appendPlainText(
            "Output:"
        )

        self.log.appendPlainText(
            str(
                self.job.output_path
            )
        )

        self.log.appendPlainText(
            ""
        )


        self.process = QProcess(
            self
        )


        self.process.setProgram(
            str(
                self.job.program
            )
        )


        self.process.setArguments(
            self.job.arguments
        )


        self.process.setWorkingDirectory(
            str(
                self.job.working_directory
            )
        )


        self.process.setProcessChannelMode(
            QProcess.MergedChannels
        )


        self.process.readyReadStandardOutput.connect(
            self._read_output
        )


        self.process.errorOccurred.connect(
            self._process_error
        )


        self.process.finished.connect(
            self._finished
        )


        self.process.start()


    # --------------------------------------------------
    # MAME console output
    # --------------------------------------------------

    def _read_output(
        self,
    ) -> None:

        if not self.process:
            return


        raw = (
            self.process
            .readAllStandardOutput()
        )


        text = (
            bytes(raw)
            .decode(
                errors="replace"
            )
        )


        if text:

            self.log.appendPlainText(
                text.rstrip()
            )


    # --------------------------------------------------
    # Qt launch error
    # --------------------------------------------------

    def _process_error(
        self,
        error,
    ) -> None:

        if not self.process:
            return


        self.log.appendPlainText(
            ""
        )

        self.log.appendPlainText(
            "QProcess error:"
        )

        self.log.appendPlainText(
            self.process.errorString()
        )


    # --------------------------------------------------
    # MAME completed
    # --------------------------------------------------

    def _finished(
        self,
        exit_code: int,
        exit_status,
    ) -> None:

        self.progress.setRange(
            0,
            1,
        )


        self.buttons.button(
            QDialogButtonBox.Close
        ).setEnabled(
            True
        )


        # ----------------------------------------------
        # MAME error
        # ----------------------------------------------

        if exit_code != 0:

            self.status_label.setText(
                "Extraction failed."
            )


            self.log.appendPlainText(
                ""
            )

            self.log.appendPlainText(
                f"MAME exit code: "
                f"{exit_code}"
            )


            self.log.appendPlainText(
                ""
            )

            self.log.appendPlainText(
                "Temporary session preserved for debugging:"
            )


            self.log.appendPlainText(
                str(
                    self.job.session_dir
                )
            )


            QMessageBox.warning(
                self,
                "Extraction failed",
                "MAME could not extract "
                "the KOF 2003 sprite region.\n\n"
                "Read the extraction log "
                "for the exact error.",
            )

            return


        # ----------------------------------------------
        # Verify result
        # ----------------------------------------------

        try:

            output = (
                self.manager
                .finalize_success(
                    self.job
                )
            )

        except ExtractionError as exc:

            self.status_label.setText(
                "Extraction validation failed."
            )

            self.log.appendPlainText(
                ""
            )

            self.log.appendPlainText(
                str(exc)
            )

            QMessageBox.warning(
                self,
                "Extraction validation failed",
                str(exc),
            )

            return


        # ----------------------------------------------
        # Success
        # ----------------------------------------------

        self.progress.setValue(
            1
        )


        self.status_label.setText(
            "Game-data extraction completed."
        )


        self.log.appendPlainText(
            ""
        )

        self.log.appendPlainText(
            "Decrypted sprite region ready:"
        )


        self.log.appendPlainText(
            str(output)
        )


        self.extraction_completed.emit(
            str(output)
        )