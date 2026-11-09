# MM7 Mage (m274) — Claude 3D model (batch B, 2026-10-20)

Sorcerer / Wizard / Archmage (monsters 292/293/294, descriptors `Mage A/B/C`, sprite palettes 275/276/277), with the
staff as a separate attachment. Same chain as the [Moon](../mm7_m170_claude/README.md) and
[Sun](../mm7_m174_claude/README.md) Clerics (settings in `creature.json`). **Not installed** (batch rule).
Status: technically complete, agent-reviewed in the viewer; user artistic acceptance pending.
[Review viewer](http://127.0.0.1:8912/level_generation/creatures/mm7_m274_claude/review/viewer/).

## Deliverables (`export/`)

| File | What |
|---|---|
| `mm7_m274.glb` | runtime body: LODs 10,188 / 5,091 / 1,833 / 609 (+ staff 664 / 332 / 118 / 37 split off), tiers `m274_a/b/c` (robe green/violet/red, cape and collar magenta shades, beard ginger/dark grey/white), head set merged |
| `mm7_m274_staff.glb` | staff attachment on node `Staff` (child of the left hand); `Socket_Staff_Head` at the gem |
| `mm7_m274_lod0.glb`, `mm7_m274.blend` | portable LOD0, editable master |
| `actors_binding.yml` | scale 108.7 (195 px native body height without the staff / 1.794 m), run → Walking, stride 1.658, Attack release 0.483 s (right palm), Cast release 0.733 s (gem at its highest) |

Install later (not run): `tools/install_model.py export/mm7_m274.glb --world mm7` and `export/mm7_m274_staff.glb`,
then the binding and a tier/height + staff regression.

## Model

- **HD masters**: `00` = Codex v2 (true three-quarter, left fist with a vertical grip opening, right hand open);
  01–04 run 2. Head turnaround: three of four views used (the back view drew a collar and black hair; the back of the
  head is hidden by the tall collar).
- **Geometry**: Smart Topology **v2** with `pose_mode` empty: v1 (`a-pose`) re-posed the hands and opened the staff
  fist. 14 parts; legs kept (the shoes show under the hem); reduced to 10,188.
- **Rig**: source-frame rig; the hand frames' thumb side is forced forward (A-pose, palms toward the thighs: the
  wider-side guess flipped both hands 150°+); fists rigid (no finger weights).
- **Weights**: sleeves below the armpit split (z 1.16) take only their own arm's bones, ramped in over 5 cm (Meshy
  gave the long bell sleeves up to 0.48 pelvis weight and the robe chains claimed their hems: 12× stretch); torso
  below the split loses its arm weight; yoke/mantle smoothed; shoes keep their leg weights.
- **Cloth**: robe 12 × 4 chains (leg capsules ×1.3, floor 6 cm: real legs), the star-and-moon cape 5 × 4 sheet chains
  from the chest (`sheet_rig.py`), both DROP_FLAT for the corpse.
- **Staff** (`make_staff.py`, `staff_texture.py`): modelled from the native (1.62 m, red-brown shaft, gold bands and
  butt, gold ring with a red faceted gem), seated in the left fist on the grip tunnel found geometrically
  (`grip_from_fist.py`: enclosure 1.0, 20.7 mm clearance) by `seat_staff.py`; carried upright in Standing, Walking,
  Hit and Attack (`author_carry.py`, the natm global elbow/roll solver), raised overhead in Cast.

## Clips

| Clip | Source |
|---|---|
| Standing / Walking | set Relax Idle / Relax Walk Forward, arms abducted 6°, staff carry |
| Attack 1.267 s | set Unarmed Cast R Attack 1 (right-hand push), planted, staff held; release 0.483 s |
| Cast 1.3 s | set Unarmed Cast L Buff 1 (the staff hand rises), planted; gem highest at 0.733 s |
| Hit 0.5 s | set Unarmed Get Hit F1, planted, staff held |
| Death 2.0 s / Dead | set Relax Lay Down (kneels, lies down; the native falls backwards), staff in hand |
| Fidget 2.0 s | authored (`staff_fidget.py`): the staff comes in front, held upright with both hands (native fa–fd) |

## Gates (`review/gates_v5.json`)

Arm stretch p99: Standing/Walking/Fidget ≤ 1.89; Attack 2.42/2.14, Cast 2.44/1.94, Hit 2.79/2.14 (L/R; over the ~2
target at the armpit junction under the gold yoke, worst edges 3–5× on a few vertices — visible only as a slight crease
in the viewer); Death 3.03 lying. Wrist swing ≤ 48° except Death 64° and Fidget 70° (the two-handed staff hold); robe
p99 ≤ 1.54 standing, 3.4 in the death. Viewer check: 24 switches, no console errors.

## Textures (`scripts/compose_m274.py`)

Body 1K + head 1K + staff 255×512. Three tier regions with ramps from the indexed bitmaps (indices from
`../mm7_m274/variants.json`): R robe green (161–177), G cape and collar magenta (214–233), B beard (137–155, in the head
set's own mask; body and head share the ramp list as `merge_head_material.py` requires). Gold re-graded.

Meshy: **35 credits** (Smart Topology v1 5 — superseded, v2 5, auto-rig 5, body retexture 10, head retexture 10;
v1 was replaced because the A-pose mode opened the fist).

## Known limits / for review

- The head is nearly bald on top (Meshy's shape; the native has receding swept-back hair).
- The cape's pink reads brighter than the native magenta.
- Arm stretch at the yoke in Attack/Cast/Hit slightly over the target (see Gates).
- The native death falls backwards; Relax Lay Down kneels and lies on the side.

## Reproduce

`TOK=<lease> scripts/rebuild.sh all`; texture chain (`export_uploads.py`, `requests/`, `transfer_uv.py`,
`uv_raster.py` ×2, `bake_ao_natm.py`, `compose_m274.py`, `staff_texture.py m274`); `TOK=<lease> scripts/build_runtime.sh`;
`viewer_tiers.py`, `update_viewer_manifest.py`.

## Revision 2026-10-20 (user review)

- Attack / Cast: `face_forward.py` (after `plant.py`) turns the pelvis, spine, neck and head back toward the front
  per frame; the set's casts and punches turned the head 45–65° to the side. Head yaw is now 0°, and the arm gates
  held or improved.
- Fidget: `staff_fidget.py` solves both arms for the full pose and blends them in from the clip's own arm rotations (bone-local slerp); solving partway twisted the free arm's upper arm in the first frames.

## Reduction (2026-10-20)

A reduced body (LOD0 10,188 -> 8,228, no retexture, staff unchanged) is in
[`../mm7_m274_reduce_claude/`](../mm7_m274_reduce_claude/README.md), awaiting user review; install its
`export/mm7_m274.glb` in place of this one if accepted.
- Feet: `flatten_feet.py` (from the Warlock; before `robe_sim.py`, every clip except Death/Dead) levels the grounded
  feet and lifts sunken ankles to rest height: the planted set clips left the shoes 3.5-10 cm under the floor. Soles
  now sit within 1 cm of it.
- Cast staff flick (user review: "really abrupt"): the set's Unarmed Cast L Buff 1 flicks the staff hand up at 12-16
  m/s for two frames. `retime_speed.py` (after `caster_timing.py`) retimes the clip so the hand stays under 5 m/s,
  spreading the flick over about six frames. The rest of the clip runs 8.8 % faster, so the length is unchanged. The
  gem's top, and so the cast release, moves to 0.667 s. `smooth_bones.py` smooths the trunk and head in Attack and
  Cast, as on the Monk.

## Installed 2026-10-20

The reduction (`../mm7_m274_reduce_claude/export/`) is installed through `../mm7_batches/BATCH_B_stage/` (assets_source + runtime copy, bindings in `assets_dev/worlds/mm7/models/actors.yml`). Rollback: `tools/install_model.py level_generation/creatures/mm7_m274_claude/export/mm7_m274.glb --world mm7` (the production export, byte-identical to the reduction's `work/mm7_m274_source_pre_reduce.glb`).
