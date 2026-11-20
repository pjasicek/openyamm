# MM6 Sorcerer (mm6_sor1): robe hip bulge in Walking and Jog (follow-up 2, 2026-11-12)

Follow-up to the [anim fix of 2026-11-11](../mm6_sor1_animfix_claude/README.md), under the rules of the
[audit fixes](../audit_mm678_20261111/fixes/COMMON.md) (lease `mm6:sor1`). Before: `work/before_followup2/mm6_sor1.glb`
(the 2026-11-11 install, SHA-256 e9605af8…); `actors.yml` is unchanged.

## Problem

The user, in the [compare viewer](../audit_mm678_20261111/compare_viewer/?role=walking#mm6_sor1): the robe below the
belt now balloons out sideways at both hips in the Walking (a bell), where the old walk hung straight. The Jog had the
same bulge (the 2026-10-31 h03 Jog too, wider still).

## Cause

The re-simulation (`resim_cloak.py`, cloak.py preset `sor1`) ran with `leg_pad` 0.03. That pad widens every leg
capsule, the thigh capsules included. The robe chains hang from `B_Pelvis` at hip height, so their first points sit
right against the padded thighs, and the one-sided collision pushes them out sideways. The robe then flares from the
belt. Measured (`scripts/bulge_probe.py`: the robe's sideways half-width per height band, the largest over the clip
minus Standing, left/right cm):

| Band (m above floor) | 0.95–1.05 | 0.85–0.95 | 0.75–0.85 |
|---|---|---|---|
| Walking, HEAD (Codex bake) | -0.1 / -0.4 | -0.1 / -0.1 | -0.4 / -2.0 |
| Walking, 2026-11-11 | **+3.3 / +3.2** | **+3.9 / +3.8** | **+3.4 / +2.1** |
| Walking, now | +0.3 / +0.1 | +0.2 / +0.2 | -0.1 / -1.8 |
| Jog, HEAD (h03) | +4.4 / +3.5 | +7.2 / +3.6 | +7.5 / +2.0 |
| Jog, 2026-11-11 | +3.3 / +3.2 | +3.8 / +3.7 | +3.6 / +1.9 |
| Jog, now | -0.1 / -0.3 | -0.4 / -0.4 | 0.0 / -1.9 |

## Fix

The same simulation over the same installed bodies (body, arms, staff and every other clip unchanged; only the 64 robe
chain joints of Walking and Jog re-keyed). `scripts/cloak.py` (copy of the animfix one) has a new spec key
`thigh_pad` (the pad on the thigh capsules alone; it defaults to `leg_pad`, so other users are unchanged):

- Walking: `leg_pad` 0 (no pad at all). This matches the HEAD walk's hip widths; legs through the robe stay 0 %.
- Jog: `leg_pad` 0.03 on the calves and feet, `thigh_pad` 0. With no pad at all, a back calf poked through the hem
  (12 % of samples, 24 mm). With the calf pad kept, it does not (0 %).

```sh
cd level_generation/creatures/mm6_sor1_followup2_claude
python3 ../audit_mm678_20261111/fixes/anim_tools/resim_cloak.py work/before_followup2/mm6_sor1.glb work/try/walk_pad0.glb \
    Walking '{"chains": "work/sor1_robe_chains.json", "preset": "sor1", "leg_pad": 0}'
python3 ../audit_mm678_20261111/fixes/anim_tools/resim_cloak.py work/try/walk_pad0.glb export/mm6_sor1.glb Jog \
    '{"chains": "work/sor1_robe_chains.json", "preset": "sor1", "leg_pad": 0.03, "thigh_pad": 0}'
```

## Numbers and checks

| Clip | Cloth bad % (motion_audit; Standing 0.7): HEAD / 11-11 / now | Legs through robe (`skirt_poke_probe.py`) | Loop pop |
|---|---|---|---|
| Walking | 21.9 / 11.1 / **5.8** | 0 % | 0 |
| Jog | 37.5 / 14.0 / **14.9** | 0 % | 0 |

- `glb_diff.py`: only Walking and Jog sampler data changed (Jog's resim appends new time accessors).
- Winding 0 inverted closed parts. `floor_audit.py` 0 problems. `gait_audit.py` (Standard and MAW) shows 0 flagged.
  Strides are unchanged.
- Regression, the whole actors suite (`../mm7_m174_followup2_claude/work/regression_actors_rerun.log`): 191 passed, 2 failed.
  `mm6_mm7_mm8_actor_models_build_every_binding` and `mm6_sorcerer_actor_model_tiers_share_the_native_height` pass.
  The two failures are unrelated: 42 MM9 maps without models, and `out05_event_clearance`. The first run
  (`regression_actors.log`) failed 66 cases on one mm6 texture that another agent's install re-cooked mid-run.
- Viewer: `review/viewer/` (`run_creature_review.py --project ... check`), no console errors, 54 switches.
- Shots (compare viewer, left HEAD, right installed): `review/final_sheet.png` (Walking and Jog front),
  `review/final_walk_front_t0.25.png`, `final_walk_front_t0.75.png`, `final_run_front_t0.25.png`. The 2026-11-11
  state as the user saw it: `review/cmp_walk_front_t0.25.png`, `cmp_run_front_t0.25.png`. Candidates against HEAD
  and the 11-11 install: `review/c2_*.png`, `review/cmp/` (private compare viewer, `scripts/build_cmp.py`).

Revert: `python3 tools/install_model.py level_generation/creatures/mm6_sor1_followup2_claude/work/before_followup2/mm6_sor1.glb --world mm6`
(the 11-11 install), or `../mm6_sor1_animfix_claude/work/before_anim/mm6_sor1.glb` together with that folder's
`actors_mm6.yml` (`run_stride_length` 2.6955) for the state before both fixes.
