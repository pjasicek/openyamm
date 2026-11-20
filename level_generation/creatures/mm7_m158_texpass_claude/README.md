# Bat texture quality pass (MM7 `mm7_m158`), 2026-11-11

This is the texpass stream of the MM6–MM8 audit fixes, done by texpass-2
([TEXPASS.md](../audit_mm678_20261111/fixes/TEXPASS.md)). It follows the
[recipe](../claude_shared/TEXTURE_QUALITY_PASS.md) and the [handoff](../claude_shared/texpass_mm678/HANDOFF.md).
Only UVs, vertex splits and images change. Mesh, rig, clips, ramps, materials, variants and `actors.yml` are
unchanged.

Production projects: [mm7_m158_claude](../mm7_m158_claude/README.md) and
[mm7_m158_reduce_claude](../mm7_m158_reduce_claude/README.md). The pass starts from the installed GLB, backed up as
`work/before_texpass/mm7_m158.glb` with `actors_entries.yml`. Lease `mm7:m158`.

**Meshy: 10 credits.** One 4K body retexture (`meshy/body_retexture_v2`) on the paid layout, using the production
HD masters.

## Route

This is the generic toolkit from [mm7_m186_texpass_claude](../mm7_m186_texpass_claude/README.md), driven by
`texpass.json` and run in this order:

`dump.py` → `uv.py` → `resample.py` → `bake_ao.py` → `compose.py` → `apply.py` → `viewer.py` → `shots.py` →
`finish.sh --install`.

Settings:
- Head factor ×1.5 on Head, Ear_L and Ear_R.
- Region R is the wing membrane.
- LOD1 is projected per chart. LOD2/3 have their own 512/256 maps, so those maps were transferred again from the new
  LOD0.

Two additions to the toolkit and the shared tool came out of this model:

- **`claude_shared/uv_atlas.py` fix.** The first layout (`work/uv_fine.npz`, unused) had 3 charts (92 triangles,
  finger membranes) collapsed to a point by SLIM. `_density_ratio` returned NaN for a fully collapsed chart, so the
  chart was not reverted. It now returns infinity, and such charts go back to their xatlas pieces. The paid layout is
  **`work/uv_fine2.npz`, with 0 zero-area triangles. Never re-run it.**
- **Detail limiter in `compose.py`** (`texpass.json detail_limit`, 1.3 here). The 4K paint gave the nose a
  high-contrast dark/light camouflage pattern. The limiter scales the paint's luminance detail down where its local
  sd over about 6 texels exceeds 1.3× the median over the surface. This damps that patch to the installed look and
  keeps the fur grain; see the close-up crops in [review/cmp_close_a.png](review/cmp_close_a.png).

## Results (`texture_quality.py`, LOD0 base colour `Bat_A`)

| | Before | After |
|---|---|---|
| Atlas | 12.4 % | **57.5 %** |
| Equivalent px | 721 | 1,554 |
| Density p10 / p50 / p90 | 833 / 1,068 / 1,587 | 2,486 / 2,556 / 2,805 (×2.4 median) |
| Spread | 1.90 | 1.13 |
| Islands / fragments | 1,773 / 29.2 % | 393 / 4.1 % |
| Stretch p90 | 1.89 | 1.13 |

**Tone** (sRGB means, approved → pass):
- membrane: (42.7, 83.7, 17.6) → (44.3, 84.1, 19.0), luminance sd 15.0 → 16.1;
- fur and skin: (164.1, 128.7, 114.7) → (162.4, 128.2, 113.2), sd 40.4 → 39.0.

The ramps are unchanged.

**LOD colour error against LOD0** (mean / p99, before → after):
- LOD1: 9.4 / 82.1 → 5.8 / 69.9;
- LOD2: 5.6 / 63.7 → 7.1 / 52.5;
- LOD3: 11.5 / 91.4 → 10.3 / 74.9.

## Checks

- `glb_diff.py`: OK. Only UVs, splits (8,863 → 9,716) and images differ.
- Winding: 0. Flat shading: 0.00.
- Clips, positions and weights are identical per corner, so motion and detached parts were not re-run.
- Floor audit (`*Bat*`): 3 bindings, 0 problems.
- Viewer check: 6 models × 5 clips, no console errors.
- `mm6_mm7_mm8_actor_models_build_every_binding`: PASS.

**Sheet:** [review/texpass_sheet_m158.png](review/texpass_sheet_m158.png). It shows head front, head 3/4, top, side
and whole body for each tier, installed against pass, with identical auto cameras on the posed Fly frame.
- Fur, ears and wing veins are crisp.
- The red eyes are unchanged.
- The membrane tiers (green, blue, red) hold.

Installed 2026-11-11 (MM7). To roll back, install `work/before_texpass/mm7_m158.glb`.
