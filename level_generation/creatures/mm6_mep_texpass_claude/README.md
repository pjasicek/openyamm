# MM6 PeasantM3 texture quality pass (`mm6_mep`, Mep A/B/C), 2026-11-12

Agent `texpass-final`, lease `mm6:mep` (token in `work/LEASE.txt`, released after the checks). The user approved this
last second-group pass on 2026-11-12 (80-credit cap for mep, m620 and figc together). Recipe:
[TEXTURE_QUALITY_PASS.md](../claude_shared/TEXTURE_QUALITY_PASS.md) section 0 (PartUV + seam pass + sparrow, gutter
fill last). Only UVs, vertex splits, images and the far LODs changed; mesh, rig, weights, clips, materials, ramps,
variants and `actors.yml` are the installed ones. Production: [mm6_mep_codex](../mm6_mep_codex/README.md),
[mm6_mep_reduce_claude](../mm6_mep_reduce_claude/README.md).

## Route

Kit: `scripts/tp_*` (texpass-1 kit, copied from `mm6_hyd_texpass_claude`), config `texpass.json`.
1. Start: the installed GLB (sha256 `41608b7d…`), copied to `work/before_texpass/mm6_mep.glb` with its `actors.yml`
   entries (`actors_entries.yml`).
2. `tp_dump.py`; head = the old head half of the 2080x1024 body | head atlas (`head_uv_min_u` 0.5: face, beard,
   turban; 11.6 % of the surface), x1.8; hands x1.3.
3. `tp_uv.py out=uv_v1` (this copy adds one vertex group per joint, so PartUV's skin-weight part tree sees the
   skeleton): PartUV charts, seam pass, sparrow, no fallbacks. **`work/uv_v1.npz` is the paid layout; never re-run it.**
4. Meshy `body_retexture_v1` (meshy-7, 4K, our UVs, production HD masters 01/03/02/04 from `mm6_mep_codex`):
   **10 credits** (backup 425 -> 415). The return kept the layout exactly (`scripts/check_return.py`, UV max diff 0.0).
   No head paint: the head atlas is the user-accepted, landmark-registered round-2 head and is kept.
5. `tp_resample.py`, `tp_bake_ao.py` (reach 0.035), `tp_compose.py` (r2, installed):
   - `keep_head` with `head_sigma 0` / `head_detail 0`: the face, beard and turban keep the approved colour and normal
     exactly (r1 without `head_sigma` gave the turban the paint's knit pattern);
   - `region_keep {"0": 0.2}` (new option): the sash region keeps the approved woven colour plus 0.2 x the paint's
     finest detail (r1 had a dotted woven patch on the sash front);
   - `detail_clip 10` with `detail_clip_all` (new option): the paint's detail soft-limited to 10 levels on every class,
     which fades the button rings and extra buttons the paint drew on the coat (r1);
   - the rest at the defaults (sigma 4, detail 0.9, tone curves per region).
6. `tp_apply.py` (LOD1 projected per chart, shadow LOD0/1 matched 6,236 / 3,115 of 6,236 / 3,115), then
   `scripts/gutter_fill_glb.py` (shared `gutter_fill.py`) on every map.
7. Far LODs per the [LOD playbook](../LOD_PLAYBOOK.md) with the merged tools (`lod_repair_claude/MERGED_20261112.md`):
   `repair.py --source <stage>` (run `texpass_final`), first step `r25_12` passes (LOD2 1,548 / LOD3 775 triangles;
   UV correspondence 92 / 84 %), then the gutter fill again. `verify_far_only.py`: OK.

## Results (`texture_quality.py`, `Mep_A`)

| | Before (2080x1024) | After (2048²) |
|---|---|---|
| Atlas | 33.7 % (uv sum 41.8 %: overlapping charts) | **77.2 %** |
| Equivalent px | 1,208 | 1,800 |
| Density p10/p50/p90 | 483 / 631 / 696 | 1,427 / 1,493 / 2,557 (head x1.8) |
| Islands / fragments | 811 / 15.0 % | 89 / 0.4 % |
| Stretch p90 | 2.09 | 1.19 |

Tiers (`tp_tier_tone.py`, every region of A/B/C): within 0.9 sRGB levels of the approved means. LOD1 against LOD0
colour error mean 3.9 -> 3.7. Far LOD audit (switch size, outline % / colour): LOD2 4.4 / 12.6, LOD3 5.7 / 12.7.

**Look** (identical review-viewer cameras, every tier): face, eyes, beard and turban unchanged; coat folds crisper,
its speckle a little calmer; buttons red as approved (faint ghost roundels of the paint's buttons remain only at close
range); sash and trousers as approved. Sheets: [review/texpass_face_sheet.png](review/texpass_face_sheet.png),
[review/texpass_body_sheet.png](review/texpass_body_sheet.png); rounds `review/r1_sheet_*.png`, `review/r2_sheet.png`.
In game (New Sorpigal, forced LOD 0-3, with m620 and figc):
`../mm8_m620_texpass_claude/review/ingame/close_crop.png`, `close_sheet.png`, `far_sheet.png`.

## Checks

- `tp_diff.py` against the installed GLB: only UVs, vertex splits, images and the far LOD triangle counts.
- `check_winding.py` 0 inverted closed parts; flat shading 0.00.
- Viewer `review/viewer/` (`run_creature_review.py check`): 72 switches, 0 console errors.
- `mm6_mm7_mm8_actor_models_build_every_binding` PASS (647 descriptors on 185 models; `work/regression_every_binding.log`).

Installed 2026-11-12: `python3 tools/install_model.py level_generation/creatures/mm6_mep_texpass_claude/export/mm6_mep.glb --world mm6`.
Revert: `python3 tools/install_model.py level_generation/creatures/mm6_mep_texpass_claude/work/before_texpass/mm6_mep.glb --world mm6`
(`actors.yml` unchanged).
