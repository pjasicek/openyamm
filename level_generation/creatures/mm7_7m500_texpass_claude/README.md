# Cat (zcat) texture quality pass (MM7 `mm7_7m500`), 2026-11-11

Texpass stream of the MM6–MM8 audit fixes, agent texpass-3 ([TEXPASS.md](../audit_mm678_20261111/fixes/TEXPASS.md)),
after the [recipe](../claude_shared/TEXTURE_QUALITY_PASS.md) and the [handoff](../claude_shared/texpass_mm678/HANDOFF.md).
Only UVs, vertex splits and images change; mesh, rig, the 7 clips, the material and `actors.yml` stay. One look (no
variants, no region mask).

Production project: [mm7_7m500_claude](../mm7_7m500_claude/README.md). Starting point: the installed GLB, backed up as
`work/before_texpass/mm7_7m500.glb` with `actors_entries.yml`. Lease `mm7:7m500`. Kit: the `tp_*.py` scripts from
[mm7_m242_texpass_claude](../mm7_m242_texpass_claude/README.md), config `texpass.json`.

## Cause

Smart UVs on the halved LOD0: 48.6 % of the 2048 atlas, 379 islands, 36.7 % of the surface on fragments. Density was
already high for a 0.95 m cat (body 1,616, head 3,743 texels per metre), so the gain here is the fragments and the 4K
paint, not resolution.

## Route

1. `tp_dump.py`: head (Head, Socket_Mouth) x2.0, paws x1.3.
2. `tp_uv.py` **`uv_v2`** (`cut_closed=1 max_stretch=1.8 retry_stretch=3.0 merge_below=20 fine=250 steps=0`): 62.7 %,
   2.1 % fragments, stretch 1.18; body 1,810, head 3,614 texels per metre. **The paid layout; never re-run it.**
3. One retexture with the production masters, meshy-7, 4K, our UVs: `body_retexture_v1`, **10 credits**.
4. `tp_resample.py`, `tp_bake_ao.py` (reach 0.015, a small animal), `tp_compose.py` (`head_sigma` 1.2), `tp_apply.py`.

The 17 small separate parts (whisker strips, eyes, nose: `work/small_parts.npy`, 748 faces) keep the approved colour
and normal (`keep_approved_faces`): with the paint's normal map the whiskers lost their highlights and disappeared
against the background in the review shots. `tp_viewer_variants.py` now writes `base_<tag>.glb` for a GLB without
variants.

## Results (`texture_quality.py`, LOD0 `M500_A`)

| | Before | After |
|---|---|---|
| Atlas | 48.6 % | **62.7 %** |
| Equivalent px | 1,428 | 1,621 |
| Density p10 / p50 / p90 | 1,355 / 1,546 / 1,633 | 1,673 / 1,722 / 2,246 |
| Islands / fragments | 379 / 36.7 % | 114 / 2.1 % |
| Stretch p90 | 1.48 | 1.18 |

Colour mean identical (47.5/46.6/45.7), luminance sd 16.2 -> 19.8 (fur grain). LOD1 against LOD0 colour error mean
1.5 -> 1.1, p99 25.5 -> 22.3; LOD2/LOD3 maps refilled.

## Checks

- `tp_diff.py` OK; winding 0; flat 0.00; viewer `check` 0 console errors (16 switches).
- `mm6_mm7_mm8_actor_models_build_every_binding`: the run right after the install failed 3 bindings (transient, as on
  the Ghost an hour earlier); the immediate re-run PASS (647 descriptors, 0 failed). Floor audit zcat a/b/c 0
  problems; motion audit re-run (`audit_after/`, clips identical).
- Sheet: [review/texpass_sheet.png](review/texpass_sheet.png) (head front and 3/4, body, back, side, legs). Eyes,
  whiskers, nose and ears match the installed ones; the fur reads finer and evener (no blotches between islands).

Installed 2026-11-11 (MM7). Rollback: install `work/before_texpass/mm7_7m500.glb`.
