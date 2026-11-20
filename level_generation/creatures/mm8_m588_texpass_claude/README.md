# Malevolent Boulder texture quality pass (MM8 `mm8_m588`), 2026-11-11

Texpass stream of the MM6–MM8 audit fixes, agent texpass-3 ([TEXPASS.md](../audit_mm678_20261111/fixes/TEXPASS.md)),
after the [recipe](../claude_shared/TEXTURE_QUALITY_PASS.md) and the [handoff](../claude_shared/texpass_mm678/HANDOFF.md).
Only UVs, vertex splits and images change; mesh, rig, clips, ramps, materials, variants and `actors.yml` stay.

Production projects: [mm8_m588_claude](../mm8_m588_claude/README.md), [mm8_m588_reduce_claude](../mm8_m588_reduce_claude/README.md)
(the installed reduction). Starting point: the installed GLB, backed up as `work/before_texpass/mm8_m588.glb` with
`actors_entries.yml`. Lease `mm8:m588`. Kit: the `tp_*.py` scripts from
[mm7_7m500_texpass_claude](../mm7_7m500_texpass_claude/README.md), config `texpass.json`.

## Cause

A 2048 atlas at 46.4 % with 828 islands and 43.9 % of the surface on fragments (each painted as its own blotch:
the mottled stones), stretch p90 1.49.

## Route

1. `tp_dump.py`: jaw stones (`Jaw*` joints, 17.7 % of the surface) x1.3.
2. `tp_uv.py` **`uv_v2`** (`cut_closed=1 max_stretch=1.8 retry_stretch=3.0 merge_below=20 fine=250 steps=0`): 55.2 %,
   2.9 % fragments, stretch 1.27. **The paid layout; never re-run it.**
3. One retexture with the production masters (`references_hd/` 01-04), meshy-7, 4K, our UVs: `body_retexture_v1`,
   **10 credits**.
4. `tp_resample.py`, `tp_bake_ao.py` (0.04), `tp_compose.py` (`detail_limit` 1.3), `tp_apply.py`.

Kit change: each shadow mesh of this GLB reuses its visible LOD's index accessor, so splitting the LOD0 vertices broke
the shadow's indices; `tp_apply.py` now gives every shared accessor its own copy first.

## Results (`texture_quality.py`, LOD0 `Boulder_A`)

| | Before | After |
|---|---|---|
| Atlas | 46.4 % | **55.2 %** |
| Equivalent px | 1,395 | 1,521 |
| Density p10 / p50 / p90 | 458 / 500 / 538 | 494 / 519 / 668 (jaw x1.3) |
| Islands / fragments | 828 / 43.9 % | 394 / 2.9 % |
| Stretch p90 | 1.49 | 1.27 |

The median density barely moves (the jaw takes its share); the gain is the even layout without blotches and the 4K
paint: the cracks and grain of each stone are crisp. Tier colours (`tp_tier_tone.py`, A/B/C) within 0.3 sRGB levels;
luminance sd 28.0 -> 28.5. LOD1 against LOD0 colour error mean 17.7 -> 15.7 (LOD1's geometry departs far from LOD0 on
this reduction: worst corner 0.34 m; unchanged by the pass); LOD2/LOD3 maps refilled.

## Checks

- `tp_diff.py` OK; winding 0; flat 0.00; viewer `check` 0 console errors (42 switches).
- `mm6_mm7_mm8_actor_models_build_every_binding` PASS (run 20 s after the install); floor audit Malevolent Boulder
  A/B/C 0 problems; motion audit re-run (`audit_after/`, clips identical).
- Sheet: [review/texpass_sheet.png](review/texpass_sheet.png) (close front and 3/4, whole 3/4 and back, every tier).

Installed 2026-11-11 (MM8). Rollback: install `work/before_texpass/mm8_m588.glb`.
