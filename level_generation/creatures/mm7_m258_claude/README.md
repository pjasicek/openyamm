# MM7 Griffin (m258) — Claude 3D model, batch E

Griffin / Hunting Griffin / Royal Griffin (monsters 280–282, sprite groups m259/m260/m261, palettes 259/260/261).
Batch E ([../mm7_batches/BATCH_E.md](../mm7_batches/BATCH_E.md)): the model stops at project exports; nothing is
installed or bound.

![tiers in the review viewer above the native palettes](review/tiers_vs_native.png)

| Item | Value |
|---|---|
| Export | `export/mm7_m258.glb` (LOD0–3 + shadow LODs, three tier variants sharing every image) |
| Editable sources | `work/rig_v1.blend` (rig), `work/anim_v2u.blend` (rig + clips + UVs, exported), `export/mm7_m258_lod0.glb` |
| Triangles LOD0/1/2/3 | 16,126 / 8,062 / 2,902 / 966 |
| Skeleton | 29 bones: Spine1–3, Neck1–2, Head, Tail1–5, eagle forelegs (UpperArm/ForeArm/FrontPaw), lion hind legs (Thigh/Shin/HindPaw), wings (Wing1–3 per side) |
| Clips (30 fps) | Fly 0.90 s loop, Attack 1.00 s (impact 0.55 s), Hit 0.75 s, Death 1.25 s, Dead 1.0 s |
| Textures | one atlas: 2K base colour, 1K normal / ORM / region mask; head islands at 2× density; three regions (plumage, flight feathers, fur) |
| Meshy credits | **15 of 100**: Smart Topology 5, retexture 10 (our UVs, `enable_original_uv: true`) |
| Viewer | `http://127.0.0.1:8912/level_generation/creatures/mm7_m258_claude/review/viewer/index.html` — check: 3 tiers × 5 clips, no console errors |

## Anatomy and motion decisions

- **Quadruped playbook, flyer rules.** The native griffin never lands: its standing, walking and fidget groups all use
  the flight frames (`m258w*`, 7 frames × 125 ms), so one Fly loop serves standing, walking, running and fidget. Body
  level, eagle forelegs reaching forward with open talons, lion hind legs trailing, tail streaming back.
- **Own rig, procedural clips** (`scripts/rig_griffin.py`, `scripts/anim_griffin.py`), joints measured on the mesh
  (`work/joints.json`: grid views, vertex sections, the wings' leading edges). No Meshy rig (not humanoid).
- **Asymmetric rest wings.** Smart Topology baked the three-quarter master's perspective in: the left wing sweeps back
  and the right forward by ~0.6 m at the tips, and the tail swings 45° to the creature's left. Each wing gets its own
  bones; every clip sets each wing segment's direction and feather-plane normal in the chest's frame from one
  parametric left-wing pose (mirrored for the right), so both wings move as one symmetric pose; the tail is aimed
  segment by segment along the body's back axis, so it streams straight back.
- **Wing beat** on the native rhythm (0.875 s, played as 0.9 s = 27 whole frames for a seamless loop), downstroke 45 %
  of the cycle, elbow/wrist fold on the upstroke, body rises on the downstroke.
- **Attack:** rears up with the wings raised (native `m258ab/ac`), rakes both talons forward and down with a hard
  downbeat; impact at 0.55 s. **Hit:** jolts back and up, wings flare, legs flail. **Death:** wings fold, it tumbles
  over onto its back, the wings spread flat on the floor as it lands (legs up), Dead holds it.
- **Floor rules:** one constant clearance for the airborne clips (the lowest vertex over the whole Fly cycle at 2 cm;
  no per-frame grounding, wyvern lesson); Attack/Hit add an eased lift only where rearing up would dip below it
  (up to 31 / 20 cm); Death moves the lowest vertex smoothly from flight height to exactly z = 0. In Death, legs that
  reach below the body swing up (rat rule) and wings are lowered no further than the back — a folded wing under a
  side-lying body, then drooping spread wings, propped the corpse up 30 cm in the first tries.

## Route (replay)

1. HD masters (`references_hd/`, Codex; brief `CODEX_BRIEF.md`, gated). Native frames rendered through the three
   palettes from the original BMPs (`scripts/native_palettes.py` → `references/native_variants/`).
2. Smart Topology 15k (`requests/smart_topology_v1.json`): 16,126 triangles; separate pieces are the two eagle
   forelegs, three tail-tuft clumps and the eyes. `step1_clean.py` normalises the wingspan to 3.6 m.
3. `rig_griffin.py`: heat weights on a hole-filled voxel proxy (2.2 cm) for the body, wings weighted along their
   chains and smoothed over mesh edges (8 passes; without it neighbouring trailing feathers sat on different bones,
   a 20× edge stretch), eagle-leg pieces rigid on their chain, tuft on Tail5, eyes on Head.
4. `anim_griffin.py work/rig_v1.blend work/anim_v1.blend`, then `uv_export.py work/anim_v1.blend work/anim_v2u.blend`
   (Smart UV Project, head islands 2×; deterministic — the re-run layout is bit-identical to the uploaded one,
   `uv_compare.py`, `texturing/m258_upload_sent.glb`).
5. Retexture (`requests/retexture_v1.json`), `uv_raster.py` (1K, 2K), `bake_ao.py`, `compose_m258.py`.
6. `scripts/build_runtime.sh <token>`; viewer `viewer_tiers.py`, `update_viewer_manifest.py`.

## Tiers

Measured on the native frames in each palette: plumage teal → blue-grey → crimson, flight feathers olive → grey →
near black, lion fur unchanged in 260 and slightly warmer in 261, gold beak and talons unchanged in 260 and slightly
more saturated in 261. Three regions (plumage, flight feathers, fur); ramps per tier by luminance histogram matching
of each region's native pixels in that palette, gain 1.15. Gold is no region: its native ramp read far brighter than
Meshy's paint, so the beak and talons keep the painted gold in all tiers.

## Gates

- Edge stretch (`outliers.py`): Fly ≤ 6.7×, Attack 6.6×, Hit 6.4×, Dead 6.3× (wing root and wrist); Death 10.5× at
  the wing root while the wings fold back (frame 12).
- Floor: airborne clips' lowest vertex 2 cm above the floor; Death/Dead lowest vertex on the floor.
- Viewer: 15 tier/clip switches, no errors; viewer shots in `review/shots/`, renders in `review/tex_v1_fly.png`.

## For the user to review

- Motion is procedural and an interpretation of the native frames, not a frame match.
- Wing tips and raised wings reach ~172 units above the model origin in the Fly cycle, above the native collision
  height 140; like the other flyers, low ceilings can clip the wings.
- UV coverage is 33 % of the atlas (Smart UV islands of the feather sheets); a repack would need a new retexture.

## Install later (not run)

**Reduced version:** [`../mm7_m258_reduce_claude/`](../mm7_m258_reduce_claude/README.md) (2026-10-20) — install its
`export/mm7_m258.glb` (the command below) instead of this one; the binding below is unchanged.

```sh
python3 tools/install_model.py level_generation/creatures/mm7_m258_reduce_claude/export/mm7_m258.glb --world mm7
```

Binding for `assets_dev/worlds/mm7/models/actors.yml` (scale 62.7 = sqrt(mean native front fly-frame area 7,496
units² ÷ model Fly front area 1.905 m²), `scripts/measure_scale.py`; stride: speed 250 × 0.9 s ÷ 62.7):

```yaml
- descriptor: Griffin A
  model: worlds/mm7/models/mm7_m258.glb
  scale: 62.7
  yaw_offset: -1.570796327
  skin: m258_a
  animation:
    sockets: {}
    cast: Attack
    run: Fly
    stride_length: 3.6
    run_stride_length: 3.6
    upper_body_root: Spine2
    events:
      attack_melee: {impact: 0.55}
      attack_ranged: {impact: 0.55}
  clips:
    standing: Fly
    walking: Fly
    attack_melee: Attack
    attack_ranged: Attack
    hit: Hit
    dying: Death
    dead: Dead
    fidget: Fly
# Griffin B / C: the same with skin m258_b / m258_c (all three tiers share the native frame scale 1.3).
```

No in-game check was run (optional for batch E).
