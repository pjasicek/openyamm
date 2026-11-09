# MM7 Gargoyle (m234) — Claude rig-first project

Batch G, model 2 ([batch file](../mm7_batches/BATCH_G.md)). Descriptors 262 Stone Gargoyle (palette 235, green
membranes), 263 Marble Gargoyle (236, blue) and 264 Obsidian Gargoyle (237, red). **Exported, not installed** (batch
rule). Status: technically complete, pending user review.

[Review viewer](review/viewer/index.html) (served at
`http://127.0.0.1:8912/level_generation/creatures/mm7_m234_claude/review/viewer/`) · [viewer shots](review/shots/) ·
[HD masters](references_hd/selected_views_review.png) · [head masters](references_head/) · [G1 clip choice](review/g1/G1.md)

| Item | Value |
|---|---|
| Export | `export/mm7_m234.glb` (body with wings and tail, LODs, shadow LODs, 3 tier variants `m234_a/b/c`, head material merged; no attachments); editable master `work/rig_v6.blend` |
| Triangles | LOD0/1/2/3 10,812 / 5,405 / 1,942 / 630 (body 7,688 after reduction, wings 2,600, tail 524) |
| Mesh | Smart Topology 15k of the HD three-quarter master: one stone shell (body, wing arms and struts, tail), two membrane sheets, the tail spade, eyes and 17 teeth; 8 slivers (< 60 triangles) deleted |
| Rig | 52 `B_*` bones cloned from the humanoid set + twist bones; 12 wing bones (`Wing_<s>_1/2` arm, `Wing_<s>_F1..F4` finger struts); 8 tail bones (`Tail_1..8`) |
| Clips (30 fps) | Standing Mixamo Mutant Breathing Idle (4.03 s); Walking authored hovering flight (1.0 s); Attack Mixamo Mutant Punch planted, 0.2 s lead (1.3 s, blow 0.95 s); Hit set Unarmed get-hit F1 (0.5 s); Death Mixamo Falling Back Death, travel halved (2.2 s); Dead; Fidget Mixamo Mutant Flexing Muscles planted (4.67 s) |
| Textures | body 1K + head 1K (Meshy retextures from the HD masters / head turnaround), AO graded, stone graded toward the native (x 0.80/0.76/0.84), ORM red = per-class specular mask; one region (the wing membranes) |
| Meshy credits | **30 of 100**: Smart Topology 5, auto-rig 5 (spine unusable, see Rig), body retexture 10, head retexture 10 |

## Install later (not run)

```sh
python3 tools/install_model.py level_generation/creatures/mm7_m234_claude/export/mm7_m234.glb --world mm7
```

Then add [actors_m234_binding.yml](actors_m234_binding.yml) to `assets_dev/worlds/mm7/models/actors.yml` (scale 91.4 =
native stand 151 px x 1.099991 over the 1.818 m Standing pose; all tiers fly above the run threshold, so `run: Walking`;
stride 3.28 m = the native 1.0 s wing beat at tier A's speed; blow 0.95 s; head look on B_Neck/B_Head).

## Anatomy decisions

- **Humanoid route, arm gate applies.** Two arms with five clawed digits each (thumb + four fingers, found by
  connectivity), so the humanoid source-frame rig and its arm/hand gates apply. No held prop: the fingers keep the
  source clips' own curl (clawed, open hands); no grip solve.
- **Long clawed feet, planted flat** (user review 2026-10-20). The humanoid `Foot` joint is the hock (ring fit) and
  `Toe0` the ball of the toes, so the Foot segment is the long foot (hock -> ball). The native standing and attack
  frames stand the whole foot flat on the ground with the toes and claws down; `foot_flat.py` keeps it so (below).
- **Horns, ears, teeth** ride the head: horns and ears are part of the stone shell (head weights), eyes and the 17
  teeth are rigid on B_Head.
- **Bat wings** (`split_parts.py`, `wing_probe.py`, `wings_rig_bat.py`): the wing arms and struts are grown from the
  wing tips on the shell (behind the back plane or beyond the arms), the membranes are their own sheets. Per side an arm
  chain root -> elbow -> wrist (the hooked claw) and four finger bones from the wrist to the strut tips; every vertex
  takes its two nearest bone segments, the root fades into B_Spine2. The Meshy auto-rig saw a wingless, tailless upload.
- **Tail** (`tail_rig.py`): eight bones along the geodesic centreline from the root to the spade; weights by arc
  position, the root blends into B_Pelvis. Motion: sway with a phase lag growing to the tip, a lash in the attack, a
  per-segment floor rule, and in the death a settle onto the floor.
- **Wing motion** (`appendages_anim.py`, rotations about rest axes; `fold_probe.py` measures them): Standing and the
  ends of every one-shot clip FOLD the wings as the native sa frames (arm raised beside the shoulder, the wrist claws by
  the horns, the fingers closed into a fan hanging down beside the body); Walking beats on the native 1.0 s cycle (top
  at wa, fingers spread on the downstroke and half closed on the upstroke); Attack, Hit and Fidget spread them (native
  attack/hit/fidget frames); Death spreads them with the fall and lays them flat beside the corpse (searched corpse pose,
  floor rule per frame).
- **Hover** (`author_flight.py`, native wa..wh): the body upright (the hunched idle tilted back 25 deg), legs dangling
  together (adducted 9 deg), feet pointed; no foot contact.

## Rig notes (what went wrong and was fixed)

- Meshy's auto-rig put the spine and clavicles 26 cm in front of the chest and the shoulders 10 cm apart in height;
  `joints_m234.py` composes the trunk from the mesh (torso centreline at the source's relative heights), the arms from
  symmetric ring fits, hips/knees from Meshy and the fits. Meshy's skin weights were still usable.
- The hand frame from the width axis was flipped 150-160 deg in the first pass (thumb search widened:
  `THUMB_NEAR=0.30`, `HAND_R=0.26`); the knuckle-line pass fixed it (6-8 deg from the forearm).
- **Feet angled (user review 2026-10-20, `review/user_feedback_20261020/feet_angled.png`):** the world-rotation retarget
  gave our long Foot segment the human foot's direction (~40 deg off its rest in the idle, standing on the heel pad,
  the sole spread 14.6 cm against 3.8 cm at rest) and the source toe channels curled the claws; `foot_level.py` could
  not see it (its heel/toe references fell on the outer toe claw). `foot_flat.py` (after the clip timing, every ground
  clip): leg IK puts each planted hock at its rest height, the foot takes its rest orientation turned only by the
  knee's heading (in every frame, so stepping feet stay level), the toes stay at rest. The earlier 8.2 cm float was
  the same fault (the tilted foot stood on its heel); `floor_fix.py` now measures 0.
- First wing fold overshot (the arm fan added to the finger fan: the fingers pointed up and inward over the head).

## Gates (final master `work/rig_v6.blend`)

- G3: joints symmetric and inside the limbs (`review/bones_wt_*.png` for the wing and tail chains).
- G4: arm stretch p99 <= 2.18 (attack), max 3.45 on the right upper arm.
- G5: hand stretch <= 3.59x (right thumb root in the attack), left <= 2.21x.
- G6: no contacts in Standing, Walking, Attack, Hit. **Fidget**: the right hand 4.8 cm into the chest at 3.2 s (the
  flex presses the claws to the chest); **Death**: the right hand 5.8 cm into the lying body for about a second.
- Feet (`sole_probe.py`, `sole_flat.py`, 2026-10-20): lowest sole 0.0-0.3 cm in Standing, Attack, Fidget and Hit
  (attack steps lift up to 2.3 cm, the hit's stagger 4.7 cm); every planted sole as flat as at rest (spread 3.8-4.0 cm,
  rest 3.8-4.0), the claws on the ground; flight lowest point 5.6 cm (no contact); tail segments >= 2.5 cm.
- Viewer: `tools/run_creature_review.py ... check`: 3 tiers x 7 clips, no console errors. Not checked in game.

## Known limits / for user review

- The Falling Back Death kicks both legs straight up for about 0.3 s before the body lands (Mixamo backward fall).
- The inner membrane by each armpit has a few torn faces from Smart Topology (visible in close-ups).
- The descriptors carry a TintColor for Marble (0xebce75) and Obsidian (0x586280); the native sprites do not show a
  stone tint (only the membranes change), so it is not applied. A second region on the stone would add it if wanted.
- The tail is skinned on bones (no simulation); the flight's hanging tail sways on the beat.

## Replay

`TOKEN=<lease> STAGE=rig scripts/rebuild.sh` (split, garments, joints, rig + fingers), `STAGE=anim DEATH_UNTIL=12 LEAD=0.2
scripts/rebuild.sh`, `STAGE=wings scripts/rebuild.sh` (flat feet, floor fix, hover, wing and tail rigs and motion, join), texture
chain once (`export_uploads.py`, Meshy `retexture_v1` and `head_retexture_v1`, `transfer_uv.py -- work/rig_v5h.blend
meshy/retexture_v1 work/rig_v6.blend`), then `MESH_NODE=M234 scripts/build_runtime.sh`, `viewer_tiers.py`,
`update_viewer_manifest.py`. Every step runs memory-capped (`scripts/cap.sh`, `scripts/b.sh`).
