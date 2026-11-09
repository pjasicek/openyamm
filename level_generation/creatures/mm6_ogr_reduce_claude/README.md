# MM6 Ogre (`ogr`, Ogre A/B/C) reduction (2026-10-14)

User: "3D tris count reduction playbook - do ogre". No-retexture route ([RETOPOLOGY_PLAYBOOK.md](../RETOPOLOGY_PLAYBOOK.md))
on the installed `mm6_ogr.glb` (12,166 tris, one merged body + head atlas material, three variants, eight
influences; project `../mm6_ogr_claude/`). Scripts copied from `../mm6_fgt_reduce_claude/`. No Meshy credits.
Limits for the 1.6 m bind height: p99 4.8 mm, max 24 mm. The sword (236 tris) is already light and is not touched.

## Per-region budgets

The welded mesh is one main body plus 28 separate armour pieces. Of the main body's 9,038 faces, the Meshy 7.1 head
has 3,784 and the hands 3,606 (the sword fist alone 2,748); torso, arms and legs together are only 1,648. A uniform
cut fails at every step (max 42 mm at the neck front, even at 70 %).
Groups (`scripts/make_groups.py`, `scripts/region_faces.py`, `scripts/components.py`): 1 head, 2 left hand,
3 right hand, 4 armour pieces (pauldrons, horns, bracers, shin wraps, belt, loin panels, harness), 0 the rest.
`scripts/run_groups.sh` converts a rest-of-body ratio to the ladder ratio.

| config | triangles | p99 / max mm | finding |
|---|---:|---|---|
| uniform 70-45 % | 8,516-5,474 | 3.0-6.4 / 42-46 | fails: neck front |
| head 50/60/70 %, right hand 35-40 %, left 60 %, armour 70 %, rest 80 % | 7,062 / 7,578 / 7,956 | 4.3 / 20.2 | skull medallion loses its face (clay) |
| same, rest 60 % | 6,732-7,626 | 5.9 / 43.7 | fails: right shoulder blade folds in Attack |
| + skull medallion and pieces up to 80 faces kept (spikes, rivets, buckles), head 50/45/40 %, rest 80 % | 7,166 / 6,976 / 6,786 | 4.5 / 20.2 | 40-45 % soften the eye creases a little (texture covers it) |
| rest 70 % | 6,620-7,000 | 5.2 / 44.2 | fails: shoulder blade again |
| **c45: head 45 %, one drift-lock round** | **7,018** | 4.5 / 20.2 | **pick**; IoU 0.992, SSIM 0.992 |

Pick `c45r57` (`work/keep_c.npy`, `work/groups_a.npy`, ratios head 0.45 / right hand 0.35 / left hand 0.6 /
armour 0.7, rest 0.8): head 3,784 -> 1,702, right fist 2,748 -> 961, left hand 858 -> 514; the skull medallion,
bracer spikes, rivets and buckles kept exactly. Texture drift (`texture_drift.py`): 5 faces above 40 on the
45 % step (bracer, arm band, pauldron back); one `drift_lock.py` round (+150 kept source faces, +42 tris) leaves
none, p99 18.

Grip (`scripts/grip_gate_posed.py`, sword at the posed `Sword` joint): the mace-handle radius of the copied gate does
not fit the sword, so only the relative numbers count: hand vertices near the hilt scale with the fist's vertex
count (0.55 of the source's), nearest 3.4 mm vs 3.0 mm. `review/props/grip_sheet.png` (Standing, mid-Attack): same
grip.

## Result (installed 2026-10-14)

`export/mm6_ogr.glb` (= `mm6_ogr_c45r57.glb`): LODs 7,018 / 3,509 / 1,258 / 415 (installed 12,166 / 6,097 / 2,197 /
725), fitted shadow LODs rebuilt, variants carried to every primitive, eight influences, 8 clips unchanged.
LOD0 with the sword 12,402 -> 7,254 (-42 %).
Review: `review/faces/s2.png` (face, rows installed, head 50/45/40 %), `review/faces/s2_face_close.png` (clay face:
installed, 45 %, 40 %), `review/faces/s3.png` (back, belt, legs, hands; rows installed, pick, then both at Attack
frame 30), `review/faces/s1*.png` (first configs), `review/props/grip_sheet.png`, `review/ladder_sheet.png`.
Viewer `review/viewer/` (body only, installed vs pick per variant; `check_viewer.mjs` 48 switches, no console errors).

Install after review: `tools/install_model.py level_generation/creatures/mm6_ogr_reduce_claude/export/mm6_ogr.glb --world mm6`,
then the `mm6_ogr_actor_models_bind_all_tiers` regression and a ledger row in
[REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md). Rollback source: `work/mm6_ogr_source_pre_reduce.glb`
(sword: `work/mm6_ogr_sword_source_pre_reduce.glb`, unchanged).

## Installed (2026-10-14)

User: "accepted". `export/mm6_ogr.glb` installed with `tools/install_model.py` (runtime back-face pass: 824 back copies); sword unchanged. `mm6_ogr_actor_models_bind_all_tiers` passes (`review/checks/ogr_regression.log`). The source had no coincident vertices with different weights, so the later weld fix (`../mm6_kni_reduce_claude/`) does not affect this pick.

## Floor fix — 2026-10-21

`--ground-loop Walking --ground-loop Running --raise Hit`. Before, in world units at tier A: walking sinks to -4.7; Running sinks to -8.8; Hit sinks to -9.9; Walking sinks to -4.7.
Applied by [`floor_fix.py`](../claude_shared/floor/README.md) to the installed source (kept in
`work/floor_fix_base/mm6_ogr.glb`), written to `export/mm6_ogr_floor.glb` and installed as `mm6_ogr.glb`; only animation
samplers changed. Earlier exports and the editable `.blend` master predate it: rerun the same operation after any
re-export. Part of the [creature post-process](../CREATURE_POSTPROCESS.md) MM6 pass.
