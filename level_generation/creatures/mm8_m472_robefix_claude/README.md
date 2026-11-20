# mm8_m472 Necromancer (monster): Run2 robe (robe fix, 2026-11-12)

Follow-up to the anim stream of the [MM6–MM8 audit fixes](../audit_mm678_20261111/fixes/ANIM.md) (part 1, deferred
on 2026-11-11), under [COMMON.md](../audit_mm678_20261111/fixes/COMMON.md) (lease `mm8:m472`, agent `fix-robes`).
Before: `work/before_robefix/mm8_m472.glb` (the installed file, SHA-256 32aca8ab…) and `work/before_robefix/actors_mm8.yml`.

## Problem

The 2026-10-21 Run2 (`../mm8_m472_claude/scripts/gait2_*.py`, Mixamo "Running (4)") pulled the floor-length robe into
a tent: 2.45 m fitted stride in 0.70 s, the garment simulation's leg enclosure padded by 0.07 m on every leg capsule
(thigh, calf, foot) and a 10 cm hem opening. Robe region 39.4 % bad in one frame (motion_audit, Standing 0.1), almost all
stretch on the two lower chain levels; calves through the robe in 48 % of samples, up to 111 mm
(`../mm8_m472_animfix_claude/scripts/skirt_poke_probe.py`); hem bands 7–11 cm wider than Standing.

## Fix

Run2 re-authored in a copy of the same pipeline (`scripts/`, copied from `../mm8_m472_claude/scripts/`; inputs
`work/rig_textured_uv.blend` and `work/necromancer_master.blend` copied from there), Run2 only, then grafted over the
installed Run2 (`scripts/gait2_graft.py` replaces it; the installed Walking re-exports with difference 0). Changes:

- **Shorter, quicker stride** (`gait2_fit.py`, `RF_FIT`): fitted stride 1.8 m in 15 frames (0.50 s; was 2.45 m in 21),
  lift 0.35, foot pitch 0.4, path shift 0.05 m, swing pull-in to 0.15 m behind the pelvis.
- **The pull-in no longer leaks into stance** (new fit key `gate` 0.02 m): the smoothed pull-in is faded out while a
  foot is within 2 cm of its planted level. Without the gate the planted foot stopped before toe-off, and the stride
  audit measured 1.35 m (2.7 m/s, tier C chase at 1.57x, outside the window); with it 1.571 m.
- **No thigh pad** (`garment_sim.py`, `RF_PAD`): enclosure pads thigh 0, calf 0.09, foot 0.09 (production 0.07 on all
  three). The thigh pad is what flares the robe at the hips (the Sorcerer lesson,
  [follow-up 2](../mm6_sor1_followup2_claude/README.md)); calf and foot pads are what keep the shins and heels inside
  between the 12 robe chains (no calf pad: pokes up to 120 mm).
- **Hem opening 0.04 m** (`gait2_cloth.py`, `RF_HEM`; was 0.10). Without any opening the back hem let the trailing calf
  through again (47 %).
- `actors.yml`: `run_stride_length` 2.12 -> **1.571** (the stride audit's measurement) on tiers A, B, C.

```sh
# from the repository root, under the lease
RF_TAG=i5 RF_FIT='{"frames":15,"stride":1.8,"lift":0.35,"pitch":0.4,"shift":0.05,"back":0.15,"gate":0.02}' \
  RF_PAD='{"Thigh":0,"Calf":0.09,"Foot":0.09}' RF_HEM=0.04 \
  level_generation/creatures/mm8_m472_robefix_claude/scripts/run_candidate.sh <token>
cp level_generation/creatures/mm8_m472_robefix_claude/work/i5/mm8_m472.glb level_generation/creatures/mm8_m472_robefix_claude/export/
```

`run_candidate.sh` runs `gait2_motion.py`, `gait2_cloth.py` and `gait2_export.py` in Blender (one at a time), grafts and
audits. `RF_TAG=base` with the defaults reproduces the installed Run2 exactly (39.4 / 35.1). `gait2_cloth.py` also has
`RF_NOCLEAR` and `RF_SMOOTH` switches, tried and not used (skipping the robe-out-of-shoe correctives puts 11 robe
vertices in the shoes and lifts the body; the smoothing breaks the loop seam).

## Candidates (Run2; cloth = motion_audit robe region %, poke = samples with a calf through the robe / farthest)

| tag | stride / frames | pads thigh/calf/foot, hem | cloth | poke | measured stride, speed |
|---|---|---|---:|---|---|
| base | 2.45 / 21 | .07/.07/.07, .10 | 39.4 | 48 %, 111 mm | 2.233, 3.19 m/s |
| a | 1.8 / 15 | 0/.03/.03, .04 | 14.4 | 40 %, 91 mm | 1.348, 2.70 (too slow) |
| b | 2.0 / 15 | 0/.03/.03, .04 | 20.0 | | 1.552, 3.10 |
| c | 1.8 / 15, no pull-in | 0/.03/.03, .04 | 14.3 | 67 %, 175 mm | 1.583, 3.17 |
| f, g | 1.8 / 13, 14 | 0/.03/.03, .04 | 19.9, 19.4 | | 2.94, 2.89 |
| h | 1.8 / 15, gate | 0/.03/.03, .04 | 15.7 | 47 %, 89 mm | 1.591, 3.18 |
| i1 | as h | 0/.07/.07, .04 | 13.2 | 27 %, 44 mm | 1.571, 3.14 |
| i3 | as h | 0/.10/.10, .04 | 15.2 | 7 %, 7 mm | |
| **i5** | as h | **0/.09/.09, .04** | **14.6** | **7 %, 19 mm** | **1.571, 3.14** |
| i6 | as h | 0/.10/.10, 0 | 14.0 | 47 %, 53 mm | |

## Numbers and checks (installed)

| | before | after |
|---|---|---|
| Run2 cloth (Standing 0.1) | 39.4 (39.3 beyond) | **14.6 (14.5 beyond)** |
| Run2 leg (calf and ankle skin) | 35.1 | 28.3 |
| Run2 other regions | hand 6.8, arm 15.3, spine 4.7, other 13.7 | hand 6.8, arm 15.5, spine 4.2, other 14.7 |
| calves through the robe | 48 %, 111 mm | 7 %, 19 mm |
| hem half-width over Standing, 0.2–0.4 m / 0.4–0.6 m (L/R cm, `../mm6_sor1_followup2_claude/scripts/bulge_probe.py`) | +3.7/+10.7, +0.4/+7.1 | +0.4/+5.7, -2.4/+4.9 (hips -2.7/-1.7) |
| length, stride, authored speed | 0.70 s, 2.12 bound (2.233 measured) | 0.50 s, 1.571 (measured 1.571), 3.14 m/s |
| chase rates A/B/C (Standard and MAW) | 1.17 / 1.29 / 1.40 | 1.13 / 1.24 / 1.35 |

- `glb_diff.py`: only Run2's samplers changed (the old Run2 accessors stay unused in the buffer). Every other clip's
  motion_audit row is identical. Loop pop 0.
- Winding 0 inverted closed parts. `floor_audit.py` 0 problems; `gait_audit.py` Standard and MAW 0 flagged;
  `stride_audit.py` binding x1.00.
- Arm and hand gate (`scripts/gait2_arm_gate.py` on `work/i5/gait2_gated.blend`): pass; wrist swing 40°, forearm
  twist 84°, no hand in the trunk, hand stretch 2.22; hand step per half frame 21° (was 16°: the same Mixamo arm pump
  in a shorter cycle).
- `check_deformation.py` (`work/i5/deformation.json`): robe vertices inside a shoe at most 2 (was 3), 8 mm deep (was 7);
  robe edge stretch max / p99 9.3 / 2.02 (was 12.3 / 2.60).
- Regression: `mm6_mm7_mm8_actor_models_build_every_binding` passes (647 descriptors, 0 failed;
  `work/regression_every_binding.log`), `mm8_necromancer_actor_models_keep_tiers_and_dual_cast` passes.
- Viewer: `review/viewer/` (`anim_viewer.py`), `run_creature_review.py check`: no console errors, 66 switches.
- Shots (audit compare viewer, left HEAD, right installed; side and three-quarter at 0, 0.25, 0.5, 0.75 of the
  clip): before `review/before_run_*.png`, `review/before_sheet.png`; after `review/after_run_*.png`,
  `review/after_sheet.png`. Candidate shots `review/{a,c,h2,i5}_*`, private compare viewer `review/cmp/`
  (`../mm6_sor1_followup2_claude/scripts/build_cmp.py`), captured with `scripts/shots.mjs` (1500x1100, stage only).

Revert:

```sh
python3 tools/install_model.py level_generation/creatures/mm8_m472_robefix_claude/work/before_robefix/mm8_m472.glb --world mm8
python3 level_generation/creatures/audit_mm678_20261111/fixes/anim_tools/binding_set.py --world mm8 --model mm8_m472.glb animation.run_stride_length=2.12
```
