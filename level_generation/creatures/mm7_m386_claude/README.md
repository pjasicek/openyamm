# MM7 Robot (m386) — 2026-10-21

> **Superseded (2026-10-21) by [`../mm7_m386_v2_claude/`](../mm7_m386_v2_claude/README.md).** User review: this
> version reads as a dinosaur skeleton with robot parts; v2 rebuilds it as an all-metal droid (new HD masters and
> Meshy model, gun-shot attack, MeshLab-ladder LOD0 of 5,223 triangles). Install v2; keep this project as the rollback.

Batch H, model 5 ([BATCH_H.md](../mm7_batches/BATCH_H.md)). Identity **mm7:m386**, descriptors **388–390** (Seeker,
Sentinel and Assassin Droid; `Robot A/B/C`), one palette 386 for all tiers, frame scales 1.0 / 1.3 / 1.7. Route:
[non-humanoid playbook](../CLAUDE_QUADRUPED_PLAYBOOK.md), "Rigid hard-surface creatures" (Patrol Unit,
[mm6_rob1_claude](../mm6_rob1_claude/README.md)): one bone per rigid part, parameters per frame. Not installed
(batch rule).

| Item | Value |
|---|---|
| Export | [`export/mm7_m386.glb`](export/mm7_m386.glb), 5.8 MB, sha256 `a3965fef91abe5df15fe2c98a8687534648fc32eebdebd6d8a707d1bb98c39c2` |
| Triangles LOD0 / 1 / 2 / 3 | 6,485 / 3,169 / 1,490 / 633 (Smart Topology 14,719 in 305 pieces) |
| Rig | 23 bones: Body (root, chassis), Gun, Neck1–2, Head, Tail1–8, per leg Leg_XX (sleeve) + Spike_XX; sockets `Socket_Eye`, `Socket_Muzzle` |
| Clips | Standing 1.5 s, Walking 1.25 s (loops), Attack 0.875 s, Hit 0.875 s, Death 0.75 s, Dead 1.0 s, Fidget 0.75 s |
| Maps | 2K base colour (AO graded), 1K normal, 1K metal/rough (R specular mask, glossy, metallic 0), 1K region mask (R steel, G bronze, B rust) |
| Meshy | **15 / 30 credits**: Smart Topology `meshy-t2.5` 15k (5), retexture `meshy-7` four HD views (10) |
| Viewer | [review/viewer](http://127.0.0.1:8912/level_generation/creatures/mm7_m386_claude/review/viewer/) |

## Decision: it walks on four spikes (not a hovering droid)

The batch file calls it "a hovering droid with gun arms". The native evidence says otherwise, so the model walks:
- `monster_data.txt`: Fly = **N** for all three tiers (Move Med/Short), unlike every other creature of the batch;
- separate standing (`m387s`), walking (`m387w`, ten frames) and fidget sprites; in the walk frames the four steel
  spikes change position in a gait and slide in their bronze sleeves while the chassis stays level;
- the spike tips touch the sprite's bottom edge (the anchor) in standing, walking and attack;
- the death frames collapse onto the floor and leave a corpse (`xa`: chassis down, spikes splayed flat), so there is
  no explosion: no `death_effect`.

The "gun arms" are the four sleeved spikes; the ranged weapon is the small ball with a blue coil emitter under the
chassis (attack frame `ad` lights the legs red). Anatomy from the frames: gunmetal chassis with a white front orb,
a robotic raptor skull with green eyes on a vertebra neck, a long curled vertebra tail.

## References

`references_hd/` (Codex, 1536×1024, two runs; records in `generation_runs.json`; inputs only the original bitmaps:
standing views `m386sa0–4` and front/side/rear frames). Gate: four sleeved spikes standing on their tips, raptor
skull with a green eye, segmented neck and curled tail, gunmetal chassis with the white orb, blue emitter under it;
03 faces image left, 04 image right. Codex noted margin shortfalls on the primary and some camera drift in the side
views; nothing is cropped.

## Rig and motion

- `rig_plan.py`: rigid binding of the 305 Meshy pieces (spikes and sleeves by piece, gun and head by region,
  vertebrae to the nearest neck/tail segment, small parts near a sleeve to that leg, the rest to Body); cables from
  the chassis to a sleeve blend per vertex from Body to the leg over 3–9 cm from the sleeve centre. Joints from point
  plots of the mesh (`plot_views.py`) refined to local centroids. Stress poses: `review/stress_sheet.png`.
- Each leg: the sleeve (Leg_XX) turns about its centre; the spike (Spike_XX) slides through it along its axis, as in
  the native walk. `place_leg()` aims the sleeve at the foothold and slides the spike to reach it, so tips stay
  planted in stance.
- `anim_robot.py`: Walking = diagonal pairs FL+RR / FR+RL, duty 0.55, step 0.24 m, lift 7 cm, body bob and roll,
  tail/neck counter-sway; body travel **0.436 m per cycle** (binding `stride_length`). Attack = brace, neck up, gun
  tilts and fires at **0.44 s** (native `ad`) with a recoil jolt. Hit = jolt sideways/back, head whip. Death = shudder,
  spikes splay out, chassis drops onto the floor, neck and tail rest on it (native `xa`); Dead holds it. Fidget = head
  looks left and right (native `fa–ff`). Standing = idle hum with a slow head scan.
- Floor (`clip_check.py` → `review/clips_r1.json`, reduced mesh): spike tips within 1.6 mm of z = 0 in every clip;
  Death/Dead rest at +3 mm (−1 mm on one Death frame).

## Textures and tiers (`compose_robot.py`)

Meshy kept our Smart UV layout (head islands 2.5×). AO grade; classes: metal 9, rubber cables 11, eye/emitter 6.
**Tiers:** all three descriptors use palette 386; the original engine multiplies tiers B and C by the descriptor
`TintColor` (Sentinel `0x93c4ba`, Assassin `0xd8c462`; OpenEnroth `BaseRenderer::BlendColors`). OpenYAMM parses that
column but does not apply it, so the sprites currently show the same colour for all tiers. The model reproduces the
original multiply with region ramps fitted to base × tint over three regions (steel/gunmetal/orb, bronze/brass, rust
plates); the green eye and the blue emitter stay out of every region. Fit mean / p95 (8-bit): steel 1.5–1.9 / 5–7,
bronze 4.5–6.0 / 14–19, rust 4.9–6.6 / 15–18.

## Reduction and size

`reduce_lod0.py 0.33 0.6` after weighting: 14,719 → 6,544 (head 60 %, everything else 33 %; tail tip Tail6–8 and the
neck vertebrae kept, because they broke into dashes at 33 %: `review/r0_*`, `review/r1_*`). Above the ~5k rigid budget
because of the thin vertebrae.

Scale **200**. The silhouette-area method (`measure_scale.py`, Walking vs `m386w?0`) gives 257, but the thin spikes and
vertebrae make the model's area small for its size. Native front height 117 px, front width 137 px and side length
184 px against the model's 0.60 / 0.66 / 0.95 m give 195–209. At 200 the tail top is 122 units (tier A collision
height 120); B/C scale by 1.3 / 1.7 (frame-scale ratio) to 158 / 207 against 140 / 160, as the sprites do.

## Checks

`check_winding.py`: 0 inverted closed parts. `run_creature_review.py check`: 3 tiers × 7 clips, no console errors.
Shots in `review/shots/`. No in-game check (optional in the batch rules).

## Rebuild

`rig_plan.py` → `rig_robot.py` → `anim_robot.py` → `uv_export.py` → `dump_uv3d.py` → (retexture) → `bake_ao.py` →
`compose_robot.py` → `reduce_lod0.py 0.33 0.6 work/uv_r1.blend` → `anim_robot.py work/uv_r1.blend work/uv_r1.blend` →
`scripts/build_runtime.sh TOKEN` → `viewer_manifest.py`.

## Install later (not done)

```sh
python3 tools/install_model.py level_generation/creatures/mm7_m386_claude/export/mm7_m386.glb --world mm7
```

```yaml
# Robot m386: walks on four spikes (Fly N), collapses to a corpse; tiers = original descriptor tints as ramps.
- descriptor: Robot A
  model: worlds/mm7/models/mm7_m386.glb
  scale: 200
  yaw_offset: -1.570796327
  skin: m386_a
  animation:
    cast: Attack
    run: Walking
    stride_length: 0.436
    run_stride_length: 0.436
    upper_body_root: Neck1
    sockets:
      eye_left: Socket_Eye
      muzzle: Socket_Muzzle
    eye_color: [90, 255, 60]
    events:
      attack_melee:
        impact: 0.44
      attack_ranged:
        impact: 0.44
        glow:
        - muzzle
        release: muzzle
  clips:
    standing: Standing
    walking: Walking
    attack_melee: Attack
    attack_ranged: Attack
    hit: Hit
    dying: Death
    dead: Dead
    fidget: Fidget
# Robot B / Robot C: same entry with skin m386_b / m386_c and `scale_reference: Robot A`.
```
