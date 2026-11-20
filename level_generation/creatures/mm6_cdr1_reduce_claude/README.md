# MM6 Red / Blue / Gold Dragon (`cdr1`, DragonCover A/B/C) reduction, new horns, retexture (installed 2026-10-14)

User: "what about the dragon ... drake? its like cdr" after the flying drake reduction; same route as
[mm6_drg1_reduce_claude](../mm6_drg1_reduce_claude/README.md), including its head colour check.

## Head colour
Head and body tier materials share their region ramps, but the head's base colour was much darker in both ramped
regions (linear luminance p10/50/90, hide 0.038 / 0.080 / 0.139 against the body's 0.087 / 0.159 / 0.234; belly
0.233 / 0.343 / 0.497 against 0.349 / 0.447 / 0.526), so the head read deeper than the neck on every tier (dark red,
navy, olive). `scripts/unify_head.py` quantile-matches each region's head luminance to the body's (after: hide
0.087 / 0.159 / 0.231, belly 0.359 / 0.453 / 0.530), scaling texels by matched/original luminance weighted by the
mask (hue and scale detail kept). Ivory horns, teeth and eyes are unchanged. `export/mm6_cdr1_unified.glb`;
close-ups `review/neck/sheet_compare.png` (rows: installed / unified per tier).

## Reduction
No-retexture route (`scripts/` copies from the drake, `REA_NODE=Body`) on the unified model. Weld 10,573 -> 110 open
edges; limits scaled to the 2.17 m bound (p99 6.5 mm, max 32.6 mm).

| step | triangles | p99 / max mm | IoU | SSIM | |
|---|---:|---|---|---|---|
| source | 13,185 | | | | |
| 70 % | 9,227 | 2.5 / 17.4 | 0.995 | 0.998 | pass |
| **55 %** | **7,249** | 4.3 / 20.1 | 0.990 | 0.997 | **auto-pick** |
| 45 % | 5,931 | 6.2 / 44.8 | 0.982 | 0.995 | fail (max) |
| 35 % | 4,613 | 8.0 / 44.8 | 0.968 | 0.993 | fail |

Small parts: teeth, horns and frill spikes survive at 55 % (`review/mouth/sheet.png`, unified / 55 %), so nothing
was rebuilt. Build: export_cand -> swap_lod0 -> build_actor_lods -> `scripts/preserve_wing_lods.py` (every LOD keeps
the LOD0 wing membranes, as the original project does) -> `mm6_cdr1_claude/scripts/shrink_shadow_lods.py` ->
carry_variants: `export/mm6_cdr1.glb`, LODs 7,249 / 4,284 / 2,384 / 1,760 (installed 13,185 / 7,603 / 4,001 /
2,654), burn maps on all 9 materials, 9 clips.
Viewer `review/viewer/` (installed / unified / 55 % per tier, 81 loads pass, `review/viewer/check.json`);
`review/neck/sheet_r55.png`, `review/close/sheet_whole.png` (silhouettes match). Not installed; previous source to
be backed up on install.

## Round 2: new horns and spikes, Meshy retexture, more saturation (2026-10-14)

User on the 55 % result: "re-do the bones from his head like the horns etc ... so that they have proper shape (check
the restored x2 master) then regenerate the head texture (make sure eyes are good also after regen) + make sure
somehow the scaling/color matches the body ... also regenerate the texture for the body ... a bit more saturated
color ... check the original restored x2 for reference".

- **Horns and spikes** (`scripts/build_horns.py`, from the 55 % candidate): the head's ivory regions (faces sampled
  ivory in the installed texture, `scripts/ivory_regions.py`) are split into single spikes by a persistence
  watershed on the geodesic height above the region border. Each region is removed (with the old red horn sheath,
  flattened onto a robust quadratic fit of the surrounding skin), its hole is closed with a fitted skin patch, and
  closed round tubes are set into the patch with sunk roots: 2 main horns (10 sides, swept like the reference:
  concave up, slight inward crescent), the centre crest (straightened, `scripts/straighten_crest.py`, gold), 6 frill
  spikes, 2 neck spikes and 2 jaw spikes; left/right mirrored. Clay close-ups: `review/horns/clay_v10.png`.
  8,581 triangles (+1,332 for horns and patches).
- **UVs and Meshy** (`scripts/uv_uploads.py`): fresh smart-project UVs (80 / 85 degrees, concave packing) for body and
  head; wings keep theirs. Both uploads carry the whole dragon so head and neck scales come out the same size:
  body islands in 92 % of the body upload, head islands in 86 % of the head upload, the other sets small beside them.
  `requests/{body,head}_texture_r1.json`: meshy-7, original UVs, PBR, 4k, the four HD masters. 20 credits; UV parity
  0 unmatched corners (`work/texture_uv_parity.json`).
- **Compose** (`scripts/compose.py`): AO grade; head and body hide/belly luminance quantile-matched to the installed
  body (one colour for both sets); ivory painted on horns, spikes, teeth, claws and spurs; eyes painted by position
  (gold iris, dark rim, slit pupil; belly region, so tiers recolour them as before); region masks. Ramps: the
  accepted v7 ramps with 1.30 (hide) / 1.45 (belly) linear chroma, tier A's gold tinted towards orange.
- **Saturation against the restored x2** (CIE LCh medians, red hide / gold belly, front and three-quarter renders):

| | red L | red C | gold C | gold hue |
|---|---:|---:|---:|---:|
| restored x2 | 28.6 | 55.0 | 57.4 | 62 |
| installed | 32-40 | 39-45 | 37 | 73 |
| new | 33-41 | 48-56 | 51-52 | 64-65 |

- **Runtime** (`scripts/texture_chain.sh`, 44 s): compose -> geometry export -> swap into the head-unified installed
  GLB (clips, variants and materials kept) -> burn maps rebaked (`textures/cdr1r_*_burn.png`) -> maps, burn maps and
  ramps swapped in -> LODs 8,581 / 4,956 / 2,619 / 1,824 -> intact wings -> shadow LODs -> variant mappings ->
  viewer tiers (`rt`). Viewer: installed vs new per tier, 54 loads pass (`review/viewer/check.json`).
- Review sheets: `review/mouth/sheet_rt.png` (head per tier), `review/mouth/sheet_eyes.png`,
  `review/neck/sheet_rt.png`, `review/close/sheet_whole_rt.png`.

## Installed (2026-10-14)

User: "yes very good, accept and install". Previous source backed up to `work/mm6_cdr1_source_pre_reduce.glb`
(rollback: install that file with `tools/install_model.py --world mm6`); `export/mm6_cdr1.glb` installed with
`tools/install_model.py`. Regressions `mm6_dragon_actor_model_tiers_and_clips` and
`mm6_drake_and_dragon_actor_model_burn_death` pass. Dev assets only; `assets/worlds/mm6.zip` and Android not repacked.
