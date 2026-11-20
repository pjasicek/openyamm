# Crystal Dragon texture quality pass (MM8 `mm8_m548`), 2026-11-11

Part of the MM6–MM8 audit fixes, texpass stream (texpass-2,
[TEXPASS.md](../audit_mm678_20261111/fixes/TEXPASS.md)). It follows the
[recipe](../claude_shared/TEXTURE_QUALITY_PASS.md) and the [handoff](../claude_shared/texpass_mm678/HANDOFF.md).

Only UVs, vertex splits and images changed. Mesh (flat facets), rig, the ten clips (including the q4 gait clips),
material values, the absence of variants and `actors.yml` are unchanged.

- Projects: [mm8_m548_codex](../mm8_m548_codex/README.md) (production),
  [mm8_m548_reduce_claude](../mm8_m548_reduce_claude/README.md),
  [mm8_crystal_material_claude](../mm8_crystal_material_claude/README.md) (the accepted "subtle" crystal look).
- Starting point: the installed GLB, backed up as `work/before_texpass/mm8_m548.glb`.
- Lease: `mm8:m548`.
- **Meshy: 10 credits** (one 4K body retexture with the production HD masters).

## Route

This uses the generic toolkit in `scripts/`, from the m186, m158 and m564 projects. The paid layout is
**`work/uv_fine.npz`** (head and jaw ×1.5). LOD1–3 share the LOD0 atlas, so their UVs are projected per chart.

**Crystal look.** The installed base colour is the Meshy paint after `crystal_material.py ... m548 subtle`, which
applies:
- a native-matched colour transform;
- subtle per-facet tones whose edges follow the triangles exactly;
- uniform gloss;
- a quiet head;
- amber eyes kept as painted.

The standard compose would carry that look at its old resolution (blurred facet edges, luminance sd 8.1 → 6.5). So
the pass rebuilds the pre-material state instead:
1. `resample.py work/uv_fine.npz work/premat ../mm8_crystal_material_claude/work/mm8_m548_pre_material.glb` carries the
   pre-material paint onto the new layout. The script asserts the source's UVs equal the installed ones.
2. `compose.py textures/premat 4 0.9 1.3 work/premat` tones the 4K paint onto that pre-material paint: the island
   low-pass plus fine detail, with the detail limiter.
3. `apply.py` writes `export/premat_m548.glb`.
4. `crystal_material.py export/premat_m548.glb export/mm8_m548.glb m548 subtle` re-applies the accepted crystal
   transform at the new density. It found the same 5,442 facets, with 1,622 triangles in the quiet zone. Its
   material values are identical to the installed ones.

## Results

| `texture_quality.py`, `CrystalDragon` | Before | After |
|---|---|---|
| Atlas | 18.4 % | **56.3 %** |
| Equivalent px | 879 | 1,537 |
| Density p10 / p50 / p90 | 450 / 501 / 539 | 777 / 816 / 1,147 (×1.6 median; head ×1.5) |
| Islands / fragments | 966 / 22.0 % | 254 / 2.1 % |
| Stretch p90 | 1.46 | 1.22 |

- **Base colour at the same surface points**: installed mean (157.2, 103.7, 129.6), luminance sd 8.1; pass mean
  (157.1, 103.7, 129.6), sd 7.1. No drift.
- **LOD colour error** (mean / p99, before → after): LOD1 2.4 / 19.5 → 1.2 / 15.2, LOD2 5.4 / 24.8 → 3.4 / 20.7,
  LOD3 6.9 / 26.6 → 4.6 / 22.8.

The visible gain is small. The crystal look is flat facets with subtle tones and specular glints. The facet edges and
the eyes are a little crisper, and the look is unchanged. **Sheet:**
[review/texpass_sheet_base.png](review/texpass_sheet_base.png) (head front, head 3/4, top, side and whole body, at
identical cameras; one look for all three tiers).

## Checks

- `glb_diff`: OK; materials identical.
- Winding: 0.
- Flat shading 1.00, intended: the facets are flat, as installed.
- Viewer check: 2 models × 10 clips, no console errors. Native reference frames missing on disk are dropped from the
  manifest; the production viewer has those 404s too.
- `mm6_mm7_mm8_actor_models_build_every_binding`: PASS.
- Floor (`*Crystal Dragon*`): 3 bindings, 0 problems.

Installed 2026-11-11 (MM8). To roll back, install `work/before_texpass/mm8_m548.glb`.
