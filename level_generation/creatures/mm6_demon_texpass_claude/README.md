# MM6 Demon texture quality pass (`mm6_demon`, Demon A/B/C) — 2026-11-11

Stream texpass-1 of the [MM6–MM8 audit fixes](../audit_mm678_20261111/fixes/TEXPASS.md), recipe
[TEXTURE_QUALITY_PASS.md](../claude_shared/TEXTURE_QUALITY_PASS.md) and
[texpass_mm678/HANDOFF.md](../claude_shared/texpass_mm678/HANDOFF.md). Only UVs, images and texture references
changed; mesh, rig, weights, clips, sockets, ramps, variants and bindings are the installed ones. Lease `mm6:demon`
(token in `work/LEASE.txt`). Production history: [mm6_demon_meshy_reference_20261004](../mm6_demon_meshy_reference_20261004/),
[mm6_demon_reduce_claude](../mm6_demon_reduce_claude/README.md), gait h06, lod_repair_claude.

## Texture quality pass (2026-11-11)

**Cause.** The body set used Meshy's 2K paint on an old Smart UV layout (33 % of the atlas, 2,043 islands, 30 % of the
surface on fragments); the white claws had their own 2K colour and 2K metal/rough images at 3.2 % atlas use (75 %
fragments). The body normal map was also bound to the claws.

**Route (`scripts/`, the generic kit `tp_*.py`; config `texpass.json`).**
1. `tp_dump.py`: LOD0 body (primitive 0) and claws (primitive 3) of the installed GLB into one surface; head = Head,
   Neck, jaw (`Bone_025`), `headfront` weights (6.8 % of the surface, x1.8), hands and claws x1.3.
2. `tp_uv.py` (Blender, `uv_atlas.py` fast packer sweep `fine=250 steps=0`): **`work/uv_fine.npz` is the paid layout;
   never re-run it.** One 2048 atlas for body and claws: claws merged into the body atlas (brief: "repack or merge").
3. HD masters: the demon predates the HD-master playbook (its only HD image is the A-pose image-to-3D input; the old
   B/C retextures used restored x2 frames, which may no longer go to Meshy). `references_hd/00_three_quarter.png` is
   that A-pose image (frozen); Codex generated `01`–`04` from it plus the native front/profile/back bitmaps
   (`CODEX_BRIEF.md`, `generation_runs.json`, `selected_views_review.png`; one correction per view; side views keep
   slightly different hands and tail, accepted since they only feed the retexture).
4. Retexture `requests/body_retexture_v1.json` (meshy-7, 4K, our UVs, four masters), job `body_retexture_v1`,
   **10 credits** (backup account). The return keeps the layout (56.9 %, 338 islands). No head-only paint: no close
   head masters exist, the eyes are separate untextured materials, and the face reads well from the body paint at
   head x1.8 (sheet below).
5. `tp_resample.py` carries the approved colour, region mask, metal/roughness and burn map (body and claws, each from
   its own images) onto the layout; `tp_bake_ao.py` bakes AO (reach 0.035); `tp_compose.py`: colour 4K -> 2K once,
   gentle grade, per-class quantile tone match (skin region, harness region, the unmasked ivory spikes, the claws)
   and per-island approved colour below 4 texels + paint luminance detail x0.9; normal from the paint, tilt scaled
   to the approved p90 (x0.46).
6. `tp_apply.py`: LOD0 body and claws get the layout (vertices split at seams), LOD1 projected per primitive from the
   LOD0 charts, the LOD0/LOD1 shadow meshes take the matching triangles' UVs; new images; body tiers A/B/C and the
   claws material all point at them (the claws material keeps no region mask); the old body and claw images are
   dropped (23 textures kept). New burn map in the atlas for LOD0/LOD1 (burn order is baked per vertex from its
   red channel); LOD2/LOD3 keep their own geometry, UVs and burn maps, their maps refilled from the new LOD0 per
   primitive (`transfer_textures.py`, 512/256 and 256/64 px as installed).

## Results (`texture_quality.py`, LOD0)

| | Before | After |
|---|---|---|
| Atlas use, body set | 33.0 % | **56.9 %** (body and claws in one 2048 atlas) |
| Claws set | own 2K colour + 2K metal/rough at 3.2 %, 75.4 % fragments, stretch 2.03 | merged into the body atlas |
| Equivalent square | 1,177 px | 1,545 px |
| Density p50 (texels per creature size) | 841 (claws 1,032) | 1,281 |
| Islands / fragments | 2,043 / 30.2 % | 338 / 1.3 % |
| Stretch p90 | 1.63 | 1.11 |
| Spread p90/p10 | 2.46 | 1.35 (head x1.8 by design) |
| Images | 2K colour, 2K mr, 2K normal, 1K mask + claws 2K colour, 2K mr | 2K colour, 2K normal, 1K mr, 1K mask, 1K burn |

Tier colours with ramps (`tp_tier_tone.py`, same surface points): every class of A, B and C within 1.1 sRGB levels of
the approved mean (A skin 47.7/46.5/43.6 -> 47.9/46.6/43.5; harness, spikes and claws likewise); luminance sd rises
slightly with the new detail (A skin 16.6 -> 18.5). LOD1 against LOD0 colour error: body mean 7.4 -> 5.0, p99
45.5 -> 38.9; claws 6.1 -> 3.1, p99 166 -> 41 (the old LOD1 claws projection was poor).

## Checks

- `tp_diff.py` against the installed GLB: OK (only UVs, vertex splits, images and texture references differ).
- `check_winding.py` 0 inverted closed parts; `flat_shading_check.py` flat 0.00 on every LOD0 material.
- Viewer `review/viewer/` (installed and pass per tier): `run_creature_review.py check` 0 console errors, 78 switches.
- Floor audit Demon A/B/C ok; motion audit unchanged (UV-only change; `audit_after/`).
- `mm6_mm7_mm8_actor_models_build_every_binding` PASS (647 descriptors on 185 models) after install.
- Sheets (review-viewer shots, identical cameras, installed vs pass, all tiers):
  [review/texpass_head_sheet.png](review/texpass_head_sheet.png) (head front and 3/4: scales on the face, same eyes and
  teeth), [review/texpass_body_sheet.png](review/texpass_body_sheet.png) (3/4, back, legs and hands).
- Drift: none in colour. The harness straps on the back show faint dark scale lines from the paint's luminance detail
  (visible at close range on A/B); left as is. The claws keep the approved flat white.

Installed 2026-11-11 with `tools/install_model.py export/mm6_demon.glb --world mm6`. Rollback:
`work/before_texpass/mm6_demon.glb` (actors.yml entries unchanged; copy in `work/before_texpass/actors_entries.yml`).

## The texture-pass kit (`scripts/tp_*`, texpass-1, 2026-11-11)

This project holds the current copy of the generic kit used for every texpass-1 model (each project copies it with
`scripts/tp_new_project.sh <world> <stem>`, which also backs up the GLB and actors.yml entries and claims the lease).
Per model: write `texpass.json`, then

1. `tp_dump.py`; `tp_uv.py` in Blender (`out=... fine=250 steps=0`, or `cut_closed=1 max_stretch=1.8 retry_stretch=3.0
   merge_below=20`); `tp_fix_collapsed.py` (charts left at zero UV area); `tp_layout_stats.py` (atlas, fragments,
   stretch, **uv sum against union: a gap means overlapping charts, never upload it**); `tp_upload.py` when a layout
   was fixed after Blender wrote the uploads.
2. Meshy retexture of the body (and head) upload, 4K, `tp_meshy_wait.sh` to poll and download.
3. `tp_bake_ao.py` (Blender), `tp_resample.py` (approved colour, mask, metal/roughness, burn map at their installed
   sizes, and the approved normal carried into the new tangent frames), `tp_compose.py <layout> <approved> <ao> <out>
   <body job> [head job|-] [sigma] [detail]`, `tp_apply.py <in> <layout> <maps> <out> [--copy]`.
4. Checks: `tp_checks.sh` (diff, winding, flat, quality, LOD1, tiers), `tp_normal_check.py`, `tp_viewer_variants.py`,
   `tp_viewer_manifest.py`, `tp_joint_pos.py` (free review cameras), `tp_sheet.py`; `tp_ledger.py` for the ledger row.

`texpass.json` keys beyond the basics: `head_uv_min_u` (old body | head atlases), `head_prims` (a separate head
primitive), `tag` + `TP_CONFIG` (several atlases or a second world), `keep_normal`, `keep_eyes` (`rule` over the
approved R, G, B, `margin_m`, `feather_m`, `min_texels`, `max_texels`), `fresh_bones` (parts whose approved paint is
rejected), `uv_followers` (meshes outside the LOD chain that share an atlas material, the Gargoyle's Rubble).
Compose pins each class's mean colour to the approved one and keeps an approved relief normal (p90 tilt > 0.3).
`detail_clip` (levels) soft-limits the paint's detail on the unmasked class (the Minotaur's fur-tip speckles);
`tp_apply.py` matches a shadow LOD whose positions are offset from its LOD by face order when the faces are identical
(the Minotaur's shadow LOD1).
