from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os
import platform
import subprocess
import sys


class RuntimeErrorBase(RuntimeError):
    """Base exception for bundled runtime problems."""


class RuntimeMissingError(RuntimeErrorBase):
    """MAME executable does not exist."""


class RuntimeProbeError(RuntimeErrorBase):
    """MAME exists but cannot be executed correctly."""


def application_root() -> Path:
    """
    Returns KOF Studio's application root.

    During normal Python development:
        project root/

    If KOF Studio is packaged later:
        directory containing the executable
    """
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent

    return Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class RuntimeInfo:
    executable: Path
    runtime_dir: Path
    version: str
    system: str


class MameRuntimeManager:
    """
    Manages the private MAME runtime bundled with KOF Studio.

    Windows:
        runtime/mame/mame.exe

    Linux:
        runtime/mame/mame

    The user does NOT choose a MAME executable.
    """

    def __init__(
        self,
        app_root: str | Path | None = None,
    ) -> None:

        if app_root is None:
            self.app_root = application_root()
        else:
            self.app_root = Path(app_root).resolve()

    @property
    def runtime_dir(self) -> Path:
        return (
            self.app_root
            / "runtime"
            / "mame"
        )

    def executable_candidates(self) -> list[Path]:
        candidates: list[Path] = []

        # Optional developer override.
        #
        # Windows:
        # set KOFSTUDIO_MAME_PATH=C:\MAME\mame.exe
        #
        # Linux:
        # export KOFSTUDIO_MAME_PATH=/usr/bin/mame
        override = os.environ.get(
            "KOFSTUDIO_MAME_PATH"
        )

        if override:
            candidates.append(
                Path(override)
                .expanduser()
                .resolve()
            )

        current_system = (
            platform.system()
            .lower()
        )

        if current_system == "windows":

            candidates.extend([
                self.runtime_dir / "mame.exe",
                self.runtime_dir / "mame64.exe",
            ])

        else:

            candidates.extend([
                self.runtime_dir / "mame",
                self.runtime_dir / "mame64",
            ])

        return candidates

    def executable(self) -> Path:
        """
        Returns the bundled MAME executable.
        """

        for candidate in self.executable_candidates():

            if candidate.is_file():
                return candidate

        locations = "\n".join(
            f"  - {candidate}"
            for candidate
            in self.executable_candidates()
        )

        raise RuntimeMissingError(
            "Bundled MAME runtime was not found.\n\n"
            "KOF Studio looked for:\n"
            f"{locations}\n\n"
            "Place the appropriate MAME runtime "
            "inside runtime/mame/."
        )

    def probe(
        self,
        timeout: int = 10,
    ) -> RuntimeInfo:
        """
        Run:

            mame -version

        to verify the runtime works.
        """

        exe = self.executable()

        if (
            os.name != "nt"
            and not os.access(exe, os.X_OK)
        ):
            raise RuntimeProbeError(
                "The bundled MAME executable exists "
                "but is not executable.\n\n"
                f"{exe}\n\n"
                "Run:\n"
                f"chmod +x '{exe}'"
            )

        try:

            result = subprocess.run(
                [
                    str(exe),
                    "-version",
                ],
                cwd=str(
                    self.runtime_dir
                ),
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
            )

        except subprocess.TimeoutExpired as exc:

            raise RuntimeProbeError(
                "Bundled MAME did not respond "
                f"within {timeout} seconds."
            ) from exc

        except OSError as exc:

            raise RuntimeProbeError(
                "Unable to execute bundled MAME.\n\n"
                f"{exe}\n\n"
                f"{exc}"
            ) from exc

        output = (
            result.stdout
            or result.stderr
            or ""
        ).strip()

        if result.returncode != 0:

            raise RuntimeProbeError(
                "Bundled MAME returned an error.\n\n"
                f"Exit code: {result.returncode}\n\n"
                f"{output}"
            )

        return RuntimeInfo(
            executable=exe,
            runtime_dir=self.runtime_dir,
            version=output or "Unknown",
            system=platform.system(),
        )