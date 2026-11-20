# Ghost texture quality pass (MM7 `mm7_m242`), 2026-11-11

Texpass stream of the MM6–MM8 audit fixes, agent texpass-3 ([TEXPASS.md](../audit_mm678_20261111/fixes/TEXPASS.md)),
after the [recipe](../claude_shared/TEXTURE_QUALITY_PASS.md) and the [handoff](../claude_shared/texpass_mm678/HANDOFF.md).
Only UVs, vertex splits and images change; mesh, rig, clips (including the animation stream's Walking loop fix of
the same day, which is in the installed GLB this started from), ramps, materials, variants and `actors.yml` stay.

Production projects: [mm7_m242_claude](../mm7_m242_claude/README.md), `mm7_m242_reduce_claude`,
`mm7_m242_animfix_claude`. Starting point: the installed GLB, backed up as `work/before_texpass/mm7_m242.glb` with
`actors_entries.yml`. Lease `mm7:m242`. Kit: the `tp_*.py` scripts from
[mm8_m584_texpass_claude](../mm8_m584_texpass_claude/README.md), config `texpass.json`.

## Cause

A 2080 x 1024 body | head atlas: robe and skeleton at 235 texels per metre on 1,232 islands, 45.6 % of the surface on
fragments (Meshy painted each as a blotch: the speckled robe of tier A); the hooded skull (head set, 8.1 % of the
surface) at 1,264.

## Route

1. `tp_dump.py`: head set = old atlas u > 0.5, x2.5; hands x1.3.
2. `tp_uv.py`: `uv_h25` (fast packer: 60.6 %, 8.7 % fragments), **`uv_h25v2`** (`cut_closed=1 max_stretch=1.8
   retry_stretch=3.0 merge_below=20 fine=250 steps=0`): 61.1 %, 3.7 % fragments, stretch 1.17. **The paid layout;
   never re-run it.** Texels per metre: skull and hood 1,264 -> 1,552, robe and skeleton 235 -> 628.
3. One retexture with the production masters (`references_hd/` 01-04), meshy-7, 4K, our UVs: `body_retexture_v1`,
   **10 credits**. No head paint (`head_sigma` 1.2 keeps the approved skull).
4. `tp_resample.py`, `tp_bake_ao.py` (0.03), `tp_compose.py` with `detail_limit` 1.3 (without it the ramp of tier A
   turned the paint's braid on the robe's front seam into a black-and-white checker), `tp_apply.py`.

Kit change: this GLB's LOD1 shadow copy is LOD1 shrunk by up to 14 mm, so no corner matched; `tp_apply.py` now copies
the visible LOD's UVs to a shadow copy with the same triangles in the same order when it is within 1.5 % of the
model's extent (texpass-2 met the same on the Gorgon).

## Results (`texture_quality.py`, LOD0 `M242_A`)

| | Before | After |
|---|---|---|
| Image | 2080 x 1024 | 2048² |
| Atlas | 49.6 % | **61.1 %** |
| Equivalent px | 1,465 | 1,600 |
| Density p10 / p50 / p90 | 328 / 453 / 1,420 | 1,142 / 1,169 / 1,476 |
| Spread | 4.33 | 1.29 |
| Islands / fragments | 1,232 / 45.6 % | 585 / 3.7 % |
| Stretch p90 | 1.60 | 1.17 |

Tiers (`tp_tier_tone.py`): robe A/B/C within 0.7 sRGB levels (A 158.2/152.4/147.0 -> 158.9/153.1/147.7), bone within
0.2; luminance sd: A robe 39.2 -> 37.6 (less speckle), bone 38.3 -> 34.4. LOD1 against LOD0 colour error mean 5.2 ->
2.1, p99 46.5 -> 24.8; LOD2/LOD3 maps refilled from the new LOD0.

## Checks

- `tp_diff.py` OK; winding 0; flat shading 0.08 (as installed); viewer `check` 0 console errors (42 switches).
- `mm6_mm7_mm8_actor_models_build_every_binding`: the first run right after the install failed 3 bindings (the same
  transient texpass-1 met on the Lich, likely a concurrent cook from another session); the immediate re-run PASS (647
  descriptors, 0 failed). Floor audit Ghost A/B/C 0 problems; motion audit re-run (`audit_after/`, clips identical).
- Sheets: [review/texpass_head_sheet.png](review/texpass_head_sheet.png) (skull front and 3/4, chest),
  [review/texpass_body_sheet.png](review/texpass_body_sheet.png). Skull, teeth and ribs match the installed ones; the
  robe loses the blotchy speckle of tier A and shows cloth weave in every tier.

Installed 2026-11-11 (MM7). Rollback: install `work/before_texpass/mm7_m242.glb`.
