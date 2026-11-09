# MM7 Dog (m509): zdog a / b / c — Claude quadruped route, batch L

MM7 batch L model 4 ([BATCH_L.md](../mm7_batches/BATCH_L.md)). Monsters 469 Dog A, 470 Dog B, 471 Dog C (descriptors
`zdog a/b/c`, ambient town animals). **Installed 2026-10-21** (the user asked for it after the batch; the batch itself
stopped at exports). Meshy: **15 of 100 credits** (Smart Topology 5, retexture 10). User artistic acceptance is not
recorded.

[Review viewer](review/viewer/index.html) (served at
`http://127.0.0.1:8912/level_generation/creatures/mm7_m509_claude/review/viewer/`) ·
[HD masters](references_hd/selected_views_review.png) · [clay clips](review/clips_v1_three_quarter.png), [side](review/clips_v1_left.png)

| Item | Value |
|---|---|
| Runtime export | `export/mm7_m509.glb`: one skinned mesh `M509`, one material, smooth-shaded (user review 2026-10-20: the first flat export showed every triangle), LODs **2,350** / 1,174 / 401 / 118 (LOD0 halved on the textured master by `halve_lod0.py` (user, 2026-10-20: "reduce tris now"; collapse before the armature, UV-seam vertices weighted 0.8, small pieces kept whole, the head, legs, paws/feet and tail protected (a face-only protection flattened the legs into blades))) tris + shadow LODs, 7 clips |
| Portable / editable | `export/mm7_m509_lod0.glb`; `work/anim_v2u.blend` (rig, clips, UVs) |
| Textures | one atlas: 2K base colour, 1K normal / ORM, class map; head islands 2.5× (our Smart UVs) |
| Skeleton | 23 bones + `Socket_Mouth`: Spine1–3, Neck1, Head, Tail1–6, legs UpperArm/ForeArm/FrontPaw and Thigh/Shin/HindPaw |
| Clips (30 fps) | Standing 2.0 s, Walking 0.867 s (stride 0.969 m), Attack 1.0 s (impact 0.5 s), Hit 0.633 s, Death 1.1 s, Dead 1.0 s, Fidget 1.6 s |

## Identity and tiers

Native `m509*` (49 frames): a lean German-shepherd-type dog with erect ears, a dark grey-olive coat and a long low
bushy tail. **All three descriptors draw group 7m509 in palette 545** (no tint): one look, no colour variants and no
region mask; the binding has no `skin`. The native has only standing, walk and death frames (attack = walk, hit =
fidget = stand).

## Route

1. HD masters (Codex, landscape), gated; Smart Topology 15k of `00_three_quarter.png` (one shell + 4 eye pieces + 21
   claws); `step1_clean.py` (1.4 m nose to tail tip).
2. `measure_quad.py` (new, reused by the cat): legs traced up from the paws to the trunk's underside, joints at fixed
   fractions of the leg height, spine and shoulders/hips from the trunk's top and bottom on the midline, the tail ordered
   by distance from its root (follows the hanging tail). `rig_rat.py` (MM7 rat): heat weights on a 1.6 cm voxel proxy of
   the shell, lower legs re-weighted along their chains, claws and eyes copy the skin.
3. `anim_dog.py` (from the rat's): trot with diagonal pairs at the native 0.875 s cycle (26 frames): at the binding
   scale MM7's speed 140 moves the dog 1.18 m/s, so the clip plays at 1.05×; crouch and lunging snap; flinch; rears up
   with the forelegs off the ground (native m509da/db), twists and falls onto its side (dc/dd, corpse xa); sniff fidget.
4. `reduce_quad.py` (new): after weighting and before the UVs, the shell 12,831 → 3,800 tris (head half-protected),
   claws 1,881 → 469, eyes 1,239 → 433: **15,951 → 4,702** (batch: a low budget for a small animal).
5. `uv_export.py` (Smart UV, head 2.5×), Meshy retexture on our UVs (`enable_original_uv: true`), `uv_raster.py`,
   `bake_ao.py`, `compose_m509.py`, `scripts/build_runtime.sh` (material extras only: `set_extras.py`).

## Gates

- Halved LOD0 (`halve_lod0.py`, 2026-10-20), edge stretch p99: Standing 1.08, Walking 1.35, Attack 1.20, Hit 1.10, Death
  1.54, Fidget 1.12; floor 0.0-0.6 cm. Viewer, winding and textured renders rechecked.
- Edge stretch p99 / max: Standing 1.06 / 1.13, Walking 1.25 / 1.99, Attack 1.17 / 1.38, Hit 1.09 / 1.29, Death
  1.51 / 2.18, Fidget 1.11 / 1.27 (reduced mesh).
- Floor: every clip's lowest point ≥ 0.0 cm; the corpse rests on z = 0 (the rear-up lifts the body up to 17 cm).
- `check_winding.py`: 0 inverted closed parts. Viewer: 7 clips, no console errors. Textured EEVEE frames (standing,
  trot, death) inspected (`work/r_glb/`). Not checked in game (optional for batch L).

## Installed (2026-10-21, user request after the batch)

```sh
python3 tools/install_model.py level_generation/creatures/mm7_m509_claude/export/mm7_m509.glb --world mm7
```

Binding for `assets_dev/worlds/mm7/models/actors.yml` (repeat for `zdog b` and `zdog c`, identical):

```yaml
# MM7 Dog m509 (469-471): ambient dog, trot at the native cycle, snap attack, rear-up death. One look (palette 545).
- descriptor: zdog a
  model: worlds/mm7/models/mm7_m509.glb
  scale: 118.4
  yaw_offset: -1.570796327
  animation:
    cast: Attack
    run: Walking
    stride_length: 0.969
    run_stride_length: 0.969
    upper_body_root: Spine2
    look:
      nodes: [Neck1, Head]
      max_yaw_degrees: 40
      max_pitch_degrees: 20
    sockets:
      mouth: Socket_Mouth
    events:
      attack_melee: {impact: 0.5}
      attack_ranged: {impact: 0.5, release: mouth}
  clips:
    standing: Standing
    walking: Walking
    attack_melee: Attack
    attack_ranged: Attack
    hit: Hit
    dying: Death
    dead: Dead
    fidget: Fidget
```

Scale = native standing silhouette 114 px (`m509sa2`, ear tips to paws, frame scale 1.0) / 0.963 m Standing height.

## For the user to review

- The attack, hit and fidget are inventions (the native shows the walk or the standing frame); `fidget: Standing` keeps
  the native's still pose if preferred.
- Motion is procedural (rat route), an interpretation of the native frames.

## Gait rollout (2026-10-31): Trot for the chase

Gait rollout package q2 ([`../gait_rollout_20261031/q2/README.md`](../gait_rollout_20261031/q2/README.md)) added
`Trot`, a fast trot for the Standard chase. The dog chases at 2.36 model units/s, where `run: Walking` played ×2.12.
- The clip is 0.4333 s long with a 0.9663 m stride (authored 2.23) and duty 0.40, with short suspensions.
- Front L and hind R strike at 0, as in Walking.
- Grafted onto the installed `mm7_m509.glb` (append only; 0 inverted) and installed.
- Binding for zdog a-c: `run: Trot`, `run_stride_length: 0.9663` (chase ×1.06, wander Walking ×1.06).
- Made by `../gait_rollout_20261031/q2/scripts/quad_gait.py m509` from `work/anim_v2u.blend` (read only).
- Viewer: the page is copied from the MM7 rat's, at revision `zdog-trot-1`; the v1 manifest is kept as
  `manifest_mm7_m509_claude_v1.json`. Shots `review/shots/t_*.png`, playback `review/playback/Trot-*`.
- A later re-export or LOD rerun must re-graft `Trot`.
