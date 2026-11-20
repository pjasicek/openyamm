# MM6 Mep / PeasantM3 A/B/C reduction (2026-10-14, installed 2026-10-15)

User: "3D tris count reduction playbook - do mm6_mep". No-retexture route ([RETOPOLOGY_PLAYBOOK.md](../RETOPOLOGY_PLAYBOOK.md)).

**Base: the runtime model, not `assets_source`.** `base/mm6_mep.glb` and `base/mm6_mep_staff.glb` are copies of
`assets_dev/worlds/mm6/models/` (= `../mm6_mep_codex/export/`, round 3: Cast = Attack copy, Death 1.82 s, round-2 head
and sash, far-LOD textures downscaled). `assets_source` still holds an older round-1 export (Cast 1.23 s, Death 3.63 s,
round-1 head); the first pass used it by mistake and is archived in `stale_round1/` (see the end).

Body 10,066 tris, 8 influences, one texture set (body | 32 px gutter | head); weld 7,868 -> 904 open edges; limits for
the 1.692 m height p99 5.08 mm, max 25.38 mm. Staff 1,616 tris. Scripts: `../reduce_installed.sh` template plus
region scripts from `../mm6_natf_reduce_claude/` and `../mm6_nobl_reduce_claude/`; `scripts/build_pick.sh` and the
prop scripts read `base/`.

## Body

`scripts/region_prep.py` (atlases, components, colour classes from `base/`) -> `scripts/mep_regions.py g1 group`.
The round-2 head paints the face in grey and colours it through the skin ramp, so skin is found by the region mask's
skin channel (A), not by colour. Kept exactly: face skin plus one ring, eyes, buttons, the separate turban-top piece
(component 22; cut at 60 % it sank into the turban wrap and showed dark slits, first pass). Group ratios: hands 50 %,
turban wrap 60 %, beard 70 %, belt + sash ends 70 %; the rest takes the ladder budget. One drift-lock round
(`drift_lock.py`: drifted area 31.2 -> 6.5 cm2, shins and left forearm).

| config | step | tris | p99 / max mm | IoU | SSIM | |
|---|---|---:|---|---|---|---|
| source | | 10,066 | | | | |
| regions g3 | 70 % | 7,042 | 3.6 / 30.9 | 0.994 | 0.992 | fails max |
| regions g3 | 62 % | 6,236 | 4.5 / 23.8 | 0.991 | 0.990 | pass |
| regions g3 | 57 % | 5,834 | 5.3 / 23.8 | 0.988 | 0.988 | fails p99 |
| **g3 + drift lock** | **62 %** | **6,236** | 4.5 / 23.8 | 0.990 | 0.990 | **pick** |

## Staff

Prop chain (`prop_dump.py` -> `prop_ladder.py` -> `prop_build.py` -> `prop_swap_glb.py`): every step passes; r25 =
404 tris (max 0.28 % / 3.9 mm of 1.41 m), close-ups identical to installed. LOD chain 404 / 352 / 160.
Grip gate (`scripts/grip_gate_mep.py`, staff at the Staff joint as at runtime, every 2nd frame of every clip):
hand-to-shaft gap max 0.33 mm (installed 0.18), no hand vertex inside the staff before the Death release.

## Result

`export/mm6_mep.glb` (= `mm6_mep_g3dr62.glb`): **6,236 tris**, LODs 6,236 / 3,115 / 1,120 / 371 (installed 10,066 /
4,494 / 3,594 / 3,494); clips, textures, variants and sockets as installed. `export/mm6_mep_staff.glb`
(= `mm6_mep_staff_r25.glb`): **404 tris**.
Renders `review/close/sheet1_face.png` (face, installed / pick), `sheet2_{whole,back,head}.png` (Standing, Death 15,
Attack 20, Cast 20), `sheet3_final.png`. Viewer `review/viewer/` (installed vs pick, all variants and clips;
`check_viewer.mjs` 54 switches, no errors).

Install after review: back up `base/` as `work/mm6_mep{,_staff}_source_pre_reduce.glb`, then
`tools/install_model.py export/mm6_mep.glb --world mm6` and the same for the staff, the actor regression, ledger row.

## Archived first pass (`stale_round1/`, README_first_pass.md)

Reduction of the stale round-1 `assets_source` model, then a Meshy face retexture (10 credits,
`meshy/head_retexture_r62`, `texturing/head_upload.glb`) after the user found smeared eyes, nose and mouth on that
round-1 face. The runtime round-2 face does not have those defects, so the retexture is not used. Its tools
(`scripts/head_uv.py`, `compose_head.py`, `head_atlas.py`) remain as a worked example: turban texels copied per
triangle with rotated normals, overlap-free face charts, class-based luminance matching to the tier ramps.

## Installed (2026-10-15)

User picked "newest staged" after the model cook had rebuilt `assets_dev` from the stale round-1 `assets_source`.
`tools/install_model.py export/mm6_mep.glb --world mm6` and `export/mm6_mep_staff.glb` (sources now = this export);
no `actors.yml` change (clips as round 3). Previous sources (round 1) are `work/mm6_mep{,_staff}_source_pre_reduce.glb`;
round 3 unreduced is `base/`. Unit suite: only the three known unrelated failures. Timing review data rebuilt.

## Gait rollout (2026-10-31)

`mm6_mep.glb` gained `Walk2` (humanoid set Relax-Walk-Forward), `Jog` (Unarmed-Run-Forward) and `Sprint`
(Unarmed-Sprint, MAW B/C chase), arms and staff from Walking / Running (staff elbow bent forward in the run and sprint
so the staff foot stays off the floor). Bindings: `walking: Walk2`, `stride_length 1.374`, `run: Jog`,
`run_stride_length 2.205`, `sprint: Sprint`, `sprint_stride_length 4.098`. Details, gates and rebuild:
[package h04](../gait_rollout_20261031/h04/README.md) (`scripts/rebuild.sh mep`). A re-export or far-LOD repair rerun
must re-graft these clips (rerun the h04 rebuild on the new source).
