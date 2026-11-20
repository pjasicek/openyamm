# mm6_mnk1 BMonk: Run2 robe (robe fix, 2026-11-12)

Follow-up to the anim stream of the [MM6–MM8 audit fixes](../audit_mm678_20261111/fixes/ANIM.md) (part 1, skipped on
2026-11-11: `../mm6_mnk1_animfix_claude/`), under [COMMON.md](../audit_mm678_20261111/fixes/COMMON.md) (lease `mm6:mnk1`,
agent `fix-robes`). Before: `work/before_robefix/mm6_mnk1.glb` (the installed file, SHA-256 b1a28ff5…) and
`work/before_robefix/actors_mm6.yml`.

## Problem

The robe hangs on virtual legs (`../mm6_mnk1_codex/README.md`, gait rework 2026-10-21): `Cloth_<s>_Thigh` swings 40 % of
the thigh, `Cloth_<s>_Calf` runs from that knee to the real ankle (stretched or squashed along its length), and the hem
hangs on `Cloth_<s>_Foot`, a child of the real foot. Run2 (Mixamo "Standard Run", 2.83 m measured stride in 0.67 s) put
the two robe halves as far apart as the feet: the front and back seams sheared into flat sheets on the floor, the heel
kick squashed the virtual calf to 0.48 of its length, and the hem rode on the boots. Robe region 37.6 % bad
(motion_audit; Standing 8.3, so 29.3 beyond). The animfix attempt (damping the GLB's virtual legs, `virtual_legs.py`)
got no better than 33.5 %: it carries the rest ankle down with the lowered run pelvis and squashes the robe.

## Fix

Run2 re-authored in a copy of the Codex pipeline (`scripts/gait2_author.py`, `gait2_export.py`, `gait2_graft.py`;
input `work/mm6_mnk1.blend`, a copy of `../mm6_mnk1_codex/export/mm6_mnk1.blend`), Run2 only, and grafted over the
installed Run2 (the re-exported Walking matches the installed one exactly). Changes:

- **Shorter, quicker stride:** fitted stride 1.6 m in 15 frames (0.50 s; was 2.55 m in 20 frames, 0.67 s); everything
  else in the Run2 cfg as before (lift 0.45, robe thigh share 0.4, pelvis 0.925, lean 11°).
- **The robe follows damped legs** (new `robe_legs` rule, `RF_HEM`): the virtual ankle keeps half (`follow` 0.5) of
  the real ankle's fore-aft offset from the hip centre, so the robe halves shear apart half as far as the feet; the
  virtual calf keeps 0.85–1.05 of its rest length (the heel kick no longer squashes it); the hem bone
  `Cloth_<s>_Foot` hangs at that calf's end with half the real foot's rotation instead of riding on the boot.
  The cloth-only floor offsets needed no lift (0 mm).
- `actors.yml`: `run_stride_length` 2.8283 -> **1.777** (the stride audit's measurement) on tiers A, B, C.

```sh
# from the repository root, under the lease
RF_TAG=s4 RF_RUN='{"stride":1.6,"frames":15}' RF_HEM='{"calf_min":0.85,"calf_max":1.05,"foot_rot":0.5,"follow":0.5}' \
  level_generation/creatures/mm6_mnk1_robefix_claude/scripts/run_candidate.sh <token>
cp level_generation/creatures/mm6_mnk1_robefix_claude/work/s4/mm6_mnk1.glb level_generation/creatures/mm6_mnk1_robefix_claude/export/
```

`run_candidate.sh` runs `gait2_author.py` and `gait2_export.py` in Blender, grafts (`gait2_graft.py` replaces Run2),
audits and measures the stride. `RF_TAG=base` with no overrides reproduces the installed Run2 exactly (37.6).

## Candidates (Run2 robe region %, Standing 8.3)

| tag | stride / frames | robe rule | cloth | measured stride, speed |
|---|---|---|---:|---|
| base | 2.55 / 20 | 2026-10-21 | 37.6 | 2.828, 4.24 m/s |
| r1 | 1.9 / 15 | 2026-10-21 | 28.5 | 2.158, 4.32 |
| r2 | 1.6 / 15 | 2026-10-21 | 26.7 | 1.777, 3.55 |
| r3 | 1.6 / 15, lift 0.35, thigh 0.3 | 2026-10-21 | 28.2 | 1.586, 3.17 |
| r2 + `virtual_legs.py` (4 settings) | | GLB damping | 29.4–30.7 | |
| s1, s2 | 1.6 / 15 | calf 0.85/0.95–1.05, hem on calf end, no follow | 29.6, 29.0 | |
| s3 | 1.6 / 15 | as s4, follow 0.7 | 25.3 | |
| **s4** | **1.6 / 15** | **follow 0.5, calf 0.85–1.05, foot rot 0.5** | **21.6** | **1.777, 3.55** |

## Numbers and checks (installed)

| | before | after |
|---|---|---|
| Run2 robe (cloth) region | 37.6 (29.3 beyond Standing) | **21.6 (13.3 beyond)** |
| Run2 hotspot | Cloth_R_Calf 58.8 % | Cloth_R_Thigh 41.4 % |
| virtual calf length (scale) | 0.48–1.15 | 0.85–1.05 |
| length, stride, authored speed | 0.667 s, 2.8283 (measured 2.828), 4.24 m/s | 0.500 s, 1.777 (measured 1.777), 3.55 m/s |
| chase rates A/B/C (Standard and MAW) | 0.90 / 0.99 / 1.08 | 1.07 / 1.18 / 1.28 |

- `glb_diff.py`: only Run2 changed (samplers; `Cloth_<s>_Foot` translation and rotation are now animated, so their
  constant STEP channels became LINEAR). Every other clip's motion_audit row is identical; loop pop 0; hands inside
  the body 0; spine 3.5 -> 3.2. The arms keep the native folded Standing pose (author rule unchanged).
- Winding 0 inverted closed parts. `floor_audit.py` 0 problems; `gait_audit.py` Standard and MAW 0 flagged;
  `stride_audit.py` binding x1.00 (its foot-joint measurement, 1.147, now follows the damped hem bones, which are leaf
  joints named Foot; the vertex measurement equals the boots' stride of candidate r2, where the hem rode on the boots).
- Regression: `mm6_mm7_mm8_actor_models_build_every_binding` passes (647 descriptors, 0 failed;
  `work/regression_every_binding.log`), `mm6_monk_actor_model_tiers_share_the_native_height` passes.
- Viewer: `review/viewer/` (`anim_viewer.py`), `run_creature_review.py check`: no console errors, 66 switches.
- Look (compare viewer, side, three-quarter, front, back): the robe hangs and swings as one garment; boots show only
  under the front hem; no sheets on the floor, no boot through the cloth. (A numpy boot-through-robe probe, the
  skirt poke probe with boot points, was tried and dropped: its rays meet the robe's inner panels between the legs.)
- Shots, audit compare viewer (left HEAD = before, right installed; the BMonk was added to it by re-running its
  `build.py`): before `review/before_run_*.png` / `review/before_sheet.png` (private viewer `review/cmp/`, built with
  `scripts/build_cmp.py`, same layout), after `review/after_run_*.png` / `review/after_sheet.png`; candidates
  `review/{r2,s4}_*`.
- Not in scope and unchanged: Walk2's robe (25.8, 17.5 beyond Standing).

Revert:

```sh
python3 tools/install_model.py level_generation/creatures/mm6_mnk1_robefix_claude/work/before_robefix/mm6_mnk1.glb --world mm6
python3 level_generation/creatures/audit_mm678_20261111/fixes/anim_tools/binding_set.py --world mm6 --model mm6_mnk1.glb animation.run_stride_length=2.8283
```
