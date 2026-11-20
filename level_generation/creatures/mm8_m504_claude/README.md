# Earth Elemental (MM7 m198 / MM8 m504) — Claude humanoid route, batch L

MM7 batch L model 1 ([BATCH_L.md](../mm7_batches/BATCH_L.md)). One model for both worlds: MM7 235 Clay / 236 Stone / 237
Earth Elemental and MM8 79 Lesser / 80 / 81 Greater Earth Elemental draw the same bitmaps. **Installed 2026-10-21** (the
user asked for it after the batch): the install command and both worlds' bindings are below. Meshy: **30 of 100
credits** (Smart Topology 5, auto-rig 5 for joint estimates, body retexture 10, head retexture 10). User artistic
acceptance is not recorded.

[Review viewer](review/viewer/index.html) (served at
`http://127.0.0.1:8912/level_generation/creatures/mm8_m504_claude/review/viewer/`) · [HD masters](references_hd/selected_views_review.png)
· [head masters](references_head/selected_views_review.png) · [clip candidates (G1)](review/g1_candidates.png),
[more](review/g1_candidates2.png) · [clay clips](review/clips_v5_three_quarter.png) · [stretch at the raise](review/heat_attack15_front.png)

| Item | Value |
|---|---|
| Runtime export | `export/mm8_m504.glb`: skinned meshes `EarthElemental` (living body) and `Rubble` (death pieces), colour LODs body **4,500** / 2,249 / 808 / 279 and rubble **5,132** / 2,564 / 919 / 314 tris + shadow LODs, 3 tier variants `m504_a/b/c` on one merged body+head material (2080x1024 atlases), 7 clips, collapsed-mesh hide keys |
| Portable / editable | `export/mm8_m504_lod0.glb` (full detail, plain materials); `work/rig_v7.blend` (rig, clips, UVs, rubble) |
| Textures | `textures/`: body and head 1K sets, one region (all stone) in both masks, `m504_ramps.json`, class maps (class 11 = stone) |
| Skeleton | 52 `B_*` bones + twist bones, 14 `Rubble_*` bones, `Socket_FistL` / `Socket_FistR` |
| Clips (30 fps) | Standing 3.0 s, Walking 1.2 s (stride 2.205 m), Attack 1.3 s (blow 0.583 s), Hit 0.5 s, Death 1.6 s, Dead 1.0 s, Fidget 4.67 s |

## Native identity, tiers and size

Native frames `m198*` (MM7) = `m504*` (MM8), 120 per family; standing silhouette 199 px. A heavy humanoid of
interlocking brown stone plates: small flat-topped head low between boulder shoulders, oversized fists, column legs on
broad boulder feet. Tier colours from the sprite frame tables (`assets_dev/engine/rendering/sprite_frames/monsters/`):

| World | Descriptor | Group | Palette | Frame scale | Binding scale | Skin |
|---|---|---|---|---:|---:|---|
| MM8 | 79 Earth Elemental A | m505 | 504 brown | 1.5 | 144.55 | m504_a |
| MM8 | 80 Earth Elemental B | m506 | 506 blue-slate | 1.5 | 144.55 | m504_b |
| MM8 | 81 Earth Elemental C | m507 | 507 red | 1.5 | 144.55 | m504_c |
| MM7 | 235 Elemental Earth A | m199 | 504 | 0.9 | 86.73 | m504_a |
| MM7 | 236 Elemental Earth B | m200 | 504 | 1.2 | 115.64 | m504_a |
| MM7 | 237 Elemental Earth C | m201 | 504 | 1.5 | 144.55 | m504_a |

The MM7 tiers share palette 504 (only the size changes), so the MM7 bindings all use skin `m504_a`.
Scale = 199 px × frame scale / 2.065 m (the Standing clip's height).

## Route

1. HD masters (Codex, `references_hd/`, `references_head/`) from the native views, palettes and actions; run 1
   (three-quarter) needed one correction (arms a little closer than 35°, rounded head kept).
2. Smart Topology 15k of `00_three_quarter.png`: one closed 15,792-tri shell plus six 20-vertex flakes
   (`drop_strays.py`). The stone plates are texture and normal map, not geometry.
3. Rig (`scripts/rebuild.sh STAGE=rig`): Meshy auto-rig joints everywhere (the skin ring fits failed on this bulk:
   the left arm's rings merged with the torso; `compose_joints.py`), cloned source frames, hands from the forearm,
   **no finger chains** (the fists are rigid stone on `B_*_Hand`), Meshy weights + shoulder fade + head free of
   the shoulders. Reduced after weighting to 9,000 tris (head and fists protected).
4. Clips (`STAGE=anim`, G1 sheets in `review/`): heavy upright sources chosen over the hunched Mutant set.
5. Textures: body retexture with Meshy's UVs copied back (`transfer_uv.py`), head retexture on its own UVs (the face
   above a mid-neck cut within 20 cm of the neck axis: the boulder shoulders rise beside the head), `compose_m504.py`.
6. `rubble.py` (death), `scripts/build_runtime.sh`, `viewer_tiers.py`, `update_viewer_manifest.py`.

## Clips

| Clip | Source and adaptation |
|---|---|
| Standing | Mixamo Standard Idle, upper arms out 14° (native holds the fists away from the thighs) |
| Walking | Mixamo Orc Walk (heavy stomp), arms out 10°; per-frame floor pass with loop-wrapped smoothing (the long boulder feet sank 9 cm at heel strike) |
| Attack | Mixamo Zombie Attack (two-handed overhead) source 0.65–3.2 s, planted with 20 % of its leg motion, ×1.4; arms out 15° and forward 35° over the raise (native `m198ab`/`ac`: fists overhead and apart), then `fist_clear.py` keeps the fists apart and clear of the head; smash in front at **0.583 s**; eased back to Standing. Also the **cast** (native shoot = attack), charging and releasing at the fist sockets |
| Hit | Humanoid set Unarmed get-hit front 1, arms out 6° |
| Death | Mixamo Standing React Death Backward (blended in) until **0.4 s**, then the body breaks into 14 rigid capped stone pieces (head, chest, belly, pelvis, per side upper arm, forearm, fist, thigh, shin+foot) that burst outward/backward, fall, bounce softly and turn onto their long sides; all at rest 1.2 s after the break (native `m198da..dd`) |
| Dead | the rubble at rest, scattered up to 1.3 m from the origin (native corpse `m198xa`) |
| Fidget | Mixamo Mutant Flexing Muscles, planted, arms out 10° (+10° over frames 34–56); fists kept off the thighs |

**Rubble swap.** `Rubble` is a copy of the body cut by dominant bone and capped (fans in the stone of the body atlas),
100 % on its own root-level bones. Every clip keys those bones at scale 1e-4; after the break `B_Pelvis` takes that
scale. `tools/model_hide_collapsed_meshes.py` then keys the hidden node's scale to 0: the body draws everywhere but
Death after 0.433 s and Dead; the rubble draws only from 0.367 s of Death and in Dead (one frame overlap at the break).
A living elemental costs the body's 4,500 triangles only. LOD0 halved on the textured master by `halve_lod0.py` (user,
2026-10-20: "reduce tris now"; collapse before the armature, UV-seam vertices weighted 0.8, small pieces kept whole, the
head protected).

## Gates (final export)

- Halved LOD0 (`halve_lod0.py`, 2026-10-20), edge stretch p99: Standing 1.30, Walking 2.10, Attack 2.19, Hit 1.81,
  Fidget 1.97. Viewer, winding and textured renders rechecked.
- G6 contacts (closed shell, inside test): Standing 0, Walking 1.7 cm (fist vs thigh, one frame), Attack 0, Fidget
  2.6 cm, Hit 0. Before `fist_clear.py` the source smash pressed the fists 9–12 cm into each other and into the head.
- Soles: grounded feet −1.2…+1.4 cm in every clip.
- Edge stretch p99 (textured master, after `armpit_smooth.py`): Standing 1.27, Walking 1.83, Attack 2.00, Fidget 2.26,
  Hit 1.86. User review (2026-10-20) found the stone smeared under the raised arms in the Attack: Meshy gave the
  clavicles 60–77 % of the chest and lats down to 26 cm below the shoulder. `armpit_smooth.py` (in `build_runtime.sh`)
  fades the clavicle weight with distance from the shoulder joint (full within 10 cm, none beyond 25 cm; the rest goes
  to the spine bones by height) and smooths the torso weights: Attack p99 2.44 → 2.00, edges above 2× 246 → 135
  (a smaller raise changed nothing). No folds or collapse in the clay and textured frames.
- Rubble: 14 closed manifold pieces (27 caps), every piece at rest on the floor (lowest point 0.0 cm).
- `check_winding.py`: 0 inverted closed parts. Viewer: 3 tiers × 7 clips, no console errors. Textured EEVEE frames
  of every tier, the attack and the death inspected (`work/r_glb/`). Not checked in game (optional for batch L).

## Installed (2026-10-21, user request after the batch)

```sh
python3 tools/install_model.py level_generation/creatures/mm8_m504_claude/export/mm8_m504.glb --world mm8
```

MM8 binding for `assets_dev/worlds/mm8/models/actors.yml` (repeat for `Earth Elemental B` / `m504_b` and
`Earth Elemental C` / `m504_c`, same scale):

```yaml
# Earth Elemental m504 (79-81): heavy stone humanoid, two-fisted smash, crumbling rubble death. Casts with the attack.
- descriptor: Earth Elemental A
  model: worlds/mm8/models/mm8_m504.glb
  scale: 144.55
  yaw_offset: -1.570796327
  skin: m504_a
  animation:
    cast: Attack
    run: Walking
    stride_length: 2.205
    run_stride_length: 2.205
    upper_body_root: B_Spine
    look:
      nodes: [B_Neck, B_Head]
      max_yaw_degrees: 35
      max_pitch_degrees: 20
    sockets:
      fist_l: Socket_FistL
      fist_r: Socket_FistR
    events:
      attack_melee: {impact: 0.583}
      attack_ranged: {impact: 0.583, release: fist_r}
      cast: {impact: 0.583, glow: [fist_l, fist_r], release: fist_r}
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

MM7 bindings in `assets_dev/worlds/mm7/models/actors.yml`, pointing to the same installed model (no MM7 copy):
`Elemental Earth A` scale **86.73**, `Elemental Earth B` **115.64**, `Elemental Earth C` **144.55**, all with `skin:
m504_a` and otherwise the block above. Every world package is mounted together (the loader enumerates `worlds/*`), so
the MM8 path resolves in MM7. MM8's Earth Elemental A–C were bound to the MM6 model (`mm6_ert.glb`) in MM6's
`actors.yml` as an interim (2026-10-19); the user chose this model instead (2026-10-21) and that interim binding was
removed.

Speeds: MM8 110/130/200 units/s play the walk at 0.41×/0.49×/0.75× (slow, heavy); MM7 220/240/260 at
1.38×/1.13×/0.98×. MM7 A (220) is above its run threshold (2.4 × 86.73 = 208), so `run: Walking` plays the same walk.

## For the user to review

- Smart Topology made a smooth muscular body; the stone plates and cracks are only in the texture and normal map.
- The rubble pieces are cut along the skin weights, so a piece's edge follows the joint region, and the caps are fans
  textured with a square of body stone. The break pops slightly (rigid pieces replace the skinned pose in one frame).
- A small smooth patch remains at the inner upper arm at the top of the raise; the head (Meshy) is rounder than the
  native's flat top.
- Tier brightness: ramps at 1.35× the native median (the sprites carry baked shading); one number in `compose_m504.py`.

## Replay

Claim the project, then `scripts/rebuild.sh` (`STAGE=rig`, then `STAGE=anim`), `export_uploads.py`, Meshy jobs
(`requests/`), `transfer_uv.py -- work/rig_v5h.blend meshy/retexture_v1 work/rig_v6.blend` and the same with
`meshy/head_retexture_v1 ... HeadUV`, then `scripts/build_runtime.sh`, `viewer_tiers.py`, `update_viewer_manifest.py`.

## Head bob (2026-10-22)

The installed source of `mm8_m504` now carries walk/run clips reshaped by [head_bob_claude](../head_bob_claude/README.md)
(`bob_fix.py`: pelvis bob rescaled or evened, legs solved to the original foot paths). `export/` holds the pre-bob GLB:
after a rebuild here, rerun `head_bob_claude/run_jobs.py --only mm8_m504` on the new export (copy it to
`head_bob_claude/work/mm8/` first) before installing.

## Gait rollout (2026-10-31)

[Gait rollout package h15](../gait_rollout_20261031/h15/README.md) appended three clips to the installed
`mm8_m504.glb`: `Walk2` (slow heavy walk, 1.50 s, stride 1.4426), `Jog` (0.82 s, 2.4246) and `Run` (0.74 s, 3.1334),
from humanoid-set loops, aligned to Walking, rubble hide keys copied from Walking. Bindings: MM7 Elemental Earth A-C
`run: Run`; MM8 Earth Elemental A/B `walking: Walk2` (chase stays on Walking), C `walking: Walk2`, `run: Jog`,
`sprint: Run` (MAW). Rebuild: `gait_rollout_20261031/h15/scripts/rebuild.sh mm8_m504`. A far-LOD repair, head-bob
rerun or re-export must re-graft these clips (copy the new source over `h15/work/mm8_m504_pre_gait.glb` and rebuild).
