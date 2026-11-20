# MM9 Thousand Terrors props as 3D decorations (2026-10-31)

The props, torches, braziers, TerrorLight lamps, chests and scripted statues of MM9's Thousand Terrors
(`1000TERRORS.dat`), converted from their LithTech ABC models into OpenYAMM 3D decorations for the native BLV
([map project](../../projects/mm9r_1000terrors/)). The route is Lindisfarne Monastery's props project
([`../mm9_lindisfarnemonastery_claude/`](../mm9_lindisfarnemonastery_claude/README.md)): one material per MM9 skin,
`specs.json` turns, the isle's `blib` build and `finish` checks, `tables.py` takes the decorations lock itself; the
build adds the Anskram/Tasar flame cards (`card` billboard, the pipeline as fixed on 2026-10-30). No paid services, no
Meshy, no Codex, no Real-ESRGAN: every model is MM9's own mesh with its skin x4 (plain Lanczos).

## Outputs

- **11 models** built and installed with `tools/install_model.py --world mm9`
  (`assets_source/worlds/mm9/models/mm9_deco_*.glb`), all through `check_winding.py` (0 inverted closed parts each, in
  `finish.py` and rerun on the installed sources):

  | Model | Source ABC (skin) | Placements | Triangles | Notes |
  | --- | --- | --- | --- | --- |
  | `terrorlight1` | TERRORLIGHT1 (TerrorLight1) | 88 | 336 | hanging cage round a stone orb; the orb glows blue (below); no LODs (the native LOD2 drops the orb) |
  | `treasureopening` | TREASUREOPENING | 27 | 334 / 194 / 98 | wall-hung gargoyle head with a red jewel; its two `Glownode` sockets are not drawn |
  | `sorcererstatue` | EVILSORCERER (props/Crystal) | 8 | 978 / 522 / 295 | the crystal Sorceress statues, posed (below); opaque, as Dark Passageway's crystal |
  | `brazierbowl` | BRAZIERBOWL | 6 | 126 + 3 flame cards | `Torch` at Scale 2: half the hanging bowls' three cards on the rim |
  | `sconce1torch` | SCONCE1 (WallTorch) | 4 | 276 / 131 / 71 + 2 cards | Verhoffin's `sconce1` mesh, flame spec and seat with the walltorch skin |
  | `dragonpharoah` | DRAGONPHAROAH (DragonPharoahStatue) | 4 | 972 / 458 / 242 | 18 NaN UVs repaired (`scripts/abc_finite.py`); orientation below |
  | `skulls1000a`, `skulls1000b` | 1000SKULLS (1000Skulls1 / 2) | 1 / 2 | 410 / 200 / 102 | the giant floating skulls, Scale 2.5, GoThruWorld |
  | `switch03` | SWITCH03 | 1 | 338 / 148 / 84 | WinMan's switch |
  | `scrollp90` | SCROLL-OPEN | 1 | 80 | ChessNote0 with MM9's pitch pi/2 baked in (Verhoffin's `scrollp268` route) |
  | `waterorb` | DAT WorldObject20 (water123.spr frame 0) | 117 | 144 | the translucent blue flame orbs over the invisible candles (below) |

- **10 reused** (same ABC and skin; their GLBs and rows stay with their owners): Beethoven's `coffinraised` (43, new
  variant row at Scale 1.5) and `urngargoyle` (32, its `_x150` row), the Chasm's `treasurechute` (21: the 5 chutes
  and the 16 NS chutes, below; new `_x90` row), `treasurepile` (8), `chest5` (7), the Lich Lab's `blackchest` (7),
  the Temple of Honk's `brazier` (7, its `card` flames), Verhoffin's `sconce1` (17, its flames), the Ruined Temple's
  `genielamp` (1, new `_x150` row).
- Rows **2404-2416** (13 rows) in `assets_dev/worlds/mm9/data_tables/decoration_data.txt`, sprites 26205-26217,
  13 bindings in `worlds/mm9/models/indoor_decorations.yml`, appended under `mm9r_common/locks/mm9_decorations.lock`:
  `mm9_brazierbowl`, `mm9_coffinraised_x150`, `mm9_dragonpharoah`, `mm9_genielamp_x150`, `mm9_sconce1torch`,
  `mm9_scrollp90`, `mm9_skulls1000a`, `mm9_skulls1000b`, `mm9_sorcererstatue`, `mm9_switch03`, `mm9_terrorlight1`,
  `mm9_treasurechute_x90`, `mm9_treasureopening`; and **2435** `mm9_waterorb` (sprite 26236; added later, rows
  2417-2434 had gone to other maps). Reused rows: `mm9_blackchest`, `mm9_brazier`, `mm9_chest5`,
  `mm9_sconce1`, `mm9_treasurechute`, `mm9_treasurepile`, `mm9_urngargoyle_x150`. A rerun of `tables.py` reports 0 rows
  to add. No row carries a light.
- `../../projects/mm9r_1000terrors/props.json`: **402 placements**: the 117 water orbs (`kind: prop`, below) and
  285 DAT props: 148 `prop`, 115 `torch` (88 TerrorLights, 21
  sconces, 6 brazier bowls), 7 `brazier`, 14 `chest`, 1 `quest` (ChessNote0). Every entry keeps its DAT name
  (`source_name`, no duplicates), `script` and `script_params`. All 285 are checked against the old map's baked
  BModel of the same object: **median of medians 0.49 units, worst 0.71** (SorceressStatue1/3/7); per model
  0.37 (urns) to 0.68 (switch). The turned ones (coffins, NS chutes, dragons) are checked as baked, then turned.
- `review/props_sheet.png`: contact sheet of the 10 built models (looked at: the flames stand in the bowl and on the
  sconce, the TerrorLight orb is blue inside its cage, the statue stands in its fidget2 pose, the skulls' two skins);
  `review/<prop>/` the renders.
- `work/not_placed.json`: the 118 objects of these classes that get no decoration (below).

## Scripted entities (entity name = DAT name in props.json)

| Entity | Decoration | Script | Notes |
| --- | --- | --- | --- |
| `SorceressStatue0` .. `7` | `mm9_sorcererstatue` | 1000T_SorcStatues.scr `<shooter> CastingSmoke<n>` | static; on `Go` MM9 loops fidget2/Taunt and triggers the named Shooter and smoke; on `Stop` the smoke goes off |
| `SkeletonHead` | `mm9_skulls1000a` | 1000T_SkeletonHead.scr `SkelHeadShooter0 SkelHeadShooter1` | on `Go` MM9 turns it 180 degrees about the vertical and triggers both shooters; decorations do not rotate |
| `WinMan` | `mm9_switch03` | WinMan.scr | the win-game switch (needs a click event); its Down/Up animation is not built; refuses below LT y -3680 |
| `Genielamp` | `mm9_genielamp_x150` | GiveRandom.scr `TriggerSmokeOn 0` | needs a click event: one random gold/exp/item/health/attribute effect, then no more use; the lamp stays |
| `ChessNote0` | `mm9_scrollp90` | BootGive.scr `598` | `kind: quest`: gives item 598 and removes itself (needs a click event and a cog to hide it) |
| `Coffin0`, `1`, `6`-`11`, `15`-`18`, `31`, `32` | `mm9_coffinraised_x150` | PropAnim.scr `ns` | turned a quarter (below); nothing to wire |
| `TreasureChest0`-`12`, `KeyChest3` | `mm9_blackchest` (7), `mm9_chest5` (7) | | `kind: chest`, `source_object` is the DAT index for the loot records |

## Notes for the map

- **Invisible candles (117 `CandleProp`, `Candle.ABC` with `Misc/Invisible.dtx`, Blue 1): not placed.** Each sits
  14 LT under a `WorldObjectN` (Alpha 0.4, `DamagePerSecond` 10, 84 polygons, water texture `WATE1XKSQP` in the old
  map, about 41 units tall) and a blue `Light` (0/39/196, radius 120 LT, BrightScale 0.9) 14 LT above it. The visible
  blue flame is that translucent damaging brush, a static face of the map; the candle is MM9's flicker-light anchor
  (an additive dynamic light the BLV does not have). Listed with positions in `work/not_placed.json`.
- **Water orbs** (added on the map agent's request: as BLV faces, 117 translucent orbs of 84 faces each overflowed
  the renderer's batches). All 117 `WorldObject`s in `../../projects/mm9r_1000terrors/work/orb_models.json` share one
  shape (15.73 x 16 x 15.73 LT, Alpha 0.4, water123.spr): `scripts/waterorb_source.py` reads WorldObject20 with the map
  converter's DAT reader (v66 second ring, MM9's surface mapping), `scripts/build_waterorb.py` builds it (triangles
  wound away from the centre, base centre at the origin, white COLOR_0), `finish.py` makes the material
  alpha-blended (`alphaMode BLEND`, base colour factor alpha 0.4 x the opaque frame, single-sided) with a faint blue
  emission 0.02/0.08/0.35 and the TerrorLight flicker (`WATERORB`; MM9 lightmapped them from the blue light inside,
  which here lights only their back faces). The engine draws `BLEND` decoration materials in its blended pass and
  multiplies the texture by the base colour factor (`fs_model.sc` `u_modelMaterial[0]`), as the flame cards rely on.
  Placed under the WorldObject names (`source_object` null), yaw 0, x/y at the box centre and z at the box bottom
  (a decoration's origin is its base centre); each checked against its own DAT points: median 0.03-0.07 units. No
  collision (MM9: not Solid; their `DamagePerSecond` 10 is not carried). The texture is the sprite's ten frames at its
  15 a second (`scripts/waterorb_flipbook.py`, a 5 x 2 flipbook; `build_waterorb.py` centres the UVs in one frame;
  2026-11-09: before, frame 0 only).
- **LeverHand** (`PeasantM1.ABC`, WG_hand.scr): not placed: its Init clears `Visible`; it is shown only by the
  WinGame cutscene (`SC07_Shot1`), which is not built.
- **TerrorLight lamps**: MM9's `Flame` socket (the one-triangle `Glow-Node`) is the orb's centre, so its blue flame
  is hidden in the orb (Yanmir's Fort's claw lamp). The orb's 72 faces have their own material `terrorlight1_orb`:
  emissive 0.08/0.20/0.62 with `openyamm_flicker` [0.15, 3] (`finish.py` `ORB`); no flame cards. Their nearest MM9
  light is a blue 0/39/196 one 67+ units away (the lamps hang at Scale 1.5); CandleProp154 (799) and CandleProp155
  (1731) have no light of their own. The emission strength is a guess from the renders, not seen in game.
- **NS chutes** (`TREASURECHUTENS.abc`, 16): the same mesh, skin and bind as `TREASURECHUTE.abc`, but MM9 shows a
  model in its first animation's pose and this one's root turns it a quarter. The old import baked the bind pose
  (the chutens' bake equals the plain chute's, fit 0.53 unturned against 31-36 turned): the old map has every NS
  chute turned 90 degrees off its wall. Here they are the Chasm's `treasurechute`, checked as baked and turned +90
  about the DAT origin (`props_table.ANIM_TURN`); with the turn every chute's back plate is 1-14 units off its wall
  (`work/wall_clearance.py`), as the plain chutes are. `pose_turn_degrees` in each entry.
- **Raised coffins with PropAnim.scr `ns`** (14 of 43): the NS animation's root is the chutens' root, so the same +90
  turn (Lindisfarne's benches, same sign): checked as baked (0.66), then turned about the DAT origin. All clear of the
  walls.
- **DragonPharoah**: the reverse case. Its `Static_Model` root is a quarter off its bind pose, and Blender's glTF
  import poses the first animation, so the built model already has MM9's facing; the old map baked the bind pose. It
  is checked against the bake turned back (0.56) and placed with the -90 (`BUILT_TURN`): its back slab then faces the
  wall behind it (112 units off), as in a niche.
- **Sorceress statues**: 1000T_SorcStatues.scr plays `fidget2` once half a second after load and holds its last frame
  (the bind pose is a T-pose); the model is built in fidget2's last frame (2.366 s), fit 0.01 to those posed points and
  0.52-0.71 to the old bake. Solid in MM9: radius 30, height 200.
- **Collisions** (rows): coffins x1.5 radius 91 / height 191 (a 488-unit-long coffin: the ends stay walk-in), dragon
  statues 160 / 439, Sorceress statues 30 / 200, chutes 62 / 404 and 56 / 364 (x0.9), brazier bowls 37 / 72, urns
  71 / 160, treasure piles 209 / 297, chests 29 / 71 and 26 / 63, braziers 24 / 149. None for the sconces, TerrorLights,
  treasure openings, the switch, the skulls, the note and the lamp.
- **Lights**: no row carries a light. Each torch, brazier, brazier bowl and TerrorLight entry names its nearest MM9
  `Light` (`light`: name, distance, radius x 2.56, colour, BrightScale): the 17 sconces' are red 255/0/0 23 units away,
  the 4 walltorch sconces' orange 255/164/72 (20), the braziers' 196/185/200 (10), the brazier bowls' 235/233/188 (15).
- **Not built**: the 21 `Fire` objects (smoke emitters with flicker lights; map work), the treasure openings' glow
  sockets, every animation (PropAnim loops, the skull's turn, the switch's Down/Up, the statues' casting).
- `scripts/build.py` assigns the action's slot when it poses a model: in Blender 5 setting
  `animation_data.action` alone left the statue in its T-pose (`work/pose_probe.py`).

## Route (`scripts/`)

```sh
cd level_generation/props/mm9_1000terrors_claude
python3 scripts/props_table.py && python3 scripts/convert_all.py && python3 scripts/textures.py
blender --background --factory-startup --python scripts/build.py
python3 scripts/waterorb_source.py                # the water orbs' DAT geometry
python3 scripts/waterorb_flipbook.py              # their texture: water123.spr's ten frames, a 5 x 2 flipbook
blender --background --factory-startup --python scripts/build_waterorb.py
python3 scripts/finish.py --install && python3 scripts/finish.py waterorb --install
python3 scripts/tables.py --apply                 # takes mm9r_common/locks/mm9_decorations.lock itself
python3 scripts/placements.py --verbose           # --preview writes work/props_preview.json instead
python3 ../../projects/mm9r_common/review_root.py
blender --background --factory-startup --python scripts/review.py && bash scripts/contact_sheet.sh
python3 work/wall_clearance.py ../../projects/mm9r_1000terrors/props.json   # turned placements against the walls
```

`work/ns_turn_probe.py`, `work/wall_probe.py` and `work/root_probe.py` are the probes behind the NS and dragon
turns (`work/wall_probe.py` writes `work/world_samples.npy`, which `wall_clearance.py` reads). `tables.py --apply`
must not run under an outer `flock` on the same lock file.

## Not checked

- Nothing was looked at in game: flame cards from the side, the TerrorLight orb's emission and flicker, the water
  orbs' translucency and blue (the Blender review render shows them opaque), how dark the props are under the bake.
- The NS and dragon turns rest on MM9 showing a model's first animation pose and on the old map's wall positions,
  not on an MM9 screenshot.


## Bone-display ball removed (2026-10-31)

Blender 5's glTF importer adds an `Icosphere` bone-display mesh (42 vertices, 80 triangles, 2.4 cm) to every skinned
(`full`) import, and the isle's `blib.import_raw` took every imported mesh, so the ball stayed in the decoration (Tasar
Academy found it). Removed from `sorcererstatue` 978 / 522 / 295  -> 898 / 442 / 215 triangles (LOD0 / LOD1 / LOD2).
`scripts/build.py` sets the isle's `blib.SKIP_BONE_SHAPES` and passes `disable_bone_shape` to its own per-face skin
import; every LOD lost exactly the ball, frame unchanged. Rebuilt, checked (`finish.py`, check_winding.py: 0 inverted
closed parts) and reinstalled with `install_model.py --world mm9`; the replaced GLBs and scripts are in
`work/backup_propfix_20261031/`. No MM9 bake depends on decoration models (stale_bakes.py lists none).
