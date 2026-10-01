# KOF Studio v0.2 Character Extractor — Drop-in Update

Copy these files over the corresponding files in your current KOF Studio tree.

## What this adds

- Complete KOF 2003 regular roster list in the **Characters** tab.
- Separate roster/sub-boss/boss filters.
- Search by name/team.
- Sprite viewer directly inside the Characters tab.
- MAME-assisted dump of the already-decrypted Neo Geo `:sprites` region.
- Neo Geo 16x16 4bpp tile decoding.
- Raw tile-range preview.
- Per-character sprite-range mappings stored in the `.kofproj.json`.
- PNG extraction into:

`<project>.workspace/extracted/characters/<character-id>/`

- Extracted PNG sheets automatically appear when the character is selected.

## Important: automatic per-character separation is not guessed

KOF 2003's C-ROMs are protected. The tool can now get a **decrypted sprite
region** from MAME and render it correctly, but KOF Studio does not yet know
which tile/animation records belong to each character.

That mapping must come from the KOF 2003 animation/sprite tables that we will
reverse-engineer next.

So the workflow is:

1. Save/open a KOF Studio project.
2. Open **Characters**.
3. Click **Dump with MAME…**.
4. Select your local MAME executable.
5. Select the MAME ROM root containing your own KOF 2003 set.
6. Dump the decrypted sprite region.
7. Select a character.
8. Browse a candidate tile start/count.
9. Preview it.
10. Once verified, assign the range to the selected character.
11. Save the project.
12. Extract the sheet PNG.

## After copying

Run:

```powershell
pytest -q
python main.py
```
