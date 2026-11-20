# MM6 rat (rat) — 3D pilot, 2026-10-07

Non-humanoid pilot: can a quadruped go through Meshy model → own rig → procedural animation without hand posing?
BRat A/B/C (619 Common, 620 Large, 621 Giant Rat), opt-in via `debug.actor_models=true`.

| Item | Value |
|---|---|
| Runtime GLB | `assets_dev/worlds/mm6/models/mm6_rat.glb` (skins `rat_a/b/c`) |
| Triangles LOD0/1/2/3 | 8,292 / 4,146 / 1,491 / 482 |
| Skeleton | 23 bones: 3 spine, neck, head, 6 tail, 3 per leg (no toes) |
| Clips | Standing, Walking (trot), Running, Attack, Hit, Death, Dead, Fidget (all procedural) |
| Meshy credits | **15 / 30** (Smart Topology 5, retexture 10) |

## Pipeline (scripts/)

1. `references/` — restored 2× sprite views (`mm6_rat/trimmed_2x/ratsta*`), three-quarter view for Smart Topology.
2. `rig_rat.py` — import, ground, skeleton from joints traced by slicing the mesh (`grid_views.py` for checks),
   Blender automatic (heat) weights. Meshy's auto-rig and animation library are biped-only (all 678 library
   clips are biped), so the rig and clips are ours. `stress.py` renders extreme poses.
3. `anim_rat.py` — procedural clips at 24 fps: two-bone IK legs on footholds (trot with diagonal pairs, front
   paws paddle high like the native walk), lagging tail wave, keyed attack/hit/death following the native
   sprites (rear up and lunge; flatten with the tail whipped up; rear, flail, fall on the side). Floor rules
   per frame: lift the body if it sinks, raise tail segments and underside legs out of the floor.
4. `uv_export.py` (Smart UV Project) → Meshy retexture with four restored views → `compose_rat.py`
   (skin/fur recoloured to native tier medians of palettes 807/808/809, eyes per tier, roughness classes).
5. `build_runtime.sh --install` (export, LODs, shadow fix, A/B/C variants).

## Results

[3D vs sprites in game](review/rat_3d_vs_sprites.png) (top 3D, bottom restored sprites, same spawn and camera).
Clip sheet: `scripts/clip_sheet.py`. Floor check: every clip within ~1.5 cm of the floor.
Regression: all MM6 actor cases pass (demon asset-count check now counts distinct bound models).

## Known flaws

- Corpse: upper-side legs stick up a little; fur reads slightly lighter/puffier than the native sprite.
- Procedural motion is generic (no per-frame match to the native sprites).
- No dedicated rat regression case yet.

## HD retexture and shared-skin tiers (2026-10-08)

Per [HD master references](../CLAUDE_HD_MASTER_REFERENCES.md) and [creature textures](../CLAUDE_CREATURE_TEXTURES.md):
- `references_hd/`: five Codex masters (1536×1024, brief `CODEX_BRIEF.md`, inputs `native_views.png` from the
  original native frames plus one restored frame for material). They replace the enlarged sprite frames.
- Meshy `retexture_v2` (10 credits; 25/30 used) on the existing mesh from `01_front`, `03_left`, `02_back` and `04_right`.
  The rig and clips are unchanged.
- `uv_export.py` now gives head islands 2.5x scale before packing (`../claude_shared/uv_head_density.py`):
  about 2x linear texel density on the head. `work/anim_v1_pre_headuv.blend` keeps the previous UVs.
- Tiers: `compose_rat.py` writes `textures/rat_region_weights.npz`, and `build_runtime.sh` fits ramps
  (`../claude_shared/fit_tier_regions.py`) and builds one shared skin with `../claude_shared/region_variants.py`.
  `textures_v1/` keeps the previous baked textures.
- Review: `review/hd_retexture_3d_vs_sprites_20261008.png` (New Sorpigal, left 3D, right sprites).

## Gait pass: Walk2 (trot) and Run2 (half-bound), 2026-10-21

[Creature post-process](../CREATURE_POSTPROCESS.md) step 3. The game plays one walk/run loop per stride of travel, and
the old Walking (0.28 m in 0.58 s) and Running (0.43 m in 0.5 s) were authored for half the game's speeds.
`scripts/gait2_rat.py` authors `Walk2` and `Run2` for the `gait_gate.py` fit ranges (walk 0.71–1.14, run 1.42–2.28
model units/s):

| Clip | Gait | Length | Stride (binding) | Authored speed | Duty | Sweep |
|---|---|---|---|---|---|---|
| Walk2 | trot (diagonal pairs) | 0.3333 s (20 keys at 60 fps) | 0.30 m | 0.90 | 0.55 | 0.165 m |
| Run2 | half-bound (hinds together, fronts staggered) | 0.2833 s (17 keys) | 0.51 m | 1.80 | 0.32 | 0.163 m |

- Paws are planted by their contact point: the front-most vertex on the floor at rest. The wrist or ankle follows from
  the paw pitch, so the heel lifts over the last 40 % of the stance and the paw rolls over its toes.
- Footholds are planned per limb. The front legs are short (0.14 m chain) and limit the sweep: a longer stride needs a
  shorter stance, not a bigger reach.
- Run2 adds the bound's body motion:
  - rocking ±5°: front up at the hind push-off, down at the front landing;
  - back flex ±8°: arched as the hind feet swing under the body, extended in the extended suspension;
  - body bob, low at the strikes, and the head kept level (it took the neck 1 cm under the floor otherwise).
- The clips are grafted onto the installed floor-fixed export with `../claude_shared/graft_clips.py` (joint rests
  checked).

```sh
blender -b --factory-startup -P scripts/gait2_rat.py -- work/gait2_clips.glb      # also saves work/gait2.blend
python3 ../claude_shared/graft_clips.py ../mm6_rat_reduce_claude/export/mm6_rat_floor.glb work/gait2_clips.glb \
  ../mm6_rat_reduce_claude/export/mm6_rat_gait.glb --clip Walk2 --clip Run2
```

Gate (`--set walking=Walk2 --set run=Run2 --set stride_length=0.30 --set run_stride_length=0.51`) passed. Both strides
are trusted: 0.300/0.299 and 0.510/0.498. The window was ×0.95–1.19 on every tier, and the floor check was ok.

## Sprint: bounding gallop for the MAW chase, 2026-10-31

The MAW ruleset moves fast melee monsters at Spd / 2 + 300, and the engine doubles that while chasing: 2.91–3.63 model
units/s for BRat A/B/C, where Run2 would play at ×1.6–2.0 and pedal. The engine now takes an optional third clip
(`animation.sprint` + `sprint_stride_length`, picked by the same misfit rule as walk/run) and caps playback at ×2.
`scripts/sprint_rat.py` (an extended copy of `gait2_rat.py`, which is unchanged) authors `Sprint` for the
`gait_gate.py` target (sprint authored speed 3.06, fits 2.42–3.87):

| Clip | Gait | Length | Stride (binding) | Authored speed | Duty | Sweep |
|---|---|---|---|---|---|---|
| Run2 | half-bound | 0.2833 s (17 keys at 60 fps) | 0.51 m | 1.80 | 0.32 | 0.163 m |
| Sprint | bound with double suspension | 0.2667 s (16 keys) | 0.853 m (×1.67) | 3.20 | 0.22 | 0.188 m |

The cadence is only 6 % higher than Run2's. The legs' reach is the limit (front chain 0.14 m), so the extra stride
comes from the air time and from the body moving relative to its average travel:
- Footfalls as in Run2, so the engine's shared gait phase does not jump on a switch: hinds 0.00/0.05, fronts
  0.43/0.50. That gives hind support 0–0.27, an extended flight 0.27–0.43, front support 0.43–0.72 and a gathered
  flight 0.72–1.0.
- Surge ±1.3 cm: the body lags while paws are planted and catches up in the flights, so a planted paw moves less
  relative to its shoulder or hip than the 0.188 m it covers on the floor.
- Back flex from +14° (arched, gathered flight, the hinds swinging under the chest) to −9° (extended flight). The front
  body's net pitch is keyed separately (−5° to +4°), and the hips pitch by the difference, so the rump tucks under
  when gathered and rises behind a low chest when extended. Keying flex and rock independently (first try) lifted the
  shoulders 14° at the front strike, leaving the fronts out of reach (1.16 of the chain), and put the neck 1.7 cm
  under the floor.
- Bob from −1.4 cm at mid support to +0.8 cm in the gathered flight. The head is kept level against the net pitch.
- Swing paths: follow-through back after push-off (fronts 3 cm, hinds 1.2 cm) and reach forward before the strike
  (fronts 3.5 cm, hinds 2 cm).
- Footholds are planned per limb against the posed shoulder or hip over the stance (surge, bob, flex and rock
  included): fronts 0.77/0.81 of the chain, hinds 0.97.
- Curves are closed Catmull-Rom splines through phase keys (`curve`).

Authoring report: lowest vertex −0.71 cm (Tail2, rump tucked) to +2.03 cm; core +0.17 cm; worst toe miss 8.3 mm
(hind mid-swing, off the floor). A hind follow-through of 3.5 cm with a −12° extension creased the flank behind the
thigh at 0.45–0.55. The final 1.2 cm and −9° leave a small knee-fold crease at 0.55, comparable to Run2's at 0.65.

```sh
blender -b --factory-startup -P scripts/sprint_rat.py -- work/sprint_clips.glb      # also saves work/sprint.blend
python3 ../claude_shared/graft_clips.py ../../../assets_source/worlds/mm6/models/mm6_rat.glb work/sprint_clips.glb \
  ../mm6_rat_reduce_claude/export/mm6_rat_sprint.glb --clip Sprint
```

The graft target was the installed source (the gait export with the far LODs rebuilt by `lod_repair_claude`, kept as
`../mm6_rat_reduce_claude/work/mm6_rat_source_pre_sprint.glb`). Install, gate and review are in
[the reduction README](../mm6_rat_reduce_claude/README.md#sprint-2026-10-31).
