# Cleric Moon texture quality pass (MM7 `mm7_m170`), 2026-11-11

Texpass stream of the MM6–MM8 audit fixes, agent texpass-3 ([TEXPASS.md](../audit_mm678_20261111/fixes/TEXPASS.md),
phase B), after the [recipe](../claude_shared/TEXTURE_QUALITY_PASS.md) and the
[handoff](../claude_shared/texpass_mm678/HANDOFF.md). Only UVs, vertex splits and images change; mesh, rig, clips
(with the animation stream's Jog/Walk2 recomposition of the same day, in the installed GLB this started from), ramps,
materials, variants and `actors.yml` stay.

Production projects: [mm7_m170_claude](../mm7_m170_claude/README.md) (masters), `mm7_m170_reduce_claude`,
`mm7_m170_animfix_claude`. Starting point: the installed GLB, backed up as `work/before_texpass/mm7_m170.glb` with
`actors_entries.yml`. Lease `mm7:m170`. Kit: the `tp_*.py` scripts from
[mm6_dru1_texpass_claude](../mm6_dru1_texpass_claude/README.md), config `texpass.json`; `work/rebuild_view.sh` runs
compose, apply, viewer and shots.

## Cause

A 2080 x 1024 body | head atlas: robe, collar, helmet wings at 259 texels per metre (688 islands, 21.3 % of the
surface on fragments, stretch p90 2.09); the face (head set, 2.3 % of the surface) at 2,904.

## Route

1. `tp_dump.py`: head set = old atlas u > 0.5, **x5.0** (the face is small and was very dense); hands x1.3.
2. `tp_uv.py` **`uv_v2`** (`cut_closed=1 max_stretch=1.8 retry_stretch=3.0 merge_below=20 fine=250 steps=0`): 63.6 %,
   0.1 % fragments, stretch 1.13; face 3,492, body 702 texels per metre. **The paid layout; never re-run it.**
3. One retexture with the production masters (`references_hd/` 01-04), meshy-7, 4K, our UVs: `body_retexture_v1`,
   **10 credits**. No head paint (`head_sigma` 1.2 keeps the approved face).
4. `tp_resample.py`, `tp_bake_ao.py` (0.03), `tp_compose.py` (sigma 2.5, detail 0.55, limiter 1.3), `tp_apply.py`
   (LOD1 projected and its shrunk shadow copy; LOD2/LOD3 refilled).

## Results (`texture_quality.py`, LOD0 `M170_A`)

| | Before | After |
|---|---|---|
| Image | 2080 x 1024 | 2048² |
| Atlas | 54.7 % | **63.6 %** |
| Equivalent px | 1,538 | 1,634 |
| Density p10 / p50 / p90 | 275 / 441 / 1,094 | 1,162 / 1,193 / 1,238 |
| Islands / fragments | 688 / 21.3 % | 162 / 0.1 % |
| Stretch p90 | 2.09 | 1.13 |

Tiers (`tp_tier_tone.py`): robe and cloak regions of A/B/C within 1.8 sRGB levels, the rest within 1.1; luminance sd
49.2 -> 46.1 (rest). LOD1 against LOD0 colour error mean 4.6 -> 1.3, p99 68.0 -> 25.5.

## Checks

- `tp_diff.py` OK; winding 0; flat 0.00; viewer `check` 0 console errors (60 switches).
- `mm6_mm7_mm8_actor_models_build_every_binding` PASS; floor audit `*Cleric*` 0 problems; motion audit re-run
  (`audit_after/`, clips identical).
- Sheets: [review/texpass_head_sheet.png](review/texpass_head_sheet.png) (face front and 3/4 at close range, every
  tier), [review/texpass_body_sheet.png](review/texpass_body_sheet.png). Face as installed; collar, helmet and gold
  trims crisper; the robe's damask pattern is a little subtler than before.

Installed 2026-11-11 (MM7). Rollback: install `work/before_texpass/mm7_m170.glb`.
