# MM6 PeasantF3 texture pass (2026-11-11): installed by the follow-up below

Stream texpass-1. Lease `mm6:mfp` (released). Nothing installed; the installed model is unchanged.

Built with the kit of [mm6_demon_texpass_claude](../mm6_demon_texpass_claude/README.md): a 2048 layout
(`work/uv_fine_fixed.npz`: 59.5 % atlas against 25.4 % of the installed 2048x1628 body | head atlas, fragments
7.9 -> 1.3 %, stretch 1.37 -> 1.13) and 4K body + head paints from the production masters (`body_retexture_v1`,
`head_retexture_v1`, **20 credits**), tone-matched to the approved paint.

**Why it is not installed.** The sari is a designed tile (`mm6_mfp_codex/work/round2/textures`, `round2_sari_tile.png`):
crisp yellow discs with white embroidery dots and thin vertical stripes. The pass keeps only the approved colour below a
few texels and takes the finer detail from the new paint, whose own pattern differs, so the discs come out soft and
the stripes and embroidery are replaced by Meshy's ornament; the new paint also adds spots on the collarbone skin and
heavier stains on the face. Both sigma 4 / detail 0.9 and sigma 2 / detail 0.5 composites lose against the installed
look (sheets [review/texpass_sheet.png](review/texpass_sheet.png), [review/texpass_sheet_s2.png](review/texpass_sheet_s2.png),
row `sk` for the sari). A worthwhile pass here would re-render the sari tile on the new layout from the production
compose scripts, which is outside the texture-pass recipe.

## Follow-up: sari re-rendered, installed (2026-11-11, followup-mfp)

Lease `mm6:mfp` (released after the checks). Started from the installed GLB at claim time
(sha256 `71062d09...`, the 17:20 install carrying today's Jog/Sprint and Attack clips), which is identical to
`work/before_texpass/mm6_mfp.glb`, so the backup and `work/before_texpass/actors_entries.yml` stay the rollback.
Reused texpass-1's layout (`work/uv_fine_fixed.npz`) and 4K body paint (`meshy/body_retexture_v1`): **0 new credits**
(20 in total, all from texpass-1). The head paint is not used.

**What the approved paint is.** `mm6_mfp_codex/scripts/round2_textures.py` paints almost everything procedurally: the
skin is one flat colour (146/85/56, no baked light), the blouse is a quiet procedural weave under the tier ramps, and
the sari is the designed tile `references_hd/round2_sari_tile.png` mapped from the bind-pose surface position (skirt:
elliptic cylinder, 8 repeats around, 12 cm high; sash: planar, 11.5 cm). Only the face, hair, jewellery and sandals are
Meshy paint. So a fresh paint has little to add, and its own pattern and skin detail were what spoiled the first try.

**Route.**
1. `scripts/mfp_sari.py work/uv_fine_fixed.npz work/approved textures/f2/mfp`: evaluates the production sari mapping
   at every texel of the new layout, 4x4 supersampled per texel (installed glTF Y-up -> round-2 Blender Z-up as
   (x, -z, y), nearest round-2 vertex distance p50 10 mm). Each triangle takes the skirt or sash mapping, whichever
   agrees better with the approved colour (both blurred to the approved bake's scale), when the median difference is
   under 12 levels, or under 45 where the approved triangle is mostly sari pink (parts of the sash that the old
   reduction transfer had smeared into streaks). 1,096 triangles (skirt 763, sash 333), 699,708 texels; 1,737 of the
   350,626 covered sari-pink texels stay approved. Difference against the approved at its own scale on the used texels:
   p50 1.9, p90 5.6 levels.
2. `scripts/mfp_keep_mask.py`: keep mask = re-rendered sari + flat skin (approved within 6 levels of 146/85/56, grown
   one texel) + blouse region (mask channel 0, grown 2 texels), 76 % of the covered texels; writes `work/approvedsari_*`
   (approved maps with the sari render as base colour).
3. `scripts/tp_compose.py` (kit updated from `mm6_demon_texpass_claude`, the texpass-1 copies in
   `scripts/kit_texpass1_before/`) with new options `keep_mask`, `keep_head` (head islands keep the approved colour and
   normal exactly: face unchanged) and `detail_guard [12, 30]` (from `mm7_m218_texpass_claude`); config in
   `texpass.json`, sigma 3, detail 0.7. The paint's detail survives only on hair, jewellery, bangles and sandals, and
   fades out where its colour disagrees. Kept texels keep the approved (flat) normal; elsewhere the approved normal
   plus 0.5 x the paint's fine normal.
4. `tp_apply.py` on the installed GLB -> `export/mm6_mfp.glb` (LOD1 projected, LOD2/3 maps refilled at 512/256).
   texpass-1's unused export is kept as `export/mm6_mfp_texpass1_not_installed.glb`.

Round 1 also let the paint's detail onto the blouse: its luminance went past the ramp's white top entry along the
neckline (a pale stipple in every tier), so round 2 (installed) keeps the blouse as approved.

**Results** (`texture_quality.py`, `PeasantF3_A`; `review/quality_after_f2.json`):

| | Before (2048x1628 body + head) | After (2048²) |
|---|---|---|
| Atlas | 25.4 % | **59.5 %** |
| Equivalent px | 1,031 | 1,579 |
| Density p10/p50/p90 | 876 / 961 / 1,017 | 1,509 / 1,566 / 1,722 |
| Islands / fragments | 734 / 7.9 % | 585 / 1.3 % |
| Stretch p90 | 1.37 | 1.13 |

Tiers (`tp_tier_tone.py`, sRGB): blouse A (132.6, 164.4, 114.8) -> (132.5, 164.4, 114.7), B (164.6, 63.3, 63.2) ->
(164.6, 63.3, 63.1), C (75.9, 122.1, 164.4) -> (75.8, 122.1, 164.3); the rest of every tier within 0.1 levels. LOD1
against LOD0 colour error mean 7.3 -> 2.6, p99 75.6 -> 55.7.

**Look** (review-viewer shots, identical cameras, every tier, `review/f2_shots/`):
- [review/f2_sheet_sari.png](review/f2_sheet_sari.png): skirt front close, sash close, skirt 3/4. The medallions'
  embroidery dots and the stripe borders are crisper than the approved; the pattern is the designed tile.
- [review/f2_sheet_face.png](review/f2_sheet_face.png) and [review/f2_face_neck_full.png](review/f2_face_neck_full.png)
  (full size): face, eyes and mouth unchanged (shot difference mean 0.44 levels); collarbone and neckline clean, no
  spots.
- [review/f2_sheet_body.png](review/f2_sheet_body.png): shoulders, 3/4 and back.

**Checks:** `tp_diff.py` and `glb_diff.py` OK (only UVs, vertex splits, images and texture references); winding 0;
flat shading 0.00; viewer `run_creature_review.py check` 66 switches, no console errors; floor audit PeasantF3 A/B/C
ok; motion audit (`audit_after/`) equal to the before GLB apart from accel p99 shifts of up to 2.4 from the
seam-split vertices (clips identical per glb_diff); `mm6_mm7_mm8_actor_models_build_every_binding` PASS (647
descriptors on 185 models). No clip changed, so the arm and hand gate was not re-run.

Installed 2026-11-11 with `tools/install_model.py level_generation/creatures/mm6_mfp_texpass_claude/export/mm6_mfp.glb
--world mm6`. Rollback: `python3 tools/install_model.py
level_generation/creatures/mm6_mfp_texpass_claude/work/before_texpass/mm6_mfp.glb --world mm6` (actors.yml unchanged).
