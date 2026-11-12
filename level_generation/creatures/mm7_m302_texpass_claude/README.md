# MM7 Peasant Dwarf texture quality pass (`mm7_m302`, Peasant Dwarf MaleA/B/C x A/B/C) — 2026-11-11

Stream texpass-1 of the [MM6–MM8 audit fixes](../audit_mm678_20261111/fixes/TEXPASS.md), recipe
[TEXTURE_QUALITY_PASS.md](../claude_shared/TEXTURE_QUALITY_PASS.md), kit as in
[mm6_demon_texpass_claude](../mm6_demon_texpass_claude/README.md#the-texture-pass-kit-scripts-tp_-texpass-1-2026-11-11).
Only UVs, images and texture references changed; mesh, rig, weights, clips (including the anim stream's Hit fix),
sockets, ramps, the nine variants, the club and bindings are the installed ones. Lease `mm7:m302`. Production
history: [mm7_m302_claude](../mm7_m302_claude/).

## Texture quality pass (2026-11-11)

**Cause.** One 2080x1024 set, body on the left half and head (face, beard, cap; 23 % of the surface) on the right:
33.9 % atlas use, 536 islands, stretch p90 1.8, density spread 3.1 (the body at half the head's density).

**Route (`scripts/`, config `texpass.json`).**
1. `tp_dump.py`: LOD0 (one primitive), head = the old head set (`head_uv_min_u` 0.5), x1.5 (the head set is a quarter
   of the surface), hands x1.3.
2. `tp_uv.py` `out=uv_v1 fine=250 steps=0`: **`work/uv_v1.npz` is the paid layout; never re-run it.** One 2048 atlas.
3. Retexture `requests/body_retexture_v1.json` (meshy-7, 4K, our UVs, the production HD masters 01–04 of
   `mm7_m302_claude/references_hd/`), job `body_retexture_v1`, **10 credits** (backup account).
4. `tp_resample.py`, `tp_bake_ao.py` (reach 0.035), `tp_compose.py` (sigma 4, detail 0.9) with `head_sigma` 1 and
   `head_detail` 0.35: at the defaults the paint's darker moustache and chin tuft came through as luminance detail
   tinted by the skin (a brown moustache the approved faces do not have, and greyer irises); the approved faces are
   now kept, with a faint trace of the paint's stubble.
5. `tp_apply.py`: LOD0 layout, LOD1 projected; shadow LOD0 by triangles, shadow LOD1 (offset copy) by face order;
   LOD2/LOD3 keep their own maps, refilled from the new LOD0.

## Results (`texture_quality.py`, LOD0)

| | Before | After |
|---|---|---|
| Atlas use | 33.9 % of 2080x1024 | **53.0 %** of 2048 |
| Equivalent square | 1,212 px | 1,491 px |
| Density p10/p50/p90 | 351 / 545 / 1,088 | 1,031 / 1,076 / 1,601 |
| Islands / fragments | 536 / 5.4 % | 169 / 0.0 % |
| Stretch p90 | 1.80 | 1.15 |
| Spread p90/p10 | 3.1 | 1.55 |

Tiers (`tp_tier_tone.py`, all nine variants, ramps applied): every class within 1.3 sRGB levels of the approved mean.
LOD1 against LOD0 colour error mean 3.6 -> 2.2, p99 45.2 -> 28.0; LOD2/LOD3 (own maps) 57.0 -> 54.2 and 55.8 -> 55.2.
Shaded normal against the installed one: p50 0.7°, p90 2.4°.

## Checks

- `tp_diff.py` OK; `check_winding.py` 0; flat 0.00.
- Viewer `review/viewer/` (18 models): `run_creature_review.py check` 0 console errors, 126 switches.
- Floor audit: all nine Peasant Dwarf Male bindings ok. Motion audit (`audit_before/`, `audit_after/`): same mesh and
  clips; only `accel_p99` moves by about 1 (seam vertex splits).
- `mm6_mm7_mm8_actor_models_build_every_binding` PASS (647 descriptors on 185 models) after install.
- Sheets (identical cameras, installed vs pass, variants a1, b2, c3):
  [review/texpass_head_sheet.png](review/texpass_head_sheet.png), [review/texpass_body_sheet.png](review/texpass_body_sheet.png).
- Drift: none visible on the faces; beard strands, cap knit and sleeves are crisper.

Installed 2026-11-11 with `tools/install_model.py export/mm7_m302.glb --world mm7`. Rollback:
`work/before_texpass/mm7_m302.glb` (actors.yml entries unchanged; copy in `work/before_texpass/`).
