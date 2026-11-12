# PeasantM4 (Cannibal) texture quality pass (MM6 `mm6_natm`), 2026-11-11

Texpass stream of the MM6–MM8 audit fixes, agent texpass-3 ([TEXPASS.md](../audit_mm678_20261111/fixes/TEXPASS.md)),
after the [recipe](../claude_shared/TEXTURE_QUALITY_PASS.md) and the [handoff](../claude_shared/texpass_mm678/HANDOFF.md).
Only UVs, vertex splits and images change; mesh, rig, the 12 clips, ramps, materials, variants, the spear and buckler
attachments and `actors.yml` stay.

Production projects: [mm6_natm_claude](../mm6_natm_claude/README.md) (model, rig, HD masters) and
[mm6_natm_reduce_claude](../mm6_natm_reduce_claude/README.md) (reduction and retexture, installed 2026-10-14).
Starting point: the installed GLB, backed up as `work/before_texpass/mm6_natm.glb` with `actors_entries.yml`.
Lease `mm6:natm`. Kit: the `tp_*.py` scripts from [mm6_nobl_texpass_claude](../mm6_nobl_texpass_claude/README.md)
(texpass-1's kit plus the Swordsman's options), config `texpass.json`.

## Cause

A 2080 x 1024 body | head atlas: the body set (97 % of the surface) at 317 texels per metre on 1,218 islands with
50.7 % of the surface on fragments; the head set (the face, 2.9 % of the surface) at 2,258 texels per metre on its own
1K half. 10.3 % of the surface is separate pieces of fewer than 8 triangles (the feathers of the cape, skirt and leg
wraps, the necklace teeth), so the fragment share cannot go under that.

## Route

1. `tp_dump.py`: head set = old atlas u > 0.5 (the face), **x3.0** so the face keeps its density; hands x1.3.
2. `tp_uv.py`: `uv_fine` (x1.8: face density 1,264, too low), `uv_h3v2` (cut_closed, 14.4 % fragments but stretch
   1.78), `uv_h3m20`, `uv_h3s16`, and **`uv_h3s25`** (`cut_closed=1 max_stretch=1.6 retry_stretch=2.5 merge_below=20
   fine=250 steps=0`): 63.3 %, stretch 1.25, face 2,001 / body 678 texels per metre. **The paid layout; never re-run
   it.** Of its 22.1 % fragments, 10.3 % are whole pieces under 8 triangles and the rest pieces of 8-15 triangles
   (feathers) that xatlas cuts in two; opening them pushed stretch to 1.78, so stretch was preferred (recipe pitfall
   "prefer stretch").
3. One retexture with the production masters (`references_hd/` 01-04 from mm6_natm_claude), meshy-7, 4K, our UVs:
   `body_retexture_v1`, **10 credits**. No head paint: the face keeps its approved density, and with `head_sigma` 1.2 it
   takes the approved colour almost texel for texel (the Swordsman showed a 4K head paint adds nothing there).
4. `tp_resample.py`, `tp_bake_ao.py` (0.03), `tp_compose.py`, `tp_apply.py` (LOD1 projected, LOD2/3 refilled).

Compose settings (`texpass.json`): `head_sigma` 1.2; no detail limiter (with 1.3 it damped 40 % of the texels and
the skin came out smoother than the installed one: luminance sd 23.8 -> 22.2; without it 25.4); the necklace pieces
(`work/necklace_faces.npy`, 448 faces: small pieces in front of the neck) keep the approved colour and normal
(`keep_approved_faces`), and within 3-5 cm of them the result fades to the approved colour as it is
(`ornament_keep_approved`, new kit option). The lower teeth of the necklace are painted on the chest skin; the default
4-texel low-pass smeared them into white streaks and the paint added soft ghost teeth.

## Results (`texture_quality.py`, LOD0 `Natm_A`)

| | Before | After |
|---|---|---|
| Image | 2080 x 1024 | 2048² |
| Atlas | 58.6 % | **63.3 %** |
| Equivalent px | 1,592 | 1,630 |
| Density p10 / p50 / p90 | 329 / 553 / 849 | 1,088 / 1,153 / 1,232 |
| Body / face texels per metre | 317 / 2,258 | 678 / 2,001 |
| Islands / fragments | 1,218 / 50.7 % | 765 / 22.1 % (10.3 % whole small pieces) |
| Stretch p90 | 1.76 | 1.25 |

Tiers (`tp_tier_tone.py`): armbands and loincloth (region 0) A/B/C within 0.3 sRGB levels, skin and the rest identical
means (130.1/109.0/94.1); luminance sd 23.8 -> 25.4. LOD1 against LOD0 colour error mean 6.0 -> 5.0, p99 50.7 -> 50.8.

## Checks

- `tp_diff.py` OK; winding 0; flat shading 0.01; viewer `check` 0 console errors (72 switches).
- `mm6_mm7_mm8_actor_models_build_every_binding` PASS after install; floor audit PeasantM4 A/B/C 0 problems; motion
  audit re-run (`audit_after/`, clips identical).
- Sheets: [review/texpass_head_sheet.png](review/texpass_head_sheet.png) (face front and 3/4, chest),
  [review/texpass_body_sheet.png](review/texpass_body_sheet.png) (3/4, back, loincloth). Face, eyes and necklace
  match the installed ones; the loincloth, armbands and feathers gain weave and barbs; the skin keeps its grain. The
  waist band now reads as a braided cord (the paint's detail on the approved colour).

Installed 2026-11-11 (MM6). Rollback: install `work/before_texpass/mm6_natm.glb`.
