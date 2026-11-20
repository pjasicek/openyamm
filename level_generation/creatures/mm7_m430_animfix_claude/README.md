# MM7 Wight (mm7_m430): anim fix (2026-11-11)

Stream `anim` of the [MM6–MM8 audit fixes](../audit_mm678_20261111/fixes/ANIM.md), part 1 (robes in the gait clips).
Production project: [mm7_m430_claude](../mm7_m430_claude/README.md). Started from the installed source
(`work/before_anim/mm7_m430.glb`, SHA-256 b551e18d…, with `actors_mm7.yml` beside it); one copy reverts it.

## Walking: the robe pulled into long sheets

**Audit:** cloth region 41.6 % bad in Walking against 2.7 % in Standing (38.9 beyond Standing), hotspot `B_Skirt0`
73.8 %. Walking plays whenever a Wight wanders.

**Cause (not the clip, not the weights):** the 2026-10-21 floor fix ran
`floor_fix.py --lift-joints … Walking --lift-only 'B_Skirt*,…'` before `--ground-loop Walking`. The Mixamo walk carries
the pelvis 4–11 cm lower than Standing, so the robe hem (55 % pelvis/skirt bones, 45 % legs) dipped up to 16.5 cm under
the floor; the lift bent all eight skirt bones up to 35° outward to raise it, which flared the robe into a bell and
stretched the panels between the legs. The pre-floor-fix export (`../mm7_m430_claude/work/floor_fix_base/`) measures
7.5 % on the same clip, which proved it.

**Fix** (`scripts/skirt_rest.py`, then the floor tool):

```sh
python3 scripts/skirt_rest.py work/before_anim/mm7_m430.glb work/w1_skirtrest.glb --clips Walking
python3 ../claude_shared/floor/floor_fix.py work/w1_skirtrest.glb work/w2_ground.glb --ground-loop Walking
```

The skirt bones go back to rest (following the pelvis) in Walking only, then the whole body is grounded per key on the
hem instead (root raised 4–16 cm; the hidden legs have no geometry). Head height while walking is now 1.47–1.52 m
against Standing's 1.46 and the accepted Jog's 1.46–1.51 (it was 1.35–1.43, a dip at every walk start); head second
difference per key 2.1 cm (installed 3.8). Only the nine Walking samplers changed (`glb_diff.py`: 8 skirt rotations, 1
root translation); meshes, skins, other clips byte-identical.

| Measure | Before | After |
|---|---|---|
| Walking cloth bad (beyond Standing 2.7) | 41.6 (38.9) | 7.5 (4.8) |
| Walking spine / arm / hand / head | 6.8 / 3.8 / 3.4 / 2.2 | 5.9 / 3.8 / 3.4 / 2.2 |
| Walking peak speed (H/s), hand inside | 3.1, 0.2 % | 1.25, 0 % |
| Other nine clips | | unchanged (`audit_after/mm7_m430.json`) |

Checks: `check_winding.py` 0 inverted; installed with `tools/install_model.py --world mm7` (source SHA-256 3469c45e…);
`floor_audit.py --world mm7 --match 'Wight*'` 0 problems (walk −0.0..+0.0); `gait_audit.py` 0 flagged (Walking
x0.89–1.09, Jog x0.94–1.15; strides unchanged, the gait's foot joints only moved vertically); regression
`mm6_mm7_mm8_actor_models_build_every_binding` PASS (647 descriptors, 0 failed); viewer
(`review/viewer/`, built by `../audit_mm678_20261111/fixes/anim_tools/anim_viewer.py`) `check` no console errors,
60 tier/clip switches. Arm and hand gate: no arm, hand or prop channel changed; hand-inside 0 %. Sheets:
`review/before_walking_{side,front}.png`, `review/after_walking_{side,front}.png` (red = bad triangles),
`review/walking_viewer_before_after.png` (viewer, tier A, top installed, bottom fixed).

**Do not** rerun the October floor fix with `--lift-joints Walking` on this model: ground Walking with
`--ground-loop` alone. Death and Dead keep their skirt fold (cloth 65–71 %: the corpse's shroud, by design, not in
scope).
