# MM9 Bathhouse props as 3D decorations (2026-10-30)

The props, urns, chests and letters of MM9's Bathhouse (Arslegard), converted from their LithTech ABC models into
OpenYAMM 3D decorations for the native BLV ([map project](../../projects/mm9r_bathhouse/README.md)). The route is the
Chasm of the Dead props project's ([`../mm9_chasmofthedead_claude/`](../mm9_chasmofthedead_claude/README.md)):
`scripts/anskram.py` runs the Anskram Keep scripts on this project's table, `build.py` runs the Anskram build,
`finish.py` the isle's. No paid services and no Codex images: every model is MM9's own mesh and skin, the skins
enlarged x4 with Lanczos (the shared `textures.py`; no Real-ESRGAN).

## Outputs

- **2 models** built and installed with `tools/install_model.py --world mm9` (`assets_source/worlds/mm9/models/mm9_deco_*.glb`,
  cooked copies in `assets_dev/engine/models/`); both pass `check_winding.py` (0 inverted closed parts).
- **Reused**, not rebuilt: the Temple's `benchstone02` (x1.5 row here), Beethoven's `urngargoyle` (its row at x1, a
  x1.5 row here), the Chasm's `chest5`, the Lich Lab's `blackchest`, Anskram's `scroll` and `gatefire` (two unlit
  rows at the furnace fires' scales).
- The MM9 world's decoration contribution: **rows 2263-2268** in `assets_dev/worlds/mm9/data_tables/decoration_data.txt`
  (sprites 26064-26069, bindings in `worlds/mm9/models/indoor_decorations.yml`, block "MM9 Bathhouse props"), appended
  under `locks/mm9_decorations.lock`.
- `../../projects/mm9r_bathhouse/props.json`: **59 placements** (12 benches, 2 pews, 18 towel racks, 21 urns, 4
  chests, 2 letters), each checked against the old map's baked BModel: median vertex distance 0.44 units, worst 0.74
  (the black chest).
- `review/props_sheet.png`: contact sheet of the two new models.

| Model | Source ABC (skin) | Placements | Triangles | Notes |
|---|---|---|---|---|
| `towelrack` | COATRACK1 (TOWELRACK1) | 18 | 338 / 168 / 84 | MM9 places them with `HidePiece0 Hat1`: the hat is stripped from the raw import (`scripts/strip_pieces.py`), towels only; x2 |
| `pew3` | PEW3 | 2 | 118 | x1.2 (`Bench16/17`) |
| `benchstone02_x150` | the Temple's BENCH_STONE02 | 12 | 156 | x1.5 |
| `urngargoyle`, `urngargoyle_x150` | Beethoven's URNGARGOYLE | 2 / 19 | 176 | `DestructableProp`s in MM9 (they break and drop a TreasureBag): decorations here (README of the map, Deviations) |
| `chest5`, `blackchest` | the Chasm's / Lich Lab's | 3 / 1 | 122 | |
| `scroll` | Anskram's SCROLL-OPEN | 2 | 80 | the two letters (BookLetter.scr) |
| `gatefire_x8`, `gatefire_x33` | Anskram's flame cards (unlit rows) | (4) | 6 | the furnace fires: FireScale 1 and 4 against the gate fires' 12; placed by the map project |

## Route (`scripts/`)

```sh
cd level_generation/props/mm9_bathhouse_claude
python3 scripts/props_table.py && python3 scripts/convert_all.py && python3 scripts/strip_pieces.py
python3 scripts/textures.py
blender --background --python scripts/build.py -- pew3 towelrack && python3 scripts/finish.py pew3 towelrack --install
blender --background --python scripts/review.py -- pew3 towelrack && bash scripts/contact_sheet.sh
flock -x ../../projects/mm9r_common/locks/mm9_decorations.lock python3 scripts/tables.py --apply
python3 scripts/placements.py && python3 ../../projects/mm9r_common/review_root.py
```

## Notes

- `strip_pieces.py` keeps the unstripped import as `work/raw/towelrack/towelrack_full.glb`: the old map's bake keeps
  the hat, so `placements.py` fits against that one (with the stripped mesh the fit was 4.7 units off).
- `tables.py` reuses a reused prop's own row when its height already matches the placement scale (no duplicate x100
  rows); `EXTRA_VARIANTS` adds rows nothing in `props.json` places (the furnace fires).
- No row carries a light: MM9's `Light` objects are the BLV's lights.
