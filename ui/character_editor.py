from __future__ import annotations


from math import ceil

from pathlib import Path


from PySide6.QtCore import (
    Qt,
)

from PySide6.QtGui import (
    QColor,
    QImage,
    QPixmap,
)

from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QSplitter,
    QVBoxLayout,
    QWidget,
)


from app.project import (
    KofProject,
)

from core.character import (
    CharacterCatalog,
    CharacterDefinition,
)

from core.extraction_manager import (
    ExtractionManager,
)

from core.runtime_manager import (
    MameRuntimeManager,
    RuntimeErrorBase,
)

from formats.neogeo.sprite_region import (
    DecryptedSpriteRegion,
)

from ui.extraction_dialog import (
    ExtractionDialog,
)


# Temporary diagnostic palette.
#
# Once actual KOF palette references are
# reverse-engineered, replace this with
# real palette data.
DEBUG_PALETTE = [

    QColor(
        0,
        0,
        0,
        0,
    ),

    QColor(32, 32, 32),
    QColor(64, 64, 64),
    QColor(96, 96, 96),

    QColor(128, 128, 128),
    QColor(160, 160, 160),
    QColor(192, 192, 192),
    QColor(224, 224, 224),

    QColor(48, 48, 48),
    QColor(80, 80, 80),
    QColor(112, 112, 112),
    QColor(144, 144, 144),

    QColor(176, 176, 176),
    QColor(208, 208, 208),
    QColor(232, 232, 232),
    QColor(255, 255, 255),

]


class CharacterEditorWidget(
    QWidget
):

    def __init__(
        self,
        parent=None,
    ) -> None:

        super().__init__(
            parent
        )


        self.project: (
            KofProject
            | None
        ) = None


        # ----------------------------------------------
        # Bundled MAME backend
        # ----------------------------------------------

        self.runtime_manager = (
            MameRuntimeManager()
        )


        self.extraction_manager = (
            ExtractionManager(
                self.runtime_manager
            )
        )


        # ----------------------------------------------
        # Character catalog
        # ----------------------------------------------

        character_file = (

            Path(__file__)
            .resolve()
            .parents[1]

            / "games"

            / "kof2003"

            / "characters.json"

        )


        self.catalog = (
            CharacterCatalog.load(
                character_file
            )
        )


        self.sprite_region: (
            DecryptedSpriteRegion
            | None
        ) = None


        self.current_character: (
            CharacterDefinition
            | None
        ) = None


        self._build_ui()


        self._populate_roster()


        self.refresh_runtime_status()


    # --------------------------------------------------
    # Project
    # --------------------------------------------------

    def set_project(
        self,
        project: KofProject,
    ) -> None:

        self.project = project


        self.project.ensure_workspace()


        self.refresh_extracted_images()


        self._load_cached_sprite_region_if_available()


    # --------------------------------------------------
    # Interface
    # --------------------------------------------------

    def _build_ui(
        self,
    ) -> None:

        # ----------------------------------------------
        # Search
        # ----------------------------------------------

        self.search_edit = (
            QLineEdit()
        )


        self.search_edit.setPlaceholderText(
            "Search character or team..."
        )


        self.search_edit.textChanged.connect(
            self._populate_roster
        )


        # ----------------------------------------------
        # Category
        # ----------------------------------------------

        self.category_combo = (
            QComboBox()
        )


        self.category_combo.addItems([
            "All",
            "Roster",
            "Sub-boss",
            "Boss",
        ])


        self.category_combo.currentIndexChanged.connect(
            self._populate_roster
        )


        # ----------------------------------------------
        # Runtime status
        # ----------------------------------------------

        self.runtime_status = QLabel(
            "Bundled MAME: checking..."
        )


        # ----------------------------------------------
        # NEW primary button
        # ----------------------------------------------

        self.extract_button = QPushButton(
            "Extract Game Data"
        )


        self.extract_button.clicked.connect(
            self.extract_game_data
        )


        # ----------------------------------------------
        # Developer-only manual loader
        # ----------------------------------------------

        self.load_region_button = QPushButton(
            "Advanced: Load Sprite Region..."
        )


        self.load_region_button.clicked.connect(
            self.choose_sprite_region
        )


        top = QHBoxLayout()


        top.addWidget(
            QLabel(
                "Characters:"
            )
        )


        top.addWidget(
            self.search_edit,
            1,
        )


        top.addWidget(
            self.category_combo
        )


        top.addWidget(
            self.runtime_status
        )


        top.addWidget(
            self.extract_button
        )


        top.addWidget(
            self.load_region_button
        )


        # ----------------------------------------------
        # Character roster
        # ----------------------------------------------

        self.roster_list = (
            QListWidget()
        )


        self.roster_list.currentItemChanged.connect(
            self._character_changed
        )


        # ----------------------------------------------
        # Sprite display
        # ----------------------------------------------

        self.sprite_label = QLabel(
            "No extracted sprite data loaded.\n\n"
            "Load your KOF 2003 ROM folder in ROM Manager,\n"
            "then click Extract Game Data."
        )


        self.sprite_label.setAlignment(
            Qt.AlignCenter
        )


        self.sprite_label.setMinimumSize(
            480,
            480,
        )


        self.sprite_scroll = (
            QScrollArea()
        )


        self.sprite_scroll.setWidgetResizable(
            True
        )


        self.sprite_scroll.setAlignment(
            Qt.AlignCenter
        )


        self.sprite_scroll.setWidget(
            self.sprite_label
        )


        # ----------------------------------------------
        # Previously extracted PNG
        # ----------------------------------------------

        self.extracted_combo = (
            QComboBox()
        )


        self.extracted_combo.currentIndexChanged.connect(
            self._show_selected_extracted_image
        )


        extracted_row = (
            QHBoxLayout()
        )


        extracted_row.addWidget(
            QLabel(
                "Extracted:"
            )
        )


        extracted_row.addWidget(
            self.extracted_combo,
            1,
        )


        # ----------------------------------------------
        # Tile controls
        # ----------------------------------------------

        self.start_tile_spin = (
            QSpinBox()
        )


        self.start_tile_spin.setRange(
            0,
            0x7FFFFFFF,
        )


        self.start_tile_spin.setDisplayIntegerBase(
            16
        )


        self.start_tile_spin.setPrefix(
            "0x"
        )


        self.tile_count_spin = (
            QSpinBox()
        )


        self.tile_count_spin.setRange(
            1,
            4096,
        )


        self.tile_count_spin.setValue(
            256
        )


        self.columns_spin = (
            QSpinBox()
        )


        self.columns_spin.setRange(
            1,
            64,
        )


        self.columns_spin.setValue(
            16
        )


        self.scale_spin = (
            QSpinBox()
        )


        self.scale_spin.setRange(
            1,
            8,
        )


        self.scale_spin.setValue(
            2
        )


        range_form = (
            QFormLayout()
        )


        range_form.addRow(
            "Start tile:",
            self.start_tile_spin,
        )


        range_form.addRow(
            "Tile count:",
            self.tile_count_spin,
        )


        range_form.addRow(
            "Columns:",
            self.columns_spin,
        )


        range_form.addRow(
            "Preview scale:",
            self.scale_spin,
        )


        # ----------------------------------------------
        # Tile actions
        # ----------------------------------------------

        self.preview_button = QPushButton(
            "Preview Tile Range"
        )


        self.preview_button.clicked.connect(
            self.preview_tile_range
        )


        self.assign_button = QPushButton(
            "Assign Range to Character"
        )


        self.assign_button.clicked.connect(
            self.assign_range
        )


        self.export_button = QPushButton(
            "Extract Sheet PNG"
        )


        self.export_button.clicked.connect(
            self.export_sheet
        )


        action_row = (
            QHBoxLayout()
        )


        action_row.addWidget(
            self.preview_button
        )


        action_row.addWidget(
            self.assign_button
        )


        action_row.addWidget(
            self.export_button
        )


        # ----------------------------------------------
        # Center panel
        # ----------------------------------------------

        center = QWidget()


        center_layout = QVBoxLayout(
            center
        )


        center_layout.addLayout(
            extracted_row
        )


        center_layout.addWidget(
            self.sprite_scroll,
            1,
        )


        center_layout.addLayout(
            range_form
        )


        center_layout.addLayout(
            action_row
        )


        # ----------------------------------------------
        # Right-side details
        # ----------------------------------------------

        self.name_value = QLabel(
            "-"
        )


        self.team_value = QLabel(
            "-"
        )


        self.category_value = QLabel(
            "-"
        )


        self.selectable_value = QLabel(
            "-"
        )


        self.mapping_value = QLabel(
            "Not mapped"
        )


        self.mapping_value.setWordWrap(
            True
        )


        self.region_value = QLabel(
            "No decrypted sprite region loaded"
        )


        self.region_value.setWordWrap(
            True
        )


        info_form = QFormLayout()


        info_form.addRow(
            "Name:",
            self.name_value,
        )


        info_form.addRow(
            "Team:",
            self.team_value,
        )


        info_form.addRow(
            "Category:",
            self.category_value,
        )


        info_form.addRow(
            "Selectable:",
            self.selectable_value,
        )


        info_form.addRow(
            "Sprite mapping:",
            self.mapping_value,
        )


        info_form.addRow(
            "Region:",
            self.region_value,
        )


        info_box = QGroupBox(
            "Character / Extraction"
        )


        info_box.setLayout(
            info_form
        )


        info_note = QLabel(
            "Bundled MAME handles KOF 2003 "
            "graphics decryption automatically.\n\n"
            "Character → animation → tile mapping "
            "still needs to be reverse-engineered, "
            "so KOF Studio does not guess "
            "per-character tile ranges yet."
        )


        info_note.setWordWrap(
            True
        )


        right = QWidget()


        right_layout = QVBoxLayout(
            right
        )


        right_layout.addWidget(
            info_box
        )


        right_layout.addWidget(
            info_note
        )


        right_layout.addStretch(
            1
        )


        # ----------------------------------------------
        # Main splitter
        # ----------------------------------------------

        splitter = QSplitter()


        splitter.addWidget(
            self.roster_list
        )


        splitter.addWidget(
            center
        )


        splitter.addWidget(
            right
        )


        splitter.setSizes([
            260,
            760,
            300,
        ])


        splitter.setStretchFactor(
            1,
            1,
        )


        layout = QVBoxLayout(
            self
        )


        layout.addLayout(
            top
        )


        layout.addWidget(
            splitter,
            1,
        )


    # --------------------------------------------------
    # Runtime status
    # --------------------------------------------------

    def refresh_runtime_status(
        self,
    ) -> None:

        try:

            info = (
                self.runtime_manager
                .probe()
            )


        except RuntimeErrorBase:

            self.runtime_status.setText(
                "Bundled MAME: MISSING"
            )

            return


        version = (

            info.version
            .splitlines()[0]

            if info.version

            else "Ready"

        )


        self.runtime_status.setText(
            f"Bundled MAME: {version}"
        )


    # --------------------------------------------------
    # NEW extraction workflow
    # --------------------------------------------------

    def extract_game_data(
        self,
    ) -> None:

        if not self.project:

            QMessageBox.information(
                self,
                "No project",
                "Open or save a project first.",
            )

            return


        if not self.project.romset:

            QMessageBox.information(
                self,
                "ROM required",
                "Load your KOF 2003 ROM folder "
                "in ROM Manager first.",
            )

            return


        try:

            job = (
                self.extraction_manager
                .prepare_sprite_extraction(
                    self.project,
                    self.project.romset,
                )
            )


        except Exception as exc:

            QMessageBox.critical(
                self,
                "Unable to start extraction",
                str(exc),
            )


            self.refresh_runtime_status()

            return


        dialog = ExtractionDialog(

            self.extraction_manager,

            job,

            self,

        )


        dialog.extraction_completed.connect(
            self.load_sprite_region
        )


        dialog.start()


        dialog.exec()


    # --------------------------------------------------
    # Auto-load existing cache
    # --------------------------------------------------

    def _load_cached_sprite_region_if_available(
        self,
    ) -> None:

        if (
            not self.project
            or
            not self.project.romset
        ):

            return


        try:

            fingerprint = (
                self.extraction_manager
                .romset_fingerprint(
                    self.project.romset
                )
            )


            (
                output_path,
                manifest_path,
            ) = (
                self.extraction_manager
                .cache_paths(
                    self.project,
                    fingerprint,
                )
            )


            if (
                self.extraction_manager
                .cache_is_valid(
                    output_path,
                    manifest_path,
                    fingerprint,
                )
            ):

                self.load_sprite_region(
                    output_path
                )


        except Exception:

            # Cache failure must not prevent
            # the Characters tab from opening.
            pass


    # --------------------------------------------------
    # Roster
    # --------------------------------------------------

    def _populate_roster(
        self,
    ) -> None:

        query = (
            self.search_edit
            .text()
            .strip()
            .lower()
        )


        category_text = (
            self.category_combo
            .currentText()
            .lower()
        )


        category_map = {

            "roster":
                "roster",

            "sub-boss":
                "sub_boss",

            "boss":
                "boss",

        }


        current_id = (

            self.current_character.id

            if self.current_character

            else None

        )


        self.roster_list.blockSignals(
            True
        )


        self.roster_list.clear()


        for character in (
            self.catalog.characters
        ):

            haystack = (

                f"{character.name} "
                f"{character.team} "
                f"{character.id}"

            ).lower()


            if (
                query
                and
                query not in haystack
            ):

                continue


            if category_text != "all":

                wanted = (
                    category_map.get(
                        category_text,
                        category_text,
                    )
                )


                if (
                    character.category
                    != wanted
                ):

                    continue


            suffix = ""


            if (
                character.category
                == "sub_boss"
            ):

                suffix = (
                    " [Sub-boss]"
                )


            elif (
                character.category
                == "boss"
            ):

                suffix = (
                    " [Boss]"
                )


            item = QListWidgetItem(

                f"{character.name}"
                f"{suffix}\n"
                f"{character.team}"

            )


            item.setData(

                Qt.UserRole,

                character.id,

            )


            self.roster_list.addItem(
                item
            )


            if (
                character.id
                == current_id
            ):

                self.roster_list.setCurrentItem(
                    item
                )


        self.roster_list.blockSignals(
            False
        )


        if (
            self.roster_list.currentRow()
            < 0
            and
            self.roster_list.count()
        ):

            self.roster_list.setCurrentRow(
                0
            )


    def _character_changed(
        self,
        current,
        previous,
    ) -> None:

        if current is None:

            return


        character_id = (
            current.data(
                Qt.UserRole
            )
        )


        character = (
            self.catalog.get(
                character_id
            )
        )


        if not character:

            return


        self.current_character = (
            character
        )


        self.name_value.setText(
            character.name
        )


        self.team_value.setText(
            character.team
        )


        self.category_value.setText(

            character.category
            .replace("_", " ")
            .title()

        )


        self.selectable_value.setText(

            "Yes"

            if character.selectable

            else "No"

        )


        self._load_mapping()


        self.refresh_extracted_images()


    # --------------------------------------------------
    # Mapping
    # --------------------------------------------------

    def _load_mapping(
        self,
    ) -> None:

        if (
            not self.project
            or
            not self.current_character
        ):

            self.mapping_value.setText(
                "Not mapped"
            )

            return


        ranges = (
            self.project
            .get_character_sprite_ranges(
                self.current_character.id
            )
        )


        if not ranges:

            self.mapping_value.setText(
                "Not mapped"
            )

            return


        text = "\n".join(

            f"0x{int(item['start_tile']):X} "
            f"+ {int(item['count'])} tiles"

            for item in ranges

        )


        self.mapping_value.setText(
            text
        )


        first = ranges[0]


        self.start_tile_spin.setValue(
            int(
                first["start_tile"]
            )
        )


        self.tile_count_spin.setValue(
            int(
                first["count"]
            )
        )


    def assign_range(
        self,
    ) -> None:

        if (
            not self.project
            or
            not self.current_character
        ):

            return


        entry = {

            "start_tile":
                self.start_tile_spin
                .value(),

            "count":
                self.tile_count_spin
                .value(),

        }


        ranges = (
            self.project
            .get_character_sprite_ranges(
                self.current_character.id
            )
        )


        if entry not in ranges:

            ranges.append(
                entry
            )


        self.project.set_character_sprite_ranges(

            self.current_character.id,

            ranges,

        )


        self._load_mapping()


        QMessageBox.information(
            self,
            "Character mapping",
            "Sprite range stored in the project.\n\n"
            "Press Ctrl+S to save.",
        )


    # --------------------------------------------------
    # Manual developer sprite region
    # --------------------------------------------------

    def choose_sprite_region(
        self,
    ) -> None:

        initial = (

            str(
                self.project.cache_dir
            )

            if self.project

            else ""

        )


        path, _ = (
            QFileDialog.getOpenFileName(

                self,

                "Open Decrypted Sprite Region",

                initial,

                "Binary files (*.bin *.rom);;"
                "All files (*)",

            )
        )


        if path:

            self.load_sprite_region(
                path
            )


    # --------------------------------------------------
    # Load extracted region
    # --------------------------------------------------

    def load_sprite_region(
        self,
        path: str | Path,
    ) -> None:

        try:

            self.sprite_region = (
                DecryptedSpriteRegion(
                    path
                )
            )


        except Exception as exc:

            QMessageBox.critical(
                self,
                "Unable to load sprite region",
                str(exc),
            )

            return


        self.start_tile_spin.setMaximum(

            max(
                0,
                self.sprite_region
                .tile_count
                - 1,
            )

        )


        self.region_value.setText(

            f"{self.sprite_region.path.name}\n"

            f"{self.sprite_region.size:,} bytes\n"

            f"{self.sprite_region.tile_count:,} tiles"

        )


    # --------------------------------------------------
    # Render tile sheet
    # --------------------------------------------------

    def _render_tile_sheet(
        self,
    ) -> QImage:

        if not self.sprite_region:

            raise RuntimeError(
                "No decrypted sprite region is loaded."
            )


        start_tile = (
            self.start_tile_spin
            .value()
        )


        tile_count = (
            self.tile_count_spin
            .value()
        )


        columns = (
            self.columns_spin
            .value()
        )


        scale = (
            self.scale_spin
            .value()
        )


        if (
            start_tile
            >=
            self.sprite_region
            .tile_count
        ):

            raise ValueError(
                "Start tile is outside "
                "the sprite region."
            )


        tile_count = min(

            tile_count,

            self.sprite_region
            .tile_count
            - start_tile,

        )


        rows = ceil(

            tile_count
            / columns

        )


        image = QImage(

            columns * 16,

            rows * 16,

            QImage.Format_ARGB32,

        )


        image.fill(
            Qt.transparent
        )


        for local_index in range(
            tile_count
        ):

            pixels = (
                self.sprite_region
                .decode_tile(
                    start_tile
                    + local_index
                )
            )


            tile_x = (

                local_index
                % columns

            ) * 16


            tile_y = (

                local_index
                // columns

            ) * 16


            for y in range(16):

                for x in range(16):

                    palette_index = (

                        pixels[
                            y * 16 + x
                        ]

                    )


                    image.setPixelColor(

                        tile_x + x,

                        tile_y + y,

                        DEBUG_PALETTE[
                            palette_index
                        ],

                    )


        if scale > 1:

            image = image.scaled(

                image.width()
                * scale,

                image.height()
                * scale,

                Qt.KeepAspectRatio,

                Qt.FastTransformation,

            )


        return image


    def preview_tile_range(
        self,
    ) -> None:

        try:

            image = (
                self._render_tile_sheet()
            )


        except Exception as exc:

            QMessageBox.information(
                self,
                "Preview unavailable",
                str(exc),
            )

            return


        pixmap = (
            QPixmap.fromImage(
                image
            )
        )


        self.sprite_label.setPixmap(
            pixmap
        )


        self.sprite_label.resize(
            pixmap.size()
        )


    # --------------------------------------------------
    # PNG extraction
    # --------------------------------------------------

    def _character_output_dir(
        self,
    ) -> Path | None:

        if (
            not self.project
            or
            not self.current_character
        ):

            return None


        output = (

            self.project
            .extracted_characters_dir

            / self.current_character.id

        )


        output.mkdir(
            parents=True,
            exist_ok=True,
        )


        return output


    def export_sheet(
        self,
    ) -> None:

        if not self.current_character:

            return


        try:

            image = (
                self._render_tile_sheet()
            )


        except Exception as exc:

            QMessageBox.information(
                self,
                "Extraction unavailable",
                str(exc),
            )

            return


        output_directory = (
            self._character_output_dir()
        )


        if output_directory is None:

            return


        filename = (

            f"tiles_"

            f"{self.start_tile_spin.value():06X}_"

            f"{self.tile_count_spin.value()}.png"

        )


        output = (

            output_directory

            / filename

        )


        success = image.save(

            str(output),

            "PNG",

        )


        if not success:

            QMessageBox.warning(
                self,
                "PNG extraction failed",
                str(output),
            )

            return


        self.refresh_extracted_images()


        QMessageBox.information(
            self,
            "Sprite sheet extracted",
            str(output),
        )


    # --------------------------------------------------
    # Extracted PNG browser
    # --------------------------------------------------

    def refresh_extracted_images(
        self,
    ) -> None:

        if not hasattr(
            self,
            "extracted_combo",
        ):

            return


        self.extracted_combo.blockSignals(
            True
        )


        self.extracted_combo.clear()


        output_directory = (
            self._character_output_dir()
        )


        files: list[Path] = []


        if (
            output_directory
            and
            output_directory.is_dir()
        ):

            files = sorted(

                output_directory
                .glob("*.png")

            )


        for path in files:

            self.extracted_combo.addItem(

                path.name,

                str(path),

            )


        self.extracted_combo.blockSignals(
            False
        )


        if files:

            self.extracted_combo.setCurrentIndex(
                0
            )


            self._show_selected_extracted_image()


    def _show_selected_extracted_image(
        self,
    ) -> None:

        path = (
            self.extracted_combo
            .currentData()
        )


        if not path:

            return


        pixmap = QPixmap(
            str(path)
        )


        if pixmap.isNull():

            return


        self.sprite_label.setPixmap(
            pixmap
        )


        self.sprite_label.resize(
            pixmap.size()
        )