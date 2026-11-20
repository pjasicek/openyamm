# MM7 Rat (m382) — Claude 3D model, batch E

Giant Rat / Lightning Rat / Fire Rat (monsters 385–387, sprite groups m383/m384/m385, palettes 383/384/385).
Batch E ([../mm7_batches/BATCH_E.md](../mm7_batches/BATCH_E.md)): the model stops at project exports; nothing is
installed or bound. This is a new model of the MM7 rat art, not a reuse of `mm6_rat_claude/` (different design: hunched
grey-furred body with bare mint skin).

![tiers in the review viewer above the native palettes](review/tiers_vs_native.png)

| Item | Value |
|---|---|
| Export | `export/mm7_m382.glb` (LOD0–3 + shadow LODs, three tier variants sharing every image) |
| Editable sources | `work/rig_v1.blend` (rig), `work/anim_v2u.blend` (rig + clips + UVs, exported), `export/mm7_m382_lod0.glb` |
| Triangles LOD0/1/2/3 | 14,751 / 7,374 / 2,634 / 837 |
| Skeleton | 23 bones + `Socket_Mouth`: Spine1–3, Neck1, Head, Tail1–6, legs UpperArm/ForeArm/FrontPaw and Thigh/Shin/HindPaw |
| Clips (30 fps) | Standing 2.0 s, Walking 1.0 s (stride 0.60 m), Running 0.6 s (0.99 m), Attack 1.0 s (impact 0.5 s), Hit 0.625 s, Death 1.1 s, Dead 1.0 s, Fidget 1.6 s |
| Textures | one atlas: 2K base colour, 1K normal / ORM / region mask; head islands 2.5×; two regions (skin, eyes) |
| Meshy credits | **15 of 100**: Smart Topology 5, retexture 10 (our UVs) |
| Viewer | `http://127.0.0.1:8912/level_generation/creatures/mm7_m382_claude/review/viewer/index.html` — check: 3 tiers × 8 clips, no console errors |

## Anatomy decisions

- **Quadruped playbook, rat route** (`mm6_rat_claude`): own rig, heat weights, legs on IK footholds, a lagging tail,
  procedural clips. The scripts are the Manticore's (`mm7_m278_claude`) adapted to the rat's scale.
- **Pieces fused by the proxy.** Smart Topology split the head, the body shells, the legs and the tail into six large
  pieces; heat weights are solved on a voxel proxy of all six (2.2 cm; 1.2 and 1.5 cm made the solver fail). The
  coarse proxy fused the thin lower legs (a left hind foot took right-shin weight: 57× edge stretch), so below 28 cm
  every skin vertex is reweighted along its nearest leg chain (not the tail, which lies beside the left hock), and the
  tail-root border is smoothed over mesh edges.
- **Attack** (native `m382aa`, `ac0`): crouch, lunging bite (impact 0.5 s), then rears up clawing with both forepaws.
  **Death** (`m382db0`): rears with the forepaws up, twists and falls onto its side. The long hind feet tip up in
  swing (toes-down pitch sank them 7 cm).
- `Socket_Mouth` at the snout for the Lightning Rat's Air and the Fire Rat's Fire ranged attack (monster table).

## Route (replay)

1. HD masters (`references_hd/`, Codex, gated); native frames through the three palettes (`scripts/native_palettes.py`).
2. Smart Topology 15k (14,751 triangles); `step1_clean.py` normalises the length to 2.0 m.
3. `rig_rat.py` (joints `work/joints.json`).
4. `anim_rat7.py work/rig_v1.blend work/anim_v1.blend`; `uv_export.py work/anim_v1.blend work/anim_v2u.blend`
   (deterministic: the re-run upload is byte-identical to `texturing/m382_upload_sent.glb`).
5. Retexture (`requests/retexture_v1.json`), `uv_raster.py` (1K, 2K), `bake_ao.py`, `compose_m382.py`.
6. `scripts/build_runtime.sh <token>`; viewer `viewer_tiers.py`, `update_viewer_manifest.py`.

## Tiers

Native palettes: the bare skin (head, ears, legs, tail) changes mint → pale blue → pink and the eyes black → amber →
red; the grey fur stays. Regions: skin (one chroma per tier at the texel's own luminance, scaled to the native mean ×
1.1) and eyes (the dark texels in the eye area of the head piece: the native eye colour per tier).

## Gates

- Edge stretch (`outliers.py`): Standing/Hit/Fidget ≤ 3.2×, Attack 7.3×, Dead 5.4×, Death 9.1×, Walking 9.3×,
  Running 11.8× — the worst vertices are a small patch on the inner hock of the left hind leg and the thigh/tail-root
  border; not visible at normal distance (`review/run_close.png`).
- Floor: all clips' lowest vertex ≥ −0.7 cm (tail segments); the corpse rests on the floor.
- Viewer: 24 tier/clip switches, no errors; shots in `review/shots/`.

## For the user to review

- The inner-hock stretch above (a cleaner fix is a finer weight solve or a retopology of the fused hind legs).
- Motion is procedural and an interpretation of the native frames.

## Install later (not run)

**Reduced version:** [`../mm7_m382_reduce_claude/`](../mm7_m382_reduce_claude/README.md) (2026-10-20) — install its
`export/mm7_m382.glb` (the command below) instead of this one; the binding below is unchanged.

```sh
python3 tools/install_model.py level_generation/creatures/mm7_m382_reduce_claude/export/mm7_m382.glb --world mm7
```

Binding for `assets_dev/worlds/mm7/models/actors.yml` (scale = native stand 60 px × frame scale 0.7 ÷ 0.799 m
Standing height = 52.6; all tiers share the frame scale):

```yaml
- descriptor: Rat A
  model: worlds/mm7/models/mm7_m382.glb
  scale: 52.6
  yaw_offset: -1.570796327
  skin: m382_a
  animation:
    sockets:
      mouth: Socket_Mouth
    cast: Attack
    run: Running
    stride_length: 0.60
    run_stride_length: 0.99
    upper_body_root: Spine2
    look:
      nodes: [Neck1, Head]
      max_yaw_degrees: 40
      max_pitch_degrees: 20
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
# Rat B / C: the same with skin m382_b / m382_c.
```

No in-game check was run (optional for batch E).

## Gait pass: Walk2 (lope) and Run2 (bound), 2026-10-21

[Creature post-process](../CREATURE_POSTPROCESS.md) step 3. The game moves this rat at 4.75 model units/s wandering and
9.51 chasing, about six and twelve trunk lengths a second. The old trot (Walking 0.6 m/s, Running 1.65 m/s) played at
2.9× and 5.8×. `scripts/gait2_rat7.py` (after `../mm6_rat_claude/scripts/gait2_rat.py`) authors gallops at those
speeds, for the `gait_gate.py` fit ranges (walk 3.17–6.34, run 6.34–12.67). Both run at the same cadence (4.3 Hz), and
the run doubles the stride with long suspensions:

| Clip | Gait | Length | Stride (binding) | Authored speed | Duty | Sweep |
|---|---|---|---|---|---|---|
| Walk2 | rotary lope (hind L, hind R, front R, front L) | 0.2333 s (14 keys at 60 fps) | 1.0453 m | 4.48 | 0.42 | 0.44 m |
| Run2 | half-bound (hinds together, fronts staggered) | 0.2333 s (14 keys) | 2.0907 m | 8.96 | 0.24 | 0.50 m |

- Paws are planted by their contact vertex, and the heel lifts at push-off. The long hind foot tips its toes up in swing,
  with the heel lifted clear.
- Footholds are planned per limb, at one place along the body for both sides (the rest pose is uneven).
- Rocking, back flex and bob follow the bound's phases as in the MM6 rat, with the head kept level.
- `gait_gate.py` also prints "one clip for both: 6.72", but that value fails its own window: wandering would play at
  ×0.71. A single clip fits only at exactly 6.34, so two clips are used.
- The clips are grafted onto the installed export with `../claude_shared/graft_clips.py` (joint rests checked).

```sh
blender -b --factory-startup -P scripts/gait2_rat7.py -- work/gait2_clips.glb     # also saves work/gait2.blend
python3 ../claude_shared/graft_clips.py ../mm7_m382_reduce_claude/export/mm7_m382.glb work/gait2_clips.glb \
  ../mm7_m382_reduce_claude/export/mm7_m382_gait.glb --clip Walk2 --clip Run2
```

Gate (`--set walking=Walk2 --set run=Run2 --set stride_length=1.0453 --set run_stride_length=2.0907`) passed.
- Both strides are trusted: 1.045/1.023 and 2.091/2.065.
- The window was ×1.06 on every tier (all three tiers share one speed).
- The floor check was ok. The lowest point is a hind heel 2–3 cm under the floor at push-off, against a 4.75 cm
  tolerance.

## Sprint (MAW chase), 2026-10-31

The MAW ruleset moves fast melee monsters at Spd / 2 + 300, and the engine doubles that while chasing. Rat A–C then
chase at 16.16 model units/s, and Run2 (8.96) would play at ×1.80. Under MAW the engine now picks a third clip,
`animation.sprint`, by the same misfit logic as walk and run (`gait_gate.py` fit range 10.77–21.55). Run2 stays for
Standard's chase. `scripts/sprint_rat7.py` authors `Sprint`. `gait2_rat7.py` is kept unchanged.

| Clip | Gait | Length | Stride (binding) | Authored speed | Duty | Sweep | MAW chase rate |
|---|---|---|---|---|---|---|---|
| Sprint | half-bound gallop (hinds together, fronts staggered) | 0.25 s (15 keys at 60 fps) | 3.30 m (1.58× Run2) | 13.2 | 0.18 | 0.59 m | ×1.22 |

- **Where the stride comes from.** The extra length comes from the flights, not the legs: the sweep is only 0.59 m
  against Run2's 0.50 m. Played at ×1.22 the cadence is 4.9 Hz, against Run2's 4.55 Hz at Standard's chase.
- **Phases.** The footfalls follow Run2's: hind L at 0, hind R at 0.06, fronts at 0.44/0.52 (Run2 0.42/0.52). A
  switch on the shared gait phase therefore lands on the same footfall.
- **Flights.** There are two long flights. The extended flight (about 0.24–0.44) has the back stretched flat, the
  hinds trailing 10 cm past lift-off and the fronts reaching 5 cm past the foothold. The gathered flight (about
  0.70–1.0) has the back humped and the hinds swung far under the body. The body rises 6 cm in both flights.
- **Back flex.** The back flexes ±26°, and the hips take back 45 % of it, so the back arches and dips between level
  shoulders and hips. Without the counter-pitch, the extension lifted the shoulders by about 17 cm and the front paws
  fell up to 7 cm short of their swing targets.
- **Footholds.** Footholds are planned against the posed body: the shoulder and hip of each stance phase come from that
  phase's flex, rocking and bob. Worst reach is 0.92 of the chain at the front and 0.97 at the hind. The planted toe
  never misses its target.

```sh
blender -b --factory-startup -P scripts/sprint_rat7.py -- work/sprint_clips.glb     # also saves work/sprint.blend
python3 ../claude_shared/graft_clips.py ../../../assets_source/worlds/mm7/models/mm7_m382.glb work/sprint_clips.glb \
  ../mm7_m382_reduce_claude/export/mm7_m382_sprint.glb --clip Sprint
```

`gait_gate.py --world mm7 --model mm7_m382.glb --candidate ../mm7_m382_reduce_claude/export/mm7_m382_sprint.glb
--set sprint=Sprint` results:
- **Stride:** Sprint is trusted, measured 3.300 m by the vertices and 3.114 m by the feet.
- **Window:** every Rat A–C row passes. Standard is Walk2 ×1.06 / Run2 ×1.06. MAW is Run2 ×0.90 wandering and
  Sprint ×1.22 chasing.
- **Floor:** ok. The lowest point is a hind heel 1.6 cm under at push-off (Run2: 2–3 cm), and the tail lies 0.6 cm
  under. The body core stays above the floor.
- **zrat a–c:** the Standard wander rows of the arena rats fail (Walk2 ×0.63). This is older than the sprint and out
  of its scope. MAW leaves their speed (Spd 140) unchanged, so they get no sprint.

Binding (Rat A/B/C only): `sprint: Sprint`, `sprint_stride_length: 3.3`.
