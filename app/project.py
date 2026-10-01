from __future__ import annotations


from dataclasses import (
    dataclass,
    field,
)

from pathlib import Path

import json


from formats.neogeo.romset import (
    NeoGeoRomSet,
)


PROJECT_FORMAT_VERSION = 3


@dataclass
class KofProject:

    name: str = (
        "Untitled KOF Studio Project"
    )

    game_id: str = (
        "kof2003"
    )

    rom_directory: (
        Path
        | None
    ) = None

    project_file: (
        Path
        | None
    ) = None

    notes: str = ""

    metadata: dict = field(
        default_factory=dict
    )

    romset: (
        NeoGeoRomSet
        | None
    ) = field(
        default=None,
        repr=False,
    )


    # --------------------------------------------------
    # ROM
    # --------------------------------------------------

    def load_rom_directory(
        self,
        directory: str | Path,
    ) -> None:

        directory = Path(
            directory
        )


        self.romset = (
            NeoGeoRomSet
            .load_directory(
                directory
            )
        )


        self.rom_directory = (
            directory
        )


    # --------------------------------------------------
    # Workspace
    # --------------------------------------------------

    @property
    def workspace_dir(
        self,
    ) -> Path:

        if self.project_file:

            filename = (
                self.project_file.name
            )


            if filename.endswith(
                ".kofproj.json"
            ):

                stem = filename[
                    :-len(
                        ".kofproj.json"
                    )
                ]

            else:

                stem = (
                    self.project_file
                    .stem
                )


            return (

                self.project_file
                .parent

                / f"{stem}.workspace"

            )


        return (

            Path.cwd()

            / ".kofstudio_workspace"

        )


    @property
    def cache_dir(
        self,
    ) -> Path:

        return (

            self.workspace_dir

            / "cache"

        )


    @property
    def extracted_characters_dir(
        self,
    ) -> Path:

        return (

            self.workspace_dir

            / "extracted"

            / "characters"

        )


    def ensure_workspace(
        self,
    ) -> None:

        self.cache_dir.mkdir(
            parents=True,
            exist_ok=True,
        )


        self.extracted_characters_dir.mkdir(
            parents=True,
            exist_ok=True,
        )


    # --------------------------------------------------
    # Character mappings
    # --------------------------------------------------

    def get_character_sprite_ranges(
        self,
        character_id: str,
    ) -> list[dict]:

        mappings = (
            self.metadata
            .setdefault(
                "character_sprite_ranges",
                {},
            )
        )


        return list(

            mappings.get(
                character_id,
                [],
            )

        )


    def set_character_sprite_ranges(
        self,
        character_id: str,
        ranges: list[dict],
    ) -> None:

        mappings = (
            self.metadata
            .setdefault(
                "character_sprite_ranges",
                {},
            )
        )


        mappings[
            character_id
        ] = ranges


    # --------------------------------------------------
    # Serialization
    # --------------------------------------------------

    def to_dict(
        self,
    ) -> dict:

        return {

            "format_version":
                PROJECT_FORMAT_VERSION,

            "name":
                self.name,

            "game_id":
                self.game_id,

            "rom_directory":
                str(
                    self.rom_directory
                )
                if self.rom_directory
                else None,

            "notes":
                self.notes,

            "metadata":
                self.metadata,

        }


    # --------------------------------------------------
    # Save
    # --------------------------------------------------

    def save(
        self,
        path: (
            str
            | Path
            | None
        ) = None,
    ) -> Path:

        if path is None:

            if self.project_file is None:

                raise ValueError(
                    "Project has no save path."
                )

            path = (
                self.project_file
            )


        path = Path(
            path
        )


        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )


        path.write_text(

            json.dumps(
                self.to_dict(),
                indent=2,
            ),

            encoding="utf-8",

        )


        self.project_file = path


        self.ensure_workspace()


        return path


    # --------------------------------------------------
    # Load
    # --------------------------------------------------

    @classmethod
    def load(
        cls,
        path: str | Path,
    ) -> "KofProject":

        path = Path(
            path
        )


        payload = json.loads(

            path.read_text(
                encoding="utf-8"
            )

        )


        project = cls(

            name=payload.get(
                "name",
                "Untitled KOF Studio Project",
            ),

            game_id=payload.get(
                "game_id",
                "kof2003",
            ),

            rom_directory=(

                Path(
                    payload[
                        "rom_directory"
                    ]
                )

                if payload.get(
                    "rom_directory"
                )

                else None

            ),

            project_file=path,

            notes=payload.get(
                "notes",
                "",
            ),

            metadata=payload.get(
                "metadata",
                {},
            ),

        )


        if (
            project.rom_directory
            and
            project.rom_directory
            .is_dir()
        ):

            project.romset = (
                NeoGeoRomSet
                .load_directory(
                    project.rom_directory
                )
            )


        project.ensure_workspace()


        return project