# MM7 Lich texture quality pass (`mm7_m270`, Lich A/B/C) — 2026-11-11

Stream texpass-1 of the [MM6–MM8 audit fixes](../audit_mm678_20261111/fixes/TEXPASS.md), recipe
[TEXTURE_QUALITY_PASS.md](../claude_shared/TEXTURE_QUALITY_PASS.md), kit as in
[mm6_demon_texpass_claude](../mm6_demon_texpass_claude/README.md#the-texture-pass-kit-scripts-tp_-texpass-1-2026-11-11).
Only UVs, images and texture references changed; mesh, rig, weights, clips, sockets, ramps, variants and bindings are
the installed ones. Lease `mm7:m270`. Production history: [mm7_m270_claude](../mm7_m270_claude/), gait h09.

## Texture quality pass (2026-11-11)

**Cause.** One 2080x1024 set, body on the left half and head (skull, mail coif, crown; 15 % of the surface) on the
right: 34.5 % atlas use with 0.8 % overlapping charts, 895 islands, 15 % of the surface on fragments, stretch p90 1.39.

**Route (`scripts/`, config `texpass.json`).**
1. `tp_dump.py`: LOD0 (one primitive), head = the old right-hand head set (`head_uv_min_u` 0.5), x1.8; hands x1.3.
2. `tp_uv.py` `out=uv_v1 fine=250 steps=0`: **`work/uv_v1.npz` is the paid layout; never re-run it.** One 2048 atlas.
3. Retexture `requests/body_retexture_v1.json` (meshy-7, 4K, our UVs, the production HD masters 01–04 of
   `mm7_m270_claude/references_hd/`, copied to `references_hd/`), job `body_retexture_v1`, **10 credits** (backup
   account). No head-only paint (the skull reads as before at x1.8).
4. `tp_resample.py`, `tp_bake_ao.py` (reach 0.035), `tp_compose.py` with the defaults (sigma 4, detail 0.9); the
   approved normal (p90 tilt 0.25) is below the keep threshold, so the paint's normal is used at the approved tilt.
5. `tp_apply.py`: LOD0 layout, LOD1 projected; shadow LOD0 matched by triangles, shadow LOD1 (an inward-offset copy of
   LOD1) by face order; LOD2/LOD3 keep their own maps, refilled from the new LOD0.

## Results (`texture_quality.py`, LOD0)

| | Before | After |
|---|---|---|
| Atlas use | 34.5 % of 2080x1024 (uv sum 35.3 %: overlaps) | **58.2 %** of 2048 |
| Equivalent square | 1,221 px | 1,562 px |
| Density p10/p50/p90 | 569 / 635 / 1,071 | 1,075 / 1,108 / 1,975 |
| Islands / fragments | 895 / 15.3 % | 297 / 1.2 % |
| Stretch p90 | 1.39 | 1.17 |

Tiers (`tp_tier_tone.py`, ramps applied): every class of A, B and C within 1.3 sRGB levels of the approved mean (mail
A 68.2/67.8/92.7 -> 67.6/67.2/91.8; plate and gold 105.7/87.7/59.6 -> 105.9/87.9/59.8). LOD1 against LOD0 colour error
mean 8.9 -> 7.3. LOD2/LOD3 against LOD0 mean 54.4 -> 48.2 and 53.9 -> 46.0 (their own maps; high before and after).
Shaded normal against the installed one: p50 4.1°, p90 23.5° (the paint's own mail rings; the plate keeps its form).

## Checks

- `tp_diff.py` OK; `check_winding.py` 0; flat 0.00.
- Viewer `review/viewer/`: `run_creature_review.py check` 0 console errors, 60 switches.
- Floor audit Lich A/B/C ok. Motion audit (`audit_before/`, `audit_after/`, source and export): same mesh and clips;
  only `accel_p99` moves by under 2 (seam vertex splits change the vertex sample).
- `mm6_mm7_mm8_actor_models_build_every_binding` PASS (647 descriptors on 185 models) after install.
- Sheets (review-viewer shots, identical cameras, installed vs pass, all tiers):
  [review/texpass_head_sheet.png](review/texpass_head_sheet.png), [review/texpass_body_sheet.png](review/texpass_body_sheet.png),
  [review/texpass_close_sheet.png](review/texpass_close_sheet.png) (chest plate and robe mail at close range: clearly sharper).
- Drift: the plate armour gains a fine hammered relief and thin dark edges along the gold trim from the paint; the mail
  rings are crisper with the same tier colours.

Installed 2026-11-11 with `tools/install_model.py export/mm7_m270.glb --world mm7`. Rollback:
`work/before_texpass/mm7_m270.glb` (actors.yml entries unchanged; copy in `work/before_texpass/`).
