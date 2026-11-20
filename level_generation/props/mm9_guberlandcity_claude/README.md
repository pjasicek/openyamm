# MM9 Guberland City props as 3D decorations (2026-10-31)

The props, chandeliers, wall candles, the well and the little sea monster in the magic shop's fish tank of MM9's
Guberland City (`GUBERLANDCITY.dat`), as OpenYAMM 3D decorations for the native BLV
([map project](../../projects/mm9r_guberlandcity/)). The route is Thronheim City's
([`../mm9_thronheimcity_claude/`](../mm9_thronheimcity_claude/README.md), itself Sturmford City's): its scripts copied
here and adapted. No paid services, no Meshy, no Codex, no Real-ESRGAN: every model is MM9's own mesh with its skin x4
by plain Lanczos (the isle's `textures.upscale`).

## Outputs

- **5 models built** and installed with `tools/install_model.py --world mm9` (`assets_source/worlds/mm9/models/mm9_deco_*.glb`,
  cooked copies in `assets_dev/engine/models/`), all through `check_winding.py` (0 inverted closed parts each: on the
  work exports, `work/check_winding_work.log`, and on the installed sources, `work/check_winding_installed.log`).
- **87 models reused** (same ABC and skin, or another project's HidePiece/tilt variant; their GLBs stay with their
  owners, `props_table.REUSED`, found with `work/registry.py`, rerun before building and before installing): Sturmford
  City (`barstool1`, `chandelier2`, `clawlampup`, `kegbeer`, `mug1`, `portalwhole`, `shelfitem03f`, `shelfitem09d`,
  `strawdummy2c/l/r`, `trainingarchery1`, `weaponracknewg2/g3`), Drangheim Prison (`anvil`, `bedwall`, `bucket01`,
  `chairdesk02`, `coalbin`, `ironingots`, `sack03`, `shelfitem06/07/08`, `stove`, `tablebench2`, `tableround2`), Anskram
  Keep (`barrel`, `bed`, `bedmedium`, `bookcase02ew/ns`, `chair02`, `crate`, `desk01ns`, `dresserns`, `scroll`,
  `tableround`, `weaponscabinet04`), Klusos House (`basketfruit`, `basketveggies`, `cabinet01`, `cabinet02ns`,
  `dresserfancy`, `pew2ns`, `pitcher01`, `stovens`, `wallcandle`), Lich Lab (`bookstack01`, `burner`, `chair03`,
  `shelfitem01/02/03/05`, `table01`, `throne`), Thronheim City (`coatrack2`, `herbrack1`, `pottedplant1/2/3`,
  `shelfitem02mp`, `shield3flat`, `shield4flat`, `suitofarmor01plain`), Tasar Academy (`bagherbs1`, `forge`,
  `scrollpickup`, `smithhammer`), Arslegard City (`clansoldierhelmet`, `dookmilitiahelmet`), Temple of Honk
  (`benchstone02`, `bookflat`), the isle (`dresser`, `well`), Lindisfarne (`podium02`, `tree04`), Frosgard City
  (`plateset2p1`, `weaponscabinet03s3`), Thjorgard City (`shelfitem03hwc`, `weaponscabinet03`), Training Hall
  (`spindummy`, `trainingmount`), Dook's Castle (`bedornate`), Ruined Temple (`chandelier3`), Drangheim City
  (`platestack2set1`).
- Rows **2637-2643** (7 rows: the 5 new models and 2 new-scale variants of reused ones, `mm9_pottedplant1_x250`,
  `mm9_pottedplant2_x250`) in `assets_dev/worlds/mm9/data_tables/decoration_data.txt`, sprites **26438-26444**, 7
  bindings in `worlds/mm9/models/indoor_decorations.yml`, appended in one run under
  `mm9r_common/locks/mm9_decorations.lock` (`work/tables_apply.log`; the table is contiguous 2001-2643). A rerun of
  `tables.py` reports 0 rows to add. No row carries a light. Every other placement uses an existing row.
- `../../projects/mm9r_guberlandcity/props.json`: **258 placements** (226 `prop`, 32 `torch`): every Prop (224),
  CandleProp (32), WellMMIX (1) and SeaMonster (1) of the DAT. This DAT has no TreasureChest, TreasureBag,
  DestructableProp, Barrel or RUDEProp, so no `chest` or `npc` kinds. **256** are checked against the old map's baked
  BModel of the same object: **median of medians 0.51 units, worst 0.80** (Mug1; next Crate0/Crate1 0.78, Sack3
  0.73); per model 0.29-0.78. The 2 not checked against a bake are posed (below), checked against MM9's own pose
  instead (`fit_pose_units` 0.03 each).
- `review/props_sheet.png`: contact sheet of the 5 built models (LOD0 front, three-quarter, side, behind-above, below;
  LODs), looked at; `review/<prop>/` the renders.

| Model | Triangles | Placements | Fit | Notes |
|---|---|---|---|---|
| `prize` | 406 / 182 / 101 | 6 | 0.48 | PRIZE.abc, the pink plush dragon prizes; cut-out wing edges, no collision |
| `suitofarmor02aged` | 666 / 333 / 166 | 4 | 0.61 | SUITOFARMOR02 with AmoredSuitAged + AmoredSuitHalberd, x1.2 (Dook's `suitofarmor02` has the gold skin) |
| `tapestry_banner7` | 48 | 1 | 0.41 | Tapestry-Old01 with Banner7, x1.5, wall-hung, double-sided, cut-out tails |
| `weaponscabinet02ns` | 32 | 1 | pose 0.03 | WeaponsCabinet02 in its `NS` pose (Cabinet7, PropAnim.scr `ns`; below) |
| `seamonster` | 690 / 293 / 172 | 1 | pose 0.03 | SEAMONSTER.abc in `standwater` (first key), skin SeaCreatureF, x0.1, non-solid, no collision; cut-out fins |

## Named entities (entity name = `source_name` in props.json)

| Entity | Decoration | Script (params) | Notes |
|---|---|---|---|
| `Prop1` | `mm9_scroll` | BookLetter.scr (569 Letter) | |
| `Sign4` | `mm9_scroll` | scripts\BookLetter.scr (578 Letter) | |
| `Prop5`, `Prop6`, `Prop7` | `mm9_scroll` | BookLetter.scr (459 Letter 1, 460 Letter 1, 461 Letter) | |
| `Book1` | `mm9_bookflat` | scripts\book.scr | |
| `Cabinet7` | `mm9_weaponscabinet02ns` | scripts\PropAnim.scr (ns) | the quarter-turned weapons cabinet |
| `TownPortal0` | `mm9_portalwhole` | TownPortal.scr (Guberland) | Sturmford's town portal |
| `Well0` | `mm9_well_x100` | - | the isle's well, `kind: prop`; the map can give it its click event by this name |
| `SeaMonster0` | `mm9_seamonster` | - | `kind: prop`, posed, in the fish tank |

No DAT name repeats. `Tree10`, `Tree11`, `Tree12` and `Bucket` are decoration names: they are `Tree10_695`,
`Tree11_696`, `Tree12_697` and `Bucket_897` (`dat_name` keeps the DAT's).

## Route (`scripts/`)

```sh
cd level_generation/props/mm9_guberlandcity_claude
python3 work/registry.py                            # the reuse check (work/registry.json)
python3 scripts/props_table.py && python3 scripts/convert_all.py && python3 scripts/textures.py
blender --background --factory-startup --python scripts/build.py
python3 scripts/finish.py --install
blender --background --factory-startup --python scripts/review.py && bash scripts/contact_sheet.sh
cd ../../.. && flock -x level_generation/projects/mm9r_common/locks/mm9_decorations.lock \
    python3 level_generation/props/mm9_guberlandcity_claude/scripts/tables.py --apply && cd -
python3 scripts/placements.py --verbose            # --preview writes work/props_preview.json instead
python3 ../../projects/mm9r_common/review_root.py
```

`tables.py` does not take the lock itself. `props_table.HIDE_OF` picks an object's HidePiece variant by its hidden set
(Thjorgard's rule), `ALIASES` maps the DAT pairs written otherwise than their model's key.

## Notes

- **Cabinet7's quarter turn.** WeaponsCabinet02.abc has an `NS` animation whose Scene Root is turned a quarter from
  `Static_Model`; PropAnim.scr `ns` plays it. The old bake is the unturned bind pose (238 x 80 units), which runs
  through the wall behind it (x 5202-5243); turned it is 80 x 238 with its back panel against that wall's face (x 5243)
  and its open shelves to the room. Built posed (`POSES`, full export, as Thjorgard's `bedmediumew`), base on the floor
  (0.0; old bake base -1), fit to MM9's NS pose 0.03.
- **The sea monster.** SeaMonster0 has no Skin property; Sea Monster A's skin (MONSTERS.txt row 177, SeaCreatureF.dtx,
  as the `mm9_seamon_claude` creature's `sea_a`) is used. It is a static decoration at its idle `standwater`'s first key,
  scale 0.1 (32 units tall, 74 long), at its DAT position (base 130.2) inside the tank's glass (WorldObject2, z 92-195,
  y -1756 to -1644): it does not wander along `seapath` as MM9's does. No collision (`NO_COLLISION`).
- **Scroll skin.** Scroll0-3 (`models\PickUpItems\Scroll.abc`) name `skins\PickUpItems\scroll.dtx`, which MM9 does not
  ship: Tasar Academy's `scrollpickup` (scrolldouble skin) at its existing x1.5 row stands in, as Arslegard City's.
- **HidePiece**: Shelfitems9/14 (ShelfItem02 without Amulets1, SkelBones1, Skull1) are Thronheim's `shelfitem02mp`;
  Shelfitems11/15/24/30 (ShelfItem03 without Crystals1, Wands1, Hourglass1) Sturmford's `shelfitem03f`; Shelfitems10
  (without Wands1, Crystals1) Thjorgard's `shelfitem03hwc`; Shelfitems17/18 (ShelfItem09 without Daggers) Sturmford's
  `shelfitem09d`; Weaponrack0/1 (without Group2 / Group3) Sturmford's `weaponracknewg2/g3`. ShelfItem05's hidden
  Wands1, Crystals1 are not pieces of ShelfItem05.abc: plain `shelfitem05`.
- **Shields**: Shield2/Shield3 (Shield.ABC, pitch pi/2) lie flat: Thronheim's `shield3flat` / `shield4flat` (0.39).
- **Lights**: no row carries a light. Each of the 32 torches (13 `chandelier3`, 1 `chandelier2`, 18 `wallcandle`,
  reused with their owners' flame cards) names its nearest light in `light`, from the map project's `work/lights.json`
  (0-42 units off, 32 distinct).
- **Not placed**: the townsfolk, shopkeepers, guards and Markel (creature classes, the map's). The two `Clover`
  objects were left out at first ("not a decoration class", Sturmford's decision);
  the two `Clover` objects are placed since 2026-11-12 (Drangheim City's `mm9_clover`, the existing row; appended to `props.json` from `placements.py --preview`, the other entries left as installed): the map's clover events had nothing to click.
- Not looked at in game: the sea monster in its tank, the banner's cut-out tails, the plush dragons' cut-out wings.
