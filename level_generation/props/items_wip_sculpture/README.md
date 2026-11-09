# Sculpture ground items — 2026-10-18

All 27 assignments examined: **25 replacements installed, one feather retained, one angel deferred**.
The 14 approved Meshy Smart Topology jobs succeeded, consuming **70 of 70 approved credits**, with no retries.
This is a WIP art handoff; it remains excluded from release packages.

## Review and receipts

- [Per-icon handoff](handoff.json), [validation](review/validation.json) and [installed source/runtime hashes](receipts/installed.json).
- Blender icon/above/three-quarter/low sheets: [1](review/blender_comparison_1.png), [2](review/blender_comparison_2.png).
- Meshy icon/above/front three-quarter/low sheets: [1](review/meshy_comparison_1.png), [2](review/meshy_comparison_2.png), [3](review/meshy_comparison_3.png).
- `review/blender_checker/`, `review/codex_tex_checker/`: UV checker renders. All review GLBs were re-imported with backface culling.
- `meshy/creature_3d_progress.json`: all paid requests, immutable reference hashes, task IDs, charges and downloads.
  The workspace claim was released after successful downloads. Raw Meshy outputs remain unchanged.
- `meshy/*/references_hd/generation_runs.json`, `textures/generation_runs.json` and `codex_tex/*/generation_runs.json`:
  prompts, source references, selected/superseded returns and hashes. The first eight texture jobs did not retain
  their exact earlier guide revision; their receipts say so. The final six exact atlas inputs are retained.
- `codex_tex/*/`: final six-view geometry guides, painted sheets, registration and bake coverage reports.
- `receipts/install_*.log`: per-icon desktop cooking through the shared installer lock. No global cook or build.

## Native checks

The earlier eleven Blender replacements passed [MM7 outdoors](review/native_outdoor_clean/sculpture_outdoor_clean.png)
and [MM6 indoors](review/native_indoor_clear/indoor_clear.png).
The fourteen new sculptures have two batches each in `review/native_meshy_outdoor_*` and `review/native_meshy_indoor_*`.
All four follow-up runs passed. Each folder retains the native capture, run record, settings snapshot and game log. NVIDIA/OpenGL desktop checks
cover grounding, culling and material readability. Original test save, retained feather and deferred angel source
hashes are unchanged. Android cooking/device checks, release builds and performance benchmarks were not run.

## Geometry and materials

The eleven Blender meshes range from 60 to 2372 triangles. The fourteen complex sculptures stay within their
2400–3200 triangle budgets. Meshes have centred footprints, glTF +Y up and lowest point zero; materials are
single-sided. No LOD chain is needed for these small rigid ground items in this art pass.

Meshy supplied untextured Smart Topology geometry. Local cleanup caps boundary seams and removes intersecting
sheets. Four problematic volumes use a 0.4%-extent voxel union, followed by removal of disconnected voxel dust
and collapse reduction. Abbey Normal's thin crown needs 1.2%-extent shell thickness before union: the final wall
is intact, verified visually as well as numerically. Raw Meshy downloads are retained for comparison.

The complex meshes use six orthographic painted views, including the underside, baked into 1024px basecolour,
OpenGL tangent-normal and metallic-roughness maps. Smart UV seams and hard shading boundaries both use 40 degrees.
Gold, blue enamel, ivory horns and the Snake Idol's red sphere have separate binary material regions. The knight
has a nonmetal stone plinth. The crystal skull is opaque frosted mineral. Mild unseen inner regions are filled
from neighbouring paint; bake reports record observed coverage. The bear/wolf sheets have disconnected cell-edge
bleed removed before registration. Paintings and final geometry are preserved separately.

The simple meshes use 512px painted material tiles. Long bone variants share the same actual femur silhouette,
while the short thigh bone and wyvern horn retain their own source contours. The four elemental hearts share
one faceted cut with explicit palette variants. The reliquary uses violet enamel plus a gold cage; the signet has
separate gold, silver and black/ivory seal materials. All exported images are embedded PNGs.

Only the assigned 25 source/runtime models were installed. Binding lengths stay unchanged, with no requested
coordinator adjustments. Shared bindings, tables, engine code, package rules and other worker projects were not
edited. Nothing was staged or committed.

## Deferred angel

**Finished later** in Blender without image generation: [Angel Statuette project](../sculpture_angel_20261018/README.md).

`7item263` retains its original model. Two image attempts produced no usable master; the second explicitly returned
an output moderation rejection. No replacement design or paid Meshy job was submitted for it. The approved budget
covers the other fourteen designs only. `quill` remains an adequate thin feather relief.

## Per-icon ledger

| Icon | Item | Decision | Triangles |
|---|---|---|---:|
| `6thybone` | Bone | REPLACED | 596 |
| `7item250` | Signet Ring | REPLACED | 568 |
| `7item261` | Knight Statuette | REPLACED | 3000 |
| `7item262` | Eagle Statuette | REPLACED | 2800 |
| `7item263` | Angel Statuette | DEFERRED: image service rejection | — |
| `7item270` | Zokarr IV's Skull | REPLACED | 2400 |
| `7item271` | Thigh Bone | REPLACED | 596 |
| `7item272` | Haldar's Remains | REPLACED | 2372 |
| `7item291` | Dragon Egg | REPLACED | 516 |
| `7item369` | Abbey Normal Golem Head | REPLACED | 3000 |
| `7item370` | Golem head | REPLACED | 3000 |
| `crysskull` | Crystal Skull | REPLACED | 2600 |
| `item270` | Heart of Fire | REPLACED | 60 |
| `item271` | Heart of Water | REPLACED | 60 |
| `item272` | Heart of Air | REPLACED | 60 |
| `item273` | Heart of Earth | REPLACED | 60 |
| `item293` | Remains of Korbu | REPLACED | 3200 |
| `item298` | Idol of the Snake | REPLACED | 3000 |
| `item305` | Bone of Doom | REPLACED | 596 |
| `item308` | Wyvern Horn | REPLACED | 596 |
| `quill` | Harpy Feather | KEEP: thin relief | — |
| `skull` | Ethric's Skull | REPLACED | 2400 |
| `statuet1` | Tiger Statuette | REPLACED | 2600 |
| `statuet2` | Bear Statuette | REPLACED | 2600 |
| `statuet3` | Wolf Statuette | REPLACED | 2600 |
| `statuet4` | Eagle Statuette | REPLACED | 2600 |
| `statuet5` | Dragon Statuette | REPLACED | 2800 |

## Reproduce checks

```sh
python3 level_generation/props/items_wip_sculpture/scripts/material_masks.py
python3 level_generation/props/items_wip_sculpture/scripts/audit_sculpture.py
/snap/bin/blender --background --factory-startup --python level_generation/props/items_wip_sculpture/scripts/review_items.py -- codex_tex
/snap/bin/blender --background --factory-startup --python level_generation/props/items_wip_sculpture/scripts/review_items.py -- codex_tex --checker
```

Authoring uses local `scripts/codex_texture.py -- prep <design>` and `-- bake <design>` through isolated Blender.
Regenerating geometry changes UVs and requires a new bake; review before any individually scoped install.
