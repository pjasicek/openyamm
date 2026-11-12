# Serpentman texture quality pass (MM8 `mm8_m524`), 2026-11-11

Texpass stream of the MM6–MM8 audit fixes, agent texpass-3 ([TEXPASS.md](../audit_mm678_20261111/fixes/TEXPASS.md),
phase B), after the [recipe](../claude_shared/TEXTURE_QUALITY_PASS.md) and the
[handoff](../claude_shared/texpass_mm678/HANDOFF.md). Only UVs, vertex splits and images change; mesh, rig, clips
(with the attack stream's re-authored attack, in the installed GLB this started from), ramps, materials, variants and
`actors.yml` stay.

Production projects: [mm8_m524_claude](../mm8_m524_claude/README.md) (masters), `mm8_m524_reduce_claude`,
`mm8_m524_attack_claude`. Starting point: the installed GLB, backed up as `work/before_texpass/mm8_m524.glb` with
`actors_entries.yml`. Lease `mm8:m524`. Kit: the `tp_*.py` scripts from
[mm7_m246_texpass_claude](../mm7_m246_texpass_claude/README.md), config `texpass.json`; `work/rebuild_view.sh` runs
compose, apply, viewer and shots.

## Cause

A 2080 x 1024 body | head atlas: coils, torso and arms at 226 texels per metre on 2,128 islands (23.4 % of the surface
on fragments); the head set (head and jaw, 13.6 % of the surface) at 657.

## Route

1. `tp_dump.py`: head set = old atlas u > 0.5, x2.0; hands x1.3.
2. `tp_uv.py` **`uv_v2`** (`cut_closed=1 max_stretch=1.8 retry_stretch=3.0 merge_below=20 fine=250 steps=0`): 49.5 %,
   0 % fragments, stretch 1.07; head 838, body 424 texels per metre. **The paid layout; never re-run it.** The long
   tapering tail keeps the atlas under 50 % (`uv_fine` without `cut_closed`: 49.4 %).
3. One retexture with the production masters (`references_hd/` 01-04), meshy-7, 4K, our UVs: `body_retexture_v1`,
   **10 credits**. No head paint.
4. `tp_resample.py`, `tp_bake_ao.py` (0.03), `tp_compose.py` (sigma 1.5, detail 0.7, limiter 1.3), `tp_apply.py`
   (LOD1 projected and its shrunk shadow copy; LOD2/LOD3 refilled).

Head: with `head_sigma` 1.2 (the setting of this stream's earlier humanoids) the snout's crisp scale outlines went
soft, because the approved head was barely less dense than the new one. Now **`head_sigma` 0.3** (the approved colour
almost as it is) and the new **`head_keeps_normal`** (the approved normal map on the head set); the head is then the
installed one. For later models whose head keeps its density, 0.3 is the better default.

## Results (`texture_quality.py`, LOD0 `Serpentman_A`)

| | Before | After |
|---|---|---|
| Image | 2080 x 1024 | 2048² |
| Atlas | 39.2 % | **49.5 %** |
| Equivalent px | 1,303 | 1,440 |
| Density p10 / p50 / p90 | 835 / 868 / 2,372 | 1,546 / 1,628 / 3,167 |
| Islands / fragments | 2,128 / 23.4 % | 148 / 0.0 % |
| Stretch p90 | 1.22 | 1.07 |

Tiers (`tp_tier_tone.py`; the three tiers share one look): scales, belly and rest within 0.2 sRGB levels. LOD1 against
LOD0 colour error mean 4.5 -> 1.2, p99 45.0 -> 19.2.

## Checks

- `tp_diff.py` OK; winding 0; flat 0.00; viewer `check` 0 console errors (48 switches).
- `mm6_mm7_mm8_actor_models_build_every_binding` PASS; floor audit `*Serpent*` 0 problems; motion audit re-run
  (`audit_after/`, clips identical).
- Sheets: [review/texpass_head_sheet.png](review/texpass_head_sheet.png) (head front and 3/4 at close range),
  [review/texpass_body_sheet.png](review/texpass_body_sheet.png). Head, fangs and eyes as installed; scales on arms
  and coils crisper.

Installed 2026-11-11 (MM8). Rollback: install `work/before_texpass/mm8_m524.glb`.
