from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import json


@dataclass
class CharacterDefinition:
    id: str
    name: str
    team: str
    category: str = "roster"
    selectable: bool = True
    notes: str = ""
    default_sprite_ranges: list[dict] = field(default_factory=list)

    @classmethod
    def from_dict(cls, item: dict) -> "CharacterDefinition":
        return cls(
            id=str(item["id"]),
            name=str(item["name"]),
            team=str(item.get("team", "")),
            category=str(item.get("category", "roster")),
            selectable=bool(item.get("selectable", True)),
            notes=str(item.get("notes", "")),
            default_sprite_ranges=list(item.get("sprite_ranges", [])),
        )


class CharacterCatalog:
    def __init__(self, characters: list[CharacterDefinition], source_path: Path | None = None):
        self.characters = characters
        self.source_path = source_path

    @classmethod
    def load(cls, path: str | Path) -> "CharacterCatalog":
        path = Path(path)
        payload = json.loads(path.read_text(encoding="utf-8"))
        return cls(
            [CharacterDefinition.from_dict(x) for x in payload.get("characters", [])],
            source_path=path,
        )

    def get(self, character_id: str) -> CharacterDefinition | None:
        return next((x for x in self.characters if x.id == character_id), None)
