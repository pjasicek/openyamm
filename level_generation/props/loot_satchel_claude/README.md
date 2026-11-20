# Loot satchel props — six tiers (2026-10-09)

> **Superseded by [v2](v2/README.md) (2026-10-09):** one shared sack in six materials (concept E), no coins. The
> files below are v1 history; the installed `loot_satchel_t1..6.glb` are now the v2 models.

Static 3D loot bags that replace a dead monster's corpse after it sinks and dissolves. The engine picks the tier from
the corpse's total loot value (gold plus item values); engine work is separate. This folder is art only.

![tiers](review/tiers.png)

| Model (`assets_dev/engine/models/`) | Loot value | Look | Plan width | Triangles (built LODs, stripped) |
|---|---|---|---|---|
| `loot_satchel_t1.glb` | 1–99 | small worn leather pouch, drawstring | 0.22 m | 396 / 189 / 96 / 30 |
| `loot_satchel_t2.glb` | 100–749 | leather satchel, brass buckle | 0.32 m | 599 / 268 / 118 / 46 |
| `loot_satchel_t3.glb` | 750–2999 | bulging bag, flap partly open, coins spilling | 0.42 m | 895 / 394 / 157 / 57 |
| `loot_satchel_t4.glb` | 3000–7999 | dark red treasure sack, gold trim and clasp, coins, ruby and sapphire | 0.52 m | 1200 / 521 / 200 / 90 |
| `loot_satchel_t5.glb` | 8000–14999 | ornate open sack, coin and gem heap, jewelled goblet | 0.62 m | 1474 / 573 / 193 / 93 |
| `loot_satchel_t6.glb` | 15000+ | royal-blue embroidered bundle, coin and gem heap, gemmed crown | 0.72 m | 1799 / 789 / 310 / 91 |

Contract: glTF Y-up metres, origin at the base centre on the ground (min Y = 0), one mesh node and **no LOD chain**,
`extras.openyamm_specular` 0.3 and `metallicFactor` 0 on every
material, no skin or animation. The LODs are still built and linked by `finalize.py`, then removed by
`scripts/lod0_only.py <tier>` (2026-10-09): in game the collapsed LODs visibly changed the satchels' shape while
walking up to them, and full detail costs little at this size. Run it after every `finalize.py`. One material per model, except t6: its ruby faces use a second material
`LootSatchelT6_Gems` (same textures, `emissiveFactor` [0.22, 0.03, 0.04]). The sapphires are not emissive because
their blue matches the velvet. Textures: base colour 1024, normal and metallic-roughness 512 (R 1, G roughness,
B 0). Plan width includes spilled coins, so the bags of t5 and t6 are smaller than the footprint.

## Route

1. **HD references** (`references_hd/`, briefs [t1–t4](references_hd/CODEX_BRIEF.md) and
   [t5–t6](references_hd/CODEX_BRIEF_T56.md)): Codex image generation, four views per tier (three-quarter,
   front, side, back; the side view shows the bag's left), transparent, returned at 1254². Coin colours come
   from the native MM6 gold pile sprites (`native_gold_piles.png`, `3coinsm/mid/lg`); no native satchel exists.
2. **Meshy** (`requests/`, receipts in `creature_3d_progress.json`, 90 of 90 credits used): Smart Topology from
   each tier's three-quarter image (5 credits), then a retexture of that full mesh (`work/tN_high_upload.glb`,
   Meshy UVs) from the front, side and back views (10 credits).
3. **Blender** (`/snap/bin/blender --background --python ...`):
   - `scripts/prep_tier.py -- N`: join, drop floaters, make the winding consistent, scale and ground, then a
     smoothed copy is collapse-decimated to the LOD0 budget, its inward faces turned out, Smart UV and packing.
     Writes `work/tN_lod0.blend` (LOD0 + High).
   - `scripts/finish_tier.py -- N`: the retexture output is fitted onto High; each LOD0 texel takes the High point
     it shows (nearest point, or the outermost surface along the face normal where the nearest point faces away),
     samples the Meshy base colour and roughness there, and stores High's normal in LOD0 tangent space. LOD1–3:
     collapse (ratios 0.45 / 0.2 / 0.08), with capped holes, dropped small islands or LOD0's convex hull where
     collapse stalls. Exports `work/tN_export.glb`.
   - `python3 scripts/finalize.py N`: link LODs, set material extras, install (0644) and parse-check.
   - `scripts/render_sheet.py`: `review/tiers.png` (all six, same scale, Eevee). `review/closeups.png`: each tier
     from the front and from behind-right (`scripts/preview.py ... eevee`).
4. **Tier 1 colour** (`base_projection`): its retexture was made on an early 400-triangle upload whose UVs used
   6 % of the atlas, so it read blotchy. `scripts/project_views.py 1` projects the four Codex views onto LOD0
   instead (yaws fitted jointly against High's silhouette, z-buffer visibility; `work/t1_projection.json`) and
   keeps the Meshy colour only where no view sees the surface (mainly the underside). Run order:
   `finish_tier.py -- 1`, `project_views.py 1`, `finish_tier.py -- 1`, `finalize.py 1`.

## Known limits

- Tier 1 still shows some faceting on its frill and cord: 400 triangles for a gathered pouch.
- Smart Topology meshes are thick-walled and keep inner faces in LOD0; culling them opened holes after collapse,
  so it was not used.
- Spilled coins are small separate pieces (pentagons at LOD0); LOD2–3 drop the smallest pieces.
