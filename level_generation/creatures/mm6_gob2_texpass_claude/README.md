# Goblin (BGoblin) texture quality pass (MM6 `mm6_gob2`), 2026-11-11

Texpass stream of the MM6–MM8 audit fixes, agent texpass-3 ([TEXPASS.md](../audit_mm678_20261111/fixes/TEXPASS.md)),
after the [recipe](../claude_shared/TEXTURE_QUALITY_PASS.md) and the [handoff](../claude_shared/texpass_mm678/HANDOFF.md).
Only UVs, vertex splits and images change; mesh, rig, clips, ramps, materials, variants, the sword and `actors.yml`
stay.

Production project: [mm6_gob2_claude](../mm6_gob2_claude/README.md) (the installed goblin). Starting point: the
installed GLB, backed up as `work/before_texpass/mm6_gob2.glb` with `actors_entries.yml`. Lease `mm6:gob2`. Kit: the
`tp_*.py` scripts from [mm8_centaur_texpass_claude](../mm8_centaur_texpass_claude/README.md), config `texpass.json`.

## Cause

A 2080 x 1024 body | head atlas whose UVs were carried onto the rebuilt rig one old triangle per new face
(`carry_uv.py`): stretch p90 4.52 (body 4.5, head 4.7), 890 islands, 14.4 % of the surface on fragments; body 293,
head 1,230 texels per metre.

## Route

1. `tp_dump.py`: head set = old atlas u > 0.5 (9.4 % of the surface), x2.2 (keeps its density); hands x1.3.
2. `tp_uv.py` **`uv_v2`** (`cut_closed=1 max_stretch=1.8 retry_stretch=3.0 merge_below=20 fine=250 steps=0`): 54.7 %,
   1.2 % fragments, stretch 1.24; head 1,365, body 622 texels per metre. **The paid layout; never re-run it.**
3. One retexture with the production masters (`references_hd/` 01-04), meshy-7, 4K, our UVs: `body_retexture_v1`,
   **10 credits**. No head paint (`head_sigma` 1.2 keeps the approved face).
4. `tp_resample.py`, `tp_bake_ao.py` (0.025), `tp_compose.py` (sigma 2.5, detail 0.55, limiter 1.3, as the Centaur),
   `tp_apply.py` (LOD1 projected and its shrunk shadow copy; LOD2/LOD3 refilled).

## Results (`texture_quality.py`, LOD0 `Goblin_A`)

| | Before | After |
|---|---|---|
| Image | 2080 x 1024 | 2048² |
| Atlas | 44.2 % | **54.7 %** |
| Equivalent px | 1,382 | 1,515 |
| Density p10 / p50 / p90 | 454 / 504 / 536 | 1,012 / 1,061 / 1,398 |
| Islands / fragments | 890 / 14.4 % | 262 / 1.2 % |
| Stretch p90 | 4.52 | 1.24 |

Tiers (`tp_tier_tone.py`): skin (region 0) and the rest of A/B/C within 0.3 sRGB levels; luminance sd 25.0 -> 23.9
(skin), 40.0 -> 38.6. LOD1 against LOD0 colour error mean 3.7 -> 2.2, p99 41.3 -> 34.1.

## Checks

- `tp_diff.py` OK; winding 0; flat 0.00; viewer `check` 0 console errors (60 switches).
- `mm6_mm7_mm8_actor_models_build_every_binding` PASS; floor audit BGoblin A/B/C 0 problems; motion audit re-run
  (`audit_after/`, clips identical).
- Sheets: [review/texpass_face_sheet.png](review/texpass_face_sheet.png) (face front and 3/4 at close range, every
  tier: eyes, teeth, brows unchanged), [review/texpass_head_sheet.png](review/texpass_head_sheet.png),
  [review/texpass_body_sheet.png](review/texpass_body_sheet.png). Leather, shoulder pads and belt are crisper; the
  skin keeps its veins slightly softer.

Installed 2026-11-11 (MM6). Rollback: install `work/before_texpass/mm6_gob2.glb`.
