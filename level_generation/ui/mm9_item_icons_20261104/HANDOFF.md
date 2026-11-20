# Handoff: MM9 item icons and paperdoll art (2026-11-05, installed at x2)

Read this first, then [`README.md`](README.md) (icons) and [`paperdoll/README.md`](paperdoll/README.md) (doll art and
placement). The whole folder is under the git-ignored `level_generation/`, so it exists only on this machine. The art
is installed into MM9 at x2 (`assets_dev/worlds/mm9/`, also git-ignored); the install tools and manifests under
`tools/mm9_import_discovery/` and the x2 icon package line are uncommitted working-tree changes.

## Where it stands

| Part | State |
|---|---|
| Inventory icons, MM7/MM8 style | **Installed** at x2 in `assets_dev/worlds/mm9/icons_x2/` (391 items, 245 designs). |
| Weapon and shield grips (Equip X/Y) | **Installed** (97 items, `mm9_item_equipment_visuals.yml` regenerated from the x2 icons). |
| Worn doll art (armour, helm, belt, boots) | **Installed**: 68 items on all five dolls, 488 x2 files. |
| Positions (`complex_item_pictures.txt`) | **Installed**: 81 rows (68 worn, five helms on a changed reference; 13 new gauntlet rows). |
| Gauntlets, amulets, rings (jewellery panel) | **Installed**: gloves 34x64 logical inside the 40x72 cell; amulets and rings are centred by the engine. |
| Follow-ups of 2026-11-05 | Witchbane's eye sockets, nose and mouth are transparent (`see_through` in `pieces.yml`). War Star, Imperial Star and Blutterbunger repainted with slim handles (old art in `items/<id>/old_thickgrip/`). Blackpowder refitted smaller so it hides behind the body like MM crossbows. Their grips recomputed. |

## The review viewer

Open `paperdoll/review/viewer/index.html` directly in a browser (self-contained, no server needed; 36 MB). Tabs:

- **Outfits:** four outfits on all five dolls, each as new MM9 art, current MM9 art and the MM7/MM8 reference
  pieces, holding the weapon or empty-handed:
  - A: Chedian Chain, Dragon Helm, Soldier's Belt, Leather Boots, Imperial Sword.
  - B: Thjoradric Plate, Jarl's Helm, Regal Belt, Prote der Fatta, War Star.
  - C: Paladin's Plate, Imperial Helm, Dragon Belt, Sabaton.
  - D: Dark Plate, Witchbane, Hubris, Death Boots.
- **Pieces:** all 68 pieces, filterable by slot or "Not flagged". Each has its review sheet (reference rows above
  the new rows, both arm poses for armour), the fill shares, and a note where its outline is not the mapping table's.
- **Weapons:** five weapons in the hand on every doll, new grip beside current.
- **All grips:** all 97 weapons, missile weapons and shields on all five dolls (`scripts/all_weapons.py`).
- **Jewellery:** the jewellery panel with MM8, MM7 and MM6 reference items, then every MM9 gauntlet with amulets and
  rings (`scripts/jewelry.py`).
- **How it works:** the method, with the prototype's and the full pass's findings.

Every piece and weapon has Good / Needs redo buttons and a note. Flags live in the browser's local storage only (the
same key as the prototype's viewer, so earlier flags are kept); **Export flags** downloads `flags.json`. Ask the user
to save it as `paperdoll/review/viewer/flags.json` and read it from there.

Refresh the viewer after changing art: `python3 scripts/outfit.py`, `python3 scripts/all_weapons.py`,
`python3 scripts/jewelry.py`, then `python3 scripts/viewer_data.py` (from `paperdoll/`). After repainting a weapon
icon, first `python3 -I scripts/check_doll_grip.py` (from the project root) and `python3 scripts/equip_table.py`.

## Install

Done on 2026-11-05 with the user's go-ahead and choice of x2; the steps, the tools changed and what is left
superseded are in [`README.md`](README.md), "Installed". Open: flags from the user's review, if any; then redo the
piece and rerun the three install commands.

## How to redo a piece

From `paperdoll/` (details in [`paperdoll/README.md`](paperdoll/README.md), "Full pass"):

- **Another pick.** `python3 scripts/finish_piece.py <piece> --pick <piece>:t<N>=gen_<n>.png` fits that
  generation, then `paperdoll.py install` is re-run for the piece (see the README's commands) and
  `scripts/viewer_data.py`.
- **A changed outline** (edit `pieces.yml`): `python3 scripts/retire_masters.py <tag> <piece> t<N> ...` moves the old
  generations aside and re-prepares. Then `python3 scripts/codex_queue.py <piece>`, then `finish_piece.py`.
- Judge the candidates sheet (`work/<piece>/review/candidates.jpg`) and the doll renders, not the fill share alone.
  Require 0 opaque magenta and 0 feet overlap (`finish_piece.py` prints any).

### Lessons

- **Cut the outline before generating** when the reference has parts the MM9 design lacks:
  - MM7 full-leg suits: `coverage_limits {1: 230}` for the human female.
  - MM8 bodysuits whose legs survive hip_length on the human male and dwarf: lower limits.
  - Helms with horns: `smooth_crown`, or, when the horns sit low (Mogred, Drogg's), another reference.
  - Shaftless footwear: `keep_lower`.

  Check every target on its doll first: `python3 scripts/targets.py <out.png> <piece> ...` shows the reference cut,
  worn, with the removed part tinted.
- Codex follows the design well but the outline only roughly, and its magenta background is never flat; the fitter
  handles both. Its self-reported "pass" flags in the job logs are not a useful filter.
- Belts often lose the reference's downward strap tab; the fit fills it, so prefer the generation that drew it.
- Armour's weapon pose (`vN`) is cut from the no-weapon master (`vNa`), not generated separately.

## Facts that are easy to get wrong

- The engine **negates** every doll-type Y value (`CharacterDollTable`). The right-hand fingers cover about anchor
  Y -9 to +8, not below the anchor. An earlier grip check of mine drew the fist 18 px too low; it is corrected in
  `scripts/check_doll_grip.py`.
- Main-hand anchor = (right-hand fingers X + fingers width / 2, right-hand closed Y + main-hand offset Y); the icon is
  drawn at anchor minus Equip X/Y. Two-handed weapons and spears below Master hide the open left hand and draw the
  left holding hand.
- Doll file names: `<Pic File>vN` (armour while holding a weapon, helm, belt, boots) and `<Pic File>vNa` (armour,
  empty hands), N = doll type + 1. Doll types: 0 human male, 1 human female, 2 minotaur (no helm or boots), 3 troll,
  4 dwarf.
- `generate_mm9_item_equipment_visuals.py` has a `MANUAL_ANCHOR_OVERRIDES` entry for item 75 (Imperial Star) made for
  the old diagonal art; drop it when installing the new icons. `check_doll_grip.py` clears it in-process; the shared
  tool itself is unchanged.
- Shared code was not modified: the Hesper paperdoll scripts, the generator, the previewer
  (`tools/mm9_import_discovery/render_paperdoll_equipment_preview.py`). The MM9 project configures them from
  `paperdoll/scripts/`.

## Rules the user set

- No `git add/commit/stash/reset/restore --staged` unless asked. Installing into `assets_dev` was approved on
  2026-11-05; reinstall through the README's install commands.
- Codex is used for image generation only, through `codex exec` workers; up to 16 at once.
- The `rm` hook blocks wildcards: list files, then remove literal paths.

## Size

The project is about 2.9 GB:

- `items/`: 681 MB (icon generations and old versions).
- `paperdoll/`: 2.2 GB, mostly `work/<piece>/review/` full-size renders and the raw Codex paintings in
  `work/<piece>/t<N>/raw/`.
- The viewer: 36 MB.

The review PNGs can be regenerated (`finish_piece.py`); the raw paintings cannot.
