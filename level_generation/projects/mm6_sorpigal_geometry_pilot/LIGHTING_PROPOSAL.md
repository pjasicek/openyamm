# Lighting the detail models without growing the lighting file

Proposal, 2026-11-11. Requirement (user): New Sorpigal's `oute3.lighting` must not grow past the unchanged map's
size because of the detail models. The current bake gives every detail face its own lightmap chart: 79.5 MB
against 17.2 MB. This document says where the size goes and how to light the detail without charts of its own.

## 1. Where the 79.5 MB goes

Both files were parsed (format: `tools/lighting/baked_outdoors/FORMAT.md`). The parser scripts are in the session
scratchpad (`lighting_research/parse.py`, `charts.py`, `hosts.py`, `geo.py`, `budget.py`). The sizes are from the
79.5 MB `build/bake` taken before the 22:17 rebuild, and from `build/rebake_original`.

| Part | Original (17.2 MB) | Detailed town (79.5 MB) |
| --- | ---: | ---: |
| Terrain sun, sky and direct-sun pages | 8.6 MB | 8.6 MB |
| Probes (62k × 52 B) | 3.2 MB | 3.3 MB |
| Building pages (sun + sky, RLE) | 4.3 MB (2 pages) | 57.1 MB (13 pages) |
| Building direct-sun pages (v5) | 0.8 MB | 6.8 MB |
| Face and vertex records (24 B per face, 12 B per vertex) | 0.25 MB | 3.7 MB |

The building charts:

| | Charts | Inner texels | Outer texels (4-texel padding) | Padding share | Charts at the 4×4 minimum |
| --- | ---: | ---: | ---: | ---: | ---: |
| Original faces | 3,140 | 218 k | 822 k | 73 % | 683 |
| Detail faces | 47,673 | 2.85 M | 11.4 M | 75 % | 19,043 |

- Every face gets a chart of at least 4×4 texels and 4 texels of padding on each side, so 144 texels to store 16
  useful ones (`tools/lighting/bake_outdoor.py:296-301`, `tools/lighting/bake_geometry.py:60`, Cycles margin 3 at
  `bake_outdoor.py:559`). Each texel is stored three times (sun, sky and direct sun, 4 B each as RGBM). After RLE a
  stored texel costs about 5.3–6.2 B.
- The detail faces are small. Their median chart is 24 texels, 77 % of them (36.9 k) are smaller than one original
  32×32-unit texel, and they hold only 19 % of the detail area. The density barely matters because the minimum
  chart and the padding dominate. This matches the 8 → 86 MB and 12 → 78.7 MB results.
- Per-face charts cannot meet the target at any setting. The detail charts' inner texels alone, with no padding,
  cost about 15 MB. The v5 face and vertex records for the detail faces add 3.4 MB. Merging coplanar detail faces
  into shared charts (as `group_coplanar_faces` does indoors) still leaves 16,987 plane groups, which costs at least
  about 6.5 MB.
- Runtime memory follows the file. The building pages are decoded to BGRA and uploaded as 26 textures of about
  4 MB each, about 105 MB of GPU memory against about 10 MB now (`game/outdoor/OutdoorRenderer.cpp:3690-3705`).

## 2. What the engine already has

- **BModel faces:** each lighting vertex carries a lightmap UV and an ABGR colour
  (`game/outdoor/OutdoorLightingData.h:22-34`, copied into the vertex at `OutdoorRenderer.cpp:2558-2560`). In the
  baked path the shader never reads that colour. It is used only in the old combined-lightmap path
  (`game/shaders/outdoor_bmodel_lightmap.sh:260` against `:267`), and the producer writes white. That gives us a free
  per-vertex channel on baked maps.
- **Runtime sun term:** the baked shader multiplies only the direct-sun share by a runtime visibility,
  `totalSun - directSun * (1 - visibility)` (`game/shaders/outdoor_baked_lighting.sh:15-37`). The visibility comes
  from three-cascade sun shadow maps (`engine/render/ModelSunShadows.h:33-35`; the default quality 2 uses 1024 px
  per cascade out to 3,072 units, roughly 1 unit per texel near the camera and 4 at the far end).
  - Casters today are actors, decoration models and the terrain (`OutdoorRenderer.cpp:4775-4799`).
  - BModels do not cast, because their shadows are baked.
  - The surface-material path already relights a baked flat face for another normal: `relight`, `skyFacing` and
    `sunStrength = directSun / max(N·L, 0.15)` (`outdoor_bmodel_lightmap.sh:163-187`).
- **Defaults:** desktop turns on sun shadows and screen-space ambient occlusion (SSAO) by default
  (`game/app/GameSettings.cpp:495-497`). Android keeps both off (`GameSettings.h:228`, `:286`).
- **Decoration GLBs show how to light geometry without lightmap charts.**
  - One baked probe per placement supplies indirect sun, sky and sun visibility (`OutdoorRenderer.cpp:3446-3476`).
  - Direct sun is N·L times the runtime shadow map (`game/shaders/fs_model.sc:440`).
  - Ambient occlusion is baked per vertex in COLOR_0 (`engine/models/ModelAsset.h:122-127`).
- **Indoor bakes show how to compute lightmap UVs from world position.** They store a per-face affine map from
  world position to page UV and compute UVs from positions (`game/indoor/IndoorBakedLighting.h:29-46`). They use
  2-texel padding (`tools/lighting/bake_indoor.py:57`).
- **Lightmaps have no mipmaps** (`game/render/TextureFiltering.cpp:43-47`), so 2 texels of padding are enough for
  bilinear sampling.
- **Hidden faces get no chart today.** The bake skips Invisible (0x2000) faces (`bake_outdoor.py:280`), so the
  replaced original faces lose the charts they had in the original bake.

Geometry of the 47,673 detail faces, measured against the 654 hidden original faces:

| Detail faces | Count | Examples |
| --- | ---: | --- |
| In the plane of a hidden face | 7,055 | the wall rebuilt around its windows |
| Parallel to a hidden face, a few units off it | 11,394 | glass, timbers, sill fronts |
| Perpendicular to a hidden face | 19,768 | recess sides, sill tops, steps |
| Near no hidden face | 8,836 | caps on visible roofs, coping, plinths, posts, rafters |

## 3. Options, ranked

### A (recommended): host charts, per-vertex detail terms and runtime detail shadows

Each detail face borrows the chart of a host face, an original face that keeps its chart. The bake covers only the
original geometry. Detail-scale shading comes from three sources: relighting the host value for the detail face's
own normal, a per-vertex occlusion and sun-visibility byte, and the detail models casting into the existing sun
shadow cascades.

- **Project generator** (`source/generate.py:157`, `Mesh.add`): record a host `(bmodel, face)` for every face it
  adds. This is the face a relief piece comes from, the wall under a sill, the roof under a cap, the top under
  coping, or the replaced post. Free-standing bits (brackets, rafter ends) take the nearest face of their building.
  `plan.json` lists the hosts.
- **Bake** (`bake_outdoor.py`):
  - Chart the Invisible faces that are hosts.
  - Bake the scene as the original map: hosts visible and casting, detail models absent. The building pages then
    equal `rebake_original`, which is a byte-level check. It also ends the black terrain patches.
  - Then compute one byte per detail vertex: 4 bits of local occlusion and 4 bits of direct-sun visibility, from
    short-range rays against detail and host geometry. Cycles can bake to vertex colours, or Blender's BVHTree can
    cast the rays.
  - Faces lying in the host plane get identity values, so values do not streak across large earcut triangles.
- **Format v6** (optional section, so v3–v5 files load unchanged):
  - Record the first detail model.
  - Give each detail face a host as `u16 model, u16 face` (4 B).
  - Give each detail vertex 1 B.
  - Detail models get no v5 face or vertex records. The count checks at `OutdoorLightingData.cpp:330-332` become
    "records + detail faces = ODM faces".
  - The loader checks that each host has a lightmap.
- **Loader and renderer:**
  - At load, derive each host's affine world-to-UV map from three of its vertices and their UVs, as indoors does.
  - Each detail vertex gets its host's page and `uvAt(position)`, which projects it onto the host's plane.
  - The vertex's free COLOR0 carries occlusion, visibility and the direct relight ratio
    `max(Nd·L, 0) / max(Nh·L, ε)`, clamped. The loader writes identity values for every ordinary face.
  - The baked shader applies the ratio and visibility to direct sun, and occlusion with a sky-facing ratio to sky
    and indirect sun. For ordinary faces it computes exactly what it computes today.
  - The detail models' triangles go into the sun-shadow pass as world casters, one static buffer per chunk. Only
    maps with a v6 detail section have them.
- **Size for New Sorpigal:** the original 17.20 MB plus 0.19 MB of hosts plus 0.19 MB of vertex bytes, about
  **17.6 MB**.
  - To end at or below the original, also set `chart_padding: 2` in the profile, as indoors uses. That gives about
    **15.4 MB**: the original charts' outer texels drop from 822 k to 470 k.
  - The probe count barely changes: 62.4 k probes in the original against 62.9 k now.
- **Quality on desktop** (shadows on by default):
  - Recess, sill, cap, eave and post shadows come from the cascades at about 1–4 units per texel. That is crisper
    than the current 4-units-per-texel bake.
  - SSAO adds contact darkening.
  - Beyond 3,072 units there are no detail shadows, but the reliefs are under a pixel there.
- **Quality with shadows off and on Android:**
  - The relight gives sunlit and shaded recess sides and dark cap undersides.
  - The vertex bytes darken crevices and give coarse recess shadows.
  - Sill shadows on the wall are lost.
- **Runtime cost:**
  - No new vertex attribute.
  - A few ALU operations in the baked fragment path.
  - About 95 k extra caster triangles, culled per cascade.
  - Load cost is one affine evaluation per detail vertex (190 k).
- **Effort:** medium.
  - Generator: host bookkeeping.
  - Bake tool: charting hosts, the vertex pass and padding.
  - Format, loader and validation, with a unit test.
  - Shader and caster pass.
  - MM6–MM8 regression check: captures of a few baked maps must be pixel-identical with shadows on and off.

### B: A, plus detail-aware host charts for chosen buildings

For hero buildings, or for Android-quality bakes, bake the host charts of hidden faces from the detail surface.
Cycles' selected-to-active bake would cast along the host normal onto the detail model, at a finer density. Faces
in or parallel to the host plane then get baked recess, timber and sill shadows on every platform. Perpendicular
faces still use the relight from A.

- Size (padding 2, all hidden hosts): about 16.2 MB at 16 units per texel, still under the original, but too
  coarse for sills. At 8 units per texel it is about 19.1 MB, over the original, so only a few named buildings
  fit at 8.
- Effort: A plus a cage bake per host chart, and a density key per host.

### C (not recommended): per-vertex lighting only

Store sun, sky and direct sun per detail vertex instead of hosts: 3 × 4 B × 190 k = 2.3 MB, so about 19.5 MB in
total. Large earcut wall triangles would interpolate the light across building-scale shadow edges, and the file
still exceeds the original. A gives better light for a sixth of the bytes.

## 4. Regressions and side notes

- Every engine change is gated on the v6 detail section, except the COLOR0 identity fill, which must give
  bit-identical results. Maps without detail models (all of MM6–MM8 and MM9's combined lightmaps) keep their files,
  draws and shadow casters.
- The same growth shows outside the lighting file. The pilot's `oute3.odm` grew from 1.9 to 18.4 MB, and
  `oute3.scene.yml` from 0.9 to 8.4 MB, mostly from 52 k `legacy_attributes` entries for the Untouchable detail
  faces. This is worth its own look.
