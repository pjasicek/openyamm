# Skeleton Warrior texture quality pass (MM7 `mm7_m398`), 2026-11-11

Texpass stream of the MM6–MM8 audit fixes, agent texpass-3 ([TEXPASS.md](../audit_mm678_20261111/fixes/TEXPASS.md),
phase B), after the [recipe](../claude_shared/TEXTURE_QUALITY_PASS.md) and the
[handoff](../claude_shared/texpass_mm678/HANDOFF.md). Only UVs, vertex splits and images change; mesh, rig, clips,
ramps, materials, variants and `actors.yml` stay.

Production project: [mm7_m398_claude](../mm7_m398_claude/README.md) (masters). Starting point: the installed GLB,
backed up as `work/before_texpass/mm7_m398.glb` with `actors_entries.yml`. Lease `mm7:m398`. Kit: the `tp_*.py`
scripts from [mm7_m170_texpass_claude](../mm7_m170_texpass_claude/README.md), config `texpass.json`;
`work/rebuild_view.sh` runs compose, apply, viewer and shots.

## Cause

A 2080 x 1024 body | head atlas: armour, bones and breeches at 405 texels per metre, the skull and helmet (head set,
10.3 % of the surface) at 1,557; 1,179 islands, 21.3 % of the surface on fragments.

## Route

1. `tp_dump.py`: head set = old atlas u > 0.5, x2.5; hands x1.3.
2. `tp_uv.py` **`uv_v2`** (`cut_closed=1 max_stretch=1.8 retry_stretch=3.0 merge_below=20 fine=250 steps=0`): 58.9 %,
   3.5 % fragments, stretch 1.23; head 1,821, body 731 texels per metre. **The paid layout; never re-run it.**
3. One retexture with the production masters (`references_hd/` 01-04), meshy-7, 4K, our UVs: `body_retexture_v1`,
   **10 credits**. No head paint (`head_sigma` 1.2 keeps the approved skull).
4. `tp_resample.py`, `tp_bake_ao.py` (0.025), `tp_compose.py` (sigma 2.5, detail 0.55, limiter 1.3), `tp_apply.py`
   (LOD1 projected and its shrunk shadow copy; LOD2/LOD3 refilled).

## Results (`texture_quality.py`, LOD0 `Skeleton_A`)

| | Before | After |
|---|---|---|
| Image | 2080 x 1024 | 2048² |
| Atlas | 54.0 % | **58.9 %** |
| Equivalent px | 1,529 | 1,572 |
| Density p10 / p50 / p90 | 630 / 694 / 1,997 | 1,196 / 1,245 / 2,837 |
| Islands / fragments | 1,179 / 21.3 % | 455 / 3.5 % |
| Stretch p90 | 1.40 | 1.23 |

Tiers (`tp_tier_tone.py`): breeches (region 0) and the rest of A/B/C within 0.3 sRGB levels; luminance sd 33.9 ->
32.1. LOD1 against LOD0 colour error mean 6.0 -> 3.4, p99 48.6 -> 33.0.

## Checks

- `tp_diff.py` OK; winding 0; flat 0.00; viewer `check` 0 console errors (60 switches).
- `mm6_mm7_mm8_actor_models_build_every_binding` PASS; floor audit Skeleton Warrior A/B/C 0 problems; motion audit
  re-run (`audit_after/`, clips identical).
- Sheets: [review/texpass_head_sheet.png](review/texpass_head_sheet.png) (skull front and 3/4 at close range, every
  tier), [review/texpass_body_sheet.png](review/texpass_body_sheet.png). Skull, teeth and blood marks as installed;
  helmet rim, gorget and gauntlets crisper.

Installed 2026-11-11 (MM7). Rollback: install `work/before_texpass/mm7_m398.glb`.
