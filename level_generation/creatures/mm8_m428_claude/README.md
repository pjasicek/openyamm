# MM8 female Dark Elf peasant (`m428`) — Claude humanoid workflow (2026-10-19)

User: "task agent to do 3D MM8 dark elf female (is likely wimp so no attack anim needed)". Complete production through
the shared Claude humanoid playbook, matching her male counterpart [`../mm8_m424_claude/`](../mm8_m424_claude/README.md)
(clip set, dagger carry, scale method, binding). Installed and accepted by the user on 2026-10-19 ("ok accepted"), as the reduced
8,154-triangle model with the beside-the-body dagger carry.

Descriptors `Dark Elf Pesant Female A/B/C` (native spelling), monster IDs **22 / 23 / 24**, display name "Dark Elf
Peasant", AI Wimp (flees, never attacks). Native sprites m429 / m430 / m431 draw the m428 art with palettes
**429 / 430 / 431** (green / blue / red dress). She lives in the Merchant House of Alvar (`d09.blv`).

## Installed assets and binding

- Source `assets_source/worlds/mm8/models/mm8_m428.glb` (= `export/mm8_m428.glb`), installed with
  `tools/install_model.py --world mm8`; the cooked runtime copy is `assets_dev/worlds/mm8/models/mm8_m428.glb`.
  `check_winding.py`: 0 inverted closed parts.
- Bindings in `assets_dev/worlds/mm8/models/actors.yml` (after the male peasant): scale **118.685078** gives the native
  **201-unit** standing height (native stand frame 201 px; model Standing height 1.6936 m), yaw offset -pi/2, skins
  `m428_a/b/c`, Walking/Running strides **1.411 / 1.636 m**, head look on `B_Neck`/`B_Head` (45/25 deg), upper body
  root `B_Spine`. `attack_melee` and `attack_ranged` alias Walking, exactly as the male peasant; no attack or cast clip.
- Dagger: the installed male dagger `worlds/mm8/models/mm8_m424_dagger.glb` on the `Dagger` bone. Her `Dagger` bone is
  built by the male's construction (`scripts/dagger.py`: handle centre and axis from the solved fist, roll from the
  hand), so the attachment authored in that bone's space fits her hand unchanged; no second dagger asset.

| LOD | 0 | 1 | 2 | 3 |
|---|---:|---:|---:|---:|
| triangles | 9,946 | 4,972 | 1,786 | 594 |

One body draw (body and head sets merged into a 2080x1024 atlas), 4 influences, 121 bones (52 body, 4 twist, 64 dress,
Dagger). Three tiers share every image; the region mask recolours only the green dress (bodice, skirt, shoulder bands)
with 16-stop ramps measured from each tier's own native palette (`textures/m428_ramps.json`). Chemise, underskirt,
hair, skin, lacing, belt, buckle and shoes stay fixed.

## References and Meshy (30 of 40 credits)

- `references_hd/`: five HD masters by Codex from the original native five-view sheet
  (`../mm8_m428/references/identity.png`; the restored 2x front frame only as surface reference). The primary needed
  two corrections (curled right hand, green lacing over bare skin); its "halo" is RGB under alpha 0 (alpha is clean).
  Records: `generation_runs.json`, `selected_views_review.png`. Body unarmed and without scabbard by design.
- `references_head/`: four-view head turnaround from the selected masters.
- Meshy (`creature_3d_progress.json`, `meshy/`): Smart Topology 15k **5**, auto-rig (joint estimate and initial
  weights) **5**, body retexture **10**, head retexture **10**. No paid animation.

## Model and rig

`scripts/step1_clean.py` joins the Smart Topology parts with a `piece` attribute: 0 one shell for head skin, bodice,
sleeves and the whole dress; 1 hidden legs and shoes; 2 hair (to mid-back); 3/4 forearms and five-finger hands;
5 fringe; 8/9 eyes; 17/18 mouth; lacing, belt and buckle pieces.

- Joints (`scripts/compose_joints.py`, X-rays `review/xray_*`): Meshy put its knees 17 cm in front of the leg mesh and
  its shoulders/spine asymmetric, so legs come from rings of the hidden leg piece, wrists from hand-piece rings,
  shoulders/elbows from Meshy mirrored, spine on source heights, head joint at mouth height.
- Source-frame rig (`build_rig.py`), fingers by connectivity (`fit_fingers.py`, `finger_joints.py`, hand X-rays
  `review/fingers_*`), Meshy weights by name, component ownership (`weights_fix.py`), reduction after weighting
  (`reduce_rigged.py`: 14,757 -> 9,964; head above 1.44 m at full density, hidden legs to 600), fist solved around the
  dagger handle (`grip_solve.py`, `review/grip_*`).
- Dress (`dress_rig.py`, `dress_sim.py`, from the MM8 Cleric's robe): 16 chains x 4 bones on the outermost skirt
  surface, underskirt layers weighted by the same angle/height; verlet cloth baked into every clip with leg capsules
  and floor. In Death the skirt follows the pelvis frame from 8 deg of tilt and is pushed off the legs faster, so the
  front split does not open over the legs during the fall.
- Long hair: B_Head above the shoulders blending into B_Spine2 down the back.
- `fix_cuffs.py`: Smart Topology fused each sleeve ruffle's tip to the dress at the hip (18 bridge faces) and Meshy gave
  the ruffles pelvis weight; the bridges are cut and the ruffles stay on arm bones (right-arm G4 p99 3.6-4.2 -> 1.9).

## Clips

Local sources chosen before finishing (no purchases; `anim_library` checked):

| Clip | Seconds | Source / finishing |
|---|---:|---|
| Standing | 2.0 | Humanoid set RelaxIdle; civilian dagger carry (male's `carry.json`) |
| Walking | 0.8 | RelaxWalkForward (RelaxWalkFemale rejected: strong hip sway and shoulder lean read as a sashay) |
| Running | 0.7333 | Mixamo Standard Run, `run_fit.py` stride 1.6 m (measured 1.636), heel kick halved for the dress (`RUN_HEEL` 0.5), dagger turned clear |
| Hit | 0.5 | UnarmedGetHitF1 recoil on the civilian stance (native hit also flings both arms out) |
| Death | 1.3 | UnarmedDeath1 backward fall; legs keep 20 % of the source motion so they stay together under the dress |
| Dead | 1.0 | Held settled last Death frame (dress included) |
| Fidget | 2.2 | Authored from the native F frames: dagger raised in front of the chest, blade up and to her left, left hand beneath it, head down; elbow pole held down, wrist roll within 90 deg (`author_fidget.py`) |

## Textures

Body retexture on Meshy's own UVs copied back by face correspondence (`transfer_uv.py`; the return dropped two
degenerate slivers, their 4 neighbours moved up to 10 mm, bounded and recorded), head set on its own 1K layout.
`compose_textures.py`: one dark-elf skin albedo across both sets (the male's), the neck column forced to skin (the head
references painted a dark choker band under the jaw), hidden legs as dark hose (Meshy painted them bare skin), material
classes, specular mask, AO in albedo, dress region mask and ramps.

## Verification

- Gates (`scripts/stage_gates.py` on `work/rig_textured_uv.blend`): arm stretch p99 <= 1.97 on every sampled frame of
  every clip; hand stretch <= 1.91x (gate ~4.5x); Fidget right-wrist swing max 55.4 deg (hold ~36); grounded soles 0 cm
  (`sole_probe.py`); jerk peaks only in the source Hit/Death recoils.
- Regression `mm8_dark_elf_female_peasant_actor_models_keep_native_roles` (`game/outdoor/HeadlessOutdoorDiagnostics.cpp`):
  three tiers at 201 +/- 4 units, seven clip durations, no Attack/Cast clip, Dagger node, three reduced LODs, unchanged
  simulation state. `OPENYAMM_REGRESSION_FILTER=mm8_ ... actors`: **56 passed, 0 failed** (`review/regressions/`).
- In game (desktop OpenGL, engine screenshots, `review/ingame/`): Dagger Wound (`out01.odm`) and the Merchant House of
  Alvar (`d09.blv`), all three tiers, walking/fleeing, hit, death and corpse, model vs native sprite at the same camera:
  `compare_model_sprite_outdoor.png`, `compare_model_sprite_indoor.png`; tours `*.yml`, logs beside them.
- Native billboards retired: 115 m428 frames used only by her sprites moved to
  `assets_legacy/sprites_mm8_monsters_20261019/` (listed in its `files.json`, README updated); the 20 fidget frames also
  referenced by unnamed sprites in `m428.yml` stay. Dagger Wound loaded 108 actors with none missing.

## Known deviations

- The native scabbard on her left hip is not modelled (body references deliberately without it).
- The red tier is a colour ramp; the native red dress's brocade pattern is not reproduced.
- Live AI: in-game model and sprite poses are not frame-synchronised.
- Android and Vulkan not tested; no performance measurement.

## Reproduction

Claim `mm8:m428` (`tools/creature_workspace.py`) and run each stage with `tools/run_creature_blender.sh --token <t>`:
`examine_parts.py <smart topology glb> st_v1` -> `step1_clean.py` -> `stage_joints.py` -> `stage_rig.py` ->
`stage_motion.py` -> `stage_finish.py` -> `export_uploads.py` -> (recorded Meshy retextures; do not resubmit) ->
`transfer_textures.py` -> `python3 scripts/compose_textures.py` -> `stage_refine.py` (fidget onward, actions synced into
the textured master `work/rig_textured_uv.blend`, `fix_cuffs.py`, LOD0 export) -> `python3 scripts/build_runtime.py`
(through `creature_workspace.py run`) -> `check_winding.py` -> `tools/install_model.py export/mm8_m428.glb --world mm8`.
`stage_gates.py`, `measure_runtime.py`, `textured_frames.py`, `closeups.py` and `render_glb.py` produce the checks.

## Review viewer

`review/viewer/index.html` (served from the repository root, e.g. port 8912). `scripts/viewer_tiers.py` bakes the
tier ramps into `review/viewer/mm8_m428_<tier>.glb` from `export/mm8_m428_runtime_lod0.glb` (three.js has no region
ramps), then `scripts/viewer_manifest.py` writes the manifest with native frame anchors. The dagger is not shown.

## Right-hand review fix (2026-10-19)

User (browser viewer, Standing): the dagger hand's palm faced outward instead of toward the thigh.

- Cause: `grip_solve.py` chose the palm side from where the rest fingertips curl. Her A-pose fingers are straight, so
  it picked the back of the hand and solved the fist closing backwards (fingertips 5 cm behind the knuckle plane), in
  every clip. The palm side now comes from the measured knuckle-plane normal (`armik.palm_local`, palm forward at rest
  as in the HD masters). Fingertips are now 3.5-6.0 cm on the palm side (`curl_check.py`); the Dagger bone moved 38 mm
  into the new fist (`sync_dagger_bone.py`), and the male dagger attachment still sits in it.
- The civilian carry (Standing, Walking) adds a palm-toward-thigh term to the global arm solve (`author_carry.py`,
  `armik.arm_dp k_palm`); the hand roll is carried by the forearm twist bones, not by bending the wrist.
- Fidget re-tuned for the new fist: wrist roll bounded to 90 deg from neutral (the unbounded solve rolled the hand
  -157 deg), blade direction re-picked by `fidget_sweep.py` (wrist swing 52.7 deg), left hand 6.5 cm lower so the
  blade stays 1.6 cm above the fingers (`fidget_touch.py`).
- Also found during the check: the hidden legs and the source run's heel kick pushed through the back of the dress
  while running. `fix_legs.py` slims the hidden leg piece toward its bones (up to 40 %, above the ankles) and
  `run_fit.py RUN_HEEL=0.5` halves the heel kick; the run stride is now 1.636 m (bindings updated).
- Gates on the final master: arm stretch p99 <= 1.97 everywhere (Fidget 1.49-1.61), hand edges <= 1.70x, Fidget wrist
  swing 52.7 deg, hand twist -57..-5 deg, soles grounded, dagger 13-18 cm from the body in every clip except the
  fidget's intended contact. Evidence and before/after close-ups: `review/hand_fix/`.

## Dagger arm beside the body (2026-10-19)

User: the dagger arm should hang beside her body (idle, walking) as in the native frames, nothing fancy. The first
carry was the male peasant's (wrist 27 cm out and 17 cm forward at belt height, elbow flared 18 cm). `carry.json` now
puts the wrist just outside the dress at upper-thigh height (fist at hip height below the belt), the dagger forward,
12 deg out and 25 deg up (native `m428sa*`, `m428w*`), and a fixed elbow plane pointing back (`pole`, no plane search;
`author_carry.py` support). Standing, Walking and Running are re-solved (`stage_armcarry.py`; Running keeps 45 % of the
source's own arm swing, and its old 100 deg dagger roll in `settle_wrists.py` is gone); Hit, Death and Fidget blend from
the new Standing. The fist (`grip_pose.json`) is unchanged; the palm still faces the thigh.

Gates: elbow 2-6 cm out from the shoulder line; fist and dagger outside the dress outline in every frame of every clip
(`dress_clear.py`, minimum 1.1 cm in Running, 2.0 cm Standing; also on the reduced GLB, `glb_dress_clear.py`); right-arm
stretch p99 1.35-1.58 in the carry clips (<= 1.97 overall); hand edges <= 1.89x; wrist bend Standing 33, Walking 25,
Running 51 deg. Installed as the reduction (`scripts/build_reduced.py`: the reduced LOD0 of `../mm8_m428_reduce_claude/`
swapped into the new production export, its LOD build, shadow shrink and variants; LODs 8,154 / 4,077 / 1,466 / 487).
Evidence and before/after beside the native frames: `review/arm_carry/`.
