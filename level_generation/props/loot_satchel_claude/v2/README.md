# Loot satchels v2 (concept E, 2026-10-09)

Supersedes v1 (the parent folder's six separate meshes with spilled coins). The user picked concept E
(`../concepts/E_material_plus_glow.png`) with tiers 5 and 6 changed to purple and crimson: **one shared drawstring
sack, the tier told by material, colour and size only**, no coins.

![tiers](review/tiers.png)
![distance](review/distance.png)

| Model (`assets_dev/engine/models/`) | Loot value | Material | Width (in-game, drawn 1:1) | Triangles |
|---|---|---|---|---|
| `loot_satchel_t1.glb` | 1-99 | undyed burlap, wooden clasp | 0.50 m | 900 |
| `loot_satchel_t2.glb` | 100-749 | patched green wool, bone clasp | 0.58 m | 900 |
| `loot_satchel_t3.glb` | 750-2,999 | rust-brown leather, brass clasp | 0.66 m | 900 |
| `loot_satchel_t4.glb` | 3,000-7,999 | blue leather, gold cord | 0.76 m | 900 |
| `loot_satchel_t5.glb` | 8,000-14,999 | purple velvet, gold embroidery, violet gem (emissive) | 1.01 m | 900 |
| `loot_satchel_t6.glb` | 15,000+ | crimson velvet, gold embroidery, amber gem (emissive) | 1.25 m | 900 |

Tiers 5 and 6 were enlarged on 2026-10-09 at the user's request (+15 % and +25 %, from 0.88 and 1.00 m).

Contract: glTF Y-up metres, base on the ground (min Y = 0), plan centre on the origin, one mesh node, **no LOD chain**,
no skin or animation. The widths are final: the engine should draw them at 1 m = 1 m (no extra enlargement).
`openyamm_specular` 0.3 (burlap, wool, leather) or 0.2 (velvet), `metallicFactor` 0. Tiers 5 and 6 have a second
material `LootSatchelT<N>_Gem` on the clasp ball (same textures, `emissiveFactor` t5 [0.18, 0.08, 0.30], t6
[0.40, 0.30, 0.12]). Textures: base colour 1024, normal and metallic-roughness 512 (R 1, G roughness, B 0).

## Route

1. **References** (`references_hd/`, [brief](references_hd/CODEX_BRIEF.md)): Codex image generation from concept E and
   the native MM6 gold pile sprites (look only). `master/00_three_quarter.png` (tier 3 leather) for the mesh, then per
   tier `01_front`, `02_back`, `03_left`, `04_right`, each generated with the master and the tier-3 view as inputs so
   the silhouette stays identical. Records: `generation_runs.json`, `selected_views_review.png`.
2. **Meshy** (`requests/`, receipts in `creature_3d_progress.json`, project claimed as `engine:loot_satchel_v2`, budget
   90): one Smart Topology from the master (5 credits), then six retextures of the same full mesh
   (`work/high_upload.glb`, Meshy UVs) from each tier's four views in the order front, left, back, right (10 credits
   each). **65 credits** in total.
3. **Blender** (`/snap/bin/blender --background --python ...`, run from the parent folder):
   - `v2/scripts/prep.py`: join, drop floaters, scale to a 1 m plan width, ground, smooth a copy and collapse it to
     900 triangles, Smart UV and packing. Writes `work/shared.blend` (LOD0 + High) and `work/high_upload.glb`.
   - `v2/scripts/finish.py -- N`: fits tier N's retexture onto High, bakes base colour, roughness and High's normal onto
     LOD0 (the v1 nearest-hit transfer), scales to the tier width, puts the clasp island in the gem material for
     tiers 5-6 (`tiers.CLASP`: the island containing the face nearest that point), exports `work/tN_export.glb`.
   - `python3 v2/scripts/finalize.py 1 2 3 4 5 6`: material extras, install (0644) and parse checks.
   - `v2/scripts/render_review.py -- tiers|distance`: `review/tiers.png`, `review/distance.png`.

## Notes

- The clasp ball is a separate 20-face island in the Smart Topology mesh, so the gem material covers exactly it.
- All six share one mesh and UV layout; a new tier or colour is one more retexture plus `finish.py`/`finalize.py`.
