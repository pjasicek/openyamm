# MM6 bones: Meshy skull pile, skull and skeleton (2026-10-09)

Revision 2 of the user's gallery review: `sklplrev` (skull pile) through Meshy, and authentic skulls and skeletons
for `torskul0` (skull torch, `../torches/`), `hngncge2` / `hngncge2_long` and `bonecage` (cages, `../hanging/`).

## Route

1. **HD masters (Codex).** Three runs, briefs in `<asset>/references_hd/CODEX_BRIEF.md`, from the ORIGINAL native
   bitmaps (`assets_dev/_legacy/sprites_original/*.bmp`, nearest-neighbour enlargements on magenta; the x2 files only
   as "surface material only"): `skullpile/` (landscape, from `sklplrev`), `skull/` (square, skull shape from the
   `torskul0` skulls, colour from `sklplrev`), `skeleton/` (portrait, neutral A-pose, anatomy from `hngncge2` and
   `bonecage`). Records: `generation_runs.json`, `selected_views_review.png`; hashes in `meshy_progress.json`.
2. **Meshy** (`tools/run_creature_meshy.sh`, state `meshy_progress.json`, budget 120, requests in `requests/`):
   Smart Topology from each `00_three_quarter`, then `scripts/prep_meshy.py` (crumbs dropped, grounded, Smart UV) and a
   `meshy-7` retexture (2k, PBR, original UVs) from `01_front`, `03_left`, `02_back`, `04_right` (the skull's left and
   right masters were labelled by screen side, so its request swaps them).

| Job | Task id | Credits |
|---|---|---|
| skeleton_smart_topology_v1 | rejected (target_polycount 20000 > 15000 limit) | 0 |
| skeleton_smart_topology_v2 (15k, A-pose) | 01a1208d-0158-771f-ad4e-eeb3979b359e | 5 |
| skullpile_smart_topology_v1 (12k) | 01a1208d-2f22-75e5-a146-9a33a3f8107a | 5 |
| skull_smart_topology_v1 (5k) | 01a12091-6b6b-726b-a750-fcbbf036024f | 5 |
| skeleton_retexture_v1 | 01a1208f-cc53-756a-a4fa-9fb0ffd9100b | 10 |
| skull_retexture_v1 | 01a12098-f202-7333-bf7f-f6d3b7cb60ad | 10 |
| skullpile_retexture_v1 | 01a1209a-c78e-76f7-bed7-60faa14ad72a | 10 |
| skullpile_hd_multiview_v1 (pile v3: `meshy-7.1` multi-image, no remesh, PBR 2k) | 01a120c1-5eb7-737b-ba66-c4a3cd4c1596 | 30 |
| **Total** | | **75** |

Assets kept here: `work/skull_tex.blend` (5329 triangles, 147 pieces incl. separate teeth),
`work/skeleton_tex.blend` (15502 triangles, 147 bone pieces), `work/skullpile_tex.blend` (11432 triangles, 120
skull-sized lumps), texture sets in `textures/`.

## Skull pile (`sklplrev`, 86 placements) -> `mm6_deco_skullpile_meshy.glb` (v3, high-to-low bake)

History: v1 (`scripts/build_skullpile.py`) was the Smart Topology pile with faces painted on lumps; v2
(`scripts/build_skullpile_inst.py`, `bake_skull_proxy.py`, `make_skullpale.py`, `shade_pile.py`) instanced a
220-triangle skull on each lump with per-vertex native shading. The user rejected v2 ("really bad": faceted skulls,
hard white facets and black blotches); its sheets are in `review/before_v2_instanced/`. v3 is the approved route:

1. **High mesh.** Meshy multi-image-to-3D (`requests/skullpile_hd_multiview_v1.json`: `meshy-7.1`,
   `should_remesh: false`, PBR 2k) from `00_three_quarter`, `03_left`, `02_back`, `04_right` (the API takes four
   images): 4,661,906 triangles, one connected mesh, real skulls with sockets, teeth and jaws
   (`review/shape/hd_thumbs.png`, `high_front.png`). Its width profile matches the sprite from 20 % of the height up,
   so no squash (bounds 246 x 246 x 153 units). `scripts/import_high.py` -> `work/pile_high.blend` (the Meshy
   GLB in `meshy/` is 145 MB).
2. **Low mesh** (`scripts/make_pile_low.py`): collapse to 400k, voxel remesh at 1.5 units, light smoothing, collapse
   to 11000, Smart UV (66 degrees). Decimating the raw Meshy mesh directly gave about 5000 tiny UV islands and seams
   that stopped every further LOD; the voxel pass makes the surface even. `scripts/add_far_lod.py` adds a far mesh
   (voxel remesh at 5 units, 2000 triangles) whose own charts take the atlas corner [0.875, 1]^2 (LOD0's charts are
   scaled into [0, 0.875]^2).
3. **Bake** (`scripts/bake_pile.py`, Cycles selected-to-active, cage 4 units, only the high mesh visible to rays):
   base colour, tangent normals, AO (30 units, 128 samples) and object-space normals of the high mesh onto LOD0 and
   the far mesh together, at 2048.
4. **Texture** (`scripts/compose_pile.py pilebaked 2048 2048 0.85 1.0 0.9 0.8`, `DENOISE=0.7`): colour x AO (0.85)
   x a baked top-and-outward light from the object normals (0.8), then a texture-level native grade (the bake read
   flat next to the sprite): luminance histogram of the exposed LOD0 texels matched to the sprite's, colour pulled
   toward the sprite's luminance-to-colour table (0.9), plus `pilebake_tone.npz` from `scripts/pile_tone.py`
   (rendered front median 0.271 vs native 0.270). The bone-pore grain is 70 % blurred (sigma 1.2) before grading so
   it does not turn into speckle. COLOR_0 is white: all light and shade are in the texture.
5. **LODs** (`scripts/build_pile_baked.py`): LOD0 10988, LOD1 3988 (LOD0 decimated), LOD2 2000 (the far mesh),
   LOD3 300 (a voxel mound on one plain bone texel of the far charts: decimating the charts to 300 smeared them into
   shards). One texture set for all; LOD3's material `BoneFar` shares the base-colour image without the normal map.
6. **Texture size:** base colour 2048, normal 1024, metallic-roughness 64 (uniform rough 0.78). 2k base colour is
   visibly sharper than 1k at close range (teeth, socket rims: `review/shape/bake_2k_vs_1k.png`); a 1k normal map
   is indistinguishable from 2k (`bake_2k_vs_mixed.png`), because most detail sits in the graded colour. GLB 5.16 MB
   (8.35 MB with a 2k normal map, 4.19 MB with both at 1k). The engine reads PNG textures only and no occlusion
   texture, so AO lives in the base colour.
7. Rebuild: `blender -b --python scripts/import_high.py`; `blender -b ../work/pile_high.blend --python
   scripts/make_pile_low.py -- 11000 1.5 2 66`; `blender -b ../work/pile_low.blend --python scripts/add_far_lod.py`;
   `blender -b ../work/pile_low.blend --python scripts/bake_pile.py -- 2048`; `scripts/pile_bake_iter.sh <tag>`
   (with `CHROMA=0.9`; repeat `pile_tone.py --update pilebake_tone.npz` until the medians agree);
   `scripts/finish.py skullpile --install --reinstall`.

Review: `review/shape/pile_close_cmp_final.png` (flat close-up beside the x2 sprite), `lit_final.png`,
`lit_final_y120.png` (lit close-ups, front and back), `review/skullpile/compare.png`, `lods.png`, gallery shots
`review/gallery_v3/` (studio and dungeon light, dungeon and outdoor bindings). The gallery's flat mode shows every
model at about 0.6 of its sprite's brightness (bag01, bonecage, ckfyr00 alike), so compare in studio or dungeon light.

## Skull (`torskul0`) and skeletons (cages)

- `../torches/scripts/build_torskul.py` now uses the Meshy skull (700 / 260 / 100 triangles per skull, 31 units
  wide, bowed 22 degrees), textured `textures/skullfire_*` (`scripts/make_skullfire.py`: the Meshy base colour's
  luminance through the sprite's fire ramp, crowns at the native (252, 168, 96)).
- `scripts/pose_skeleton.py hanging|sitting` poses the Meshy skeleton rigidly: rest joints measured on the mesh
  (`skeleton/skeleton_joints.json`), each bone piece bound wholly to its nearest capsule (`scripts/skelpose.py`),
  trunk aimed at targets, limbs by two-bone IK, joints fitted on overlays with the x2 sprites
  (`review/shape/hanging_overlay.png`, `sitting_overlay_side.png`). The Meshy skull replaces the skeleton's own
  (fitted to its bounds). LODs by per-piece decimation (no bone collapses into shards); LOD2/3 drop fingers and toes.
  Output `work/skeleton_<pose>.blend` + `.json` (posed wrists), read by `../hanging/scripts/build_cage.py`.
  Hanging 2390 / 1114 / 360 / 168 triangles (185 units standing), sitting 2577 / 1114 / 360 / 168 (235 units).
- Cage textures are 512 (skeleton and skull), so each cage GLB is about 3.2 MB.

## Installed models and suggested bindings

| GLB (`assets_dev/worlds/mm6/models/`) | LOD triangles | Size |
|---|---|---|
| `mm6_deco_skullpile_meshy.glb` (new, v3) | 10988 / 3988 / 2000 / 300 | 5.16 MB |
| `mm6_deco_torskul.glb` (rebuilt) | 2573 / 1069 / 450 | 2.39 MB |
| `mm6_deco_torskul_free.glb` (rebuilt) | 3206 / 1314 / 534 | 2.46 MB |
| `mm6_deco_hngncge2.glb` (rebuilt) | 4875 / 2495 / 656 / 262 | 3.22 MB |
| `mm6_deco_hngncge2_long.glb` (rebuilt) | 7339 / 3671 / 656 / 262 | 3.36 MB |
| `mm6_deco_bonecage.glb` (rebuilt) | 4206 / 2127 / 612 / 256 | 3.21 MB |

The rebuilt GLBs were installed as new files (the previous ones stay hard-linked in `output/textures_x4_runs/`).
The cage, torch bindings are unchanged (heights 321 / 1159 / 250 / 179, swing pivot at the bounds top). The skull
pile needs its binding switched in both manifests (`decorations.yml` and `indoor_decorations.yml`):

```yaml
  - name: sklplrev
    model: worlds/mm6/models/mm6_deco_skullpile_meshy.glb
    height: 153
    height_jitter: 0.05
```

Outdoor maps whose bakes reference `sklplrev` need a re-bake after the switch.

## Compromises

- The pile's LOD0 (11k) is above the brief's band for tens of placements, as the coordinator specified (10-12k).
- The pile's light is baked in its texture (from above and outward at every azimuth) and the engine lights it again
  on top; the base is about 1.4 times the sprite's bottom width (Meshy's lowest skulls spread out).
- Skeleton poses are rigid per bone piece (no bending inside a bone); the bone cage's huddled pose follows the
  sprite's silhouette from the front and side, not every bone.
- The torch skull crowns read slightly pale under the gallery's studio light (COLOR_0 clamps at one onto the
  texture's orange); at the sprite's own light the flat render matches.

## Sources and licences

All geometry and textures here come from paid Meshy generations on the project's account (job ids above; output
owned by the account under Meshy's terms) driven by Codex-generated HD masters, derived from the original MM6
sprites. No CC0 scans were used (no suitable CC0 skeleton was found; the Meshy route fitted the sprites better).
