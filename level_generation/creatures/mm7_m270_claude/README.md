# MM7 Lich (m270) — Claude rig-first project

Batch D, model 3 ([batch file](../mm7_batches/BATCH_D.md)). Descriptors 289 Lich (palette 271, blue-violet chain),
290 Power Lich (272, silver chain) and 291 Lich King (273, rose-gold chain). **Installed 2026-10-20** in `assets_source/worlds/mm7/models/` and `assets_dev/worlds/mm7/models/` (bindings in its `actors.yml`).
Status: technically complete, pending user review.

[Review viewer](review/viewer/index.html) (served at
`http://127.0.0.1:8912/level_generation/creatures/mm7_m270_claude/review/viewer/`) ·
[clip sheets](review/clips_three_quarter.png) · [attack, front](review/clips_attack_front.png) ·
[HD masters](references_hd/selected_views_review.png) · [head masters](references_head/selected_views_review.png)

| Item | Value |
|---|---|
| Exports | `export/mm7_m270.glb` (body, LODs, 3 tier variants, head merged), `export/mm7_m270_staff.glb` (attachment on `Staff`); editable master `work/rig_v6.blend` (MIRRORED, see below) |
| Triangles | body LOD0/1/2/3 7,830 / 3,895 / 1,389 / 451 (incl. the 776-triangle staff before the split; was 10,737 / 5,350 / 1,910 / 617). Second cut on the textured master (`reduce_textured.py`, user review 2026-10-20): skull + coif 1,667 -> 1,200, crown 806 -> 560, arms 2,600 -> 1,870 (bony hands and fingers protected), skirt 999 -> 700, hidden legs 700 -> 264 (shoes protected), plates and belt about -25 % |
| Mesh | Smart Topology of the flipped HD three-quarter master: separate plate, pauldrons, cuffs, belt, arms (chain sleeve + bony hand), legs and shoes under a separate chain skirt. The skull came back as a human face with a beard-like jaw: a head-only Smart Topology (skull + coif, crown, crown band, studs, teeth) replaces it (`graft_head.py`) |
| Rig | 52 `B_*` bones + twist bones + 8 skirt bones; Meshy auto-rig joints, wrists from the narrowest ring of the arm pieces |
| Weights | `weights_fix.py`: plate and belt on a smooth spine chain; pauldrons and shoulder caps rigid on clavicle/upper arm; arm pieces and cuffs on their own arm; legs on the legs; the chain skirt a dress (pelvis -> 85 % legs at the hem: 45 % let the striding legs split it); the hidden legs above the shoes take the skirt's own weights (`legs_follow_skirt.py`, after the skirt bones: the thighs poked through the robe by 11 cm in the walk and 21 cm in the run); head pieces by height from the head to the neck. Gap check 0/0 |
| Staff | modelled from the native frames (`make_props.py`: dark wood, gold foot/collars/crescent cage, red orb), gripped 0.63 up; carried upright by the authored carry (`author_carry.py`, `carry.json`) in Standing, Walking, Running, Hit and Fidget |
| Clips (30 fps) | Standing Mixamo Standard Idle + carry (3.0 s); Walking Mixamo Walk + carry (1.0 s, 1.734 m stride); Running Mixamo Standard Run fit + carry; **Attack** (spell, 1.47 s): Mixamo "Standing 1H Cast Spell 01" body at 1.3x, cut at 1.75 s of the source, its spine/neck/head turn damped to 60/40 % of the clip (the head stays on the target), the staff arm solved on its own hand path (`author_staff_attack.py`): the staff tips toward the target as the hand goes low-forward, rises with the hand overhead and out to the side (25 cm wider than the clip) for the release at 0.749 s, and returns to the carry, like native m270a. The free arm keeps 25 % of the clip's motion (it held it out from the side, still) and casts on top: it reaches toward the target as the staff tips and thrusts forward, nearly straight just below the shoulder, on the release (a hanging arm read as idle, user review); the staff-side clavicle lifts up to 25 deg as the hand rises (the pauldron, ~42 % clavicle, lifted off the shoulder); the body takes 70 % of the unplanted clip's pelvis travel (8 cm dip as the staff tips, 6 cm weight shift for the raise) with the legs solved back onto the planted feet. The first attack (Mixamo "Standing 1H Magic Attack 01" with keyed staff offsets) swept both arms out and turned the chest 46 deg with the head (user review); Hit set Unarmed get-hit F1 + carry; Death Mixamo Standing React Death Backward, travel halved, skirt folded; Dead; Fidget Mixamo Annoyed Head Shake planted + carry |
| Textures | body 1K + head 1K (Meshy retextures from the flipped HD masters / head turnaround; after the second cut the body maps are baked piece by piece from the unreduced master onto a new Smart UV layout, `rebake_body_uv.py` -> `texturing/rebake_v2/`: Meshy's fragmented layout smeared the chain mail through a collapse), AO graded, ORM red = per-class specular mask; one region (the chain: skirt, sleeves, shoulder caps and the coif in the head set, same ramps); ramps: a square-root luminance curve through each tier's native median (the chain texture is high-contrast), chroma by luminance rank from the native pixels, tier A keeping the texture's own chroma |
| Meshy credits | **35 of 100**: Smart Topology 5, auto-rig 5, head Smart Topology 5, body retexture 10, head retexture 10 |

## Built mirrored

The native lich holds the staff in its LEFT hand; every grip, carry, clearance and arm-solver script in the shared route
is written for the right hand. The whole build is therefore mirrored: Smart Topology got the horizontally flipped
primary, the head model the flipped head primary, the retextures flipped views with the left and right profiles
swapped (`references_*/mirrored/`). The staff sits in `B_R_Hand` of the build; `scripts/mirror_glb.py` (run by
`build_runtime.sh` right after the LOD0 export) mirrors the GLB across X (positions, normals, tangents, winding, node
transforms, inverse binds, animation keys) and swaps the `_L_`/`_R_` bone names, so the delivered model holds the staff
in its left hand with correct names. Everything in `work/` is mirrored.

## Installed 2026-10-20 (user request; commands as run)

```sh
python3 tools/install_model.py level_generation/creatures/mm7_m270_claude/export/mm7_m270.glb --world mm7
python3 tools/install_model.py level_generation/creatures/mm7_m270_claude/export/mm7_m270_staff.glb --world mm7
```

[actors_m270_binding.yml](actors_m270_binding.yml) is added to `assets_dev/worlds/mm7/models/actors.yml` (scale 116.9 =
native stand 199 px x 1.0 over the 1.703 m Standing pose; stride 1.734 m; spell release 0.749 s with the charge glow at
`staff_head`, an offset of 0.575 m along the `Staff` node to the orb; head look; staff attachment). Tier speeds
180/200/220 stay under the run threshold (280).

## Replay

`scripts/rebuild.sh` (`STAGE=rig`, then `STAGE=anim` twice on a fresh build: the carry, the authored attack and the
clearance need `work/grip_pose.json`), texture chain once (`export_uploads.py`, Meshy `retexture_v1` and
`head_retexture_v1`, `transfer_uv.py -- work/rig_v5h.blend meshy/retexture_v1 work/rig_v6.blend`), `make_props.py`,
then `scripts/build_runtime.sh` (on the textured master, once each: `legs_follow_skirt.py`, `reduce_textured.py`, which keeps `work/rig_v6_full.blend`, and `rebake_body_uv.py`), `viewer_tiers.py`, `update_viewer_manifest.py`.

## Gates (final export)

- G4: arm stretch p99 <= 1.43, max 2.01 (attack: 1.50 / 2.04 as the staff tips, 1.46 / 1.96 raised). G5: hand stretch <= 2.16x; staff fist clearance 0.55 cm at the thumb, 1.6-2.1
  cm for the fingers.
- Skirt: legs out of the robe 0.6 cm in the walk, 1.6 cm in the run, 0 in the hit (were 11.4 / 20.9 / 5.5 cm); death 8.4 cm at the floor while lying.
- G6: closed shells (plate, belt) <= 0.6 cm (the staff forearm against the belt in the walk); `sword_clear.py` turns the
  staff hand <= 36 degrees in the death.
- Staff: carry wrist swing <= 37 degrees (idle, walk, fidget), the hit reaches 87 degrees briefly. Attack: the staff
  tips to ~40 degrees above horizontal (a hammer grip cannot aim a long prop along the forearm: the first version rolled
  the hand ~170 degrees) with up to 25 degrees of solver freedom, part of the solver state with a transition cost and
  zero at the clip ends. The hand roll is measured from world X, not world up (the carried staff is 86 degrees up, where
  the up projection is nearly undefined: the hand flipped 90-120 degrees in one frame). Wrist swing <= 67 degrees, hand
  twist 20-38 degrees, hand step <= 12 degrees and head step <= 6.5 degrees per 1/48 s, spine twist 5 degrees (was 46).
  A raised hand lower than the clip's (blended toward the carry, or dropped 10-25 cm) rolled the forearm ~150 degrees;
  moving it out to the side does not.
- Feet: grounded soles -3.9..+3.3 cm in the walk. Viewer: 3 tiers x 8 clips, no console errors; textured EEVEE frames
  in `work/r_glb/`, close-ups in `work/r_glb2/`. Not checked in game.

## Known limits

- The chain skirt is skinned (85 % on the legs at the hem): it shows the knees in the walk and does not swing.
- Pauldrons are rigid on 55-60 % upper arm; with the arm raised they lift with it (in the attack's raise the staff-side
  pauldron rises beside the jaw, against the coif).
- The staff's crescent cage and orb are simple modelled shapes with our own flat paint.
- Mirrored build: the HD-master paint details (stains, asymmetries) appear on the side the masters show them.

## Floor fix (2026-10-21, MM7 creature post-process)

[Creature post-process](../CREATURE_POSTPROCESS.md) step 2. Audit before: Attack sinks to -3.7; Hit sinks to -5.3; Running sinks to -2.7; Walking sinks to -11.0; dying sinks to -4.5; walking sinks to -11.0.
`claude_shared/floor/floor_fix.py work/floor_fix_base/mm7_m270.glb export/mm7_m270.glb --lift-joints Attack Dead Death Hit Running Walking --lift-only 'B_Skirt*,Robe_*,…' --ground-loop Running --ground-loop Walking --raise Attack --raise Hit --ground-death Death Dead`, then
`check_winding.py` (0 inverted) and `tools/install_model.py --world mm7`. Only animation samplers changed; the
pre-fix export is `work/floor_fix_base/mm7_m270.glb`, and the `.blend` master predates the fix (rerun the same operation
after any re-export).

## Gait rollout (2026-10-31, package h09)

New clips appended to the installed source: `Walk2` (Mixamo Walk, 1.10 s, stride 1.7572; hem kept on the floor like `Walking`) bound as `walking`, and `Jog` (humanoid set Staff-Run-Forward, 0.70 s, 2.2601, low knee for the chain skirt) bound as `run`. MAW does not change the Lich's speeds (no sprint). `Walking` and `Running` stay, unbound.

Rebuild: `level_generation/creatures/gait_rollout_20261031/h09/scripts/rebuild.sh m270` (composes from the pre-gait copy
`h09/work/mm7_m270_pre_gait.glb` and `h09/jobs/`, runs `gait_gate.py` and `check_winding.py`), then
`python3 tools/install_model.py level_generation/creatures/gait_rollout_20261031/h09/export/mm7_m270.glb --world mm7 --name
mm7_m270.glb`. Bindings: `h09/bindings.yml` (applied by the rollout coordinator). A far-LOD repair, head-bob, floor or
reduction rerun on this model must re-graft these clips: copy the new installed source over the pre-gait copy and
rebuild. Details, gates and doubts: [h09 README](../gait_rollout_20261031/h09/README.md).
