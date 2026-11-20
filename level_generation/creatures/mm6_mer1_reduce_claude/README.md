# MM6 Merchant (`mer1`, Merchant A/B/C) reduction (installed 2026-10-14)

User: "do merchant", then (asked about the earlier body-only instruction) "head and hands too". No Meshy.

## Source

The game runs Codex round 3 (`../mm6_mer1_codex/export/mm6_mer1.glb`, sha256 `cc687d18…`, copied into `assets_dev`
directly while that project is on QA hold); `assets_source/worlds/mm6/models/mm6_mer1.glb` is an older 9,546-triangle
single-material model. Input here: the round-3 export (`work/mm6_mer1_installed_r3.glb`): 14,954 triangles = clothing
6,998 + head 4,946 + hands 3,010 (three texture sets), LODs 2,399 / 1,727 / 682 (an 84 % drop at the first switch).
Installing this result through `tools/install_model.py` also replaces the stale source.

## Reduction

A uniform ladder (`work/selection.json`) fails every step (p99 above 5.1 mm, max 52+ mm already at r70) and flattens the
lips from r55 (`review/close/sheet4_head.png`). `scripts/decimate_tex.py` gained `REA_HEAD_RATIO`: with
`REA_PROTECT_HEAD=1` the head faces (B_Head dominated, 4,790) are decimated separately at that ratio instead of kept,
both parts keeping their shared cut edge (open edges stay at the source's 652, no cracks).

| variant | tris | head / body / hands | |
|---|---:|---|---|
| installed r3 | 14,954 | 4,946 / 6,998 / 3,010 | |
| head 85 %, rest 45 % | 8,642 | 4,192 / 3,372 / 1,078 | |
| **head 70 %, rest 45 %** | **7,924** | 3,474 / 3,372 / 1,078 | **picked** |
| head 55 %, rest 45 % | 7,206 | 2,756 / 3,372 / 1,078 | jaw line starts to facet |
| head 85 %, rest 35 % | 7,626 | 4,184 / 2,680 / 762 | palms angular |

Review: `review/face/sheet.png`, `sheet2.png` (face profile and three-quarter), `review/close/sheet_h85_{head,hand}.png`
(hand close-ups: fingers kept at r45), `review/pose/sheet_h85.png` (Attack, Walking, Death, Hit; front and side).
Trial viewer models are in `work/viewer_trials/`.

## Result

`export/mm6_mer1.glb`: LODs **7,924 / 3,959 / 1,423 / 472** (installed 14,954 / 2,399 / 1,727 / 682). Textures (three
sets), variants (carried to every LOD/shadow primitive), clips, the Club socket and the separate club GLB unchanged;
no collapsed meshes. Viewer `review/viewer/` (installed vs reduction, A/B/C, all clips): `check_viewer.mjs` 48 loads,
no errors.

## Installed

User accepted (2026-10-14). Previous runtime (Codex round 3) backed up to `work/mm6_mer1_runtime_r3_pre_reduce.glb`,
the stale source to `work/mm6_mer1_source_stale_pre_reduce.glb`; installed with `tools/install_model.py` (runtime
back-face pass: 1,097 back copies). `mm6_merchant_actor_model_tiers_share_the_native_height` passes; the `actor_model`
cases were run after install. Ledger row added. The Codex project's own QA findings (contact, grip) remain open there.

## Gait rollout (2026-10-31, package h05)

New in-place locomotion clips appended to the installed `assets_source/worlds/mm6/models/mm6_mer1.glb` (every existing
clip, mesh, skin and material unchanged): Jog (humanoid set Relax-Run-Forward, 0.72 s, 1.88: a short, low shuffling jog under the robe). Bindings for Merchant A-C (applied by the rollout coordinator from
`../gait_rollout_20261031/h05/bindings.yml`): run Jog, run_stride_length 1.88. Details, gates and doubts:
[package h05](../gait_rollout_20261031/h05/README.md). Rebuild: `../gait_rollout_20261031/h05/scripts/rebuild.sh mer1`
from the pre-gait copy `work/mm6_mer1_pre_gait.glb` there. A far-LOD repair (`lod_repair_claude`) or head-bob rerun on
this model must re-graft these clips (copy the repaired source over that pre-gait copy and rerun the rebuild).
