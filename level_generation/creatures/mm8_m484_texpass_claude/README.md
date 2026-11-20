# MM8 Minotaur texture quality pass (`mm8_m484`, Minotaur A/B/C and Minotaur Pesant) — 2026-11-11

Stream texpass-1 of the [MM6–MM8 audit fixes](../audit_mm678_20261111/fixes/TEXPASS.md), recipe
[TEXTURE_QUALITY_PASS.md](../claude_shared/TEXTURE_QUALITY_PASS.md), kit as in
[mm6_demon_texpass_claude](../mm6_demon_texpass_claude/README.md#the-texture-pass-kit-scripts-tp_-texpass-1-2026-11-11).
Only UVs, images and texture references changed; mesh, rig, weights, clips (including the anim stream's recomposed
Jog/Sprint, `mm8_m484_gait_h20_claude`), sockets, ramps, variants, the axe and bindings are the installed ones. Lease
`mm8:m484`. Production history: [mm8_m484_claude](../mm8_m484_claude/), `mm8_m484_reduce_claude`, `mm8_m484_animfix_claude`.

## Texture quality pass (2026-11-11)

**Cause.** One 2080x1024 set with the body on its left half and the head (head, neck, mane, horns, 25 % of the surface)
on its right: 37.6 % atlas use, 658 islands, 21 % of the surface on fragments, stretch p90 1.83, density spread 3.7
(the body at less than half the head's density).

**Route (`scripts/`, config `texpass.json`).**
1. `tp_dump.py`: LOD0 (one primitive); head = the old right-hand head set (`head_uv_min_u` 0.5), x1.5 (not 1.8: the
   head set is a quarter of the surface; 1.8 would give it half the atlas), hands x1.3.
2. `tp_uv.py` `out=uv_v1 fine=250 steps=0`: **`work/uv_v1.npz` is the paid layout; never re-run it.** One 2048 atlas.
3. Retexture `requests/body_retexture_v1.json` (meshy-7, 4K, our UVs, the production HD masters 01–04 of
   `mm8_m484_claude/references_hd/`, copied to `references_hd/`), job `body_retexture_v1`, **10 credits** (backup
   account). No head-only paint.
4. `tp_resample.py` (approved colour, region mask, metal/roughness at 2048, approved normal in the new frames),
   `tp_bake_ao.py` (reach 0.035), `tp_compose.py ... body_retexture_v1 - 2 0.7` with `head_sigma` 1, `keep_eyes`
   and the new `detail_clip` 8. The paint's fur reads as bright orange speckles (fur tips painted as dots: a scaly look
   on the forehead and chest at sigma 4 / detail 0.9), so the approved fur strokes are kept down to 2 texels (1 on the
   head) and the paint's detail on the unmasked fur is soft-limited to 8 levels (`detail_clip`, new in the kit: tanh
   limit, weighted by the `rest` class so the mail kilt keeps its full detail). The glowing eyes are the approved
   ones (`keep_eyes`, orange rule, 6 eye islands).
5. `tp_apply.py`: LOD0 layout, LOD1 projected, shadow LOD0 matched by triangles. The shadow LOD1 is an inward-offset
   copy of LOD1 (same faces, positions 2–15 mm in), which the triangle match missed: the kit now falls back to the
   face order when the faces are identical (`tp_apply.py`, copied to the kit). LOD2/LOD3 keep their own maps,
   refilled from the new LOD0 (512 / 256 px as installed).

## Results (`texture_quality.py`, LOD0)

| | Before | After |
|---|---|---|
| Atlas use | 37.6 % of 2080x1024 (body half + head half) | **57.8 %** of 2048 |
| Equivalent square | 1,275 px | 1,557 px |
| Density p10/p50/p90 | 310 / 443 / 1,146 | 1,044 / 1,091 / 1,631 |
| Islands / fragments | 658 / 21.4 % | 243 / 4.9 % |
| Stretch p90 | 1.83 | 1.20 |
| Spread p90/p10 | 3.7 | 1.56 (head x1.5 by design) |

Tiers (`tp_tier_tone.py`, ramps applied): every class of A, B and C within 0.6 sRGB levels of the approved mean (mail
kilt A 113.4/87.7/42.5 -> 113.9/88.2/42.8; fur 114.2/65.6/46.6 unchanged). LOD1 against LOD0 colour error mean
5.8 -> 2.9, p99 87.9 -> 49.6. LOD2/LOD3 against LOD0: mean 37.4 -> 34.5 and 37.0 -> 34.1 (high before and after: their
own maps and UVs). Shaded normal against the installed one: p50 1.2°, p90 6.4°.

## Checks

- `tp_diff.py` OK (only UVs, vertex splits, images and texture references); `check_winding.py` 0; flat 0.01.
- Viewer `review/viewer/` (installed and pass per tier): `run_creature_review.py check` 0 console errors, 72 switches.
- Floor audit: Minotaur A/B/C and Minotaur Pesant A/B/C ok. Motion audit (`audit_before/` source, `audit_after/`
  runtime): same clips; only `accel_p99` moves (Attack 110 -> 130) because the seam vertex splits change the vertex
  sample (positions, weights and clips are identical; the runtime cook's backface split gives 7,491 LOD0 triangles
  before and after alike).
- `mm6_mm7_mm8_actor_models_build_every_binding` PASS (647 descriptors on 185 models) after install.
- Sheets (review-viewer shots, identical cameras, installed vs pass, all tiers):
  [review/texpass_head_sheet.png](review/texpass_head_sheet.png) (face front and 3/4: same fur strokes and glowing
  eyes), [review/texpass_body_sheet.png](review/texpass_body_sheet.png) (3/4, back, mail kilt).
- Drift: the mail kilt's rings are smaller and more regular than the old stretched pattern (same tier colours); the
  fur is the approved stroke pattern with finer grain, not the paint's speckle.

Installed 2026-11-11 with `tools/install_model.py export/mm8_m484.glb --world mm8`. Rollback:
`work/before_texpass/mm8_m484.glb` (actors.yml entries unchanged; copy in `work/before_texpass/`).
