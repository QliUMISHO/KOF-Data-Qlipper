# KOF Studio — Starter

Early-stage external Neo Geo / KOF 2003 research and modding tool.

## Current features

- Open a ROM directory without modifying the original files.
- Classify common Neo Geo P/S/C/M/V ROM filenames.
- Calculate CRC32, SHA-1 and SHA-256.
- Inspect ROM data in a basic hex viewer.
- Save/load a `.kofproj.json` project.
- Generic big-endian binary reader/writer.
- Strict patch engine with expected-byte validation.
- Definition-driven KOF 2003 game data files.
- Placeholder character and sprite workspaces.
- Unit tests for binary I/O and patch safety.

## Setup

```bash
python -m venv .venv
```

Windows:

```powershell
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

Run tests:

```powershell
pytest -q
```

## Important design rule

Original ROM files are treated as source inputs. Do not overwrite them.
Later build steps should generate a separate output ROM set.

## Next milestones

1. Add ROM-set profiles and verified KOF 2003 hashes.
2. Add a searchable symbol/bookmark database.
3. Add ROM compare/diff.
4. Add patch-management UI.
5. Add safe generated build output.
6. Validate the KOF 2003 graphics decode path before implementing sprite rendering.
