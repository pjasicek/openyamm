# MM8 Bedraggled Human texture quality pass (`mm8_m620`, Bedraggled Human A/B/C), 2026-11-12

Agent `texpass-final`, lease `mm8:m620` (token in `work/LEASE.txt`, released after the checks). User approval
2026-11-12. Adopts the [UV study](../uv_research_20261111/REPORT.md)'s m620 layouts and paints ("Adoption notes"):
**0 new credits** (body paint = study job 4, 8K, 15 credits; hair = study job 6, 10 credits; both charged to the
study). Production: [mm8_m620_claude](../mm8_m620_claude/README.md), [mm8_m620_reduce_claude](../mm8_m620_reduce_claude/README.md).

## Why two texture sets

The installed set was one 4128x2048 atlas (body left, head right), which the cook (creature cap 2048) draws at
2048x1024: each half had about a 1024 square. The study laid the body and the head out as two squares, as the report
recommends. `scripts/m620_split.py` splits LOD0 and LOD1 into two primitives by the old UV (u < 0.5 body, 5,172 / 2,835
triangles; u > 0.5 head, 3,828 / 1,632) and adds the material `Bedraggled_Head` (Bedraggled_A without region mask
and ramps: the head half of the installed mask is zero in every channel, so the tiers never recoloured it; mapped for
all three variants). Corners (position, normal, joints, weights) are unchanged as a set (`scripts/m620_verify.py`).
`actors.yml` does not name materials and is unchanged. Shadow meshes stay one primitive.

## Route

Kit `scripts/tp_*` (from `mm6_hyd_texpass_claude`); configs `texpass.json` (body, prim 0) and `texpass_head.json`
(head, prim 1); `tp_common.before_glb` reads `before` = `work/split.glb`.
1. `m620_import_layout.py` (the hydra's importer): every LOD0 triangle found in the study uploads
   (`paint/uploads/m620_{body,head}_winner_p1t125_upload.glb`) and the Meshy returns (jobs 2, 3, 4, 6) carry the same
   UVs (max diff 0.0) -> `work/uv_study_{body,head}.npz`. Paints hard-linked into `meshy/`.
2. `tp_resample.py` (approved maps on both layouts, from the 4128x2048 source at full resolution), `tp_bake_ao.py` per set.
3. Body compose (r3, installed), job 4 (8K, downsampled once):
   - `region_keep {"0": 0.3}` (new option): the vest region keeps the approved mossy colour and normal plus 0.3 x the
     paint's finest detail. Every study paint turns the vest into pebbled scale (r1: tier C lost its black/white moss);
   - `keep_mask` = the body skin piece (`scripts/m620_keep.py`, largest connected piece of the body set): the paint drew
     veins, a navel and the vest's dotted edge on the approved flat skin (r2); `tone_skip_keep` keeps kept texels out of
     the tone curves;
   - trousers, belt, cords, boots: the paint at the defaults (sigma 4, detail 0.9, tone per region).
4. Head compose, job 6: `keep_mask` = the head skin piece (face, ears, scalp, neck; job 6 is a different, younger face
   with an olive neck), `tone_skip_keep`, `keep_normal` (approved head normals, custom-normal shading kept); the hair
   volume and strands take job 6's detail on the approved colour.
5. `tp_apply.py` per set (body, then head on its output; LOD1 projected per chart; shadow LOD0 9,000/9,000 matched,
   shadow LOD1 is an offset copy and keeps old UVs, unused by the opaque shadow), `gutter_fill_glb.py` on every map.
6. Far LODs: `repair.py --source <stage>` (run `texpass_final`): `r25_12` misses LOD2 (7.7 % outline), `r30_16` passes
   (LOD2 2,680 / LOD3 1,430 triangles, one primitive per set). The head set got 256 / 128 px maps by its surface share,
   and its ~100 hair-strand charts at 4 px padding filled only 8 % / 5 % of them (far head density 39 / 16 against
   the body's 317 / 143). Rebuilt on the same `r30_16.built.glb` (no second collapse) with
   `scripts/m620_unwrap_lods.py` (head at the full 512 / 256, padding 1, brute-force pack), then `transfer_textures.py`
   (UV correspondence: body 85 / 74 %, head 66 / 48 %: hair strands), `apply_bake.py`, `audit.sh` (same scores), gutter
   fill. `verify_far_only.py` OK.

## Results (`texture_quality.py`)

| | Before (4128x2048 atlas, cooks to 2048x1024) | After body `Bedraggled_A` | After head `Bedraggled_Head` |
|---|---|---|---|
| Image | 4128x2048 | 2048² | 2048² |
| Atlas | 33.7 % | **69.8 %** | **69.7 %** |
| Equivalent px | 2,395 (at 4128 wide) | 1,711 | 1,710 |
| Density p10/p50/p90 | 1,037 / 1,388 / 2,007 | 1,409 / 1,511 / 1,611 | 821 / 864 / 903 (own set) |
| Spread | 1.94 | 1.14 | 1.10 |
| Islands / fragments | 1,945 / 9.9 % | 72 / 0.2 % | 743 / 28.8 % (hair strands, a mesh matter) |
| Stretch p90 | 2.19 | 1.18 | 1.18 |
| Far LOD2 / LOD3 density | 309 / 140 (one map) | 317 / 143 | 175 / 83 |

The installed density was measured on the 4128-wide source; the game drew it at half that. Tiers: vest A/B/C within
0.6 sRGB levels, rest 0.0, head 0.0. LOD1 against LOD0 colour error mean 5.9 -> 5.7 (body), 5.6 (head). Far LOD
audit: LOD2 5.3 % / 10.9, LOD3 8.6 % / 9.7 (installed 4.4 / 11.4, 7.1 / 8.6; gates 6 / 16, 13 / 19.5).

**Look** (identical viewer cameras, every tier): face, eyes, stubble and ears identical; hair strands crisper; mossy
vest pattern as approved in all three tiers; skin as approved; trousers' weave and tears sharper. Sheets:
[review/texpass_face_sheet.png](review/texpass_face_sheet.png), [review/texpass_body_sheet.png](review/texpass_body_sheet.png);
rounds `review/r1_sheet_a.png`, `r1_sheet_bc.png`, `r2_sheet.png`, `r3_sheet.png`.
In game (New Sorpigal, isolated minimized run, forced `render lod 0..3`, with mep and figc; `review/ingame/run.sh`):
[review/ingame/close_crop.png](review/ingame/close_crop.png), `close_sheet.png`, `far_sheet.png`: every level loads,
no tier swap, head and hair present down to LOD3.

## Checks

- `m620_verify.py`: nodes, skin, inverse binds, all 7 clips, variants identical; LOD0/LOD1/shadow corners identical;
  tier materials equal apart from textures. `tp_diff.py` lists only the expected split, UV, image and far LOD changes.
- Winding 0; flat shading 0.00 on both sets. Viewer check: 42 switches, 0 console errors.
- `every_binding` PASS (647 descriptors on 185 models, 0 failed; `work/regression_every_binding.log`).

Installed 2026-11-12: `python3 tools/install_model.py level_generation/creatures/mm8_m620_texpass_claude/export/mm8_m620.glb --world mm8`.
Revert: `python3 tools/install_model.py level_generation/creatures/mm8_m620_texpass_claude/work/before_texpass/mm8_m620.glb --world mm8`
(`actors.yml` unchanged).
