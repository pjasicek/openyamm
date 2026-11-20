# MM9 Dook's Castle props as 3D decorations (2026-10-30)

The props, wall sconces, braziers, hanging bowls, chests, suits of armour, shields and banners of MM9's Dook's Castle,
converted from their LithTech ABC models into OpenYAMM 3D decorations for the native BLV
([map project](../../projects/mm9r_dookscastle/README.md)). The route is Drangheim Prison's props project (itself the
Lich Lab's): one material per MM9 skin, a placement tilt baked in, the isle's `blib` build and `finish` checks. No paid
services, no Meshy, no Codex: every model is MM9's own mesh with its skin x4 (plain Lanczos, the user's rule since
2026-10-30).

## Outputs

- **9 models** built and installed with `tools/install_model.py --world mm9` (`assets_source/worlds/mm9/models/mm9_deco_*.glb`),
  all through `check_winding.py` in `finish.py`: `bedornate` (the Dook's four-poster), `cards`, `suitofarmor02` (two
  skins: the gold armour and its halberd), `shield1`, `shield2`, `shield4`, `shield3r` (Klusos House's `shield3` skin
  rolled), `tapestry_banner4` (the green banners, `TEXTURES\LevelTextures\misc\banner4.dtx`), `weaponracknew`.
- **20 reused** (same ABC and skin; their GLBs and rows stay with their owners): Anskram's `barrel03`, `bedmedium`,
  `bookcase02ew`, `chair`, `desk01`, `scroll`, `tableround`, `weaponscabinet04`, `chest`; the Temple of Honk's
  `brazier`, `hangingbowl`, `chairdesk01`; the Chasm's `boxornamental`; Klusos House's `cabinet02`, `cabinet05`,
  `dresserfancyns`; the Lich Lab's `throne`, `blackchest`; Verhoffin Ruins' `sconce1` (flame cards on the head, the
  18 `WallTorch`es).
- Rows **2278-2294** (17 rows: the 9 models and the scale variants `mm9_bedmedium_x100`, `mm9_bookcase02ew_x100`,
  `mm9_boxornamental_x150`, `mm9_cabinet02_x125`, `mm9_desk01_x120`, `mm9_dresserfancyns_x150`,
  `mm9_hangingbowl_x200`, `mm9_throne_x120`) in `assets_dev/worlds/mm9/data_tables/decoration_data.txt`, sprites
  26079-26095, bindings in `worlds/mm9/models/indoor_decorations.yml`, appended under
  `mm9r_common/locks/mm9_decorations.lock` (`tables.py --apply` takes it). No row carries a light: every sconce,
  brazier and bowl has its MM9 `Light` beside it, kept as a BLV light or bake-only.
- `../../projects/mm9r_dookscastle/props.json`: **97 placements** (57 props, 18 wall torches, 12 braziers, 7 chests,
  3 barrels), each checked against the old map's baked BModel: median of medians 0.49 units. Worst: the four shields
  (36.8-39.7, below); four hanging bowls the old import did not bake (placed by the transcoder's rule).

## Route (`scripts/`)

```sh
cd level_generation/props/mm9_dookscastle_claude
python3 scripts/props_table.py && python3 scripts/convert_all.py && python3 scripts/textures.py
blender --background --factory-startup --python scripts/build.py
python3 scripts/finish.py --install
python3 scripts/tables.py --apply                 # takes the decorations lock itself
python3 scripts/placements.py
python3 ../../projects/mm9r_common/review_root.py
blender --background --factory-startup --python scripts/review.py && bash scripts/contact_sheet.sh
```

## Notes

- **Shields**: MM9 hangs them on the shield room's walls at pitch 1.571, the two on the north wall with roll 0, the two
  on the south wall with roll pi. Through the transcoder's tilt (pitch, then roll) roll 0 hangs a heater shield point up
  (Klusos House's `shield3`, its review v04 l09); all four are baked with roll pi, point down, as a shield hangs
  (`props_table.TILTS`; the models are double-sided). Their fit (36.8-39.7) measures the old import, which baked them
  lying flat. `Sheild0` hangs over MM9's invisible `Tempbutton`: its click is the secret door's event (map README).
- **`suitofarmor02`**: the ABC binds skin 0 (`AmoredSuitGold`) and skin 1 (`AmoredSuitHalberd`); `build.py` keeps a
  material per skin. Two closed pieces came out inverted; `build.py` reverses negative-volume closed pieces (Klusos
  House's `fix_closed_parts`) before smoothing.
- **`weaponracknew`** carries MM9's quarter turn (`specs.json` `turn: 90`, as Drangheim's `weaponrackns`).
- `cards` is a flat fan of cards on the table (0.2 units tall), no collision.
- Contact sheet: `review/props_sheet.png` (looked at).


## Bone-display ball removed (2026-10-31)

Blender 5's glTF importer adds an `Icosphere` bone-display mesh (42 vertices, 80 triangles, 2.4 cm) to every skinned
(`full`) import, and the isle's `blib.import_raw` took every imported mesh, so the ball stayed in the decoration (Tasar
Academy found it). Removed from `weaponracknew` 1355 / 676 / 336  -> 1275 / 635 / 317 triangles (LOD0 / LOD1 / LOD2).
`scripts/build.py` sets the isle's `blib.SKIP_BONE_SHAPES` and passes `disable_bone_shape` to its own per-face skin
import; LOD0 lost exactly the ball (inside the rack), LOD1/LOD2 were remade. Rebuilt, checked (`finish.py`,
check_winding.py: 0 inverted closed parts) and reinstalled with `install_model.py --world mm9`; the replaced GLBs and
scripts are in `work/backup_propfix_20261031/`. No MM9 bake depends on decoration models (stale_bakes.py lists none).
