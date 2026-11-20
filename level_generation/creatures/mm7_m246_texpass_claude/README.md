# Goblin texture quality pass (MM7 `mm7_m246`), 2026-11-11

Texpass stream of the MM6–MM8 audit fixes, agent texpass-3 ([TEXPASS.md](../audit_mm678_20261111/fixes/TEXPASS.md),
phase B), after the [recipe](../claude_shared/TEXTURE_QUALITY_PASS.md) and the
[handoff](../claude_shared/texpass_mm678/HANDOFF.md). Only UVs, vertex splits and images change; mesh, rig, clips,
ramps, materials, variants and `actors.yml` stay.

Production project: [mm7_m246_claude](../mm7_m246_claude/README.md) (masters). Starting point: the installed GLB,
backed up as `work/before_texpass/mm7_m246.glb` with `actors_entries.yml`. Lease `mm7:m246`. Kit: the `tp_*.py`
scripts from [mm6_natf_texpass_claude](../mm6_natf_texpass_claude/README.md), config `texpass.json`;
`work/rebuild_view.sh` runs compose, apply, viewer and shots.

## Cause

A 2080 x 1024 body | head atlas: armour, scale mail and skin at 347 texels per metre (1,109 islands, 24.3 % of the
surface on fragments, stretch p90 2.21); the face (head set, 5.2 % of the surface) at 1,461.

## Route

1. `tp_dump.py`: head set = old atlas u > 0.5, x3.0; hands x1.3.
2. `tp_uv.py` **`uv_v2`** (`cut_closed=1 max_stretch=1.8 retry_stretch=3.0 merge_below=20 fine=250 steps=0`): 57.3 %,
   1.2 % fragments, stretch 1.19; face 2,051, body 686 texels per metre. **The paid layout; never re-run it.**
3. One retexture with the production masters (`references_hd/` 01-04), meshy-7, 4K, our UVs: `body_retexture_v1`,
   **10 credits**. No head paint (`head_sigma` 1.2 keeps the approved face).
4. `tp_resample.py`, `tp_bake_ao.py` (0.025), `tp_compose.py` with **sigma 1.5, detail 0.7**, limiter 1.3 (with
   2.5 / 0.55 the scale mail's pattern went soft and the vest of tier A came out 6 levels lighter), `tp_apply.py`
   (LOD1 projected and its shrunk shadow copy; LOD2/LOD3 refilled).

## Results (`texture_quality.py`, LOD0 `M246_A`)

| | Before | After |
|---|---|---|
| Image | 2080 x 1024 | 2048² |
| Atlas | 43.7 % | **57.3 %** |
| Equivalent px | 1,375 | 1,551 |
| Density p10 / p50 / p90 | 434 / 604 / 1,005 | 1,129 / 1,169 / 1,294 |
| Islands / fragments | 1,109 / 24.3 % | 343 / 1.2 % |
| Stretch p90 | 2.21 | 1.19 |

Tiers (`tp_tier_tone.py`): vest (region 0, 5.5 % of the surface) 2-3 sRGB levels lighter, scale mail (region 1) and
the rest within 1.0; luminance sd 41.9 -> 39.9 (rest). LOD1 against LOD0 colour error mean 9.9 -> 3.7, p99 78.9 ->
39.9.

## Checks

- `tp_diff.py` OK; winding 0; flat 0.00; viewer `check` 0 console errors (60 switches).
- `mm6_mm7_mm8_actor_models_build_every_binding` PASS; floor audit Goblin A/B/C 0 problems; motion audit re-run
  (`audit_after/`, clips identical).
- Sheets: [review/texpass_head_sheet.png](review/texpass_head_sheet.png) (face front and 3/4 at close range, every
  tier), [review/texpass_body_sheet.png](review/texpass_body_sheet.png). Face, eyes and beard as installed; gold
  armour, helmet and scale mail crisper (the scales' pink highlights are a little greener).

Installed 2026-11-11 (MM7). Rollback: install `work/before_texpass/mm7_m246.glb`.
