# MM9 Arslegard City props as 3D decorations (2026-10-31)

The props, candles, chandeliers and street lamps of MM9's Arslegard City (`ARSLEGARDCITY.dat`), converted from their
LithTech ABC models into OpenYAMM 3D decorations for the native BLV ([map project](../../projects/mm9r_arslegardcity/)).
The route is Sturmford City's ([`../mm9_sturmfordcity_claude/`](../mm9_sturmfordcity_claude/README.md)), with the
scripts of Thjorgard City's copy ([`../mm9_thjorgardcity_claude/`](../mm9_thjorgardcity_claude/README.md)) adapted
here. No paid services, no Meshy, no Codex, no Real-ESRGAN: every model is MM9's own mesh with its skin x4 by plain
Lanczos (the isle's `textures.upscale`).

## Outputs

- **5 models built** and installed with `tools/install_model.py --world mm9` (`assets_source/worlds/mm9/models/mm9_deco_*.glb`,
  cooked copies in `assets_dev/engine/models/`), all through `check_winding.py` (0 inverted closed parts each: on the
  work exports, `work/check_winding_work.log`, and on the installed sources, `work/check_winding_installed.log`).
- **85 models reused** (same ABC and skin, or another project's HidePiece/tilt variant; their GLBs stay with their
  owners, `props_table.REUSED`, found with `work/registry.py`): Anskram Keep, Lich Lab, Klusos House, Drangheim Prison,
  Tasar Academy, Temple of Honk, Dook's Castle, Connecting Tunnels, Beethoven, Thjorad Mine, Training Hall, Ruined
  Temple, Lindisfarne, Inventa Storca (the Orb of Linking), the isle (`coatrack`, `logsburning`), Dark Passageway
  (`tree05`, `tree06`), and the cities: Sturmford (`chandelier2`, `clawlampup`, `kegbeer`, `vials`, `winebottle04`,
  the training dummies and archery target, `shield1flat`/`shield2flat`, `shelfitem03f`, `shelfitem09d`/`09sg`,
  `weaponracknewg3`), Thronheim (`benchlarge1`, `steinfancy01`, `suitofarmor01plain`, `shield3flat`/`shield4flat`,
  `weaponracknsnewg1`/`g3`), Drangheim City (`barstool2`, `cart02`, `jug1`, `shelfitem09`/`09g`, `shelfitem03hc`,
  `weaponrackg1`, `winebottle02`/`03`/`05`), Thjorgard City (`suitofarmor01gold`, `weaponracknsnewg2`).
- Rows **2610-2622** (13 rows: 6 for the 5 new models, one of them at two scales, and 7 new-scale variants of reused
  ones: `mm9_kegbeer_x200`, `mm9_platestack1_x200`, `mm9_platestack2_x200`, `mm9_steinfancy01_x200`,
  `mm9_tree05_x100`, `mm9_tree06_x100`, `mm9_weaponrackg1_x150`) in `assets_dev/worlds/mm9/data_tables/decoration_data.txt`,
  sprites **26411-26423**, 14 bindings in `worlds/mm9/models/indoor_decorations.yml`, appended in one run under
  `mm9r_common/locks/mm9_decorations.lock` (`work/tables_apply.log`). A rerun of `tables.py` reports 0 rows to add. No
  row carries a light. The trees take Dark Passageway's trunk blocker scaled to scale 1 (radius 31 / 30, height 250);
  the burning logs use the existing unlit `mm9_logsburning_x100` and `_x150` rows.
- `../../projects/mm9r_arslegardcity/props.json`: **419 placements** (360 `prop`, 59 `torch`), every Prop and
  CandleProp of the DAT except the five whose model MM9 does not ship (below). **412** are checked against the old
  map's baked BModel of the same object: **median of medians 0.50 units, worst 0.95** (the suits of armour; next crate
  0.78). The 7 not checked: the six pickaxes (posed `onside`, checked against MM9's own pose, `fit_pose_units`
  0.14-0.16) and the GiveTake scroll (Prop8, no bake: the old import made it a world item).
- `review/props_sheet.png`: contact sheet of the 5 built models (LOD0 front, three-quarter, side, behind-above, below;
  LODs), looked at; `review/<prop>/` the renders.

| Model | Triangles | Placements | Fit | Notes |
|---|---|---|---|---|
| `lamppost1` | 170 + 1 flame | 29 | 0.5 | the street lamps (CandleProp, no MM9 Light of their own); flame cards on the `Flame` socket, cut-out panes, no LODs |
| `horsestatue3` | 523 / 241 / 129 | 2 + 2 | 0.5 | HORSESTATUE with HorseStatue3, x1.5 and x2 (two rows) |
| `plate1p80` | 84 | 10 | 0.5 | PLATE1 with plate2, stood on edge: MM9's pitch 79.9 / 80.9 degrees as one variant at 80.4 (0.7 units apart at the rim), x2 |
| `clansoldierhelmet`, `dookmilitiahelmet` | 70 / 64 | 2 / 1 | 0.5 | helmets on the armourer's shelves, x1.5 |

## Notes

- **Not shipped by MM9** (`work/missing_models.txt`, MODELS.REZ has no such file; the old import's
  `baked_model_missing_source: 5`): `models\Props\GoblinStatue1.ABC` (Prop57, Prop188, Prop189, the three statues
  on the north terrace) and `models\PickupItems\spellbook1.abc` / `spellbook3.abc` (Prop6, Prop36): no decoration
  (`props_table.SKIPPED`); MM9 shows nothing there. Njam's own model (`models\NjamtheMeddler.abc`) is not shipped
  either: he is an actor of the map project (MM9 row 261), not a decoration.
- **Scroll1/Scroll2** name `skins\PickUpItems\scroll.dtx`, which MM9 does not ship: the same ABC with Tasar Academy's
  `scrolldouble` skin (its `scrollpickup`, a new x1.5 row of theirs reused) stands in.
- **The burning logs**: Prop51 and Logs0 lie under MM9's two `Fire` objects (Fire0, FireScale 1; Fire3, FireScale 4):
  the isle's `logsburning` (its flame cards; `OBJECT_PROP`).
- **Pickaxes** (PropAnim `onside`): Tasar Academy's posed `dwarfaxeonside`, base on the DAT surface under them (the
  smithy's shelves at LT -156 and -124: MM9's MoveToFloor). The old map's BModels have no floor there (the old import
  dropped them 10-80 units lower), so `placements.py` asks the DAT (`dat_floor`).
- **HidePiece**: every combination here is another project's variant (`HIDDEN`); ShelfItem05 has no Wands1 or
  Crystals1, so its three shelves are the plain `shelfitem05` (`NO_SUCH_PIECE`).
- **Lights**: the 30 chandeliers, wall candles and the claw lamp each name the nearest DAT `Light` (0-41 units off) in
  `light`. The 29 street lamps have none in MM9 (it lit the streets by its lightmaps), so they carry only their flame.

## Route (`scripts/`)

```sh
cd level_generation/props/mm9_arslegardcity_claude
python3 work/registry.py && python3 scripts/props_table.py && python3 scripts/convert_all.py && python3 scripts/textures.py
blender --background --factory-startup --python scripts/build.py
python3 scripts/finish.py --install
blender --background --factory-startup --python scripts/review.py && bash scripts/contact_sheet.sh
cd ../../.. && flock -x level_generation/projects/mm9r_common/locks/mm9_decorations.lock \
    python3 level_generation/props/mm9_arslegardcity_claude/scripts/tables.py --apply && cd -
python3 scripts/placements.py --verbose            # --preview writes work/props_preview.json instead
python3 ../../projects/mm9r_common/review_root.py
```
