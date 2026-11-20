# MM9 Hall of the Gods props as 3D decorations (2026-10-31)

The stone benches, lion statues, throne, letter, dragon braziers, wall torches and the six god statues of MM9's Hall of
the Gods (`HALLOFTHEGODS.dat`), converted from their LithTech ABC models into OpenYAMM 3D decorations for the native
BLV ([map project](../../projects/mm9r_hallofthegods/)). The route is Dark Passageway's props project
([`../mm9_darkpassageway_claude/`](../mm9_darkpassageway_claude/README.md), itself Yanmir's Fort's and Lindisfarne
Monastery's: one material per MM9 skin, `POSES` for posed creature ABCs, the isle's `blib` build and `finish` checks)
with the Anskram flame cards (`card` billboard, seated on the head: the pipeline as fixed on 2026-10-30). No paid
services, no Meshy, no Codex: every model is MM9's own mesh with its skin x4 (plain Lanczos, the isle's
`textures.upscale`).

## Outputs

- **10 models** built and installed with `tools/install_model.py --world mm9`
  (`assets_source/worlds/mm9/models/mm9_deco_*.glb`), all through `check_winding.py` (0 inverted closed parts, in
  `finish.py` and rerun on the installed sources):

| Prop | ABC / skin | Triangles (LODs) | Notes |
| --- | --- | --- | --- |
| `dragonbrazier2` | DRAGONBRAZIER2 / DragonBrazier | 252 + 2 flame cards | flame cards on the bowl's rim (below) |
| `torchmetalorange` | TORCH2 / torch_metal | 178 + 2 flame cards | the Ruined Temple's `torchmetal` mesh with **orange** flames (its are blue); MM9's static_object pose (below) |
| `lionstatue` | LIONSTATUE / LionStatue | 440 / 220 / 110 | |
| `krohnstatue` | KROHN / Krohnsculpt + KROHNSwordsculpt + KrohnSpearsculpt | 1047 / 523 / 261 | posed `statue`; three materials (body, sword, spear; skin order below) |
| `skraelosstatue` | SKRAELOS / skraelossculpt | 683 / 341 / 170 | posed `statue` |
| `njamstatue` | NJAM / Njamsculpt | 738 / 400 / 184 | posed `statue` |
| `frestatue` | FRE / Fresculpt | 583 / 291 / 145 | posed `statue` |
| `wyrdoldstatue` | WYRD_OLD / wyrdoldsculpt | 622 / 310 / 154 | posed `statue` |
| `wyrdmaturestatue` | WYRD_MATURE / wyrdmaturesculpt | 632 / 316 / 158 | posed `statue` |
| `wyrdyoungstatue` | WYRD_YOUNG / wyrdyoungsculpt | 638 / 318 / 158 | posed `statue` |

- **Reused** (same ABC and skin; their GLBs and rows stay with their owners): the Temple of Honk's `benchstone02`
  (row `mm9_benchstone02_x150`, already there from Klusos House), the Lich Lab's `throne` (`mm9_throne`), Anskram
  Keep's `scroll` (`mm9_scroll`, the letter Prop3).
- Rows **2441-2451** (11 rows) in `assets_dev/worlds/mm9/data_tables/decoration_data.txt`, sprites **26242-26252**,
  bindings in `worlds/mm9/models/indoor_decorations.yml`, appended in one run under
  `mm9r_common/locks/mm9_decorations.lock` (`flock -x ... tables.py --apply`). No row carries a light. Row 2442
  `mm9_dragonpharoah_x150` (the 1000 Terrors' `dragonpharoah` at Scale 1.5) was appended for the DragonPharoah
  stand-in, which is then not placed (below); it is unused and left for the map to take if it wants the stand-in. The
  brazier's and torch's binding heights (and the brazier row's collision height) were set once more by
  `work/fix_flame_rows.py` under the same lock after their flames were rebuilt larger (below).

| Prop | Scale | Decoration (row) | Height | Collision r/h | Placements |
| --- | --- | --- | --- | --- | --- |
| dragonbrazier2 | 2.0 | `mm9_dragonbrazier2` (2441) | 372.6 | 87/373 | 18 |
| frestatue | 9.0 | `mm9_frestatue` (2443) | 1587.7 | 276/1588 | Frestat |
| krohnstatue | 7.0 | `mm9_krohnstatue` (2444) | 1944.4 | 358/1944 | Krohnstat |
| lionstatue | 2.0 | `mm9_lionstatue` (2445) | 312.6 | 129/313 | Lionstat0, Lionstat1 |
| njamstatue | 9.0 | `mm9_njamstatue` (2446) | 1616.5 | 276/1616 | Njamstat |
| skraelosstatue | 9.0 | `mm9_skraelosstatue` (2447) | 1580.7 | 276/1581 | Skraelosstat |
| torchmetalorange | 3.0 | `mm9_torchmetalorange` (2448) | 338.0 | none | WallTorch6-9 |
| wyrdmaturestatue | 9.0 | `mm9_wyrdmaturestatue` (2449) | 1590.4 | 276/1590 | Wyrd2stat |
| wyrdoldstatue | 9.0 | `mm9_wyrdoldstatue` (2450) | 1478.5 | 276/1479 | Wyrd1stat |
| wyrdyoungstatue | 9.0 | `mm9_wyrdyoungstatue` (2451) | 1591.1 | 276/1591 | Wyrd3stat |
| benchstone02 | 1.5 | `mm9_benchstone02_x150` (2263, reused) | 85.2 | 60/85 | Bench0-7 |
| throne | 1.0 | `mm9_throne` (2112, reused) | 267.9 | 72/268 | Throne |
| scroll | 1.0 | `mm9_scroll` (2034, reused) | 46.6 | none | Prop3 |

  The statues' collision is MM9's own Solid box (the `statue` animation's half-width 12 LT, Krohn's 20 LT, x 2.56 x
  Scale), not the posed footprint (spear and staff would give up to 356 units).
- `../../projects/mm9r_hallofthegods/props.json`: **41 placements** (19 `prop`, 22 `torch`: 18 braziers, 4 wall
  torches), each under its DAT object name (`source_name`; no name repeats, none is a decoration's name) with `script`
  and `script_params`. **34** are checked against the old map's baked BModel: **median of medians 0.48 units**
  (benches 0.43, braziers 0.48, lions 0.49, letter 0.52, throne 0.54). The four wall torches measure 17.42 against the
  bake, which is TORCH2's bind pose a quarter turn off what MM9 shows; against MM9's `static_object` pose they fit
  0.33-0.55 (`fit_pose_units`), so with the torches by their pose the median of medians is 0.48, worst 0.55. The seven
  posed statues are checked against MM9's own `statue` pose instead (`fit_pose_units` 0.00-0.03) and stand on the
  floor under their DAT position, their bases within 2 units of the old bakes' bases except Skraelos (-9) and Njam
  (-18): the old bake floated those two over the floor (`bake_base_delta`).
- `review/props_sheet.png`: contact sheet of the 10 built models (LOD0 front, three-quarter, side, behind-above,
  below, LODs; looked at: the statues stand naturally, arms down, Krohn with spear in hand and sword on his back; the
  flames stand on the brazier rim and the torch head). `review/placements_plan.png`: top views of every placement over
  the old bakes and a side view of the throne dais (`work/plan_view.py`). `review/game01/`, `review/game02/`: in-game
  captures on the review root (`work/run_tour.sh`, `work/run_tour02.sh`; game01 has the first, smaller flames).

## Scripted and named entities (entity name = `source_name` in props.json)

| Entity | Decoration | Script | Notes |
| --- | --- | --- | --- |
| `Prop3` | `mm9_scroll` | BookLetter.scr `480 Letter 1` | the letter on the floor of the west hall (Solid, MoveToFloor); bind the click event to `Prop3` |
| `Krohnstat` | `mm9_krohnstatue` | PropAnim.scr `statue` | behind the throne on the dais (floor 850 native) |
| `Skraelosstat`, `Wyrd2stat`, `Wyrd3stat` | `mm9_skraelosstatue`, `mm9_wyrdmaturestatue`, `mm9_wyrdyoungstatue` | PropAnim.scr `statue` | south row of the throne hall (floor 676) |
| `Njamstat`, `Wyrd1stat`, `Frestat` | `mm9_njamstatue`, `mm9_wyrdoldstatue`, `mm9_frestatue` | PropAnim.scr `statue` | north row (floor 676) |
| `Throne` | `mm9_throne` | | in front of Krohn |
| `Brazier0`-`17`, `WallTorch6`-`9` | `mm9_dragonbrazier2`, `mm9_torchmetalorange` | | `light`: the MM9 Light beside each (82-164 units), kept as a BLV light |

No decoration (`props_table.SKIPPED`): `DragonAzure0`, `DragonAzure1`, `DragonThrone`, `DragonPharoah` (below).

## Notes for the map

- **Missing models: the dragons.** MM9 does not ship `models\DragonAzure.abc`, `models\props\DragonThrone.abc`,
  `models\DragonPharoah.abc` or `skins\DragonPharoah.dtx`: they are not in `MODELS.REZ` / `SKINS.REZ` (strings of the
  archives) nor in `mm9/extracted` (`work/missing_models.txt`; the same holds for the map's `TheGreatHonk.abc` and the
  three `Wyrdeofthe*.abc` NPC models, which are the map's). MM9 itself therefore shows nothing at those four objects.
  - **DragonAzure0/1: not built.** There is no model to pose, not even a bind pose. The only MM9 dragon, `DRAGON.abc`
    (the Dragon King), is 1050 units tall and 950 long in its `stand` pose at Scale 1.5 and would cut into the statue
    rows; no stand-in was made. If the map wants dragons there, that is a new decision (a scaled-down DRAGON.abc
    stand-in, its own skin).
  - **DragonPharoah / DragonThrone: not placed.** The only DragonPharoah MM9 ships is `models\props\DragonPharoah.abc`
    with its DragonPharoahStatue skin (the 1000 Terrors' `dragonpharoah`, a dragon seated on its own throne). Placed at
    the DAT spot (in its Static_Model pose, base on the dais: x 6358.5, y 2948.9, z 850, yaw 90, decoration
    `mm9_dragonpharoah_x150`) it stands inside Krohn's statue (the DAT puts them 32 LT apart; the stand-in is 659 units
    tall while Krohn's skirt hangs 103 units over the dais) and overlaps the throne in front by 34 units
    (`review/placements_plan.png`, side view). The DAT's dragon pair looks like a leftover of an earlier layout of the
    dais; it is left out. The entry above can be added by hand if wanted.
- **God statues.** PropAnim.scr `statue` loops each model's `statue` animation (two keys, 0 and 1 ms: one pose); the
  first animation, which the old import baked, is a T-pose. Built in `statue` at its first key (`props_table.POSES`),
  LODs included. **There is no pedestal**: the DAT's y 768 LT is 504 LT over the throne hall floor (264 LT; the dais
  332 LT under Krohn), the BLV source and the old map have no face between (`work/probe_blv_floors.py`,
  `work/probe_columns.py`), and MoveToFloor drops them: the old bake's origins (570 = 264 + 34 x 9, Krohn's 710 =
  332 + 54 x 7) are exactly MM9's drop by the `statue` box. They stand on the floor, as in the old import's captures.
- **Krohn's skins.** The DAT lists `Krohnsculpt;KrohnSpearsculpt;KROHNSwordsculpt`, but ABC material 1 is the sword
  piece and 2 the spear (MM9's own Krohn monster row binds Krohn.dtx, KrohnSword.dtx, KrohnSpear.dtx). The spear
  sculpt's layout fits the sword's UVs worse (0.91 of the sword's UV samples on drawn texels against 1.00 for the sword
  sculpt; the spear 0.84 on the sword sculpt against 0.99 on its own), so each weapon takes its own sculpt skin
  (`props_table.SKIN_ORDER`: DAT skins 0, 2, 1). Not the literal DAT order; the reason is above.
- **Wall torches** face MM9's way: TORCH2's `static_object` root is a quarter turn from its bind root; the built model
  has the static_object facing (Blender's import evaluates the first animation), its back plate on the pillar
  (-1.7..-0.7 units into the wall plane, the arm 141 units out: `work/wall_probe.py`), while the old bake lay along
  the wall. This is the "torch2 known offset" of the Ruined Temple (5.7-5.9 at Scale 1), which has the same cause.
- **Flames.** Cards on the head (the top 12 % of LOD0's vertices): the brazier's rim (its FireNode is 1.6 LT under
  the rim), the torch's cup top (its fire-node socket is 4.6 LT down inside the cup, where cards would hide). The DAT's
  `FireOffset` (0, 6, 0) on the braziers is not applied (it would float the card's foot 4.4 LT over the rim). The cards
  are the Anskram torch's in model space, so they grow with the placement scale like the Ruined Temple's torchmetal at
  Scale 1; the first build divided them by the scale (world size kept, Klusos House's hanging-bowl rule), and in game
  the brazier flames hid behind the 68 LT bowls from eye level and the torch flames read as sparks (`review/game01`
  03, 04 against `review/game02` 01, 04). **Looked at from the side in game** (`review/game02/01-torch7_side.png`):
  the flame stands on the torch head, not over the bracket.
- **Lights.** Each wall torch and 16 of the 18 braziers name their MM9 Light (82-164 units; 20 distinct, all kept in
  `work/lights.json`). **Brazier1 and Brazier10 have no MM9 Light** (no DAT Light within 300 LT): `light` is null with
  a `light_note`. The rows carry none.
- **Dark middle statues.** In game the middle statue of each row (Wyrd1stat, Skraelosstat) draws much darker than
  its neighbours, which stand next to braziers; the skins are equally bright (mean 130-141) and the Blender renders
  match, so it is the map's model lighting (far from any brazier light). The map's lighting pass should look at it.
- The letter (scroll-open) stands upright on the floor, as MM9's bake has it (18 LT tall; fit 0.52).

## Route (`scripts/`)

```sh
cd level_generation/props/mm9_hallofthegods_claude
python3 scripts/props_table.py && python3 scripts/convert_all.py && python3 scripts/textures.py
blender --background --factory-startup --python scripts/build.py
python3 scripts/finish.py --install
cd ../../.. && flock -x level_generation/projects/mm9r_common/locks/mm9_decorations.lock \
    python3 level_generation/props/mm9_hallofthegods_claude/scripts/tables.py --apply && cd -
python3 scripts/placements.py --verbose           # needs the map's work/lights.json
python3 ../../projects/mm9r_common/review_root.py
blender --background --factory-startup --python scripts/review.py && bash scripts/contact_sheet.sh
python3 work/plan_view.py                         # review/placements_plan.png
bash work/run_tour02.sh                           # review/game02 (needs the map built with props.json)
```

`tables.py` does not take the lock itself (Dark Passageway's); run it under `flock` as above. A rebuild of the
brazier or torch that changes its height needs its binding height updated (`work/fix_flame_rows.py` did it once).

## Not done

- No decoration for DragonAzure0/1, DragonThrone, DragonPharoah (MM9 ships none of their models; above).
- MM9's flame particles, flicker and the braziers' `FireOffset` lift are approximated by two static flipbook cards.
- The middle statues' darkness is reported, not fixed (map lighting).
- Only the views in `review/game01` and `review/game02` were looked at in game; the LOD switches of the statues at
  distance and the collision of the statues (party against the 276-358 unit cylinders) were not tested.


## Bone-display ball removed (2026-10-31)

Blender 5's glTF importer adds an `Icosphere` bone-display mesh (42 vertices, 80 triangles, 2.4 cm) to every skinned
(`full`) import, and the isle's `blib.import_raw` took every imported mesh, so the ball stayed in the decoration (Tasar
Academy found it). Removed from `frestatue` 583 / 291 / 144  -> 503 / 251 / 125 triangles; `krohnstatue` 1047 / 522 /
259  -> 967 / 483 / 240 triangles; `njamstatue` 738 / 400 / 183  -> 658 / 320 / 164 triangles; `skraelosstatue` 683 /
341 / 169  -> 603 / 301 / 149 triangles; `wyrdmaturestatue` 632 / 316 / 157  -> 552 / 276 / 138 triangles;
`wyrdoldstatue` 622 / 310 / 153  -> 542 / 270 / 134 triangles; `wyrdyoungstatue` 638 / 318 / 157  -> 558 / 278 / 138
triangles (LOD0 / LOD1 / LOD2). `scripts/build.py` sets the isle's `blib.SKIP_BONE_SHAPES` and passes
`disable_bone_shape` to its own per-face skin import. LOD0 lost exactly the ball (inside each statue), frames unchanged;
decimated LODs were remade from the clean LOD0. `wyrdmaturestatue`'s single-sided material held only the ball and is
gone. Rebuilt, checked (`finish.py`, check_winding.py: 0 inverted closed parts) and reinstalled with `install_model.py
--engine`; the replaced GLBs and scripts are in `work/backup_propfix_20261031/`. No MM9 bake depends on decoration
models (stale_bakes.py lists none).
