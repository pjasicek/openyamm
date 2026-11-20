# MM9 Lindisfarne Monastery props as 3D decorations (2026-10-30)

The props, bells, wall torches, the candle and the quest maul Thjorad of MM9's Lindisfarne Monastery, converted from
their LithTech ABC models into OpenYAMM 3D decorations for the native BLV
([map project](../../projects/mm9r_lindisfarnemonastery/)). The route is Dook's Castle's props project (itself Drangheim
Prison's and the Lich Lab's): one material per MM9 skin, cut-out skins, `specs.json` turns, the isle's `blib` build and
`finish` checks; `tables.py` takes the decorations lock itself. No paid services, no Meshy, no Codex: every model is
MM9's own mesh with its skin x4 (plain Lanczos, the user's rule since 2026-10-30).

## Outputs

- **11 models** built and installed with `tools/install_model.py --world mm9`
  (`assets_source/worlds/mm9/models/mm9_deco_*.glb`), all through `check_winding.py` (0 inverted closed parts each, in
  `finish.py` and rerun on the installed sources):
  `bell` (258/127/62 tris, posed, below), `pew2`, `benchlarge1ns` (MM9's quarter turn, `specs.json`), `bookcase01ew2`
  (BOOKCASE01EW with the `bookcase02` skin: the Temple of Honk's `bookcase01ew` has `bookcase01`), `chairdesk03b`,
  `desk03b` (the `b` skins of the Lich Lab's `chairdesk03` / Temple's `desk03`), `washtubtable`, `podium02`,
  `reliquary`, `tree04` (two skins: bark and cut-out branch cards), `thjorad` (the quest maul).
- **8 reused** (same ABC and skin; their GLBs and rows stay with their owners): the Temple of Honk's `benchstone02`
  (29) and `bookflat` (Book0: the isle's `book` is baked tilted for its lectern, Book0 lies flat), the Lich Lab's
  `chair03`, Anskram Keep's `tableround`, `scroll` (the four BookLetter scrolls) and `walltorch` (22: flame cards in
  `card` mode on the torch head, the pipeline as fixed on 2026-10-30), the Chasm's `pillarstand`, Tasar Academy's
  `candle` (flame cards on the wick).
- Rows **2323-2337** (15 rows) in `assets_dev/worlds/mm9/data_tables/decoration_data.txt`, sprites 26124-26138,
  bindings in `worlds/mm9/models/indoor_decorations.yml`, appended under `mm9r_common/locks/mm9_decorations.lock`:
  `mm9_bell` (scale 1.0), `mm9_bell_x90`, `mm9_bell_x85`, `mm9_bell_x75`, `mm9_bell_x70`, `mm9_benchlarge1ns`,
  `mm9_bookcase01ew2`, `mm9_chairdesk03b`, `mm9_desk03b`, `mm9_pew2`, `mm9_podium02`, `mm9_reliquary`, `mm9_thjorad`,
  `mm9_tree04` (scale 0.75), `mm9_washtubtable`. Reused rows: `mm9_benchstone02`, `mm9_bookflat`, `mm9_candle`,
  `mm9_chair03`, `mm9_pillarstand`, `mm9_scroll`, `mm9_tableround`, `mm9_walltorch` (all at their owners' scale 1).
  No row carries a light.
- `../../projects/mm9r_lindisfarnemonastery/props.json`: **125 placements** (101 props, 22 wall torches and 1 candle as
  `kind: torch`, Thjorad as `kind: quest`), each under its DAT object name with its `script` and `script_params`.
  124 are checked against the old map's baked BModel: **median of medians 0.52 units**; without the five bells
  (below) the worst is Thjorad 1.49, then Book0 0.73; per model 0.39-0.59 for everything else.
- `review/props_sheet.png`: contact sheet of the 11 built models (looked at: the bell hangs straight under its beam,
  the tree's branch cards cut out, the large bench's back runs along its long side); `review/<prop>/` the renders;
  `review/placements_plan.png`: top view of every placement over the old bakes (`work/plan_view.py`; looked at: the
  courtyard's four benches make a square round the trees, the NS benches run along the hall walls).

## Scripted entities (entity name = DAT name in props.json)

| Entity | Decoration | Script | Notes |
| --- | --- | --- | --- |
| `Bell1` .. `Bell5` | `mm9_bell`, `_x90`, `_x85`, `_x75`, `_x70` | LindisfarneBell.scr `256 4096 n` | each its own entity; static (no ring swing: decorations do not animate) |
| `Book0` | `mm9_bookflat` | book.scr | on Table1 in the library |
| `Prop5`, `Prop6`, `Prop7`, `Prop8` | `mm9_scroll` | BookLetter.scr `470`/`471`/`472 Letter 1`, `473 Letter` | Prop8 is NonSolidUse, no MoveToFloor |
| `thjorad` | `mm9_thjorad` | Thjorad.scr | `kind: quest`, no collision: needs a click event and a cog to hide it |

## Notes for the map

- **Bells**: built in MM9's `static_model` pose (`props_table.POSES`, full export posed in Blender): the ABC's bind
  pose, which the old import baked, swings the bell and clapper about 19 degrees off the vertical. The bells' fit to the
  old bake (25.5-36.9) measures that error; their fit to the `static_model` pose points is 0.00-0.02 (`fit_pose_units`).
  They hang at their DAT positions (GoThruWorld, no MoveToFloor), no collision. LindisfarneBell.scr plays `Ring` then
  `Stop` on use and a bell sound (`churchbellring[2-4].wav` by its third parameter); only the sound can be carried.
- **Stone benches with PropAnim.scr "NS"** (27 of 29): the script loops the ABC's `NS` animation, whose root stands the
  bench a quarter round from `Static_Model`. `placements.py` checks them as baked (0.43) and then turns them about their
  DAT origin: `yaw_degrees` already includes the turn (`pose_turn_degrees: -90`). Bench26/27 (no script) keep the
  baked facing; with the turn the courtyard's four benches form a square round the trees.
- **`benchlarge1ns`** carries MM9's `ns` quarter turn in the model (`specs.json` `turn: 90`; 0.40 against 204.9
  unturned and 12.4 with 270).
- **Reliquary (Prop4)** stands on its pillar stand (Prop3): MM9 drops it (MoveToFloor, Gravity, Solid) onto the stand;
  the old import dropped it through to the floor, inside the stand. `placements.py` (`ON_TOP`) puts its base on the
  stand's top (z 191.0); its fit field is `null` (`fit_as_baked_units` 0.54 for the model at the floor).
- **Thjorad** stands upright on its head-end (MM9's `Static_Model`; its `down` animation is unused), no collision.
  Thjorad.scr acts only after `MONK_HOSTILITY`'s link breaks (the monks turned hostile): with key 2 and without key 31
  it gives key 31, item 197, 1000 experience and `sounds\events\quest.wav`; otherwise, without key 162, key 162,
  item 197 and 1000 experience; either way it removes the object. Its init removes it again once taken.
- **Courtyard trees** (`tree04`, Scale 0.75, 1281 units tall): MM9 leaves them walk-through; the row gives a trunk
  blocker (radius 30, height 202) instead of the canopy's footprint. Remove it (`COLLISION` in `tables.py`) if the
  map wants MM9's behaviour.
- **Lights**: each wall torch names its MM9 `Light` 51-61 units away (22 distinct, radius 768); the candle has no MM9
  light of its own, its entry names the room's fill light `Light73` (346 units, radius 1280). The rows carry none.
- Prop2 (wash tub) has `ScriptParams "Wash 301"` without a script: nothing to wire. The chairs (`chair03`,
  `chairdesk03b`) have no collision, as MM9 (not Solid). The wash tub skin's transparent spot (two tub triangles) is
  a cut-out.

## Route (`scripts/`)

```sh
cd level_generation/props/mm9_lindisfarnemonastery_claude
python3 scripts/props_table.py && python3 scripts/convert_all.py && python3 scripts/textures.py
blender --background --factory-startup --python scripts/build.py
python3 scripts/finish.py --install
python3 scripts/tables.py --apply                 # takes mm9r_common/locks/mm9_decorations.lock itself
python3 scripts/placements.py                     # --preview writes work/props_preview.json instead
python3 ../../projects/mm9r_common/review_root.py
blender --background --factory-startup --python scripts/review.py && bash scripts/contact_sheet.sh
python3 work/plan_view.py                         # review/placements_plan.png
```

`tables.py --apply` must not run under an outer `flock` on the same lock file: it takes the lock itself, and a second
`flock` on another descriptor of the file would wait for the first forever.


## Bone-display ball removed (2026-10-31)

Blender 5's glTF importer adds an `Icosphere` bone-display mesh (42 vertices, 80 triangles, 2.4 cm) to every skinned
(`full`) import, and the isle's `blib.import_raw` took every imported mesh, so the ball stayed in the decoration (Tasar
Academy found it). Removed from `bell` 258 / 127 / 62   -> 178 triangles (LOD0 / LOD1 / LOD2). `scripts/build.py` sets
the isle's `blib.SKIP_BONE_SHAPES` and passes `disable_bone_shape` to its own per-face skin import (the face counts must
agree). Without the ball the bell has 178 triangles, under the 250-triangle LOD threshold, so it has no LODs any more.
Rebuilt, checked (`finish.py`, check_winding.py: 0 inverted closed parts) and reinstalled with `install_model.py
--engine`; the replaced GLBs and scripts are in `work/backup_propfix_20261031/`. No MM9 bake depends on decoration
models (stale_bakes.py lists none).
