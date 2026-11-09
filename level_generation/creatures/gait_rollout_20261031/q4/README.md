# Gait rollout package q4: MM8 Centaur, Unicorn, Crystal Dragon and MM7 Chicken (2026-10-31)

Brief: [the rollout README](../README.md). Every new clip is procedural, grafted onto the **installed** source with
`../../claude_shared/graft_clips.py` (`graft_byte_check.py`: the old file is a byte prefix, every old mesh, skin,
material and clip unchanged). All four models are installed; the coordinator applies [bindings.yml](bindings.yml).
MAW changes none of these speeds (no melee monster faster than 150), so no model needs a sprint.

| model | body (by eye) | descriptors | new clips | binding |
|---|---|---|---|---|
| mm8_m544 | horse (unicorn), hooves with pasterns | Unicorn A-C | Walk2 | walking Walk2 0.3981 |
| mm7_7m504 | **two-legged** hen (the ledger's "multi-legged" is wrong) | zchicken a-c | Run2 | run Run2 0.552 |
| mm8_m548 | wingless four-legged crystal dragon | Crystal Dragon A-C | Walk2, Run2 | walking Walk2 0.4933, run Run2 0.8213 |
| mm8_centaur | horse body (four legs, hooves) with a human archer's torso, bow and quiver | Centaur A-C | Walk2, Run2 | walking Walk2 1.776, run Run2 3.0656 |

## Scripts

- `scripts/gait_m544.py` (Unicorn). Copies `../../mm8_m544_claude/scripts/animate_unicorn.py`'s leg, body and tail
  functions (that script keys every clip when run) and q3's Gorgon gait loop; reads `mm8_m544_claude/work/anim_v1.blend`.
- `scripts/gait_m504.py` (Chicken). Executes `../../mm7_7m504_claude/scripts/anim_chicken.py` unchanged up to its clip
  table (as q1's Cockatrice) on `mm7_7m504_claude/work/anim_v2u.blend`, then keys Run2.
- `scripts/gait_m548.py` (Crystal Dragon). Imports `../../mm8_m548_codex/scripts/motion.py` unchanged (its leg IK,
  root and floor rule) on `mm8_m548_codex/export/mm8_m548.blend`.
- `scripts/gait_centaur.py` (Centaur). New horse body with `../../mm8_m532_claude/scripts/animate.py`'s leg() on
  `mm8_m532_claude/work/centaur_master_carry.blend`; the rider (Spine and everything under it: torso, head, both arms
  with the carry-fixed bow hold, bow and string bones) and Quiver and Arrow are copied as local channels from the
  installed Walking (for Walk2) or Running (for Run2) at the same phase, so the accepted bow carry is unchanged
  (equal at every key; in between, linear sampling differs by under 0.015 in quaternion components), then Spine takes
  back 70 % of the new body's rocking.
- Every script saves `work/<model>_gaits.blend`, `work/<model>_gaits_info.json` and the new clips only to
  `work/<model>_clips.glb`. `QG_SET="Clip:key=value,..."` overrides clip parameters for trials.
- Probes and review: `quad_probe.py`, `low_probe.py` (q3's; `--skip <joint>` added for the centaur's hidden arrow,
  which collapses at Root at scale 0.001 in every locomotion clip), `probe_rig.py`, `glb_info.py`, `crop_sheet.py`,
  `clay_strip.py` (Blender clay filmstrips), `merge_attach.py` (review-only GLB with the bow and quiver attachments
  merged under their nodes), q3's `viewer_manifest.py` and `viewer_page.sh`.

## Per model

### Unicorn (mm8_m544): Walk2

**Targets.** It wanders at 0.46-0.51 and chases at 0.93-1.02. Its two clips are transverse gallops (the native walk is
a gallop): Walking 0.64 m in 1.0 s (0.64), Running 0.64 m in 0.75 s (0.853). Unicorn C wandered on Walking ×0.72. Walk
target 0.34-0.62.

**Walk2.** A four-beat lateral-sequence walk (hind L 0, front L .25, hind R .5, front R .75; hind L at 0 as the
gallops), 0.8125 s (39 keys at 48 fps), stride 0.3981, authored 0.49, duty 0.60, sweep 0.24 m (the fore leg's reach:
0.278 overreached by 14 mm), body 3 cm lower than Standing, the head nodding twice a loop, footholds centred at y ∓0.19
as Walking. Planted hoof miss 0; lowest vertex -0.01 cm. The chase stays on Running.

**Gate** (window section; MAW is the same):

| tier | wander | chase |
|---|---|---|
| A | Walk2 ×1.04 | Running ×1.19 |
| B | Walk2 ×1.02 | Running ×1.17 |
| C | Walk2 ×0.94 | Running ×1.08 |

Stride: Walk2 0.398 / feet 0.398, trusted. Floor: ok. PASSED.

**Probes.** Head bob 3.1 % (Walking 8.5 %, Running 11.5 %, gallops). Hoof toe-out 0.0 planted and swinging on all four,
as every installed clip (the hooves only pitch). Touchdowns: hind L 0.00, front L 0.23, hind R 0.49, front R 0.74.

### Chicken (mm7_7m504): Run2

**Targets.** It wanders at 0.98 and chases at 1.95. Its run was bound to Walking (0.40 m in 0.4333 s, 0.92): ×2.12,
held at 2× with sliding feet. Run target 1.30-2.60.

**Run2.** A hen's run: 0.30 s (18 keys at 60 fps), stride 0.552, authored 1.84, duty 0.40 (short flights), Walking's
stance sweep (0.22 m), body leaning 12° forward and lowest at mid-stance, neck stretched and the head held level with a
smaller thrust than the walk's, wings held a little out, tail lowered, feet lifted 6.5 cm with the toes curled. The
footholds sit 4 cm further back than Walking's and the hips 3 cm lower: centred like Walking's, the ankle missed its
target by 42 mm at touchdown (Walking itself misses about 20 mm there). Left foot down at 0, as Walking. Worst
planted ankle miss 3.4 mm; lowest vertex -0.05 cm.

**Gate** (window section; MAW is the same): every tier wanders on Walking ×1.06 and chases on Run2 ×1.06.
Stride: Run2 0.552 / feet 0.551, trusted. Floor: ok. PASSED.

**Probes** (`quad_probe.py --paws Foot_L,Foot_R`; `bob_audit.py` and `foot_heading_probe.py` read humanoid joints
only). Head bob: Run2 1.4 %, Walking 2.0 % (a hen steadies its head). Planted toe-out L +9.9, R +2.6 (Walking +9.9 /
+2.5, the rest pose's); swing L +6.2..+9.9, R +1.5..+2.9.

### Crystal Dragon (mm8_m548): Walk2, Run2

**Targets.** It wanders at 0.71-0.84 and chases at 1.43-1.67. Walking (0.32 m in 1.0 s) and Running (0.43 m in 0.75 s,
0.57) are both trots: it wandered on Running ×1.25-1.47 and chased on it ×2.48-2.92 (held at 2×). Targets: walk
0.56-0.95, run 1.12-1.90.

**New clips** (48 fps):

| clip | length | stride | authored | duty | sweep | gait |
|---|---|---|---|---|---|---|
| Walk2 | 0.6667 s (32 keys) | 0.4933 | 0.74 | 0.52 | 0.26 m | trot as Walking/Running: front L + hind R at 0 |
| Run2 | 0.5625 s (27 keys) | 0.8213 | 1.46 | 0.32 | 0.26 m | transverse gallop: front L 0, front R .1, hind L .55, hind R .65 |

Run2 has a gathered flight after the fores and a short extended one after the hinds, flexes the back 8° (arched as the
hinds swing under), pitches the body 3° nose-down as the fores land, the neck taking back 70 % of pitch and flex.
Sweeps match Running's 0.24 m. Worst planted paw miss 1.5 / 1.7 mm (Walk2 at duty 0.55 overreached the hind by 10 mm).

**Gate** (window section; MAW is the same):

| tier | wander | chase |
|---|---|---|
| A | Walk2 ×1.13 | Run2 ×1.15 |
| B | Walk2 ×1.02 | Run2 ×1.04 |
| C | Walk2 ×0.96 | Run2 ×0.98 |

Stride (measured / feet, trusted): Walk2 0.493 / 0.493, Run2 0.821 / 0.820. Floor: ok. PASSED.

**Probes.** Head bob: Walk2 0.6 %, Run2 8.9 % (Walking 2.5 %, Running 2.4 %; q3's Gorgon gallop 11 %, q2's wolf
11.7 %). Planted toe-out front +11.3, hind +5.7 on every clip (the rest pose's). Touchdowns: Walk2 as Walking; Run2
front L 0.96, front R 0.05, hind L 0.53, hind R 0.62.

### Centaur (mm8_centaur): Walk2, Run2

**Targets.** It wanders at 2.68-2.88 and chases at 5.37-5.76 (the model is in metres: 2.6 m tall, 102.5 units/m).
Walking (1.129 m in 0.75 s, 1.51) and Running (2.212 m in 0.6667 s, 3.32) are trots: A and B wandered on Walking
×1.78-1.85 (C on Running ×0.87), and all chased on Running ×1.62-1.74. Targets: walk 1.92-3.58, run 3.84-7.15.

**New clips** (48 fps):

| clip | length | stride | authored | duty | sweep | gait |
|---|---|---|---|---|---|---|
| Walk2 | 0.6458 s (31 keys) | 1.776 | 2.75 | 0.52 | 0.92 m | working trot as Walking: front L + hind R at 0; a diagonal pair always down |
| Run2 | 0.5625 s (27 keys) | 3.0656 | 5.45 | 0.34 | 1.04 m | left-lead canter: hind R 0, hind L .2, front R .26, front L .5; one suspension |

- The horse legs are fully extended at the sweep's ends: the body is lowered 17 cm (Walk2) and 20 cm (Run2), as the
  installed clips lower it 10 and 24 cm. Sweeps stay under Running's 1.15 m.
- In the swing the hooves tuck (35° / 55°) and lift early, then reach nearly straight to land (`early` 0.8 / 0.55 for
  the fores; a symmetric lift bent the fore knee backward with the hoof low ahead of it). Run2's hind footholds sit
  7 cm further back, to reduce the protraction under the belly.
- Run2 rocks the horse body ±2.5° (forehand down as the leading fore lands), bobs 3.5 cm once a loop and lifts the
  tail 12°; Spine takes back 70 % of the rocking so the rider stays upright. A tail floor rule lifts Tail1 until the
  hair clears 1 cm.
- Worst planted fetlock miss 0.6 mm. Lowest vertex (without the hidden arrow) -0.08 cm.

**Gate** (window section; MAW is the same):

| tier | wander | chase |
|---|---|---|
| A | Walk2 ×0.98 | Run2 ×0.98 |
| B | Walk2 ×1.01 | Run2 ×1.02 |
| C | Walk2 ×1.05 | Run2 ×1.06 |

Stride (measured / feet, trusted): Walk2 1.776 / 1.776, Run2 3.062 / 3.060 (bound at the authored 3.0656). Floor: ok.
PASSED.

**Probes.** Rider's head bob: Walk2 2.4 %, Run2 4.6 % (Walking 2.4 %, Running 2.6 %). Hoof toe-out planted: front 0.0,
hind +4.8 on every clip (the rest pose's); swing within 2° of it. Touchdowns: Walk2 front L 0.99 / hind R 0.00 (as
Walking); Run2 hind R 0.00, hind L 0.18, front R 0.26, front L 0.47. Bow and quiver (review merge in the viewer) stay
clear of the legs in every frame looked at.

## Gates run on every export

- `gait_gate.py`: PASSED (above; each model is bound in one world).
- `graft_byte_check.py`: OK. `check_winding.py`: 0 inverted.
- `quad_probe.py`: head bob, paw/hoof/foot heading, touchdowns. Floor: the gate and `low_probe.py`.
- Viewer: `tools/run_creature_review.py ... check`, no console errors, and shots looked at:

| viewer project | revision | models | switches |
|---|---|---|---|
| `mm8_m544_reduce_claude` | `unicorn-gait-1` | the export | 10 |
| `mm7_7m504_claude` | `chicken-gait-1` | the export | 8 |
| `mm8_m548_reduce_claude` | `dragon-gait-1` | the export | 10 |
| `mm8_centaur_reduce_claude` | `centaur-gait-1` | A with bow and quiver (`merge_attach.py`), A, B, C (`viewer_variants.py`, unchanged) | 44 |

  Previous manifests are kept as `manifest_<old revision>.json` (the Unicorn, Chicken and Dragon viewers had only a
  manifest and no page, so `viewer_page.sh` added one). Shots are in each viewer project's `review/shots/q4_*`;
  sheets and clay filmstrips in `review/`.
- Regressions (headless actor suite, on the installed files with the current bindings), all pass
  (`review/regression_*.log`):
  - `mm8_centaur_actor_models_keep_native_roles`
  - `mm8_crystal_dragon_actor_models_keep_native_sizes_and_roles`
  - `mm8_unicorn_actor_models_keep_native_tiers_gallop_and_horn`
  - `mm6_mm7_mm8_actor_models_build_every_binding` (647 descriptors on 185 models, 0 failed)

  These check the original clips by name (Walking, Running kept) and durations; none names a bound walk or run that
  changes meaning, so no diagnostic needs the new names. There is no case for the MM7 Chicken.

## Doubts

- **Unicorn wandering now walks** instead of a slow gallop (the native walk is a gallop; the project interpreted it
  so). At 0.46-0.51 units/s a gallop played ×0.72-0.80; a walk is the gait for that speed. Only Unicorn C failed the
  window; binding Walk2 for all three keeps the tiers alike.
- **Centaur hind-leg crease.** When a hind leg reaches far under the belly (Walk2 at mid-swing, Run2 at phase 0) the
  skin creases at the stifle, as it already does in the installed Running; it comes from the rig's weights.
- **Centaur Run2 is a canter**, the installed clips are trots; the rider's channels come from Running (a trot), whose
  upper-body sway runs once a loop and fits the canter's rhythm.
- **Crystal Dragon Walk2 head bob** is 0.6 % (Walking 2.5 %): the neck takes back the body's pitch.
- **Chicken Run2** has short flights (duty 0.40); a grounded run would need duty 0.5 and 8 steps a second.
- **MAW wandering** is unchanged by MAW for all four (no speed change), so nothing extra is ungated.

## Problems found in tools

- None in the shared tools. `quad_probe.py` and `low_probe.py` (q3's copies) were used on hooves, the hen's feet and
  the centaur; `low_probe.py` reported the centaur's hidden arrow (scale 0.001, collapsed at Root, 24 cm under the
  floor in the installed Running too) as the lowest vertex, hence `--skip`. `gait_gate.py`'s floor check passes it.
- The Chicken, Unicorn and Crystal Dragon viewers had no pages or GLBs (only a manifest), as q1 found for its models.

## Rebuild

From this directory:

```sh
blender -b --factory-startup -P scripts/gait_m544.py -- work/m544_clips.glb          # Unicorn Walk2
blender -b --factory-startup -P scripts/gait_m504.py -- work/m504_clips.glb          # Chicken Run2
blender -b --factory-startup -P scripts/gait_m548.py -- work/m548_clips.glb          # Crystal Dragon Walk2, Run2
blender -b --factory-startup -P scripts/gait_centaur.py -- work/centaur_clips.glb    # Centaur Walk2, Run2
G=../../claude_shared/graft_clips.py
python3 $G work/rollback/mm8_m544.glb work/m544_clips.glb export/mm8_m544.glb --clip Walk2
python3 $G work/rollback/mm7_7m504.glb work/m504_clips.glb export/mm7_7m504.glb --clip Run2
python3 $G work/rollback/mm8_m548.glb work/m548_clips.glb export/mm8_m548.glb --clip Walk2 --clip Run2
python3 $G work/rollback/mm8_centaur.glb work/centaur_clips.glb export/mm8_centaur.glb --clip Walk2 --clip Run2
python3 ../../../../tools/install_model.py export/<glb> --world <mm7|mm8> --name <glb>
```

The scripts read the projects' blends read only (paths under Scripts). A far-LOD repair rerun (`lod_repair_claude`) or
any rebuild of these GLBs must re-graft these clips.

**Rollback.** The pre-change sources are in `work/rollback/`. Install one with
`tools/install_model.py work/rollback/<glb> --world <w> --name <glb>`, then revert the q4 entries of `actors.yml`.
