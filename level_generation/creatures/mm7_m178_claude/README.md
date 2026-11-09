# MM7 Devil (m178) — Claude rig-first project

Batch F, model 1 ([batch file](../mm7_batches/BATCH_F.md)). Descriptors 220 Devil Worker (palette 44, ochre-brown
hide: the native frames' own palette), 221 Devil Warrior (45, teal-green hide) and 222 Devil Captain (46, red hide,
brownish plates). **Exported, not installed** (batch rule). Status: technically complete, pending user review.

[Review viewer](review/viewer/index.html) (served at
`http://127.0.0.1:8912/level_generation/creatures/mm7_m178_claude/review/viewer/`) ·
[clip sheet](review/clips_three_quarter.png) · [G1 candidates](review/cand_all.png) ·
[HD masters](references_hd/selected_views_review.png) · [head masters](references_head/selected_views_review.png)

| Item | Value |
|---|---|
| Exports | `export/mm7_m178.glb` (body, LODs, 3 tier variants, head merged; unarmed); editable master `work/rig_v6.blend` (rest pose in the working frame; the export moves the origin, see below) |
| Triangles | LOD0/1/2/3 9,977 / 4,988 / 1,782 / 579 (head 2,548 kept at full density) |
| Mesh | Smart Topology (15k) of the HD three-quarter master: one closed skin (head, ears, all head/shoulder/forearm spikes, four-fingered clawed hands, slate feet with heel spurs, 1.5 m tail) plus 8 tooth pieces, 2 eyes and 12 tail spikes. Three small holes on the skin (upper chest fold, belly groove, tail root) filled in `step1_clean.py` |
| Rig | 52 `B_*` bones with cloned source frames + twist bones + an 8-bone tail chain `B_Tail0..7`. Meshy's auto-rig put the shoulders 22 cm behind the back and the spine/neck/head on the chest and throat surface, so the joints are measured on the mesh: horizontal slices for trunk and legs (`body_slices.py`), rings perpendicular to the arm (`arm_rings.py`), geodesic rings for the tail; Meshy's elbows/hips/ankles agree within 2-5 cm (`fit_joints.py`, `review/xray_fit_*.png`) |
| Weights | bone heat on our joints (head bone 17 cm long so the heat reaches the skull spikes), then `weights_fix.py`: hands rigid (the skin component beyond the wrist plane: the curled fingers lie beside the thighs, where a leg bone was nearer); no leg weight on the arms; upper-arm weight moved to the clavicle above the shoulder joint; every spike, ear tip, toe claw and heel spur rigid on the skin under its base (42 spikes found by inward thickness < 3.5-6 cm); head, jaw and lips rigid on `B_Head`; teeth and eyes rigid; tail spikes from the skin under them |
| Clips (30 fps) | retarget with `KEEP_REST` (trunk, neck and head keep the mesh's rest; the world rule tilted the head 33 deg back). Standing Mixamo Standard Idle, arms out 22 deg, both feet planted by leg IK (3.0 s); Walking Mixamo Mutant Walking in place (1.878 m of source travel per 1.433 s cycle), arms out 14 deg; Running Mixamo Mutant Run in place (2.063 m per 0.867 s, from the pack's root-motion copy), arms out 18 deg; **Attack** Mixamo Standing Melee Attack Downward planted for the arms and trunk, 1.1x, with the lower body authored (`attack_legs.py`, see "Attack feet" below): right arm overhead with the weight back, a left-foot lunge step and a deep crouch into the downward claw swipe (blow 0.750 s), the rear heel peeling, a step back to Standing (2.2 s); Hit Zombie Reaction Hit cut at its flinch (0.87 s), arms out 12 deg; Death Standing React Death Forward (arms up, falls on its face like m178da..dd), travel halved, floor pass; Dead; Fidget Mixamo Roar planted, arms out 20 deg (5.4 s). The tail is procedural (`tail_bones.py`): a 26 deg carriage so it rises behind as in the sprites, 60-85 % of the pelvis tilt taken back at its root, a travelling sway, a lift in the attack, laid flat in the death |
| Textures | body 1K + head 1K (Meshy retextures from the HD masters / head turnaround, UVs carried back face by face), AO graded into the base colour, ORM red = per-class specular mask (`openyamm_specular_mask`), class map `textures/m178_material_classes.png` (+ head); two regions in both sets with the same ramps: R hide, G slate plates; ramps from each tier's native palette entries (variants.json channels: hide 140-215, plates 62-75), tier A keeps the texture's chroma (`compose_m178.py`) |
| Origin | the working frame was centred on the bounding box (tail included), which put the pelvis 0.53 m in front of the origin; `export_runtime.py` moves mesh and armature rest 0.626 m back so the origin lies halfway between the Standing soles and the pelvis, on the midline |
| Meshy credits | **30 of 100**: Smart Topology 5, auto-rig 5 (joints used as second estimate only), body retexture 10, head retexture 10 |

## Install later (not run)

```sh
python3 level_generation/decorations/mm8_3d/animated/scripts/check_winding.py level_generation/creatures/mm7_m178_claude/export/mm7_m178.glb
python3 tools/install_model.py level_generation/creatures/mm7_m178_claude/export/mm7_m178.glb --world mm7
```

Then add [actors_m178_binding.yml](actors_m178_binding.yml) to `assets_dev/worlds/mm7/models/actors.yml` (scale 107.9
= native stand 190 px x 1.0 over the 1.761 m Standing pose; stride 1.878 m, run stride 2.063 m; blow 0.750 s; spells and
the fire missile charge at `claw_r`, the right palm, and leave at the swipe's impact; head look 40/20 deg).
Tier speeds 200/250/300 against the run threshold 2.4 x 107.9 = 259: A and B walk (1.42x and 1.78x the Mutant walk's
natural 141 units/s), C runs (1.18x). Not checked in game (optional for this batch).

## Replay

`scripts/rebuild.sh` (`STAGE=rig`, then `STAGE=anim`), texture chain once (`export_uploads.py`, Meshy `retexture_v1` and
`head_retexture_v1`, `transfer_uv.py -- work/rig_v5h.blend meshy/retexture_v1 work/rig_v6.blend`), then
`scripts/build_runtime.sh`, `viewer_tiers.py`, `update_viewer_manifest.py`; gates with `scripts/gates.sh`
(results of the final run in `work/gates_final.txt`).

## Feet and walk fix (user review 2026-10-20)

User: in the Standing pose both feet were rolled sideways, the soles 15-20 degrees to the floor. Batch A's fixes
(`mm7_m222_claude`, as applied by batch J `mm7_m322_claude`), adapted and replayed (STAGE=anim, runtime build, viewer):
- **Rest pose checked first:** the floor-contact sole (every Foot/Toe0 vertex within 2.5 cm of the floor: ~100 pads
  and claws per foot) is level at rest (roll 0.3 deg), so the feet are levelled to their rest relation. The devil's
  B_*_Foot holds only the ankle (46 vertices above 12 cm); batch A's sole set (Foot vertices near the lowest point) had
  2-4 vertices here, so `foot_level.py` uses the Foot/Toe0 floor-contact set instead.
- **Ankle roll:** `foot_level.py` copied from batch A: stance clips (Standing, Hit, Fidget, Attack, Death before the
  fall) level roll and pitch weighted by flatness, capped at 20 deg and smoothed; the walk takes one constant roll per
  foot in the foot's own frame (13.8 / 11.3 deg) plus one constant pelvis shift, the run one constant roll (13.1 / 26.4
  deg). Stance frames are those where the foot carries the frame's lowest point (the claws touch first, so batch A's
  heel/toe reference never came within 1.5 cm). Toe0 is reset to rest in every clip (it carries most of the sole; the
  source toe channel bent the whole sole). Measured roll of the stance sole (`head_bob.py`):

  | Clip | before | after |
  |---|---|---|
  | Standing | L 6.4, R -8.9 deg | L 0.2, R -0.1 deg |
  | Attack / Fidget / Hit | up to 10.0 / 6.4 / 9.9 deg | 0.2 / 0.2 / 1.9 deg |
  | Walking (stance frames) | L 20.4..32.2, R -29.1..-1.7 deg | L 3.1..10.3, R -18.2..8.6 deg (heel strike and toe-off included) |
  | Running (stance frames) | L 13.5..29.0, R -61.1..-20.4 deg | L -5.3..11.4, R -28.1..11.2 deg |

  The walk keeps its own heel-up stance (sole pitched ~24 deg: the devil walks on its toe pads); levelling the pitch as
  well (`:flat`) was tried and rejected (the left stance then rolled -5 deg and the swing feet pitched up to 55 deg).
- **Head zigzag:** `walk_bob.py` (batch A) after `clip_timing.py` evens the pelvis height of both steps; also run on
  Running (`ACTION=Running`). Head height second difference per frame: Walking 1.64 -> 0.83 cm, Running 5.04 -> 1.83 cm.
- **Checks:** soles Standing/Attack/Fidget/Hit -0.1..+0.2 cm, Walking -0.8..+1.0 cm, Running -2.3..+3.1 cm (flight
  frames); foot rotation steps per 1/48 s equal the pre-fix chain (Walking 10.8 / 12.7 deg, Running 15.0 / 13.2 deg).
  G6 re-run: the lower run bob put the right claws 5.4 cm into the right foot, so the run's arm abduction went 10 -> 18
  deg (2.9 cm); all other clips unchanged. Standing became 2.4 cm lower: scale 106.4 -> 107.9.
- Feet close-ups from the export (front and side, Standing, Attack and three walk frames): `review/feet/`.
  Viewer check and `check_viewer.mjs`: 3 tiers x 8 clips, no console errors. Previous masters kept as
  `work/rig_v5_prefootfix.blend` / `work/rig_v6_prefootfix.blend` (and the old script as
  `scripts/foot_level_prefootfix.py.txt`).

## Attack feet (user review 2026-10-20)

User: "please use feet - his feet are totally stationary and not part of the windup or release". Cause: the attack was
retargeted `:plant`, which holds the legs at Standing frame 0, and no unplanted copy was blended back (clip_timing's
LEG_KEEP share needs an `AttackFull` retarget, which this chain never had). The source's own legs were not usable: the
unplanted Standing Melee Attack Downward stands in a 0.5 m fencing stance and only pivots its feet (no lift). The
native m178aa..ah rise with the arm overhead and then drop into a deep forward crouch for the swipe.
`scripts/attack_legs.py` (numbers in `scripts/attack_legs.json`, the playbook's authored-blow rules after
mm6_natm_claude) layers on the planted clip, after the feet are levelled:
- pelvis draws back 5 cm in the wind-up, then drives 14 cm forward and sinks 15 cm into the crouch, recovering by
  source frame 60; hip yaw -8 deg (right shoulder back) then +14 deg into the swipe, the chest following 50 ms later;
  trunk lean -4 deg back in the wind-up, +14 deg forward at the blow;
- foot plan: the left foot steps 30 cm forward with a 9 cm sine lift and lands with the blow (source frames 13-23),
  steps back in the recovery (44-57); the right heel peels 16 deg about the front claw tips (a pivot at the ball joint
  pushed the 17 cm claws 5 cm into the floor); the planted foot never slides; toes at rest;
- legs by two-bone IK in their knee plane (largest ankle miss 0.0 mm), feet keep the levelled Standing rotation.
Results: blow 0.817 -> 0.750 s (wind-up stretch 1.00x against the native 0.75 s; binding updated); soles: the planted
foot -0.1..+0.2 cm, the stepping foot lifts to 8.9 cm, stance sole roll 0.2 / -0.2..3.1 deg (the peeling heel);
foot rotation steps 5.0 / 1.8 deg per 1/48 s; trunk step 9.1 deg (was 6.9). G4 leg max 2.41 (stepping ankle), arm
p99 1.77. G6: off hand vs tail root 4.4 cm (was 4.5); the swiping claws pass 3.9 cm over the stepped left foot at the
bottom of the swipe (new, about two frames). Sheets: `review/attack_feet_sheet.png` (front, side, three-quarter),
foot close-ups `review/feet/Attack_*`. Previous masters kept as `work/rig_v5_preattackfeet.blend` /
`work/rig_v6_preattackfeet.blend`. Viewer check: 3 tiers x 8 clips, no console errors.

Knee fix (user review 2026-10-21: "caves in and rotates/twists unnaturally" from about 0.62 s): the leg IK aimed each
knee at its previous place, which fell behind the hip-ankle line once the lead foot was 30 cm ahead, so the left knee
flipped backwards (its angle to the toes about the hip-ankle line went +30 -> +172 deg) from 0.6 s to 1.65 s.
`attack_legs.py` now aims each knee along its foot at its Standing angle to the toes (L +16.3, R -26.4 deg, held
through the whole clip) and turns the thigh as a whole frame, so the knee stays a hinge. `STAGE=anim scripts/rebuild.sh`,
`TEXTURES=0 scripts/build_runtime.sh`, then the reduce project's build (its README); only Attack changed (every other
clip 0.00 cm). Before/after: `../mm7_m178_reduce_claude/review/shots/knee_fix_sheet.png`, `knee_fix_legs.png`. Previous
masters: `work/rig_v5_prekneefix.blend`, `work/rig_v6_prekneefix.blend`, `work/mm7_m178_export_prekneefix.glb`.

## Gates (final export)

- G3: joints inside the limbs, mirror differences <= 3.7 cm; frame error 0.
- G4 (edge stretch over every 2nd frame, `stretch_all.py`): p99 <= 1.75 (attack arm), max 2.94 (death upper arm);
  trunk max 2.48 after the spike, jaw and head rules (the shoulder spikes sheared up to 9.7x before).
- G5: hands rigid, so the gate reduces to the wrist band: max 2.0 (attack).
- G6 (closed skin, inside test, half frames): Standing, Walking and Fidget 0; Hit 2.2 cm; Running 2.9 cm (right
  claws vs right foot); Attack 4.4 cm (the off hand swings back into the tail root in the follow-through; yawing the tail
  either way did not clear it) and 3.9 cm (the swiping claws over the stepped left foot); Death 6.1 cm (hands on the body while falling). Mutant Roaring (hands crossed through
  the thighs, 5.6 cm) was replaced by Roar.
- Soles: Standing, Attack, Fidget, Hit -0.1..+0.2 cm; Walking -0.8..+1.0 cm; Running -2.3..+3.1 cm (see the feet fix).
- Jerk (`jerk_probe.py`): equal to the source clips except the death's blend-in from Standing (upper-arm step 26.7 deg
  per 1/48 s vs the source's 14.1).
- Viewer: `run_creature_review.py check` and `check_viewer.mjs`: 3 tiers x 8 clips, no console errors; playback
  recorded in `review/playback/`, close-ups in `review/shots/`. Textured EEVEE frames from the export in `work/r_glb/`.
- `check_winding.py`: 0 inverted closed parts.

## For the user to review

- The hide reads brighter and more saturated than the dark-shaded sprites in all tiers (ramp gain 1.3 per the texture
  guide; one number in `compose_m178.py`).
- Tiers A and B walk faster than the Mutant walk's natural speed (1.42x, 1.78x); the hunched Mutant walk was chosen
  because it matches the native walk frames.
- The tail is long (1.5 m of mesh); its end curl rises steeply in three-quarter views, like m178sa1.
- The Standing idle stands more upright than the native (straight legs of the Mixamo idle).

## Known limits

- The claws do not articulate (rigid hands); the source finger motion is not shown.
- The tail motion is procedural (carriage, sway, lift), not physics.
- Contacts listed under G6 remain (attack follow-through 4.5 cm, death 6.1 cm).
