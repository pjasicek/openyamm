# Projectile models (2026-10-16)

3D models replace the native flight sprites of every solid projectile (the user's request: deprecate the flight
sprites, keep projectiles very cheap, mind quality, triangles and textures). Since 2026-10-16 (second request: no
classic style) no projectile or impact draws its native sprite at all: the rest are effects
(`engine/effects/projectiles.yml`: Sparks' effect draws its whole crackling ball, debuffs that only fly from events
have `sprite: hidden`, a projectile falling into water plays `water_splash`). `video.projectile_style` and
`features.monster_projectile_visuals` were removed. The regression cases `projectile_visuals_draw_no_native_sprites`
(every spell's flight, every monster missile, the party's missiles, every impact and the splash) and
`projectile_models_present_armed_fire_spike_traps` (suite `projectiles`) keep it so.

## Engine binding

`assets_dev/engine/models/projectiles.yml` (schema `openyamm.projectileModels.v1`) binds a model to an object id
(`object_list.txt` ObjectId) with its length in world units and an optional spin:

```yaml
projectiles:
  - {object: 4070, model: engine/models/projectile_rock.glb, length: 85, spin: {axis: side, degrees_per_second: 360}}
```

`WorldFxSystem::loadProjectileModels` (called by the outdoor and indoor views at map load) loads the bindings and
models; `syncProjectileModels` (in `syncProjectileFx`) keeps one model instance (static stand-in, so flipbook and
additive materials work) per flying projectile, turned by yaw then pitch along its velocity, then by its spin
(forward = roll, up = whirl in its own plane, side = end over end; 128 projectile ticks a second, a per-projectile
starting angle), at the projectile's effect anchor (`projectileRecipeAnchorOffset`), so it lines up with its enhanced
trail. A settled projectile (an armed Fire Spike) lies level and still; a still one keeps its last heading. Indoors the
models follow the portal-revealed sectors (`setProjectileModelVisibility`). `projectileShowsNativeSprite` is false for a
bound projectile in both projectile styles; its effects (trail, light, impact) are unchanged.

Armed party Fire Spikes are world traps (`IGameplayWorldRuntime::collectFireSpikeTrapPresentationStates`, both runtimes):
the sync adds them as settled projectiles (keyed apart from projectile ids), so their model lies level where the trap
is; the outdoor renderer's trap sprite is skipped like a projectile's.

Sprite loading: `MapAssetLoader` preloads only item sprites (unpickable objects are missiles and impacts, presented by
models and effects), and the outdoor event-spell sprite warmup is gone. Thrown items (307 dagger, 309 axe, 384 egg) are
pickable: their item sprites still show them lying on the ground.

Tests: `*Projectile model bindings*` (parser, and every bound model of the real file exists).

Model contract: points along glTF +Z (Blender -Y), origin at the projectile's centre (the sprite's centre), scaled
uniformly so its +Z extent equals `length`.

## Models

| Model (`engine/models/projectile_*.glb`) | Objects | Triangles | Built by | Spin |
|---|---|---|---|---|
| arrow | 545 Arrow | 96 | `build_arrow.py` | |
| fire_arrow | 550 FireArrow | 100 (+ flipbook flames) | `build_arrow.py` | |
| cannonball | 560 Cannonball (the "Rock" missile of Malevolent Boulders and Earth Elementals) | 320 | `build_solids.py` | |
| boulder | 565 Cyclops boulder (no monster fires it in the merged data) | 320 | `build_solids.py` | side 300 |
| rock | 4070 Rock Blast, 4090 Death Blossom, 4092 its shards | 320 | `build_solids.py` | side 360-480 |
| ice_shard | 3030 Ice Bolt, 3090 Ice Blast, 3092 its shards | 42 | `build_solids.py` | forward 360-480 |
| blades | 4050 Blades | 212 | `build_solids.py` | up 900 |
| shrapnel | 9040 Shrap Metal | 96 | `build_solids.py` | side 540 |
| fire_spike | 1060 Fire Spike | 68 | `build_solids.py` | up 360 |
| starburst | 2100 Starburst star | 84 (+ flipbook flames) | `build_solids.py` | |
| meteor | 1080 Meteor Shower | 84 (+ flipbook flames) | `build_solids.py` | |
| fist | 7090 Flying Fist | 1380 | `build_fist.py` | |
| serpent | 7030 Harm (the painted spell is a golden serpent) | 372 | `build_solids.py` | |
| toxic_cloud | 9010 Toxic Cloud (a skull of green poison; the effect rolls the cloud round it) | 583 | `build_toxic.py` | |
| dagger, axe, egg | 307, 309 (thrown: party, MM9), 384 (MM9) | 152, 300, 192 | `build_traced.py` | side 720 / 540 / 360 |

Cooked sizes 5-19 KB (fist 68 KB). No LODs (all far under the budgets; projectiles are small and short-lived).

- **Arrows** (`build_arrow.py`): traced from the side-view sprites (`arrowa2`, `frarwa2`; 400 x 120 at x2):
  hexagonal shaft, ferrule, flat broadhead, three vanes outlined by the top feather's contour, all UVs on sprite
  pixels (`make_textures.py`: the side view with colours dilated outward; the shaft samples a strip of per-column
  means of the painted shaft rows without the highlight line, x1.4). The fire arrow adds two crossed cards over its
  front half with the six painted flame frames (`openyamm_flipbook [2, 4, 12]`, additive, unlit, double-sided),
  keyed to the flames by saturation and brightness so no ghost shaft or head is added.
- **Surfaces** (`build_solids.py`, `make_solid_textures.py`): CC0 Poly Haven scans of the MM8 props batch
  (`../../decorations/mm8_3d/props/source/`: rust_coarse_01 as dark iron, rock_boulder_dry, metal_plate_02 as steel),
  256 px, graded to each sprite's mean colour x1.35 (the sprites carry their painted light), with the scans' normal
  maps. Rocks are displaced icospheres with box UVs and COLOR_0 cavity shading (`projlib.cavity_colour`) for the
  painted crevices. Blades are four closed crescent blades with a raised ridge round an octagonal boss. The caltrop has
  twelve square spikes along the icosahedron's vertex directions. Ice is procedural with a faint cold glow.
- **Star and meteor**: an unlit lava core (`lava_hot`: mostly white-yellow; `lava`: dark crust, glowing cracks) where
  the painted ball or rock was, and crossed flame cards trailing behind with eight painted frames turned so the core
  leads (`flames.json` records the windows; the origin is the sprite frame's centre, as the native sprite).
- **Fist** (`build_fist.py`): an MPFB (MakeHuman, CC0) right hand curled into a fist (fingers flexed toward the palm
  normal, the thumb's base solved by search so its tip rests on the middle and index fingers' middle segments), cut
  with 0.55 hand lengths of forearm, knuckles forward, back of the hand up, decimated, the cut capped and hidden in
  ten thin ice crystals (the sprite's frayed wrist). Saturated ice blue with a cold glow: the enhanced Flying Fist
  effect lights it red-orange, which turned the paler sprite blue pink in game. COLOR_0: ray-cast occlusion.
- **Serpent** (`build_solids.py serpent`): 194 long, 8.5 thick at most, a gentle S (sideways and a little up and
  down), tapering to the tail, a neck and a flattened head bulge; procedural gold-brown scales with a chain of dark
  diamonds along the back and a paler belly. The Harm effect's blood-red halo and wisps fly with it.
- **Toxic Cloud** (`build_toxic.py`): the MM6 skeleton creature's skull (MM8 props bone kit, read only) decimated to
  583 triangles, its bone texture recoloured poison green, blended at alpha 0.6 with a faint glow. The toxic_cloud
  effect now draws the cloud body (two breathing green smoke puffs) and a denser smoke trail round it.
- **Thrown items** (`build_traced.py`): rings along the item sprite's length follow its outline per column, each an
  ellipse with a width ratio per part (thin blades, round grips), the side view projected as the texture, tip
  vertices closing the ends.

Meshy was not used: at these sizes the sprites and CC0 scans give the closer match.

Rebuild:

```sh
python3 -I scripts/make_textures.py && python3 -I scripts/make_solid_textures.py
blender --background --python scripts/build_arrow.py -- arrow            # or fire_arrow
blender --background --python scripts/build_solids.py -- rock blades ...  # cannonball boulder rock ice_shard blades
                                                                          # shrapnel fire_spike starburst meteor
blender --background --python scripts/build_traced.py -- dagger axe egg
blender --background --factory-startup --python scripts/build_fist.py
blender --background --python scripts/build_toxic.py
blender --background --python scripts/review.py -- rock work/rock_export.glb   # review/rock/*.png
python3 -I scripts/sheet.py <out> rock:sp41b10_p5 ...                     # review/<out>.png with the sprites
python3 ../../decorations/mm8_3d/animated/scripts/check_winding.py work/rock_export.glb   # 0 inverted
python3 ../../../tools/install_model.py work/rock_export.glb --engine --name projectile_rock.glb
```

The winding check only flags closed pieces with a negative total volume: a wrongly wound cap on a closed mesh passes
it (the traced items' caps did), so look at the tail-on and head-on renders too. Blender shows the whole flipbook
atlas on the flame cards; the engine shows one frame.

## Retired sprites

`scripts/retire_sprites.py [--list] [--archive YYYYMMDD]` finds the textures of the projectile objects' sprites (the
unpickable objects spells, monster missiles and the water splash use) that no other sprite of any sprite frame table,
no other object and no decoration uses, and moves their restored x2 files. On 2026-10-16: first 158 files (the
model-bound flights), then 300 more (every spell missile and impact, the splash): 458 files, 20.8 MB, in
`assets_legacy/projectiles_x2_20261016/` (git-ignored). `spell70c` (the cannonball) is shared with another sprite and
stays. A missing x2 sprite falls back to the native bitmap. The texture builders read the archive.

## In-game checks

New Sorpigal (`oute3.odm`) quiet spot from the quadruped playbook and Agar's Laboratory (`6d19.blv`), slow motion
(`debug.time_scale=0.1`), scripted input tours that open the console and fire across the view:

```sh
./tools/run_game.sh --isolated solids-check --world mm6 --map oute3.odm --position -3718.493 3245.946 1 \
  --yaw-radians 3.359 --pitch-degrees -8 --set debug.immortal=true --set debug.time_scale=0.1 \
  --set debug.menu_input_tour_path=/abs/tour.yml --warmup 3 --seconds 60
```

Tour commands (one console open/close per command): `projectile spell <id> -3984 2829 70 -3978 3495 70 10 4` with
7 Fire Spike, 9 Meteor Shower, 22 Starburst, 26 Ice Bolt, 32 Ice Blast, 39 Blades, 41 Rock Blast, 43 Death Blossom,
76 Flying Fist, 93 Shrapmetal (Starburst and Meteor Shower fall from above the target: aim 800 units out, pitch -2);
`actor spawn 271 1 ...` (goblin, `attack2` Arrow), `202` (Archer, `attack2` FireAr), `142` (Malevolent Boulder,
`attack2` cannonball), then `projectile actor last attack2 <x y z>`. Indoors: from (1350, -3150, 10) to
(1350, -2720, 10). Checked 2026-10-16 in both: every model flies, oriented and spinning, with its effects; no sprite
or load errors in the logs. Second round (2026-10-16): Sparks (spell 15), Harm (70) and Toxic Cloud (90) checked the
same way. Not checked in game: boulder (no monster fires it), dagger, axe, egg (MM9 and party throwing), the water
splash (the test shots hit the shore; the regression case covers its binding) and an armed party Fire Spike (the
debug cast targets the nearest actor anywhere; the regression case covers its model).
