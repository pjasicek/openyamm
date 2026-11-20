# Druidess texture quality pass (MM6 `mm6_dru1`), 2026-11-11

Texpass stream of the MM6–MM8 audit fixes, agent texpass-3 ([TEXPASS.md](../audit_mm678_20261111/fixes/TEXPASS.md)),
after the [recipe](../claude_shared/TEXTURE_QUALITY_PASS.md) and the [handoff](../claude_shared/texpass_mm678/HANDOFF.md).
Only UVs, vertex splits and images change; mesh, rig, clips, ramps, materials, variants and `actors.yml` stay.

Production projects: [mm6_dru1_claude](../mm6_dru1_claude/README.md) (masters), `mm6_dru1_reduce_claude`,
`mm6_dru1_anim_claude`. Starting point: the installed GLB, backed up as `work/before_texpass/mm6_dru1.glb` with
`actors_entries.yml`. Lease `mm6:dru1`. Kit: the `tp_*.py` scripts from
[mm6_gob2_texpass_claude](../mm6_gob2_texpass_claude/README.md), config `texpass.json`.

## Cause

A 2080 x 1024 body | head atlas: body 199, head set (face, hair, hood: 12.8 % of the surface) 447 texels per metre;
564 islands, 36.7 % of the surface on fragments, stretch p90 3.12.

## Route

1. `tp_dump.py`: head set = old atlas u > 0.5, x2.0; hands x1.3.
2. `tp_uv.py` **`uv_v2`** (`cut_closed=1 max_stretch=1.8 retry_stretch=3.0 merge_below=20 fine=250 steps=0`): 55.1 %,
   0.1 % fragments, stretch 1.11; head 1,116, body 559 texels per metre. **The paid layout; never re-run it.**
3. Retextures with the production masters, meshy-7, 4K, our UVs: `body_retexture_v1` (`references_hd/` 01-04) and
   `head_retexture_v1` (head faces, `references_head/` front, three-quarter, left, back), **20 credits**.
4. `tp_resample.py`, `tp_bake_ao.py` (0.03), `tp_compose.py` (sigma 2.5, detail 0.55, limiter 1.3, head paint crossfaded
   over the head set), `tp_apply.py` (LOD1 projected and its shrunk shadow copy; LOD2/LOD3 refilled).

Face decision: with the head paint and the approved colour low-passed (`head_sigma` 0) the eyes and brows washed out
and the expression changed; with `head_sigma` 1.2 the face is the approved one texel for texel, and the head paint
only adds fine detail to the hair and hood. Kept 1.2 (as on every earlier humanoid of this stream).

## Results (`texture_quality.py`, LOD0 `Druidess_A`)

| | Before | After |
|---|---|---|
| Image | 2080 x 1024 | 2048² |
| Atlas | 39.0 % | **55.1 %** |
| Equivalent px | 1,299 | 1,521 |
| Density p10 / p50 / p90 | 243 / 354 / 774 | 927 / 953 / 1,868 |
| Islands / fragments | 564 / 36.7 % | 139 / 0.1 % |
| Stretch p90 | 3.12 | 1.11 |

Tiers (`tp_tier_tone.py`): cloak (region 0) and the rest of A/B/C within 0.2 sRGB levels; luminance sd 13.3 -> 13.5
(cloak A), 62.8 -> 61.2 (rest). LOD1 against LOD0 colour error mean 2.6 -> 0.8, p99 48.9 -> 11.2.

## Checks

- `tp_diff.py` OK; winding 0; flat 0.00; viewer `check` 0 console errors (54 switches).
- `mm6_mm7_mm8_actor_models_build_every_binding` PASS; floor audit Druidess A/B/C 0 problems; motion audit re-run
  (`audit_after/`, clips identical).
- Sheets: [review/texpass_head_sheet.png](review/texpass_head_sheet.png) (face front and 3/4 at close range, every
  tier, and shoulders), [review/texpass_body_sheet.png](review/texpass_body_sheet.png). Face and eyes as installed;
  hair strands, hood cloth, the studded dress and the gold belt are crisper.

Installed 2026-11-11 (MM6). Rollback: install `work/before_texpass/mm6_dru1.glb`.
