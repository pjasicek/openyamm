# MM8 Dire Wolf texture quality pass (`mm8_wolf`, A/B/C) — 2026-11-11

Stream texpass-1 of the [MM6–MM8 audit fixes](../audit_mm678_20261111/fixes/TEXPASS.md), recipe
[TEXTURE_QUALITY_PASS.md](../claude_shared/TEXTURE_QUALITY_PASS.md). Only UVs, images and texture references changed.
Lease `mm8:wolf` (token in `work/token.txt`). Production [mm8_m512_claude](../mm8_m512_claude/README.md), reduction
[mm8_wolf_reduce_claude](../mm8_wolf_reduce_claude/README.md). Kit: [mm6_demon_texpass_claude](../mm6_demon_texpass_claude/README.md).

## Texture quality pass (2026-11-11)

**Cause.** One 2K set at 32.8 % (1,765 islands, 24.9 % fragments, stretch p90 1.80). LOD2 and LOD3 draw with the body
material and their own UVs into that atlas.

**Route.** Head and jaw x1.8 (11.4 %). Layout **`work/uv_v2_fixed.npz`** (`cut_closed=1 max_stretch=1.8
retry_stretch=3.0 merge_below=20 fine=250 steps=0`: 59.8 %, 5.2 % fragments, stretch 1.20, no overlap; the fast packer
alone gave 60.3 % with 6.1 %). Retexture with the production masters (`mm8_m512_claude/references_hd/01`–`04`),
meshy-7, 4K: **10 credits**; no head paint (no head masters). Tone with mean pinning; paint normals at the approved
strength.

**Far LODs.** LOD2 and LOD3 are `uv_followers` in the new **`3d`** mode: each triangle is projected from the new LOD0
charts in bind space, like LOD1 (the UV-remap mode used for the Gargoyle's and Juggernaut's debris gave LOD2 error
mean 24.5 here; 3D projection 19.1). Colour error against LOD0: LOD1 7.6 -> 10.1, LOD2 13.4 -> 19.1, LOD3 17.2 ->
24.2; much of the rise is the sharper fur against coarse far geometry.

## Results (`texture_quality.py`, LOD0)

| | Before | After |
|---|---|---|
| Atlas | 32.8 % | **59.8 %** |
| Equivalent square | 1,174 px | 1,584 px |
| Density p50 | 876 | 1,259 |
| Islands / fragments | 1,765 / 24.9 % | 346 / 5.2 % |
| Stretch p90 | 1.80 | 1.20 |

Tiers (shared colouring) within 0.2 levels on the fur; the small eye region within 8 levels in green.

## Checks

`tp_diff.py` OK; winding 0; flat 0.00; viewer check 0 console errors; floor audit Dire Wolf A/B/C ok; motion audit
re-run; `mm6_mm7_mm8_actor_models_build_every_binding` PASS after install. Sheet [review/texpass_sheet.png](review/texpass_sheet.png):
fur strands and the mane's spikes crisper, eyes as installed; a small curl mark on the left nostril comes from the
new paint.

Installed 2026-11-11. Rollback `work/before_texpass/mm8_wolf.glb`.
