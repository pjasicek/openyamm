# MM6 FighterChain texture quality pass (`mm6_figc`, FighterChain A/B/C), 2026-11-12

Agent `texpass-final`, lease `mm6:figc` (token in `work/LEASE.txt`, released after the checks). User approval
2026-11-12 (80-credit cap for mep, m620 and figc together). Recipe:
[TEXTURE_QUALITY_PASS.md](../claude_shared/TEXTURE_QUALITY_PASS.md) section 0. Only UVs, vertex splits, images and the
far LODs changed; mesh, rig, weights, clips, materials, ramps (incl. the round-6 matte steel), variants, the axe and
shield attachments and `actors.yml` are the installed ones. Production: [mm6_figc_codex](../mm6_figc_codex/README.md),
[mm6_figc_reduce_claude](../mm6_figc_reduce_claude/README.md).

## Route

Kit: `scripts/tp_*` (copied from `mm6_hyd_texpass_claude`), config `texpass.json`.
1. Start: the installed GLB (sha256 `eb46cee3…`) in `work/before_texpass/` with its `actors.yml` entries.
2. `tp_dump.py`: head = B_Head/B_Neck faces (helmet, face, neck mail; 8.1 %), x1.8; hands x1.3.
3. `tp_uv.py out=uv_v1` (per-joint vertex groups added for PartUV): PartUV, seam pass, sparrow, no fallbacks.
   **`work/uv_v1.npz` is the paid layout; never re-run it.**
4. Meshy `body_retexture_v1` (meshy-7, 4K, our UVs, HD masters 01/03/02/04 from `mm6_figc_codex`): **10 credits**
   (backup 415 -> 405). Layout kept exactly (UV max diff 0.0).
5. `tp_compose.py` (r3, installed): defaults (sigma 4, detail 0.9, tone per region) plus
   - `detail_guard [12, 30]`: r1 had a yellow emblem ring painted on the red back panel (the paint's own design);
     the guard drops the paint's detail where its colour disagrees with the approved one;
   - `keep_head` with `head_sigma 0` / `head_detail 0`: face, eyes, helmet and neck mail keep the approved paint
     exactly (r2 at head_sigma 1 / detail 0.35 changed the mouth shading).
6. `tp_apply.py` (LOD1 projected; shadow LOD0 6,797/6,797 matched; shadow LOD1 is an offset copy and keeps its old UVs,
   which an opaque shadow does not sample), gutter fill, far LODs: `repair.py` first step `r25_12` passes (LOD2 1,693 /
   LOD3 843; UV correspondence 92 / 87 %), gutter fill again; `verify_far_only.py` OK.

## Results (`texture_quality.py`, `FighterChain_A`)

| | Before (1809x2048, cooks to a 1024-wide power of two) | After (2048²) |
|---|---|---|
| Atlas | 33.8 % | **75.6 %** |
| Equivalent px | 1,051 | 1,781 |
| Density p10/p50/p90 | 818 / 855 / 958 | 1,333 / 1,432 / 1,752 |
| Islands / fragments | 458 / 8.8 % | 78 / 0.6 % |
| Stretch p90 | 1.18 | 1.19 |

Tiers: every region of A/B/C within 0.7 sRGB levels. LOD1 against LOD0 colour error mean 10.5 -> 10.8 (as installed).
Far LOD audit: LOD2 4.4 % / 11.4, LOD3 4.1 % / 9.8.

**Look** (identical viewer cameras, every tier): face and helmet unchanged; tabard halves, mail, pauldrons and greaves
crisper with the approved colours; the broken black/white patch on the back strap of the installed paint is gone.
Sheets: [review/texpass_face_sheet.png](review/texpass_face_sheet.png),
[review/texpass_body_sheet.png](review/texpass_body_sheet.png); rounds `review/r1_sheet_*`, `r2_sheet`, `r3_sheet`.
In game: `../mm8_m620_texpass_claude/review/ingame/`.

## Checks

- `tp_diff.py`: only UVs, vertex splits, images and far LOD triangle counts. Winding 0; flat shading 0.00.
- Viewer check: 60 switches, 0 console errors. `every_binding` PASS (647 / 0, `work/regression_every_binding.log`).

Installed 2026-11-12: `python3 tools/install_model.py level_generation/creatures/mm6_figc_texpass_claude/export/mm6_figc.glb --world mm6`.
Revert: `python3 tools/install_model.py level_generation/creatures/mm6_figc_texpass_claude/work/before_texpass/mm6_figc.glb --world mm6`.
