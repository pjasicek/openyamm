# MM6 statuette pedestals ped01–ped05 (2026-10-09)

The five filled shrine pedestals (Bear, Tiger, Eagle, Wolf, Dragon Statuette). An MM6 shrine event swaps
`ped06` (the empty pedestal, `mm6_deco_pedestal.glb`) for `ped0N`; without a model it fell back to the 2D sprite.

## Models

| Decoration | GLB (`assets_dev/worlds/mm6/models/`) | LOD triangles (pedestal + figure) | Binding height | File |
|---|---|---|---|---|
| ped01 Bear | `mm6_deco_pedestal_bear.glb` | 3164 / 1276 / 496 | 177 | 2.16 MB |
| ped02 Tiger | `mm6_deco_pedestal_tiger.glb` | 3163 / 1275 / 496 | 179 | 2.18 MB |
| ped03 Eagle | `mm6_deco_pedestal_eagle.glb` | 3159 / 1273 / 495 | 210 | 2.33 MB |
| ped04 Wolf | `mm6_deco_pedestal_wolf.glb` | 3164 / 1276 / 496 | 185 | 2.21 MB |
| ped05 Dragon | `mm6_deco_pedestal_dragon.glb` | 3163 / 1275 / 492 | 210 | 2.26 MB |

**Enlarged past the sprite** (the user approved the models but wanted bigger figures, a deliberate departure from
the sprite size): from the sprite fit, each figure is scaled up uniformly so its footprint is FILL = 87.5 % of the
64.8-unit slab top along x (and at most that across), capped at CAP = 40 % of the pedestal height (60 units), never
smaller than the sprite fit, and centred on the slab (`statuette.py prep`). Nothing overhangs the slab.

| Figure | Scale | Size (x, y, z units) | Limit |
|---|---|---|---|
| Bear | 1.10 | 56.7 x 28.1 x 26.9 | slab length |
| Tiger | 1.00 | 61.6 x 19.4 x 28.7 | already 95 % of the slab (tail), kept |
| Eagle | 1.71 | 55.0 x 28.9 x 60.0 | height cap |
| Wolf | 1.03 | 56.7 x 21.9 x 35.2 | slab length |
| Dragon | 1.30 | 55.5 x 41.3 x 60.0 | height cap |

Each figure is 1400 / 600 / 220 triangles, on the ped06 pedestal's own LODs (1764 / 676 / 276) and materials
(`Granite`, `Gold`), loaded unchanged from `../props/work/pedestal.blend`. Filling a pedestal changes only what stands
on top. The binding height is the model's bounds height, so the pedestal stays exactly 150 units (the sprites' art
extents, 165.8 / 177.0 / 180.1 / 180.5 / 192.8, would shrink it; ped01's sprite also draws its pedestal smaller).

## Route

1. **HD masters (Codex)**, one run per animal: `<animal>/references_hd/CODEX_BRIEF.md`, from the native BMP
   (`assets_dev/_legacy/sprites_original/ped0N.bmp`): an 8x nearest-neighbour crop of the statuette and the whole
   sprite at 3x. Three views each: `00_three_quarter` (sent to Meshy), `01_left`, `02_front`. No x2 frame was used.
   Gate: `review/masters_00.png` (primary next to the native crop).
2. **Meshy** `meshy-7.1` image-to-3D, `model_type: standard`, no texture, no remesh (`requests/<animal>_hd_v1.json`,
   state `meshy_progress.json`). Full-detail meshes of 163k to 927k triangles, one piece each.

| Job | Task id | Credits |
|---|---|---|
| bear_hd_v1 | 01a1210c-b7ed-7203-9c02-5677c550208f | 20 |
| tiger_hd_v1 | 01a1210d-4f8f-74b0-b560-0f8ef0c1d04d | 20 |
| eagle_hd_v1 | 01a1210d-56fa-777d-a542-867b5ed1d0df | 20 |
| wolf_hd_v1 | 01a1210d-5ffe-749b-9a07-c9a59bc9e18b | 20 |
| dragon_hd_v1 | 01a1210d-6981-76c9-ab72-c58a661a427a | 20 |
| **Total** | | **100** |

3. **Blender** (`scripts/statuette.py`, stages `prep`, `bake`, `textures`, `build`; `scripts/run_one.sh <animal>
   <sprite>` runs all of them plus finish and review):
   - **Facing.** The Meshy front (-y) is turned -90 degrees, so the head points to -x. The sprite shows the animal's left
     side from the camera at -y.
   - **Size.** Each figure is first fitted to its sprite box, measured on the x2 sprite against the slab (172 px = the
     model's 66.6-unit capital): length along x, height above the slab, and horizontal offset (`ANIMALS`). Height may
     differ from a uniform scale by up to 20%. The dragon is fitted by height (its raised neck), with its length
     following within 20%. Then the enlargement above.
   - **Mesh.** Game mesh: collapse to 200k, voxel remesh at 0.35 units, collapse to 1400, Smart UV.
   - **Bake.** Tangent normals and AO (6 units) from the full-detail mesh at 512.
   - **Surface.** A polished, worn gold, not a Meshy texture. Metallic 1. Base colour (186, 156, 84) is darkened by a
     cavity term from the AO, toward the sprite's dark olive-brown hollows. Fine seeded pitting appears in colour and
     roughness, as the sprite's grainy gold. Roughness is about 0.3 on exposed forms and 0.6 in the hollows.
   - **LODs.** LOD1 decimates the figure to 600. LOD2 is a voxel mound of it at 220, using the pedestal's shared
     `Gold`.
   - COLOR_0 is white on the figure, and the pedestal keeps its own occlusion.
4. `scripts/finish.py <animal> --install` (LOD link and validation; budgets 3300 / 1350 / 520).

## Review

- `review/<animal>/compare.png`: native x2 sprite, LOD0 front, three-quarter and side, then the statuette's top in
  close-up (sprite crop, ortho front, three-quarter).
- `review/<animal>/lods.png`, `review/lods_all.png`, `review/tops_all.png` (all five close-ups).
- Gallery: `review/gallery/outdoor_ped0N_side.png` and `review/gallery/gallery_all.png`.

## Compromises

- The figures are Meshy sculpts of the Codex masters. Their forms are a little fuller than the sprite's thin pixel
  legs (bear, wolf), but pose, facing and silhouette follow the sprites.
- The gold reads a little more saturated than the sprite's olive gold under the review's studio light, because a
  metal's colour depends on the reflected environment.
- The dragon's crest is gold, not the sprite's few red-tipped spike pixels.

## Sources and licences

Geometry: paid Meshy generations on the project account (job ids above) from Codex-generated HD masters of the
original MM6 sprites. Textures: generated here (`scripts/statuette.py textures`) from the bakes. The pedestal is the
props batch's procedural model with its textures (`../props/`).
