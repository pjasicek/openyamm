# PeasantF4 texture quality pass (MM6 `mm6_natf`), 2026-11-11

Texpass stream of the MM6–MM8 audit fixes, agent texpass-3 ([TEXPASS.md](../audit_mm678_20261111/fixes/TEXPASS.md),
phase B), after the [recipe](../claude_shared/TEXTURE_QUALITY_PASS.md) and the
[handoff](../claude_shared/texpass_mm678/HANDOFF.md). Only UVs, vertex splits and images change; mesh, rig, clips,
ramps, materials, variants, attachments and `actors.yml` stay.

Production projects: [mm6_natf_codex](../mm6_natf_codex/README.md) (masters: `references_hd/adapted_v1/`, the ones its
retexture used), `mm6_natf_reduce_claude`, `mm6_natf_anim_claude`. Starting point: the installed GLB, backed up as
`work/before_texpass/mm6_natf.glb` with `actors_entries.yml`. Lease `mm6:natf`. Kit: the `tp_*.py` scripts from
[mm7_m398_texpass_claude](../mm7_m398_texpass_claude/README.md), config `texpass.json`; `work/rebuild_view.sh` runs
compose, apply, viewer and shots.

## Cause

A 2080 x 1024 body | head atlas: dress, feathers and skin at 370 texels per metre on 828 islands (22.0 % of the surface
on fragments, stretch p90 2.43); the head set (face, hair, headband: 12.7 % of the surface) at 1,114.

## Route

1. `tp_dump.py`: head set = old atlas u > 0.5, x2.5; hands x1.3.
2. `tp_uv.py` **`uv_v2`** (`cut_closed=1 max_stretch=1.8 retry_stretch=3.0 merge_below=20 fine=250 steps=0`): 63.1 %,
   4.4 % fragments (feather pieces), stretch 1.14; head 1,680, body 676 texels per metre. **The paid layout; never
   re-run it.**
3. One retexture with the production masters, meshy-7, 4K, our UVs: `body_retexture_v1`, **10 credits**. No head
   paint (`head_sigma` 1.2 keeps the approved face).
4. `tp_resample.py`, `tp_bake_ao.py` (0.03), `tp_compose.py` (sigma 2.5, detail 0.55, limiter 1.3), `tp_apply.py`
   (LOD1 projected; LOD2/LOD3 refilled).

## Results (`texture_quality.py`, LOD0 `Natf_A`)

| | Before | After |
|---|---|---|
| Image | 2080 x 1024 | 2048² |
| Atlas | 54.0 % | **63.1 %** |
| Equivalent px | 1,529 | 1,626 |
| Density p10 / p50 / p90 | 424 / 643 / 1,718 | 1,085 / 1,121 / 2,675 |
| Islands / fragments | 828 / 22.0 % | 329 / 4.4 % |
| Stretch p90 | 2.43 | 1.14 |

Tiers (`tp_tier_tone.py`): dress (region 0) and skin (region 1) and the rest of A/B/C within 1.0 sRGB levels;
luminance sd 16.6 -> 14.3 (dress A: fewer dirt blotches). LOD1 against LOD0 colour error mean 5.9 -> 1.9, p99 63.3 ->
26.0.

## Checks

- `tp_diff.py` OK; winding 0; flat 0.00; viewer `check` 0 console errors (72 switches).
- `mm6_mm7_mm8_actor_models_build_every_binding` PASS; floor audit PeasantF4 A/B/C 0 problems; motion audit re-run
  (`audit_after/`, clips identical).
- Sheets: [review/texpass_head_sheet.png](review/texpass_head_sheet.png) (face front and 3/4 at close range, every
  tier), [review/texpass_body_sheet.png](review/texpass_body_sheet.png). Face, eyes and headband as installed;
  feathers, gold collar and the dress's stitching crisper.

Installed 2026-11-11 (MM6). Rollback: install `work/before_texpass/mm6_natf.glb`.
