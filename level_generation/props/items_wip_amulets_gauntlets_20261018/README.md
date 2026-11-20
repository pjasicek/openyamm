# Amulets and gauntlets in 3D — 2026-10-18

38 replacements installed in the development `engine/world_items` mount: 20 amulets modelled in Blender and
18 gauntlets finished from 17 existing paid Meshy Smart Topology shapes. The explicit user follow-up assigns these
families to this project. The equipment worker's project and Meshy lease were left untouched. No new Meshy credits
were spent; the reused jobs consumed 85 credits in the earlier equipment batch.

| Family | Models | LOD0 triangles, per model | Total LOD0 triangles | Models with LOD1 |
|---|---:|---:|---:|---:|
| Amulets | 20 | 664–4,576 | 50,990 | 8 |
| Gauntlets | 18 | 2,438–5,040 | 72,174 | 16 |

Per-icon source/runtime counts, hashes and material inventory are in [model_stats.csv](review/model_stats.csv) and
[model_stats.json](review/model_stats.json). Every material has base colour, packed metallic/roughness and OpenGL
tangent normal textures. Amulet material tiles are 256²; gauntlet maps are 512². Source and cooked LOD0 counts match.

## Geometry and materials

Amulets have separate closed pendant bodies, backs, settings, stones, bails, interlinked chain loops and raised
ornaments. The eye is a sphere with a cap and suspension; the hand charm has four fingers and one thumb.
Identical icon groups retain the same design: Morgan/Hera/Fire/Ruby Star, the two sun pendants and the two skull pendants.

Gauntlets retain the paid shapes and the selected five-digit Troll Gauntlets correction. Open shells received real
wall thickness. Lining duplicated inside already closed fittings was removed; the connected cuff lining remains.
Curved gloves have individual dorsal-up rest poses. The returned originals, copied prepared scenes and HD masters
are retained under `references/`, with geometry and rest-pose receipts under `receipts/`.

Imagegen painted the jewellery material atlas and gauntlet projection sheets/material masks. Metalness is binary;
roughness follows declared metal, leather, horn and gem/enamel classes. Normal detail is derived from the paintings,
with restrained strength. No albedo brightness rule decides metalness. Albedo channels are limited to 30–243.

The gauntlet baker uses four registered side views. Axial paintings that changed perspective were rejected;
unobserved outer caps inherit the nearest painted surface in 3D and tagged interior walls use painted leather.
Raw paintings, rejected first passes, prompts, material masks and registration measurements are retained.

LODs normally use about 50% of LOD0. `item128` and `item261` retain LOD0: both 50% and 65% automatic reductions
opened their thin cuff surfaces. Invalid LODs are quarantined under `work/lod_stage_rejected/` and are not installed.
These two need a deliberately modelled LOD if their distant draw cost becomes significant.

## Review

Each comparison row contains the inventory icon, above, three-quarter, low and underside views:

- Amulets: [1](review/amulets_finished_1.png), [2](review/amulets_finished_2.png),
  [3](review/amulets_finished_3.png), [4](review/amulets_finished_4.png).
- Gauntlets: [1](review/gauntlets_finished_1.png), [2](review/gauntlets_finished_2.png),
  [3](review/gauntlets_finished_3.png).

Native NVIDIA/OpenGL captures use isolated settings/saves. They check ground placement, ordinary viewing size,
materials and indoor/outdoor lighting; they are not performance measurements. Final records and copied game logs
are in [native_review.json](receipts/native_review.json) and `receipts/native_runs/`.
Two attempts failed during EGL surface creation before assets loaded; fresh isolated retries succeeded.
Both failed attempts are retained separately under `receipts/native_failures/`.

- [Amulets outdoors A](review/native_outdoor_a/outdoor_a.png),
  [B](review/native_outdoor_b/outdoor_b.png), [C](review/native_outdoor_c/outdoor_c.png).
- [Amulets indoors A](review/native_indoor_a/indoor_a.png),
  [B](review/native_indoor_b/indoor_b.png), [final suspension check](review/native_amulets_final/amulets_final.png).
- [Gauntlets outdoors A](review/native_gauntlet_outdoor_a/gauntlet_outdoor_a.png),
  [B](review/native_gauntlet_outdoor_b/gauntlet_outdoor_b.png),
  [gauntlets indoors](review/native_gauntlet_indoor_a/gauntlet_indoor_a.png).

## Validation and handoff

[validation.json](review/validation.json) checks all 38 source GLBs and their accepted LODs: finite attributes,
unit normals, UV range, no degenerate triangles, closed outward-facing components, opaque culling, embedded PNGs,
all three material maps, binary metalness, albedo range and centred/grounded footprints. Every replacement was
installed with `tools/install_model.py --world-items` and passed exact desktop cooking verification.
Source SHA-256 guards stopped conflicting edits; no overlapping source changes were found.

The original `saves/Ground items test.oysav` is unchanged:
`795fffeb87a7d95962e0e4e5af72b166ca9b6986400f43ad96c0d95edbe2fffa`.

[handoff.json](handoff.json) contains 38 proposed collision/picking bounds for the coordinator. Existing filenames
and binding lengths were preserved. Shared `items.yml` was not edited; its old bounds still need reconciliation
before global acceptance. The archive and other workers' projects are unchanged.

This is development WIP. Release/Android promotion, Android device checks and engine builds were outside this
asset job. No staging or commits were performed.

## Reproduction

The local scripts retain the production steps: `build_amulets.py` / `material_tiles.py` for jewellery;
`prepare_gauntlets.py`, `remove_hidden_shells.py`, `rest_poses.py`, guide packing, mask cleanup and registration,
then `bake_gauntlets.py` for gloves. `build_lods.py` exports the accepted reductions, which are linked with the
shared `tools/link_static_model_lods.py`. `validate_items.py`, `contact_sheets.py`, `install_ready.py` and
`report.py` produce the checked installation and per-icon ledger. `receipts/lod_decisions.json` records the two
deliberately unreduced gloves.
