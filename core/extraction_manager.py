from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path

import json
import os
import shutil
import time
import uuid


from app.project import KofProject

from core.runtime_manager import (
    MameRuntimeManager,
)

from formats.neogeo.mame_backend import (
    build_extraction_arguments,
    build_sprite_dump_script,
)

from formats.neogeo.romset import (
    NeoGeoRomSet,
)


class ExtractionError(
    RuntimeError
):
    pass


@dataclass
class ExtractionJob:

    system_name: str

    program: Path

    arguments: list[str]

    working_directory: Path

    session_dir: Path

    rom_root: Path

    script_path: Path

    output_path: Path

    manifest_path: Path

    fingerprint: str

    cached: bool = False


class ExtractionManager:
    """
    Handles:

    KOF Studio
       ↓
    temporary ROM staging
       ↓
    bundled MAME
       ↓
    decrypted sprite region
       ↓
    project cache
    """

    SYSTEM_NAME = "kof2003"

    CACHE_FORMAT_VERSION = 1


    def __init__(
        self,
        runtime: MameRuntimeManager | None = None,
    ) -> None:

        self.runtime = (
            runtime
            or MameRuntimeManager()
        )


    # --------------------------------------------------
    # ROM fingerprint
    # --------------------------------------------------

    def romset_fingerprint(
        self,
        romset: NeoGeoRomSet,
    ) -> str:

        digest = sha256()

        sorted_roms = sorted(
            romset.roms,
            key=lambda item:
            item.name.lower(),
        )

        for rom in sorted_roms:

            digest.update(
                rom.name
                .lower()
                .encode("utf-8")
            )

            digest.update(
                b"\0"
            )

            digest.update(
                len(rom.data)
                .to_bytes(
                    8,
                    "big",
                )
            )

            digest.update(
                sha256(
                    bytes(
                        rom.data
                    )
                ).digest()
            )

        return digest.hexdigest()


    # --------------------------------------------------
    # File copy
    # --------------------------------------------------

    @staticmethod
    def _link_or_copy(
        source: Path,
        destination: Path,
    ) -> None:
        """
        Try hard-link first.

        This prevents copying huge ROM files
        when the filesystem supports links.

        Falls back to copying.
        """

        destination.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        try:

            if destination.exists():

                destination.unlink()

            os.link(
                source,
                destination,
            )

            return

        except OSError:

            pass


        shutil.copy2(
            source,
            destination,
        )


    # --------------------------------------------------
    # Neo Geo BIOS
    # --------------------------------------------------

    def _stage_neogeo_bios(
        self,
        source_directory: Path,
        rom_root: Path,
    ) -> None:
        """
        Look for a user-provided Neo Geo BIOS
        beside the game ROM directory.

        We do NOT bundle BIOS data.
        """

        directories = [

            source_directory,

            source_directory.parent,

        ]

        for base in directories:

            for filename in (

                "neogeo.zip",

                "neogeo.7z",

            ):

                candidate = (
                    base
                    / filename
                )

                if candidate.is_file():

                    self._link_or_copy(
                        candidate,
                        rom_root / filename,
                    )

                    return


            loose_directory = (
                base
                / "neogeo"
            )

            if loose_directory.is_dir():

                destination = (
                    rom_root
                    / "neogeo"
                )

                if destination.exists():

                    shutil.rmtree(
                        destination
                    )

                shutil.copytree(
                    loose_directory,
                    destination,
                )

                return


    # --------------------------------------------------
    # Stage KOF ROM
    # --------------------------------------------------

    def _stage_romset(
        self,
        romset: NeoGeoRomSet,
        rom_root: Path,
    ) -> None:

        rom_root.mkdir(
            parents=True,
            exist_ok=True,
        )

        source_directory = (
            romset.directory
        )


        # ----------------------------------------------
        # Existing MAME archive
        # ----------------------------------------------

        for filename in (

            "kof2003.zip",

            "kof2003.7z",

        ):

            archive = (
                source_directory
                / filename
            )

            if archive.is_file():

                self._link_or_copy(
                    archive,
                    rom_root
                    / filename,
                )

                self._stage_neogeo_bios(
                    source_directory,
                    rom_root,
                )

                return


        # ----------------------------------------------
        # Loose ROM files
        # ----------------------------------------------

        if not romset.roms:

            raise ExtractionError(
                "The selected ROM folder "
                "contains no ROM files."
            )


        set_directory = (

            rom_root

            / self.SYSTEM_NAME

        )

        set_directory.mkdir(
            parents=True,
            exist_ok=True,
        )


        for rom in romset.roms:

            source = rom.path


            if not source.is_file():

                raise ExtractionError(
                    "A ROM file disappeared "
                    "from disk:\n\n"
                    f"{source}"
                )


            # Do not accidentally put the
            # Neo Geo BIOS archive inside
            # the kof2003 directory.
            if source.name.lower() in {

                "neogeo.zip",

                "neogeo.7z",

            }:

                continue


            destination = (

                set_directory

                / source.name

            )


            self._link_or_copy(

                source,

                destination,

            )


        self._stage_neogeo_bios(

            source_directory,

            rom_root,

        )


    # --------------------------------------------------
    # Cache
    # --------------------------------------------------

    def cache_paths(
        self,
        project: KofProject,
        fingerprint: str,
    ) -> tuple[
        Path,
        Path,
    ]:

        cache_directory = (

            project.cache_dir

            / "mame"

            / fingerprint[:16]

        )

        cache_directory.mkdir(
            parents=True,
            exist_ok=True,
        )


        return (

            cache_directory
            / "sprites_decrypted.bin",

            cache_directory
            / "manifest.json",

        )


    def cache_is_valid(
        self,
        output_path: Path,
        manifest_path: Path,
        fingerprint: str,
    ) -> bool:

        if not output_path.is_file():

            return False


        size = (
            output_path
            .stat()
            .st_size
        )


        if size <= 0:

            return False


        # Neo Geo tiles are 0x80 bytes.
        if size % 0x80:

            return False


        if not manifest_path.is_file():

            return False


        try:

            manifest = json.loads(

                manifest_path
                .read_text(
                    encoding="utf-8"
                )

            )

        except (
            OSError,
            json.JSONDecodeError,
        ):

            return False


        return (

            manifest.get(
                "cache_format_version"
            )
            == self.CACHE_FORMAT_VERSION

            and

            manifest.get(
                "rom_fingerprint"
            )
            == fingerprint

            and

            manifest.get(
                "system"
            )
            == self.SYSTEM_NAME

        )


    # --------------------------------------------------
    # Prepare extraction
    # --------------------------------------------------

    def prepare_sprite_extraction(
        self,
        project: KofProject,
        romset: NeoGeoRomSet,
    ) -> ExtractionJob:

        runtime_info = (
            self.runtime.probe()
        )


        project.ensure_workspace()


        fingerprint = (
            self.romset_fingerprint(
                romset
            )
        )


        (
            output_path,
            manifest_path,
        ) = self.cache_paths(

            project,

            fingerprint,

        )


        # ----------------------------------------------
        # Already extracted
        # ----------------------------------------------

        if self.cache_is_valid(

            output_path,

            manifest_path,

            fingerprint,

        ):

            return ExtractionJob(

                system_name=self.SYSTEM_NAME,

                program=
                    runtime_info.executable,

                arguments=[],

                working_directory=
                    runtime_info.runtime_dir,

                session_dir=
                    project.cache_dir,

                rom_root=
                    project.cache_dir,

                script_path=
                    project.cache_dir
                    / "cached",

                output_path=
                    output_path,

                manifest_path=
                    manifest_path,

                fingerprint=
                    fingerprint,

                cached=True,

            )


        # ----------------------------------------------
        # Temporary runtime session
        # ----------------------------------------------

        session_name = (

            f"{int(time.time())}-"

            f"{uuid.uuid4().hex[:8]}"

        )


        session_directory = (

            project.cache_dir

            / "runtime_sessions"

            / session_name

        )


        rom_root = (

            session_directory

            / "roms"

        )


        script_path = (

            session_directory

            / "dump_sprites.lua"

        )


        session_directory.mkdir(

            parents=True,

            exist_ok=True,

        )


        self._stage_romset(

            romset,

            rom_root,

        )


        script = (
            build_sprite_dump_script(
                output_path
            )
        )


        script_path.write_text(

            script,

            encoding="utf-8",

        )


        arguments = (
            build_extraction_arguments(

                self.SYSTEM_NAME,

                rom_root,

                script_path,

            )
        )


        return ExtractionJob(

            system_name=
                self.SYSTEM_NAME,

            program=
                runtime_info.executable,

            arguments=
                arguments,

            working_directory=
                runtime_info.runtime_dir,

            session_dir=
                session_directory,

            rom_root=
                rom_root,

            script_path=
                script_path,

            output_path=
                output_path,

            manifest_path=
                manifest_path,

            fingerprint=
                fingerprint,

            cached=False,

        )


    # --------------------------------------------------
    # Successful result
    # --------------------------------------------------

    def finalize_success(
        self,
        job: ExtractionJob,
    ) -> Path:

        if not job.output_path.is_file():

            raise ExtractionError(
                "MAME finished but KOF Studio "
                "did not receive the decrypted "
                "sprite region.\n\n"
                f"Expected:\n{job.output_path}"
            )


        size = (
            job.output_path
            .stat()
            .st_size
        )


        if size <= 0:

            raise ExtractionError(
                "The extracted sprite region "
                "is empty."
            )


        if size % 0x80:

            raise ExtractionError(
                "The extracted sprite region "
                "has an invalid Neo Geo tile "
                "alignment.\n\n"
                f"Size: {size:,} bytes"
            )


        manifest = {

            "cache_format_version":
                self.CACHE_FORMAT_VERSION,

            "system":
                job.system_name,

            "rom_fingerprint":
                job.fingerprint,

            "sprite_region":
                str(
                    job.output_path
                ),

            "sprite_region_size":
                size,

            "tile_count":
                size // 0x80,

        }


        job.manifest_path.write_text(

            json.dumps(
                manifest,
                indent=2,
            ),

            encoding="utf-8",

        )


        # Temporary copies are only removed
        # AFTER successful extraction.
        if not job.cached:

            shutil.rmtree(

                job.session_dir,

                ignore_errors=True,

            )


        return job.output_path