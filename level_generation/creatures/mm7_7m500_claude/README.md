# MM7 Cat (7m500): zcat a / b / c — Claude quadruped route, batch L

MM7 batch L model 5 ([BATCH_L.md](../mm7_batches/BATCH_L.md)). Monsters 463 Cat A, 464 Cat B, 465 Cat C (descriptors
`zcat a/b/c`, ambient town animals). **Installed 2026-10-21** (the user asked for it after the batch; the batch itself
stopped at exports). Meshy: **15 of 100 credits** (Smart Topology 5, retexture 10). User artistic acceptance is not
recorded.

[Review viewer](review/viewer/index.html) (served at
`http://127.0.0.1:8912/level_generation/creatures/mm7_7m500_claude/review/viewer/`) ·
[HD masters](references_hd/selected_views_review.png) · [clay clips](review/clips_v1_three_quarter.png), [side](review/clips_v1_left.png)

| Item | Value |
|---|---|
| Runtime export | `export/mm7_7m500.glb`: one skinned mesh `M500`, one material, smooth-shaded (user review 2026-10-20: the first flat export showed every triangle), LODs **2,198** / 1,095 / 382 / 119 (LOD0 halved on the textured master by `halve_lod0.py` (user, 2026-10-20: "reduce tris now"; collapse before the armature, UV-seam vertices weighted 0.8, small pieces kept whole, the head, legs, paws/feet and tail protected (a face-only protection flattened the legs into blades))) tris + shadow LODs, 7 clips |
| Portable / editable | `export/mm7_7m500_lod0.glb`; `work/anim_v2u.blend` (rig, clips, UVs) |
| Textures | one atlas: 2K base colour, 1K normal / ORM, class map; head islands 2.5× (our Smart UVs) |
| Skeleton | 23 bones + `Socket_Mouth`: Spine1–3, Neck1, Head, Tail1–6, legs UpperArm/ForeArm/FrontPaw and Thigh/Shin/HindPaw |
| Clips (30 fps) | Standing 2.0 s, Walking 0.867 s (stride 0.608 m), Attack 1.0 s (impact 0.5 s), Hit 0.633 s, Death 1.1 s, Dead 1.0 s, Fidget 1.6 s |

## Identity and tiers

Native `7m500*` (51 frames): an ordinary black short-haired cat with green eyes, upright ears and a long thin tail.
**All three descriptors draw group m500 in palette 545** (no tint): one look, no colour variants and no region mask;
the binding has no `skin`. The native has only standing, walk and death frames (attack = walk, hit = fidget = stand).

## Route (the Dog's, `../mm7_m509_claude/`)

1. HD masters (Codex, landscape), gated; Smart Topology 15k (one shell + eyes, nose and 13 whisker strips + a flake);
   `step1_clean.py` (0.95 m nose to tail tip).
2. `measure_quad.py` (`LEG_R=0.04`), `rig_rat.py` (`BIG_MIN=1000 VOXEL=0.011`; the lower-leg rule below
   `LOW_Z=0.12` within `LEG_NEAR=0.08` and the tail-root smoothing radius `TAILROOT_R=0.12`, scaled to the cat: the
   dog's 0.28 m rule took the whole belly).
3. `anim_cat.py` (from the dog's): lateral walk (LH, LF, RH, RF) at the native 0.875 s cycle, 0.608 m per cycle (MM7's
   speed 140 at the binding scale is 0.70 m/s: the clip plays at its natural speed); crouch and pounce-swipe; flinch with
   the tail up; rears up twisting and falls onto its side (native 7m500da–de, corpse xa); head-turn fidget.
4. `reduce_quad.py` (`SHELL_TRIS=3200 CLAW_RATIO=0.4 EYE_RATIO=0.35`, pieces 5+ = whiskers): **15,685 → 4,398**.
5. Smart UV (head 2.5×), Meshy retexture on our UVs, `compose_m500.py` (classes: eyes, nose, whiskers 11 'other',
   fur), `scripts/build_runtime.sh` (material extras only).

## Gates

- Halved LOD0 (`halve_lod0.py`, 2026-10-20), edge stretch p99: Standing 1.12, Walking 1.45, Attack 1.22, Hit 1.10, Death
  1.46, Fidget 1.13; floor -0.1-0.0 cm. Viewer, winding and textured renders rechecked.
- Edge stretch p99 / max: Standing 1.11 / 1.31, Walking 1.40 / 2.15, Attack 1.19 / 1.58, Hit 1.09 / 1.24, Death
  1.46 / 1.91, Fidget 1.14 / 1.22 (reduced mesh).
- Floor: every clip's lowest point ≥ 0.0 cm; the corpse rests on z = 0.
- `check_winding.py`: 0 inverted closed parts. Viewer: 7 clips, no console errors. Textured EEVEE frames (standing,
  head close-up with whiskers, walk, death) inspected (`work/r_glb/`). Not checked in game (optional for batch L).

## Installed (2026-10-21, user request after the batch)

```sh
python3 tools/install_model.py level_generation/creatures/mm7_7m500_claude/export/mm7_7m500.glb --world mm7
```

Binding for `assets_dev/worlds/mm7/models/actors.yml` (repeat for `zcat b` and `zcat c`, identical):

```yaml
# MM7 Cat 7m500 (463-465): ambient cat, walk at the native cycle, pounce-swipe attack, rear-up death. One look (palette 545).
- descriptor: zcat a
  model: worlds/mm7/models/mm7_7m500.glb
  scale: 200.4
  yaw_offset: -1.570796327
  animation:
    cast: Attack
    run: Walking
    stride_length: 0.608
    run_stride_length: 0.608
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

Scale = native standing silhouette 94 px (`7m500sa2`, ear tips to paws, frame scale 1.0) / 0.469 m Standing height.

## For the user to review

- The attack, hit and fidget are inventions (the native shows the walk or the standing frame); `fidget: Standing` keeps
  the native's still pose if preferred.
- Motion is procedural (rat route), an interpretation of the native frames.

## Gait rollout (2026-10-31): Trot for the chase

Gait rollout package q2 ([`../gait_rollout_20261031/q2/README.md`](../gait_rollout_20261031/q2/README.md)) added
`Trot` for the Standard chase. The cat chases at 1.40 model units/s, where `run: Walking` played ×1.99.
- The clip is 0.3667 s long with a 0.484 m stride (authored 1.32) and duty 0.42.
- Hind L and front R strike at 0, matching the walk's hind L strike.
- Grafted onto the installed `mm7_7m500.glb` (append only; 0 inverted) and installed.
- Binding for zcat a-c: `run: Trot`, `run_stride_length: 0.484` (chase ×1.06, wander Walking ×1.00).
- Made by `../gait_rollout_20261031/q2/scripts/quad_gait.py 7m500` from `work/anim_v2u.blend` (read only).
- Viewer: the page is copied from the MM7 rat's, at revision `zcat-trot-1`; the v1 manifest is kept. Shots
  `review/shots/t_*.png`, playback `review/playback/Trot-*`.
- A later re-export or LOD rerun must re-graft `Trot`.
