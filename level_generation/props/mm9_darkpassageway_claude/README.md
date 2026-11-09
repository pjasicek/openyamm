# MM9 Dark Passageway props as 3D decorations (2026-10-31)

The claw torches, chests, crystals, rune stone, canyon bushes and trees, the bridge puzzle's ice statuettes, the
canyon's stone banshees and the spike pit of MM9's Dark Passageway (`DARKPASSAGEWAY.dat`), converted from their
LithTech ABC models into OpenYAMM 3D decorations for the native BLV ([map project](../../projects/mm9r_darkpassageway/)).
No paid services, no Meshy, no Codex: every model is MM9's own mesh with its skin x4 (plain Lanczos, the isle's
`textures.upscale`).

**Route (decided, not the brief's).** The brief named the Training Hall's scripts (the Anskram Keep build: one skin per
model). This map needs two things that build does not do: the trees carry two skins each (bark, cut-out branch cards)
and the monster statues are skinned ABCs posed in an animation. So the scripts are Yanmir's Fort's
([`../mm9_yanmirsfort_claude/`](../mm9_yanmirsfort_claude/README.md)), which is the same family (Lindisfarne
Monastery's build: one material per MM9 skin, `POSES`, cut-outs, the isle's `blib` and `finish` checks, plus the
Anskram flame cards and Yanmir's glowing claw orb). Same steps and outputs as the Training Hall's, with
`tables.py --apply` run under the decorations lock as the brief asks (it no longer takes the lock itself).

## Outputs

- **17 models** built and installed with `tools/install_model.py --world mm9`
  (`assets_source/worlds/mm9/models/mm9_deco_*.glb`), all through `check_winding.py` (0 inverted closed parts, in
  `finish.py`):

| Prop | ABC / skin | Triangles (LODs) | Notes |
| --- | --- | --- | --- |
| `clawtorch` | CLAWTORCH / ClawTorch | 309 / 135 / 76 | upright wall claw (Yanmir's `clawtorchr180` is rolled pi); blue glowing orb, no flame: not placed here any more, kept for Dungeon of Secrets' 34 `Prop` claw torches |
| `clawtorchlit` | CLAWTORCH / ClawTorch | 325 / 151 / 92 | the same claw for the four CandleProps, with four small blue flames rising from the orb between the talons (2026-10-31, below) |
| `crystal` | CRYSTAL / Crystal | 38 | opaque (the skin's soft alpha ignored) |
| `runestone` | RUNESTONE / RuneStone | 221 | |
| `bush03` | BUSH03 / Bush03 | 48 | cut-out leaf cards, double-sided |
| `bush05` | BUSH05 / Bush05 | 48 | cut-out leaf cards, double-sided |
| `tree01b` | TREE01B / TreeBark1 + TreeBranch1 | 99 | two materials, branches cut-out |
| `tree02` | TREE02 / TreeBark2 + TreeBranch3 | 128 | (the Ruined Temple's/Lindisfarne's `tree04` is TREE04, another model) |
| `tree05` | TREE05 / TreeBark3 + TreeBranch4 | 135 | (the isle's `ref_tree05` is a reference, never installed) |
| `tree06` | TREE06 / TreeBark3 + TreeBranch5 | 169 | (the isle's `ref_tree06` likewise) |
| `iceskeleton` | SKELETON / spells/Icebolt | 563 / 266 / 139 | posed `stand`, its dagger iced too |
| `icezombie` | ZOMBIE / Icebolt | 756 / 376 / 186 | posed `stand` |
| `icelich` | LICH / Icebolt | 1026 / 488 / 242 | posed `stand` |
| `icebanshee` | BANSHEE / Icebolt | 713 / 298 / 131 | posed `standAir` |
| `iceterror` | TERROR / Icebolt | 892 / 446 / 221 | posed `stand` |
| `iceskeletonwarrior` | SKELETONWARRIOR / Icebolt | 1279 / 620 / 318 | posed `stand`, its scimitar iced too |
| `stonebanshee` | BANSHEE / spells/Debris | 713 / 298 / 131 | posed `standAir`; the canyon's four stone banshees at Scale 2 |

- **Reused** (same ABC and skin; GLBs and rows stay with their owners): Chasm of the Dead's `chest5` (row `mm9_chest5`,
  the 7 treasure chests); the isle's `logsburning` (its flame cards; a new unlit row, below); Anskram Keep's `scroll`
  (`mm9_scroll`, Prop38) and `spikepit` (`mm9_spikepit_x100`, the PropDamager `Spikes1`, added at the map agent's
  request).
- **The exit's barrel** (Prop36 at ExitPoint, the portal behind the Wyrde): MM9 skins it with a water sprite frame
  (`SpriteTextures\Water\water125\water125_0000.dtx`, one frame: static), so it reads as a portal. Built here as
  `barrelwater` (Barrel.ABC with that skin x4, 192 triangles, double-sided), row **2815** `mm9_barrelwater` (hint
  "portal", no collision: Prop36 is not Solid), 2026-11-09. Before, it reused Anskram's barrel with its wooden skin, and
  players did not see the portal.
- Rows **2383-2403** (21 rows) and **2453** (`mm9_clawtorchlit`, 2026-10-31) in
  `assets_dev/worlds/mm9/data_tables/decoration_data.txt`, sprites **26184-26204**, bindings in
  `worlds/mm9/models/indoor_decorations.yml`, appended in one run under `mm9r_common/locks/mm9_decorations.lock`. No
  row carries a light. Decoration per prop and DAT scale (the names props.json uses):

| Prop | Scale | Decoration (row) | Height | Collision r/h | Placements |
| --- | --- | --- | --- | --- | --- |
| bush03 | 1.5 | `mm9_bush03` (2383) | 113.4 | none | 22 |
| bush03 | 3.0 | `mm9_bush03_x300` (2384) | 226.7 | none | 16 |
| bush05 | 3.0 | `mm9_bush05` (2385) | 245.3 | none | 13 |
| clawtorchlit | 1.0 | `mm9_clawtorchlit` (2453) | 77.7 | none | 4 (CandleProp0-3) |
| clawtorch | 1.0 | `mm9_clawtorch` (2386) | 77.7 | none | none here (Dungeon of Secrets' row) |
| crystal | 1.0 | `mm9_crystal` (2387) | 66.0 | 22/66 | 7 (incl. `Gemstone`) |
| icebanshee | 0.4 | `mm9_icebanshee` (2388) | 73.3 | 20/73 | SwitchCreature3 |
| icelich | 0.4 | `mm9_icelich` (2389) | 74.0 | 13/74 | SwitchCreature2 |
| iceskeleton | 0.4 | `mm9_iceskeleton` (2390) | 69.5 | 15/70 | SwitchCreature0 |
| iceskeletonwarrior | 0.4 | `mm9_iceskeletonwarrior` (2391) | 77.4 | 17/78 | SwitchCreature4 |
| iceterror | 0.4 | `mm9_iceterror` (2392) | 102.2 | 45/102 | SwitchCreature5 |
| icezombie | 0.4 | `mm9_icezombie` (2393) | 69.1 | 12/69 | SwitchCreature1 |
| logsburning | 1.0 | `mm9_logsburning_x100` (2394) | 106.6 | none | Prop37 |
| runestone | 1.0 | `mm9_runestone` (2395) | 190.4 | 71/190 | StoneOfFate |
| stonebanshee | 2.0 | `mm9_stonebanshee` (2396) | 366.7 | 100/367 | BansheeProp0-3 |
| tree01b | 0.9 / 0.7 | `mm9_tree01b` (2397) / `mm9_tree01b_x70` (2398) | 1400 / 1089 | 54/225, 42/175 | 1 / 1 |
| tree02 | 0.75 / 0.7 / 0.3 | `mm9_tree02` (2399) / `_x70` (2400) / `_x30` (2401) | 1281 / 1196 / 512 | 38/188, 35/175, 15/75 | 1 / 6 / 1 |
| tree05 | 0.7 | `mm9_tree05` (2402) | 891.8 | 22/175 | 8 |
| tree06 | 0.7 | `mm9_tree06` (2403) | 693.1 | 21/175 | 7 |
| chest5 | 1.0 | `mm9_chest5` (2145, reused) | 63.0 | 26/63 | 7 |
| barrel | 1.5 | `mm9_barrel` (2018, reused) | 122.9 | 53/123 | 1 |
| scroll | 1.0 | `mm9_scroll` (2034, reused) | 46.6 | none | Prop38 |
| spikepit | 1.0 | `mm9_spikepit_x100` (2320, reused) | 175.1 | none | Spikes1 |

  As in Yanmir's Fort, the scale nearest 1 takes the plain name (so `mm9_bush03` is Scale 1.5, `mm9_tree05` 0.7).
- `../../projects/mm9r_darkpassageway/props.json`: **109 placements** (97 `prop`, 7 `chest`, 4 `torch`, 1 `quest`),
  each under its DAT object name (`source_name`; no name repeats) with `script` and `script_params`. **99** are
  checked against the old map's baked BModel: **median of medians 0.54 units**, worst 0.87 (CandleProp1). Per model:
  chests 0.40, barrel 0.48, logs 0.48, scroll 0.50, bush03 0.54, spike pit 0.54, tree06 0.53, tree02 0.43 (worst
  0.80), tree01b 0.60-0.68, runestone 0.63, bush05 0.64, tree05 0.65, claw torches 0.65-0.87, crystals 0.75. The 10
  posed statues are checked against MM9's own pose instead (`fit_pose_units` 0.00-0.03 since the bone ball went,
  2026-10-31; 0.00-0.50 before) and their bases sit within one unit of the old bakes' bases.
- `review/props_sheet.png`: contact sheet of the 16 built models (LOD0 front, three-quarter, side, behind-above, below,
  LODs; looked at). `review/pose_study/sheet.png`: each statue in its first animation (left two) and in `stand`
  (right two).

## Scripted entities (entity name = `source_name` in props.json)

| Entity | Decoration | Script | Notes |
| --- | --- | --- | --- |
| `SwitchCreature0`-`3` | `mm9_iceskeleton`, `mm9_icezombie`, `mm9_icelich`, `mm9_icebanshee` | DarkP_RaisingSwitch.scr `PuzzleManager0 HitA Skeleton` .. `HitD banshee` | the bridge puzzle's switches |
| `SwitchCreature5` | `mm9_iceterror` | DarkP_BridgeReset.scr `PuzzleManager0` | bridge reset |
| `SwitchCreature4` | `mm9_iceskeletonwarrior` | DarkP_CanyonSwitch.scr | canyon switch |
| `Gemstone` | `mm9_crystal` | PassageGemstone.scr `CageTerror 0 5` | |
| `Prop38` | `mm9_scroll` | Givetake.scr `483 false 1` | `kind: quest` (the party takes item 483: a click and a cog) |

## Notes for the map

- **Statues (how they came out).** The ABCs' first animation (`static_model`, `static_model1`, `bansetup`: what the
  converter's full export and Blender's import evaluate, and what the old map baked) is a **T-pose for the skeleton
  and the zombie** and a flat spread cape for the banshee; the lich, terror and skeleton warrior were usable. So all
  seven use the idle `stand` (`standAir` for the banshee) at its first key (`props_table.POSES`), LODs included: they
  stand naturally, weapons in hand, the banshee hanging in her cape. Not the literal "first animation frame" of the
  brief; the reason is in `review/pose_study/sheet.png`. They stand with their base on the floor under their DAT
  position (MoveToFloor 1), at the old bakes' base height (within 1 unit).
- **Ice and stone skins**: Icebolt.dtx (and Crystal.dtx) carry a soft translucency mask MM9 blends (alpha 0.38-0.83,
  mean 0.59). The six ice statuettes are **blended** in it (`finish.py` `BLEND`, 2026-10-31), as MM9 draws them. The
  engine draws a blended model without depth writes and each body's triangles in index order, so far limbs and the
  lich's cloak lining show through the front; in game (`review/propfix_game/blend/`, against `opaque/`, and
  `ice_compare_close.png`, `ice_compare_zoom.png`) this reads as cut ice, not as a sorting fault, and nothing pops as
  the camera moves (the order is fixed). The opaque bodies had black occlusion patches instead. A cut-out was not
  tried: at a 0.5 cutoff Icebolt's alpha would punch holes through every body. The terror in its dark room is faint
  (a translucent ice ghost; the room is dark either way). The crystals (pink) and the stone banshees (Debris.dtx, a
  sandy stone, 64 px x4 to 256) stay opaque.
- **Claw torches: blue flames between the talons (2026-10-31).** These four CandleProps are unrolled (DAT rotation
  pitch 0, roll 0; Yanmir's Fort's are rolled pi, so its `clawtorchr180` does not apply): upright, the claw's palm
  rests on the orb's top and three talons (front, left, right) wrap it, the arm behind, so one flame rising from the
  orb's top would burn through the wrist. `clawtorchlit` instead has four small blue flames (the shared blue Flame02
  flipbook, `card` mode) rising from the orb's surface in the gaps between the talons: two 0.22 m high in the front
  gaps (40 degrees up the orb), two 0.15 m in the back gaps (20 degrees), each on its own `Fire_<k>` material so the
  engine turns each about its own seat; the seats are where no claw stands over the flame
  (`work/propfix/claw_gaps.py`). Looked at in game from eight sides at orb height
  (`review/propfix_game/opaque/0*-torch_a*.png`; a045 is inside the pillar): from the front the flames rise either
  side of the front talon, from the side they stand in front of the palm, none through the wrist. Close-ups:
  `review/clawtorch/propfix_flames/sheet.png`. MM9's `Prop` claw torches have no fire, so the flameless `clawtorch`
  stays (Dungeon of Secrets reuses it); `props_table.py` gives a CandleProp claw torch `clawtorchlit` (`LIT`,
  `SOURCES`) and keeps building `clawtorch` (`KEPT`). The orb glows blue (`<prop>_orb`: emission 0.12/0.28/0.62,
  `openyamm_flicker`). Each is `Blue 1` in MM9 and has its own blue Light (136/136/255, radius 270 LT) 81-96 units
  away, named in its props.json entry (`light`; map project's `work/lights.json`): keep them as BLV lights.
- **Burning logs** (Prop37): the isle's `logsburning` with its flame cards on a new **unlit** row
  `mm9_logsburning_x100` (`tables.py` `OWN_ROW`): the isle's `mm9_logsburning` is an outdoor row with an orange light
  and another height. The nearest MM9 light (Light56, 305 units, 255/196/196) is a room light, not the fire's; if the
  fire should light its surroundings, the map adds a point light there.
- **Trees** are not Solid in MM9; each row gets a trunk blocker (`COLLISION` in `tables.py`, two thirds of the trunk
  foot, 250 units up at scale 1), Lindisfarne's rule. Remove it for MM9's walk-through behaviour. Bushes: none.
- `Spikes1` (PropDamager): only the decoration; its damage is the map project's.

## The desert mirrors (2026-11-09)

MM9 turns each of the desert's four mirrors 10 degrees a click (PassageMirror.scr `:Rotate`: `Rotate 0,1,0, 10, 180`,
clockwise at 180 degrees a second). As BLV movers they could not turn, so the map converter now skips their brushes
(`Mirror0-3: skip` in the map's overrides.yml) and places this model four times, which the map script turns with
`evt.AimDecoration`.

- `scripts/mirror_source.py` reads the four WorldObject brushes from the DAT (the converter's reader and ring, MM9's
  surface mapping) and checks they are one shape (0.00 units apart about their box centres). It writes
  `work/mirror/mirror.json` (Mirror0's 36 triangles in LT about its box centre) and the placements in
  `../../projects/mm9r_darkpassageway/mirrors.json` (worst DAT point off the placed model: 0.00). The DAT keeps a
  WorldObject's brush in world space: the Rotation (90 for Mirror0/2, 270 for Mirror1/3) does not turn the geometry, so
  every placement has facing 0.
- `scripts/build_mirror.py` (Blender) builds it: each face wound to its DAT front (Newell of MM9's ring), flat shaded,
  white COLOR_0, base centre at the origin. Two materials: `mirror` (the rusty frame, the map's x4 master of
  refinerysolidrusta.dtx, `refixbtk8r`) and `mirror_glass` (Icebolt.dtx, the map's `icebh2sdfc` master, opaque: the
  glass surface's flags 0x1081 have no transparency bit). `textures/mirror_basecolor.png` and
  `mirror_glass_basecolor.png` are those masters as RGB.
- `finish.py mirror --install`: 36 triangles, no LODs (a 36-triangle frame), 0 inverted closed parts;
  `assets_source/worlds/mm9/models/mm9_deco_mirror.glb`.
- Row **2814** `mm9_mirror` (sprite 26615, binding height 163.8), from `tables.py`'s `EXTRA`: collision radius 41 (half the
  82-unit width: the circle it sweeps as it turns, not the half-depth rule of the other Solid props) and height 164.
- The pivot is the box centre; MM9 turns about the object's Pos, 1 LT (2.6 units) away.

## Route (`scripts/`)

```sh
cd level_generation/props/mm9_darkpassageway_claude
python3 scripts/props_table.py && python3 scripts/convert_all.py && python3 scripts/textures.py
blender --background --factory-startup --python scripts/build.py
python3 scripts/finish.py --install
cd ../../.. && flock -x level_generation/projects/mm9r_common/locks/mm9_decorations.lock \
    python3 level_generation/props/mm9_darkpassageway_claude/scripts/tables.py --apply && cd -
python3 scripts/placements.py --verbose           # needs the map's work/lights.json
python3 ../../projects/mm9r_common/review_root.py
blender --background --factory-startup --python scripts/review.py && bash scripts/contact_sheet.sh
blender --background --factory-startup --python work/pose_study.py     # review/pose_study/ (statue poses)
```

`textures/flame02_basecolor.png` is a copy of Chasm of the Dead's blue flipbook (the lit claw torch's flames). `build.py` also removes the actions each raw import leaves behind: with them,
Blender 5's slotted actions left the posed import (and every LOD) in the first animation.

## Not done

- Not looked at in game: the cut-out leaves at distance (the torches and ice statues were, 2026-10-31).

## Fixes (2026-10-31)

- **Bone-display ball removed.** Blender 5's glTF importer adds an `Icosphere` bone-display mesh (42 vertices, 80
  triangles, 2.4 cm) to every skinned (`full`) import, and the build kept it in all seven posed statues (inside the
  body, or under the feet). `build.py` now sets the isle's `blib.SKIP_BONE_SHAPES` and passes `disable_bone_shape` to
  its own per-face skin import; rebuilt and reinstalled (triangles above; each LOD0 lost exactly 80, the geometry
  otherwise identical, `work/propfix/cmpglb.py`). The ball sat under the feet of the ice skeleton, skeleton warrior
  and zombie, so these now stand 1.0-1.5 cm (0.8-1.25 units at scale 1) lower in their frame, feet on the floor: their
  bindings were set to the new heights (69.5, 77.4, 69.1; `work/propfix/fix_heights.py`, under the lock). The
  decoration rows keep their integer heights (70, 78, 69; the warrior's 78 would round to 77). The posed placements
  put the lowest point on the floor, so props.json kept their positions; their pose fits went from 0.31-0.50 to 0.00.
- **Claw torch flames** and **blended ice**: above. The map's props.json now places `mm9_clawtorchlit` at
  CandleProp0-3 (`placements.py`); the map was rebuilt with `convert.py` (the BLV changed only in those four ids) and
  re-baked through `bake_slot.sh`.
- Backups of the replaced GLBs, metas, scripts, README, props.json and the map outputs:
  `work/backup_propfix_20261031/`.
