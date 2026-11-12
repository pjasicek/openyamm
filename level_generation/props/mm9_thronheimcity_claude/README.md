# MM9 Thronheim City props as 3D decorations (2026-10-31)

The props, candles, chandeliers, street lamps, flower boxes, the treasure chest and the council's six RUDEProps of
MM9's Thronheim City (`THRONHEIMCITY.dat`), converted from their LithTech ABC models into OpenYAMM 3D decorations for
the native BLV ([map project](../../projects/mm9r_thronheimcity/)). The route is Sturmford City's
([`../mm9_sturmfordcity_claude/`](../mm9_sturmfordcity_claude/README.md)), its scripts copied here and adapted. No paid
services, no Meshy, no Codex, no Real-ESRGAN: every model is MM9's own mesh with its skin x4 by plain Lanczos (the
isle's `textures.upscale`).

## Outputs

- **25 models built** and installed with `tools/install_model.py --world mm9` (`assets_source/worlds/mm9/models/mm9_deco_*.glb`,
  cooked copies in `assets_dev/engine/models/`), all through `check_winding.py` (0 inverted closed parts each: on the
  work exports, `work/check_winding_work.log`, and on the installed sources, `work/check_winding_installed.log`).
- **63 models reused** (same ABC and skin, or Sturmford's HidePiece/tilt variants; their GLBs stay with their owners,
  `props_table.REUSED`, found with `work/registry.py`): Sturmford City (`barstool1`, `bjarnisitting`, `chandelier2`,
  `clawlampup`, `kegbeer`, `portalwhole`, `shelfitem03f`, `shelfitem09sg`, `shelfitem09d`, `shield2flat`,
  `strawdummy2c/l/r`, `trainingarchery1`), Anskram Keep (`barrel`, `barrel03`, `bookcase02ew/ns`, `chair`, `chair02`,
  `chest1`, `scroll`, `tableround`), Lich Lab (`chair03`, `podium01`, `shelfitem01/02/03/05`, `table01`, `table01ns`),
  Drangheim Prison (`anvil`, `cabinet04ns`, `coalbin`, `ironingots`, `sack03`), Klusos House (`cabinet02`, `pew2ns`,
  `pitcher01`, `tableround5`, `tabletrestle2`, `wallcandle`), Beethoven (`jar01`-`jar06`), Tasar Academy (`bagherbs1`,
  `forge`, `smithhammer`), the isle (`coatrack`, `logsburning`, `well`), Lindisfarne (`benchlarge1ns`, `pew2`), Training
  Hall (`spindummy`, `trainingmount`), Dook's Castle (`suitofarmor02`), Temple of Honk (`bookflat`), Ruined Temple
  (`chandelier3`), Chasm of the Dead (`chest5`), Thousand Terrors (`scrollp90`).
- Rows **2516-2551** (36 rows: the 25 new models and 11 new-scale variants of reused ones) in
  `assets_dev/worlds/mm9/data_tables/decoration_data.txt`, sprites **26317-26352**, 36 bindings in
  `worlds/mm9/models/indoor_decorations.yml`, appended in one run under `mm9r_common/locks/mm9_decorations.lock`
  (`work/tables_apply.log`; the table is contiguous 2001-2551). A rerun of `tables.py` reports 0 rows to add. No row
  carries a light. New-scale rows: `mm9_bagherbs1_x200`, `mm9_chandelier2_x75`, `mm9_jar02/03/05/06_x150`,
  `mm9_kegbeer_x100`, `mm9_pew2_x110` (no collision: those pews are not Solid), `mm9_pew2_x120`,
  `mm9_shelfitem03f_x150`, `mm9_tableround5_x100`. The burning logs use the existing unlit `mm9_logsburning_x100` and
  `_x150` rows.
- `../../projects/mm9r_thronheimcity/props.json`: **307 placements** (235 `prop`, 64 `torch`, 6 `npc`, 1 `chest`,
  1 `quest`), every Prop, CandleProp, DestructableProp, Barrel, WellMMIX, TreasureChest and RUDEProp of the DAT except
  the 14 on the cinema stage (below). **298** are checked against the old map's baked BModel of the same object:
  **median of medians 0.51 units, worst 0.86** (Prop12, a chair; next Shelfitems11 0.85, Table0 0.84); per model
  0.31-0.84. The 9 not checked: the six seated council members and Markel dead (no posed bake; checked against MM9's
  own pose, `fit_pose_units` 0.01-0.03), TreatyProp (lying by its script, checked against the tilted MM9 model at the
  bake's centre and base, 0.13) and Kira's shield (no bake: on the floor under its DAT position, MoveToFloor).
- `review/props_sheet.png`: contact sheet of the 25 built models (LOD0 front, three-quarter, side, behind-above, below;
  LODs), looked at; `review/<prop>/` the renders.

| Model | Triangles | Placements | Fit | Notes |
|---|---|---|---|---|
| `lamppost3` | 158 + 1 flame | 35 | 0.50 | the street lamps; flame cards on the Flame socket (as Sturmford's `lamppost4`), cut-out panes, no LODs |
| `flowerboxns`, `flowerboxew` | 23 | 8 + 5 | 0.62 | DestructableProps, x1.4; `flowerboxns` carries MM9's quarter turn (`specs.json` `turn: 90`) |
| `herbrack1` | 268 | 8 | 0.48 | hanging herb racks, x1.5, cut-out herbs; no LODs (the decimated LODs lost the herbs) |
| `pottedplant1/2/3` | 134 / 118 / 203 | 6 / 3 / 2 | 0.47-0.57 | x2, cut-out leaves |
| `steinfancy01`, `plateset2` | 320 / 298 | 8 / 3 | 0.49-0.71 / 0.52 | table things, no collision |
| `benchlarge1`, `coatrack2` | 120 / 576 | 3 / 1 | 0.40 / 0.54 | |
| `suitofarmor01plain` | 542 | 3 | 0.49 | SUITOFARMOR01 with AmoredSuitPlain, x1.2 |
| `tapestry_banner8` | 48 | 2 | 0.47-0.49 | Tapestry-Old01 with Banner8, x2, wall-hung, double-sided |
| `shield3flat`, `shield4flat` | 104 | 1 each | 0.39 | Shield.ABC lying flat (pitch pi/2; the bake is 10 units high), Sturmford's rule |
| `shelfitem02mp` | 282 | 2 | 0.77 | ShelfItem02 without Amulets1, SkelBones1, Skull1 (HidePiece) |
| `weaponracknsnewg1`, `weaponracknsnewg3` | 965 / 1001 | 1 each | 0.58 / 0.60 | WeaponRackns without Group1 / Group3, quarter turn baked in (as Dook's `weaponracknew`) |
| `kirashield` | 140 | 1 | - | Kira's shield, quest pickup (KiraShield.scr) |
| `svensitting` | 794 | 1 | pose 0.02 | Sven_ARG `sitting` on its own chair piece (two skins: Sven, ChairPlain) |
| `tryggvasit`, `markelsit`, `foradsit`, `sigmundsit` | 652-722 | 1 each | pose 0.01-0.03 | the council, `sit` |
| `markeldie2` | 652 | 1 | pose 0.03 | Markel dead (PropAnim `static_die2`) |

## RUDEProps and other named entities (entity name = `source_name` in props.json)

The six RUDEProps sit at the council table (on the room's chairs Prop13-17; Sven on his model's own chair), each a
static decoration in its pose, `kind: npc`, with `script`, `script_params` and `rude_npc_id` (the DAT's RUDENPCId, a
float stored as its bits, decoded). MM9 places them hidden (Visible 0): ARG_Unhide.scr shows them, BookProp and
TreatyProp once keys 90 and 91 are held and hides them again with key 94. They carry `visible: false` in props.json, as
does MarkeProp0 (NPC239.scr shows it).

| Entity | Decoration | Script (params) | rude_npc_id | Notes |
|---|---|---|---|---|
| `SvenProp` | `mm9_svensitting` | PropAnim.scr (Sit) | 3 | hidden at start; Sven_ARG has no `Sit`, MM9 plays its first animation `sitting` |
| `TryygvaProp` | `mm9_tryggvasit` | PropAnim.scr (Sit) | 180 | hidden at start |
| `MarkeProp` | `mm9_markelsit` | PropAnim.scr (Sit) | 127 | hidden at start |
| `ForadProp` | `mm9_foradsit` | PropAnim.scr (Sit) | 2 | hidden at start |
| `SigmundProp` | `mm9_sigmundsit` | PropAnim.scr (Sit) | 87 | hidden at start |
| `BjarniProp` | `mm9_bjarnisitting` | PropAnim.scr (Sit) | 45 | hidden at start; Sturmford's model |
| `MarkeProp0` | `mm9_markeldie2` | PropAnim.scr (static_die2) | - | `kind: prop`, Markel dead on the floor, not Solid, hidden at start |
| `TreatyProp` | `mm9_scrollp90` | Propanim.scr (Down) | - | the treaty on the council table, lying flat, hidden at start |
| `BookProp` | `mm9_bookflat` | Book.scr | - | council table, hidden at start |
| `Book1` | `mm9_bookflat` | scripts\book.scr | - | |
| `Prop18`, `Prop19`, `Prop20`, `Prop21` | `mm9_scroll` | BookLetter.scr (467, 466, 468, 469 `Letter 1`) | - | |
| `Shield` | `mm9_kirashield` | KiraShield.scr | - | `kind: quest`: with key 214 and not 216, gives key 216 and item 375 and removes itself |
| `TownPortal0` | `mm9_portalwhole` | TownPortal.scr (Thronheim) | - | |
| `Prop16` | `mm9_chair` | arguetreaty.scr (ChairMarker2) | - | a council chair (the script only moves it on `Play`) |
| `Prop97`, `Prop96`, `Prop124` | `mm9_chest1_x100` | scripts\PropAnim.scr (static_model) | - | `kind: prop` (no loot) |
| `Flowerboxes3/7/10/12/17/18/19/20` | `mm9_flowerboxns` | scripts\PropAnim.scr (ns) | - | the `ns` animation is not in FlowerBoxNS.abc |
| `TreasureChest0` | `mm9_chest5` | - | - | `kind: chest`, `loot_container: 0` |

No DAT name repeats. `Plant10` is a decoration's name (MM8's plant) and is `Plant10_252` (`dat_name` keeps the DAT's).

## Route (`scripts/`)

```sh
cd level_generation/props/mm9_thronheimcity_claude
python3 scripts/props_table.py && python3 scripts/convert_all.py && python3 scripts/textures.py
blender --background --factory-startup --python scripts/build.py
python3 scripts/finish.py --install
blender --background --factory-startup --python scripts/review.py && bash scripts/contact_sheet.sh
cd ../../.. && flock -x level_generation/projects/mm9r_common/locks/mm9_decorations.lock \
    python3 level_generation/props/mm9_thronheimcity_claude/scripts/tables.py --apply && cd -
python3 scripts/placements.py --verbose            # --preview writes work/props_preview.json instead
python3 ../../projects/mm9r_common/review_root.py
```

`tables.py` does not take the lock itself. `work/registry.py` maps every (ABC, skin) of the other MM9 props projects
to its prop and owner (`work/registry.json`): the reuse check, rerun right before installing.

## Notes

- **Not placed: the cinema stage.** The Argument cinema under the city (DAT y < 900, about the origin) is not built in
  the native map (the map agent's decision): `CandleProp14/17/18/19` (chandelier3), `Prop10` (burning logs under
  Fire5), the chairs `Prop2/3/4/6/7/11`, `Prop9` (the treaty, arguetreaty.scr `treatymarker 4 1`), `Prop8` (Book.scr)
  and `Sven` (ARG_Sven.scr). No model is used only there (`props_table.STAGE_Y`).
- **The two `Clover` objects** were left out at first ("not a decoration class", Sturmford's decision);
  the two `Clover` objects are placed since 2026-11-12 (Drangheim City's `mm9_clover`, the existing row; appended to `props.json` from `placements.py --preview`, the other entries left as installed): the map's clover events had nothing to click.
- **Quarter turns.** FlowerBoxNS.abc and WeaponRackns.abc are authored north-south but MM9 shows them east-west (the old
  bakes: 308 x 106 and 239 x 89); without the turn they fit at 143 and 38 units, with it 0.62 and 0.58-0.60.
- **ShelfItem05's HidePieces** (Wands1, Crystals1) name no piece of ShelfItem05.abc (five jars): plain `shelfitem05`.
- **Scroll `down`.** Scroll-open's `down` animation is exactly pitch pi/2 of the static model (0.0 LT), so the scrolls
  that a script lays down (TreatyProp, and the stage's Prop9) are 1000 Terrors' `scrollp90`; TreatyProp's base is on
  the old bake's base (the table top, 3362).
- **Burning logs.** All three LogsBurning props lie under a Fire (Prop22 under Fire4, Prop5 under Fire2 + Fire3,
  Prop10 under Fire5 on the stage): the isle's `logsburning` with its flame, unlit rows (the map keeps the fires'
  lights).
- **Seats.** The council sits with feet on the floor (3277; MoveToFloor), on the room's chairs; their pose fits MM9's
  at 0.01-0.03. Whether each clears its chair seat was not looked at in game.
- **Lights.** No row carries a light. Of the 64 torches, the 29 chandeliers and wall candles name the nearest DAT
  `Light` (0-41 units off, 29 distinct) in `light`; the 35 street lamps have no DAT Light within 400 units (`light:
  null`, `light_note`): MM9 lights the streets otherwise. The map project's `work/lights.json` did not exist yet.
- **Shared names with Thjorgard City.** The Thjorgard City props project plans the same names for the same ABC and
  skin (`coatrack2`, `herbrack1`, `plateset2`, `shield3flat`, `shield4flat`, `steinfancy01`, `suitofarmor01plain`);
  this project installed them first (2026-10-31 18:24), so Thjorgard can reuse them.
- Not looked at in game: the street lamps' flames and panes, the council on their chairs, the cut-out plants.
