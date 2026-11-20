# MM7 Spider (m402) — Claude 3D model, batch E

Giant Spider / Venomous Spider / Widowmaker (monsters 400–402, sprite groups 7m403/m404/7m405, palettes 66/67/68).
Batch E ([../mm7_batches/BATCH_E.md](../mm7_batches/BATCH_E.md)): the model stops at project exports; nothing is
installed or bound.

![tiers in the review viewer above the native palettes](review/tiers_vs_native.png)

| Item | Value |
|---|---|
| Export | `export/mm7_m402.glb` (LOD0–3 + shadow LODs, three tier variants sharing every image) |
| Editable sources | `work/rig_v1.blend` (rig), `work/anim_v2u.blend` (rig + clips + UVs, exported), `export/mm7_m402_lod0.glb` |
| Triangles LOD0/1/2/3 | 13,808 / 6,899 / 2,479 / 822 |
| Skeleton | 28 bones: Thorax (root), Abdomen, Fang_L/R, per leg L1–L4 / R1–R4 (front to back) Femur, Tibia, Tarsus |
| Clips (30 fps) | Standing 2.0 s, Walking 1.0 s (stride 0.9 m), Running 0.6 s (1.4 m), Attack 1.0 s (impact 0.55 s), Hit 0.75 s, Death 1.2 s, Dead 1.0 s, Fidget 1.0 s |
| Textures | one atlas: 2K base colour, 1K normal / ORM / region mask; cephalothorax and fangs at 2×; one region (abdomen) |
| Meshy credits | **15 of 100**: Smart Topology 5, retexture 10 (our UVs) |
| Viewer | `http://127.0.0.1:8912/level_generation/creatures/mm7_m402_claude/review/viewer/index.html` — check: 3 tiers × 8 clips, no console errors |

## Anatomy decisions

- **Eight legs, each on its own chain.** Quadruped playbook, spider section (`mm6_spi1_claude`). Unlike the MM6
  spider, Smart Topology fused each leg into ONE piece, so every leg gets a Femur/Tibia/Tarsus chain whose joints
  are measured on the piece (`work/leg_joints.json`: hip = closest point to the body, knee = top of the centreline,
  foot = farthest low point, ankle 62 % of the way knee → foot) and weights by the closest point on the chain
  (4 cm blend, smoothed over mesh edges). The red hair-fringe cards copy their leg.
- **Extras removed.** Meshy also returned a ninth leg along the midline under the abdomen and a short stub; both (and
  the fringe card hanging on the stub) are deleted in `rig_spider.py`, leaving the native eight.
- **Feet stay planted:** two-bone IK on symmetric footholds, all on the floor (the rest legs are uneven, one rear foot
  14 cm up); alternating tetrapod gait (L1 R2 L3 R4 / R1 L2 R3 L4) on the native 1.0 s cycle; the body rides
  1.6 cm higher in the gait so the low abdomen never grazes the floor.
- **Attack** (native `m402ab/ac`): rears up with the front legs raised and fangs spread, then lunges and bites.
  **Death** (`m402da0`–`dd0`, corpse `xa0`): rears with the front legs flailing, then collapses flat with the legs
  splayed (the MM6 spider rolled over; MM7 does not).

## Route (replay)

1. HD masters (`references_hd/`, Codex, gated); native frames through the three palettes (`scripts/native_palettes.py`).
2. Smart Topology 15k (15,381 triangles); `step1_clean.py` normalises the leg span to 2.4 m.
3. `rig_spider.py` → `work/rig_v1.blend` (13,808 triangles after the extras are removed).
4. `anim_spider.py work/rig_v1.blend work/anim_v1.blend`; `uv_export.py work/anim_v1.blend work/anim_v2u.blend`
   (deterministic: the re-run upload is byte-identical to `texturing/m402_upload_sent.glb`).
5. Retexture (`requests/retexture_v1.json`), `uv_raster.py` (1K, 2K), `bake_ao.py`, `compose_m402.py`.
6. `scripts/build_runtime.sh <token>`; viewer `viewer_tiers.py`, `update_viewer_manifest.py`.

## Tiers

Only the glossy abdomen changes (dark green → dark blue → dark red); legs, fringes, the skull pattern and eyes stay.
One region; the ramp takes hue and saturation from each palette's abdomen pixels and the luminance from the texel
scaled to the native mean × 1.25 (manticore rule). The abdomen keeps a strong specular class (glossy).

## Gates

- Edge stretch (`outliers.py`): ≤ 2.1× in every clip.
- Floor: Standing/Walking/Running/Attack lowest vertex ≥ 0 (walk 0.1 cm, run 1.5 cm); the corpse rests on its legs
  and abdomen at z = 0.
- Viewer: 24 tier/clip switches, no errors; shots in `review/shots/`.

## For the user to review

- Motion is procedural and an interpretation of the native frames.
- The red leg fringes are Meshy's brighter red (not a tier region); the native fringes are darker.

## Install later (not run)

**Reduced version:** [`../mm7_m402_reduce_claude/`](../mm7_m402_reduce_claude/README.md) (2026-10-20) — install its
`export/mm7_m402.glb` (the command below) instead of this one; the binding below is unchanged.

```sh
python3 tools/install_model.py level_generation/creatures/mm7_m402_reduce_claude/export/mm7_m402.glb --world mm7
```

Binding for `assets_dev/worlds/mm7/models/actors.yml` (scale 100.4 = sqrt(native front standing/walk area 10,428
units² ÷ model Standing front area 1.035 m²), `scripts/measure_scale.py`; all tiers share frame scale 1.4):

```yaml
- descriptor: Spider A
  model: worlds/mm7/models/mm7_m402.glb
  scale: 100.4
  yaw_offset: -1.570796327
  skin: m402_a
  animation:
    sockets: {}
    cast: Attack
    run: Running
    stride_length: 0.9
    run_stride_length: 1.4
    upper_body_root: Thorax
    events:
      attack_melee: {impact: 0.55}
      attack_ranged: {impact: 0.55}
  clips:
    standing: Standing
    walking: Walking
    attack_melee: Attack
    attack_ranged: Attack
    hit: Hit
    dying: Death
    dead: Dead
    fidget: Fidget
# Spider B / C: the same with skin m402_b / m402_c.
```

No in-game check was run (optional for batch E).

## Gait pass: Walk2 and Run2 (2026-10-21)

[Creature post-process](../CREATURE_POSTPROCESS.md) step 3. The game plays one walk/run loop per stride of travel; the
old Walking (0.9 m) and Running (1.4 m) loops played at 1.1–1.3× wandering and 2.2–2.6× chasing.
`scripts/gait2_m402.py` (after `../mm6_spi1_claude/scripts/gait2_spi1.py`) authors `Walk2` and `Run2` for the
`gait_gate.py` fit ranges (walk 1.99–3.45, run 3.98–6.91 model units/s):

| Clip | Length | Stride (binding) | Authored speed | Duty (front pair) | Sweep per stance |
|---|---|---|---|---|---|
| Walk2 | 0.4167 s (25 keys at 60 fps) | 1.0917 m | 2.62 | 0.55 (0.44) | 0.60 m |
| Run2 | 0.300 s (18 keys) | 1.572 m | 5.24 | 0.45 (0.36) | 0.71 m |

- Tetrapod with a small metachronal lead and per-leg planned footholds, as in the MM6 spider.
- The front pair has a shorter stance (`pair_duty`). It sweeps less ground, so R1 does not fold its tibia flat.
- Each planted tarsus tip sits on the floor at its own height (the rest legs are uneven).
- The abdomen bounces upward only, because it rests on the floor. The body is raised until the thorax, abdomen and palps
  clear the floor by 5 mm: +3.2 cm in Walk2, +5.3 cm in Run2. Pitching the body for the run drove the long palps or
  the abdomen tip through the floor.
- **Hanging fringe cards.** In the reduced export, cards that hang from tibiae L1/L2/L3/R1/R2/R3 reach the floor at
  rest, because they were re-rigged onto their legs (`../mm7_m402_reduce_claude/`). Any tibia pitch pushes them
  through the floor (R1: -4.1 cm). The script reads their bind positions from that export. When a card would dip
  below -5 mm, it raises the planted foot instead, by up to R1 3.5 cm, R2 1.7 cm and L2 0.9 cm at the worst frame of
  the stance. These are under 4 world units at scale 100.4.
- The clips are grafted onto the installed export with `../claude_shared/graft_clips.py` (joint rests checked).

```sh
blender -b --factory-startup -P scripts/gait2_m402.py -- work/gait2_clips.glb     # also saves work/gait2.blend
python3 ../claude_shared/graft_clips.py ../mm7_m402_reduce_claude/export/mm7_m402.glb work/gait2_clips.glb \
  ../mm7_m402_reduce_claude/export/mm7_m402_gait.glb --clip Walk2 --clip Run2
```

Gate (`--set walking=Walk2 --set run=Run2 --set stride_length=1.0917 --set run_stride_length=1.572`) passed.
- The vertex strides measured 1.018 and 1.484, within 7 % of the bindings. Cards near the floor dilute the median; the
  planted tips move at exactly the binding stride.
- The window was ×0.99–1.14 on every tier, and the floor check was ok.

## Gait rollout: Sprint (2026-10-31)

[Gait rollout package q1](../gait_rollout_20261031/q1/README.md) added `Sprint` for MAW's chase. Before, Run2 played
it at ×1.63-1.71. The script is `../gait_rollout_20261031/q1/scripts/sprint_m402.py`, a copy of
`scripts/gait2_m402.py` with only a Sprint.

- The same tetrapod, with duty 0.33 (front pair 0.26).
- Run2's sweep, 0.73 m.
- 0.2667 s, stride 2.2027, authored speed 8.26.
- The hanging fringe cards are read from the installed source.

It was grafted onto the installed source; the existing clips are byte-identical. Binding: `sprint: Sprint`,
`sprint_stride_length: 2.2027` (authored, as for Walk2 and Run2). The gate passed: MAW chase ×1.04-1.09.

```sh
cd ../gait_rollout_20261031/q1
blender -b --factory-startup -P scripts/sprint_m402.py -- work/m402_clips.glb
python3 ../../claude_shared/graft_clips.py work/rollback/mm7_m402.glb work/m402_clips.glb export/mm7_m402.glb --clip Sprint
```

A far-LOD repair rerun (`lod_repair_claude`) must re-graft Walk2, Run2 and Sprint.
