# MM9 Thjorgard City props as 3D decorations (2026-10-31)

The props, candles, chandeliers, lamp posts, lanterns, wall torches, the two beakers, the clover patches and the well
of MM9's Thjorgard City (`THJORGARDCITY.dat`), converted from their LithTech ABC models into OpenYAMM 3D decorations
for the native BLV ([map project](../../projects/mm9r_thjorgardcity/)). The route is Sturmford City's
([`../mm9_sturmfordcity_claude/`](../mm9_sturmfordcity_claude/README.md)): one material per MM9 skin, `specs.json`
turns, `POSES`, HidePiece variants, the isle's `blib` build and `finish` checks, and the Anskram flame cards on the ABCs'
Flame socket markers. No paid services, no Meshy, no Codex, no Real-ESRGAN: every model is MM9's own mesh with its skin
x4 by plain Lanczos (the isle's `textures.upscale`).

## Outputs

- **20 models built** and installed with `tools/install_model.py --world mm9` (`assets_source/worlds/mm9/models/mm9_deco_*.glb`,
  cooked copies in `assets_dev/engine/models/`), all through `check_winding.py` (0 inverted closed parts each, in
  `finish.py` and rerun on the installed sources: `work/check_winding_installed.log`).
- **114 models reused** (same ABC and skin, same pose, tilt and hidden pieces; their GLBs stay with their owners,
  `props_table.REUSED`): Sturmford City (`candelabra`, `chandelier2`, `clawlampup`, `kegbeer`, `portalwhole`,
  `shelfitem03f`, `shelfitem09d`, `shelfitem09sg`, `strawdummy2c/l/r`,
  `trainingarchery1`, `winebottle04`, `winerack`), Klusos House (15), Anskram Keep, Lich Lab and Drangheim Prison (13
  each), Thronheim City and Drangheim City (below), Tasar Academy (`bagherbs1`, `dwarfaxeonside`, `forge`,
  `scrollpickup`, `smithhammer`), Temple of Honk (`bookflat`, `cabinet01ns`, `cabinet04`, `table02`), Dook's Castle
  (`bedornate`, `suitofarmor02`, the hung `shield1`, `shield2`, `shield3r`, `shield4`), The Arena (`tapestry_banner6`, `torchrust`), the isle (`coatrack`, `well`),
  Lindisfarne (`pew2`, `washtubtable`), Thjorad Mine (`oillamp`, `woodbin`), Connecting Tunnels (`sack01`, `sack02`),
  Training Hall (`spindummy`, `trainingmount`), Ruined Temple (`chandelier3`), Beethoven (`winebottle`).
- **Built the same afternoon by the sibling city projects and reused** (both had built and installed them minutes before
  this project's install; this project's own builds of the same models were dropped): Thronheim City's `coatrack2`,
  `herbrack1`, `plateset2`, `steinfancy01`, `suitofarmor01plain`, `shelfitem02mp` and
  `weaponracknsnewg1`/`g3`; Drangheim City's `barstool2`, `clover`, `jug1`, `shelfitem09`, `shelfitem09g`,
  `shelfitem03hc` and `winebottle02`/`03`/`05`. This project's Group2 rack follows Thronheim's name scheme
  (`weaponracknsnewg2`).
- Rows **2579-2609** (31 rows: the 20 new models and 11 new-scale variants of reused ones: `mm9_barrel_x50`,
  `mm9_bed_x100`, `mm9_chandelier3_x75`, `mm9_dresserfancy_x120`, `mm9_logs_x120`, `mm9_logs_x125`,
  `mm9_podium01_x80`, `mm9_sack01_x200`, `mm9_scrollpickup_x150`, `mm9_table01_x120`, `mm9_tapestry_banner6_x200`) in
  `assets_dev/worlds/mm9/data_tables/decoration_data.txt`, sprites **26380-26410**, 31 bindings in
  `worlds/mm9/models/indoor_decorations.yml`, appended in one run under `mm9r_common/locks/mm9_decorations.lock`
  (`work/tables_apply.log`). A rerun of `tables.py` reports 0 rows to add. No row carries a light.
- `../../projects/mm9r_thjorgardcity/props.json`: **730 placements** (588 `prop`, 142 `torch`): every Prop (583),
  CandleProp (136), Torch (6), DestructableProp (2), Clover (2) and WellMMIX (1) of the DAT. **722** are checked
  against the old map's baked BModel of the same object: **median of medians 0.53 units, worst 5.71** (the six
  `torchrust` wall torches, 5.6-5.71: the torch2 model's known offset, The Arena's 5.76-5.87; next Bed10 `bed` 1.08,
  Dresser6 0.97, the logs 0.89). The 8 not checked against a bake: the 4 EW beds and 3 pickaxes, checked against MM9's
  own pose instead (`fit_pose_units` 0.00 and 0.14-0.16), and BookKey (not baked by the old import; on the surface under
  its DAT position, MoveToFloor).
- `review/props_sheet.png`: contact sheet of the 20 built models (LOD0 front, three-quarter, side, behind-above,
  below; LODs), looked at; `review/<prop>/` the renders.

| Model | Triangles | Placements | Fit | Notes |
|---|---|---|---|---|
| `lamppost2` | 242 + 1 flame | 27 | 0.59 | the street lamps (Lamppost2 with Lamppost1); flame card on its `Flame` socket, cut-out panes; no collision (below) |
| `lantern2` | 238 + 1 flame | 12 | 0.50 | the hanging lanterns (Scale 2); half-size flame on the candle top (its `fire node` marker, 1.5 LT across), cut-out panes |
| `clawlampupblue` | 396 / 172 / 99 | 1 | 0.44 | Clawlamp0, a CandleProp with Blue 1: Sturmford's upright claw lamp with Yanmir's Fort's glowing blue ice orb |
| `bedmediumew` | 92 | 4 | pose 0.00 | Bed3, Bed18-20: BedMedium in its `EW` pose (PropAnim.scr `ew`), below |
| `desk02ns` | 36 | 1 | 0.37 | MM9's `ns` quarter turn baked in (`specs.json` `turn: 90`; 37.1 unturned) |
| `weaponracknsnewg2` | 936 / 468 / 234 | 1 | 0.61 | Weaponrack0: WeaponRackns without Group2, `turn: 90` as Dook's / Thronheim's |
| `weaponscabinet03` | 26 | 8 | 0.56 | WeaponsCabinet03 with WeaponsCabinet06: MM9's model is an empty case |
| `suitofarmor01gold` | 542 / 271 / 134 | 1 | 0.49 | Armor2; the gold skin's alpha is a gloss mask, so opaque (`specs.json` `alpha: false`) |
| `shelfitem03hwc`, `shelfitem07hbread/hfruit/hpie`, `shelfitem08hbasket/hbottle/honions/hsack` | 172-472 | 1 each | 0.48-0.55 | HidePiece variants (below) |
| `herbrack2` | 66 | 5 | 0.45 | Herb-Rack2 with the Herb-Rack1 skin, wall-hung (Scale 2), cut-out herbs |
| `plateset1` | 298 | 8 | 0.48 | table settings (Scale 0.75); no LODs (the native ones lose the plate) |
| `basket01`, `bookkey` | 76 | 1 each | 0.51 / - | BookKey is the Great Book's key (`GreatBookKey.scr`) |

## Named and scripted entities (entity name = `source_name` in props.json)

No DAT name of these classes repeats and none is a decoration's name: every `source_name` is the DAT's name. Each entry
keeps `script` and `script_params`:

| Entity | Decoration | Script (params) | Placement |
|---|---|---|---|
| `WellMMIX0` | `mm9_well_x100` (the isle's well) | class WellMMIX (the drinkable well), no script | on the floor at (-4246, 5120, 1.3) |
| `BookKey` | `mm9_bookkey` | GreatBookKey.scr | not baked by the old import: dropped 51 units (DAT 163.8) onto the world surface under it at 113.0, MoveToFloor |
| `TownPortal0` | `mm9_portalwhole` (Sturmford's) | TownPortal.scr (Thjorgard) | |
| `Barrel` | `mm9_barrel_x100` | orbtrigger.scr | object 1110 |
| `Book1`, `Book2` | `mm9_bookflat` | scripts\book.scr | |
| `Prop3`-`Prop7` | `mm9_scroll` | BookLetter.scr (424 Letter 1, 425 Letter 1, 427 Letter 1, 428 Letter 1, 429 Letter) | |
| `Pickaxe0`-`Pickaxe2` | `mm9_dwarfaxeonside` (Tasar Academy's) | scripts\PropAnim.scr (onside) | posed, below |
| `Bed4`, `Bed5` | `mm9_bed_x100` | scripts\PropAnim.scr (ew) | plain bed, below |
| `Bed3`, `Bed18`-`Bed20` | `mm9_bedmediumew` | scripts\PropAnim.scr (ew) | posed, below |
| `Beaker1`, `Beaker2` | `mm9_beaker01` (Lich Lab's) | class DestructableProp | `kind: prop` |
| `Clover1`, `Clover2` | `mm9_clover` (Drangheim City's) | class Clover | `kind: prop`, the old map baked them as static props |
| `Clawlamp0`, `CandleProp10` | `mm9_clawlampupblue`, `mm9_chandelier3` | CandleProp with Blue 1 | `blue: true`; both name a blue DAT Light (Light26 0/128/255 at 41 units, Light14 at 0) |

## Route (`scripts/`)

```sh
cd level_generation/props/mm9_thjorgardcity_claude
python3 scripts/props_table.py && python3 scripts/convert_all.py && python3 scripts/textures.py
blender --background --factory-startup --python scripts/build.py
python3 scripts/finish.py --install                # check assets_source/engine/models/ for the names first
blender --background --factory-startup --python scripts/review.py && bash scripts/contact_sheet.sh
cd ../../.. && flock -x level_generation/projects/mm9r_common/locks/mm9_decorations.lock \
    python3 level_generation/props/mm9_thjorgardcity_claude/scripts/tables.py --apply && cd -
python3 scripts/placements.py --verbose            # --preview writes work/props_preview.json instead
python3 ../../projects/mm9r_common/review_root.py
```

`tables.py` does not take the lock itself (run it under `flock` as above). `props_table.py` also checks that every
reused prop's owner has its raw GLB, build meta, binding origin and installed model (placements.py fits with them) and
lists every PropAnim.scr object with its decoration. `convert_all.py` strips `HIDDEN` pieces (keeping
`<prop>_full.glb`). `work/registry.py` maps every (ABC, skin) of the other MM9 props projects to its prop and owner
(`work/registry.json`): the reuse check (it misses the isle, whose table is keyed by model only: its `well` and
`coatrack`).

## Notes

- **PropAnim.scr poses.** PropAnim loops the animation named by its parameter. `Dwarfaxe.ABC` `onside` lays the pickaxe
  on its side: Tasar Academy's `dwarfaxeonside` (`PLACE_POSES`); placed on MM9's pose, base on the raised world surface
  under them at 92 (DAT 122.9; the buckets beside them stand at 11), fit to the pose 0.14-0.16. `BedMedium.ABC` `EW`
  turns its Scene Root a quarter about the vertical (the same rotation the `ns` models' static animation carries, which
  Sturmford's `pewns` and Dook's `weaponracknew` bake in as `turn: 90`): `bedmediumew` is built posed (`POSES`, full
  export) and the four beds stand on the upper floor at 532 (DAT 532.5, MoveToFloor 0), fit to the pose 0.00; the old
  bake (the unturned bind pose) sits 52 units lower. `Bed.ABC` has no `ew` animation (only `Bed`): LoopAnim finds
  nothing and MM9 keeps its default pose, so Bed4/Bed5 are the plain `bed` (fit 0.44 to their bakes).
- **HidePiece**: each object's hidden pieces are stripped from its variant (`HIDE_OF` picks the variant by the hidden
  set; built here: `shelfitem03hwc` hides Wands1, Crystals1; `shelfitem07hbread/hfruit/hpie` hide Bread1 / Fruit1 /
  Pie1; `shelfitem08hbasket/hbottle/honions/hsack` hide Basket / Bottle / Onions / Sack; `weaponracknsnewg2` hides
  Group2). ShelfItem05 has only Jar01-05, so its four shelves' Wands1/Crystals1 hide nothing (`NO_SUCH_PIECE`): Lich
  Lab's plain `shelfitem05`. The old bake keeps the hidden pieces, so HidePiece variants are centred on their bake's box
  across only, not in height (centring in height had lifted the shorter Group2 rack 11 units off the floor).
- **Shields** (2026-11-02): Shield0-3 (Shield.ABC, pitch pi/2, yaw pi/2) hang on the armoury wall, their centres 5
  units off it (half a shield's thickness): Dook's Castle's hung `shield1`/`shield2`/`shield4`/`shield3r` (pitch pi/2,
  roll pi: point down, as Dook's). They took Sturmford's `shield1flat`/`shield2flat` and Thronheim's
  `shield3flat`/`shield4flat` before, which lie flat (Sturmford had measured the pitch against the old import's flat
  bake); the play-test found them sticking out of the wall.
- **Wall notices** (2026-11-02): a MoveToFloor prop within 8 units of a wall and at least 24 over its floor stays at its
  DAT height (`placements.wall_distance`, `wall_hung_raise`): Prop7, the letter beside a door, stood on the floor.
- **Letters lie flat** (2026-11-02, `props_table.LAID_FLAT`): scroll-open stands (Anskram Keep hangs it on walls) and
  MM9 lays it down only by PropAnim's `down`; a BookLetter letter that MoveToFloor sets on a counter stood upright like
  a placard. An upright `scroll` with MoveToFloor away from a wall (`props_table.at_wall`, the wall rule above) takes 1000
  Terrors' `scrollp90`, centred on its old bake with its base on the bake's base (Thronheim's TreatyProp route):
  Prop3-6. Prop7, pinned beside the door, stays upright.
- **Placements in 16 s** (2026-11-02, was 22 minutes): the floor and wall lookups test the old map's world triangles
  filed in 256-unit plan cells (`placements.WorldTriangles`), all candidates at once, instead of every face in Python
  (1.3 s a lookup over Thjorgard's 167 795 faces). Same answers on 357 sample points; `props.json` byte-identical.
- **Flames** use the pipeline as fixed on 2026-10-30 (the isle's `finish.py` gives the `Fire` material
  `openyamm_billboard: card`): `lamppost2` carries the candle cards on its `Flame` socket marker, `lantern2` half-size
  cards on its `fire node` (the candle is 4 LT tall in a 15 LT lantern, x2 as placed). Reused lit models keep their
  owners' flames (`wallcandle`, `chandelier3`, `chandelier2`, `candelabra`, `torchrust`). `clawlampupblue` has no flame:
  its glow is the orb's emission (Yanmir's `ORB`: `emissiveFactor` 0.12/0.28/0.62, `openyamm_flicker` [0.15, 3]).
  The logs have no MM9 Fire here: all 13 are Lich Lab's unlit `logs`.
- **Lights**: no row carries a light. Each of the 103 indoor lit objects (47 `chandelier3`, 44 `wallcandle`, 6
  `torchrust`, 4 `chandelier2`, the candelabra and Clawlamp0) names its nearest DAT `Light` in `light` (0-82 units off,
  103 distinct); the six Torch-class wall torches name Light31-Light36 (40 units each). The **27 street lamps and 12
  lanterns have no DAT Light within 400 units** (the nearest 788-3836): MM9 lights the streets with its
  StaticSunLight only, so their entries have `light: null` and a `light_note`; the map may give them lights of its own.
- **Lamp post collision**: none. The decoration origin is the footprint centre, which for this arm lamp lies under the
  arm 65 units from the post, so a cylinder there would stop the party in the air and miss the post.
- **Not placed**: none of the decoration classes. Not decoration classes, left to the map: the 60 townsfolk,
  shopkeepers and Sven (`models\PeasantMale.abc` creature classes: TownDwarfMaleA, ShopkeeperElfMaleA, SvenSvenssen, ...).
- Not looked at in game: the flames from the side, the blue orb's emission, the lamp posts' and lanterns' cut-out panes.
