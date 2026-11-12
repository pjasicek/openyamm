# Thunderbird / Roc texture quality pass (MM8 `mm8_m552`, MM7 `mm7_m390`) — 2026-11-11

Stream texpass-1 of the [MM6–MM8 audit fixes](../audit_mm678_20261111/fixes/TEXPASS.md), recipe
[TEXTURE_QUALITY_PASS.md](../claude_shared/TEXTURE_QUALITY_PASS.md) and
[texpass_mm678/HANDOFF.md](../claude_shared/texpass_mm678/HANDOFF.md). Only UVs, images and texture references
changed. Leases `mm8:m552` (this project) and `mm7:m390` (held through
[mm7_m390_texpass_claude](../mm7_m390_texpass_claude/README.md), a pointer project; tokens in each `work/LEASE.txt`).
Production: [mm8_m552_claude](../mm8_m552_claude/README.md), reductions
[mm8_m552_reduce_claude](../mm8_m552_reduce_claude/README.md) and [mm7_m390_reduce_claude](../mm7_m390_reduce_claude/README.md).
Scripts are the generic kit of [mm6_demon_texpass_claude](../mm6_demon_texpass_claude/README.md) (`tp_*.py`,
config `texpass.json`, MM7 `texpass_mm7.json` via `TP_CONFIG`) plus `tp_fix_collapsed.py`, `tp_upload.py`,
`tp_joint_pos.py`, `tp_checks.sh` added here.

## Texture quality pass (2026-11-11)

**Cause.** One 2K body set on the old Smart UV layout at 13.2 % of the atlas (1,845 islands, 25.8 % of the surface on
fragments). The MM7 Roc is the same body and the same images with MM7 ramps, but its own reduction (6,237 against
6,867 LOD0 triangles), so it cannot take the MM8 layout as is.

**Route.**
1. `tp_uv.py` on the MM8 LOD0 (head = Head, Neck, HeadSocket x1.8). Three runs: `uv_fine` (fast packer, 59.0 %,
   6.1 % fragments), **`uv_v2`** (`cut_closed=1 max_stretch=1.8 retry_stretch=3.0 merge_below=20 fine=250 steps=0`,
   55.9 %, 5.2 %), `uv_v3` (merge_below 30, max_cost 3: 54.8 %, 5.6 %). Every run left one chart of the left hand
   wing collapsed onto a point (Blender "failed to solve 1 island"; 41–46 triangles with zero UV area).
   `tp_fix_collapsed.py` re-lays such groups by a planar projection into a free rectangle (here 27 triangles at x0.7
   density) -> **`work/uv_v2_fixed.npz`, the paid layout; never re-run it**; `tp_upload.py` wrote its upload.
2. Retexture `requests/body_retexture_v1.json` (the production HD masters `references_hd/01`–`04`, meshy-7, 4K),
   job `body_retexture_v1`, **10 credits**. Layout kept (56.0 %, 432 islands). No head paint (bird head 2.1 % of the
   surface, no close head masters).
3. `tp_resample.py`, `tp_bake_ao.py` (reach 0.02 m for the 0.69 m span), `tp_compose.py` (classes: body feathers
   region 0, flight feathers region 1, the unmasked beak/talons; normal tilt x0.61 to the approved p90).
4. `tp_apply.py` on the installed MM8 GLB; on the MM7 GLB with `--copy`: its LOD0 and LOD1 take, per triangle, the
   MM8 LOD0 chart under them (worst corner 45 mm at feather tips), the same images, MM7 materials and ramps kept.
   LOD2/LOD3 maps refilled from each world's new LOD0.

## Results (`texture_quality.py`, LOD0)

| | MM8 before | MM8 after | MM7 before | MM7 after |
|---|---|---|---|---|
| Atlas use | 13.2 % | **56.0 %** | 12.9 % | **53.8 %** |
| Equivalent square | 745 px | 1,532 px | 734 px | 1,503 px |
| Density p50 | 840 | 1,723 | 837 | 1,722 |
| Islands / fragments | 1,845 / 25.8 % | 432 / 5.3 % | 1,601 / 30.6 % | 482 / 10.8 % |
| Stretch p90 | 1.49 | 1.16 | 1.60 | 1.26 |

Fragments: the remaining 5.3 % on MM8 are small charts of the thin wing and feather sheets (no separate pieces under
8 triangles); accepted at 0.3 % over the target. On MM7 the projected layout splits a few more islands where its
triangles straddle MM8 chart borders; the paint was made on the MM8 layout, so these are seams, not new Meshy specks,
and the MM7 sheet shows none.

Tier colours (`tp_tier_tone.py`, ramps applied, same surface points): every class of MM8 A/B/C and MM7 Roc A/B/C
within 1 sRGB level of the approved mean (e.g. Roc B flight feathers 110.0/49.5/34.4 -> 109.8/49.4/34.3). LOD1
against LOD0 colour error: MM8 mean 5.7 -> 6.0, p99 36.4 -> 44.8; MM7 5.9 -> 6.5, p99 37.5 -> 48.3 (sharper paint,
same projection quality).

## Checks

- `tp_diff.py`: OK for both (only UVs, vertex splits, images, texture references). Winding 0, flat shading 0.00.
  LOD1 shadow meshes are edge-shrunk copies, so only 45/25 of their triangles matched and the rest keep their old UVs
  (shadows draw depth only).
- Viewer `review/viewer/` (12 models, both worlds, installed and pass): check 0 console errors, 72 switches.
- Floor audit: Thunderbird A/B/C, Roc A/B/C ok (fliers). Motion audit (`audit_after/`): identical apart from vertex
  statistics (accel p99 within 0.3, LOD1 deviation 5.3 -> 5.5 mm) from the seam splits.
- `mm6_mm7_mm8_actor_models_build_every_binding` PASS after both installs.
- Sheets (identical free cameras: head 3/4, head front, body 3/4, top): [review/texpass_mm8_sheet.png](review/texpass_mm8_sheet.png),
  [review/texpass_mm7_sheet.png](review/texpass_mm7_sheet.png). The head, wing coverts and flight feathers read as
  feathers instead of soft mottling; tiers unchanged.

Installed 2026-11-11 (`tools/install_model.py export/mm8_m552.glb --world mm8`, `export/mm7_m390.glb --world mm7`).
Rollback: `work/before_texpass/mm8_m552.glb`, `mm7_m390.glb`; actors.yml entries unchanged (copies in
`work/before_texpass/actors_entries_mm{7,8}.yml`).
