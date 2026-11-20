# MM6 flowers — static 3D decorations (2026-10-08; rose bush and sunflowers 2026-10-09)

| Sprite | Placements | Installed GLB | LOD triangles | File |
|---|---|---|---|---|
| `6flower02` (orange gazania) | 16 | `assets_dev/worlds/mm6/models/mm6_deco_flower02.glb` | 570 / 136 / 103 | 0.45 MB |
| `6flower07` (purple crocus) | 16 | `assets_dev/worlds/mm6/models/mm6_deco_flower07.glb` | 724 / 402 / 130 | 0.58 MB |
| `6flower06` (pink rose bush) | other MM6 maps | `assets_dev/worlds/mm6/models/mm6_deco_flower06.glb` | 1564 / 598 / 224 | 0.98 MB |
| `6flower08` (sunflower clump) | other MM6 maps | `assets_dev/worlds/mm6/models/mm6_deco_flower08.glb` | 1212 / 576 / 218 | 0.67 MB |

`6flower06`/`6flower08` are not placed in New Sorpigal; they were built for Misty Islands, Silver Cove, Castle
Ironfist and Eel Infested Waters (binding heights 131 and 88 units). Review: `review/6flower02_compare.png`,
`review/6flower07_compare.png`, `review/6flower06_compare.png`, `review/6flower08_compare.png` (native | enhanced | 3D LOD0 eye level |
three-quarter) and `review/<id>_lods.png`.

## Sources and licences

No external images: `scripts/make_atlas.py` paints each 512² atlas (base colour RGBA + tangent normal) from leaf and
petal shapes with numpy, coloured to the native sprites' means. Original work for this project; no attribution
needed. Poly Haven `flower_gazania` (CC0) was considered as a source but not used.

## Build

`./build.sh 6flower02 --install` (or `6flower07`, `6flower06`, `6flower08`): atlas → Blender plant (`scripts/build_plant.py`) →
`scripts/post_process.py` (MASK 0.5 double-sided, `tools/link_static_model_lods.py`, `tools/cut_foliage_cards.py`,
validation, install) → review renders (`scripts/render_review.py`) and sheets with LOD consistency (`scripts/sheet.py`).

## Construction

- Contract as the trees: glTF Y-up metres, origin at the base centre, meshes `Plant`, `Plant_LOD1`, `Plant_LOD2`
  linked as LODs; one MASK material `Plant` (double-sided), extras `openyamm_wind` 0.02, `openyamm_specular` 0.1,
  `openyamm_translucency` 0.3; COLOR_0 occlusion (dark at the ground and inside the clump).
- Gazania (0.32 m tall): 20 foliage cards (atlas cells 0/1, a dense dome of grey-green leaves) leaning out from a low
  base; 17 daisy heads as shallow cup meshes (cell 2 mapped from above) on the dome surface turned outward so they
  read from eye level, five raised on thin stem quads (cell 3 strip).
- Crocus (0.23 m tall): 14 grass-leaf cards; 12 blooms as 8-segment lathed goblets wrapped in a tileable six-petal strip
  (cell 2) with a stamen disc inside the opening and a short pale stem (cell 3).
- Rose bush (revised 2026-10-09): a loose mound, wider at the base. Leaf cards sit near an ellipsoid shell widened
  toward the ground (horizontal radius ×1.2 − 0.4·z) and broken by 18 soft random lobes and dents. There are 124
  outer cards of 0.38–0.5 m, each tilted off the shell tangent at random and never facing far downward, so no large
  single plane forms a shell. Gaps show 36 inner cards darkened to 40 % (COLOR_0), and 18 sprigs (three cards in a
  star, a rose near the tip) poke out of the silhouette. The 124 roses (4.5–7 cm) sit on the outer leaves over the
  sides and top. The foliage cells carry small dark leaves, 16 % of them sunlit, plus leaflet sprays that break the
  clump outline and ten painted roses each. Roses are pink-red with light outer petals and a dark red core (cell 2).
- Sunflower clump (revised 2026-10-09): 78 heads (13–22 cm) cover the whole hemisphere from near the ground to the
  top, each on a short stem strip (crossed at LOD0) and facing outward 10–40° up, so none is edge-on from the side.
  60 leaf cards form a low skirt (shell 0.80 × 0.38 m round z 0.22) between and below the heads.
- Heads on both are flat cones (one triangle per segment): rose 8 / 6 / 4 segments keeping 100 / 45 / 18 % of the
  heads and 100 / 50 / 28 % of the cards (enlarged ×1.2 / ×1.5); sunflower 10 / 8 / 4 keeping 100 / 65 / 55 % of
  the heads and 100 / 55 / 38 % of the cards (×1.14 / ×1.3). Budgets in
  `post_process.py`: 2200 / 700 / 260 (rose) and 1600 / 600 / 220 (sunflower); the small flowers keep
  1500 / 600 / 200. Neighbouring levels: rose within 2.4/255 colour and 5 % coverage; sunflower LOD2 9.2/255 (red,
  fewer heads) with 3 % coverage.
- Gazania and crocus LOD1/LOD2 keep a seeded subset of the cards (enlarged to hold coverage) and every flower with fewer segments.
  Neighbouring levels (Eevee, eye level): mean colour within 4.0/255, coverage within 4.4 %.

## Compromises

- Flower heads are geometry rather than painted texture, so a few gazania heads seen edge-on read as thin slivers.
- The gazania foliage is a little more uniform and darker than the sprite's leafy grey-green mass.
- Crocus goblets are smooth and closed; the sprite's bright highlights and veins are simpler here.
- The rose bush reads as overlapping leafy cushions rather than the sprite's separate sprays, and it is darker
  overall; a few sprig cards show as thin dark slivers when seen end-on. The roses are less bright than the
  sprite's pink highlights.
- The review renders scale the whole specular term by `openyamm_specular`, as the engine does
  (`scripts/render_review.py`). Earlier renders lowered only Eevee's specular level, which left the full grazing
  Fresnel sky sheen on edge-on cards; that sheen showed as grey "glass" sheets on the first rose revision.
- Sunflower heads are flat discs (no ray depth); at LOD2 they are four-sided.
