# Organic ground items — 2026-10-18 WIP

**Assigned job complete: 39 examined, 30 replaced and installed, 9 kept, 0 deferred.** The approved sixteen Meshy Smart Topology jobs succeeded and consumed exactly **80/80 credits**. No paid retries or retexture jobs. All binding lengths are unchanged. This remains development WIP, excluded from release packages.

## Visual review

- [First fourteen Blender replacements: source / above / low](review/blender_sheet_1.png).
- [Sixteen Smart Topology replacements: source / above / low](review/meshy_sheet_1.png).
- [Blender UV checker](review/blender_checker_sheet_1.png) and [Smart Topology UV checker](review/meshy_checker_sheet_1.png).
- [All sixteen HD masters](review/masters.png), [plain mesh shapes](review/clay_shapes.png) and [six-view guide sheets](review/all_guide_sheets.png).
- [Outdoor native gallery](review/native/st_outdoor_sheet.png), [indoor overview](review/native/st_indoor/01-organic-st-overview.png), [indoor closer view](review/native/st_indoor/02-organic-st-close.png). Earlier fourteen-model native captures remain under `review/native/outdoor/` and `review/native/indoor/`.
- [Original baselines, sheet 1](review/baseline_sheet_1.png) and [sheet 2](review/baseline_sheet_2.png).

## Per-icon ledger

| Icon | Item | Action | Route | Triangles |
|---|---|---|---|---:|
| 7item140 | Phirna Root | replaced | Smart Topology | 3330 |
| 7item141 | Widowsweep Berries | replaced | Blender | 2924 |
| 7item143 | Poppysnaps | keep | existing relief | — |
| 7item144 | Crushed Rose Petals | keep | existing relief | — |
| 7item147 | Dragon's Eye | keep | existing relief | — |
| 7item149 | Harpy Feather | replaced | Blender thin relief | 384 |
| herb01 | Poppysnaps | keep | existing relief | — |
| herb02 | Phirna Root | replaced | Smart Topology | 3188 |
| herb03 | Widoweeps Berries | replaced | Blender | 1582 |
| item157 | Phima Root | replaced | Smart Topology | 3350 |
| item158 | Widowsweep Berries | replaced | Blender | 1250 |
| item161 | Wolf's Eye | replaced | Blender | 1494 |
| item164 | Phoenix Feather | replaced | Blender thin relief | 95 |
| item167 | Datura | keep | existing relief | — |
| item169 | Thornbark | replaced | Blender | 172 |
| item174 | Wasp Wing | replaced | Blender thin relief | 320 |
| 7item269 | Flower (Rose) | keep | existing relief | — |
| 7item275 | Wealthy Hat | replaced | Smart Topology | 3252 |
| 7item279 | Seashell | replaced | Blender | 920 |
| 7item282 | Season's Stole | replaced | Smart Topology | 3172 |
| 7item297 | Heart of the Wood | replaced | Smart Topology | 3251 |
| claw | Dragon Claw | replaced | Smart Topology | 2948 |
| clover | Four Leaf Clover | keep | existing relief | — |
| heart | Spider Queen's Heart | replaced | Smart Topology | 3318 |
| item300 | Naga Hide | replaced | Smart Topology | 3093 |
| item301 | Dire Wolf Pelt | replaced | Smart Topology | 3302 |
| item303 | Royal Wasp Jelly | replaced | Blender | 524 |
| item304 | Dragonbane Flower | keep | existing relief | — |
| item310 | Pirate Hat | replaced | Smart Topology | 3652 |
| item314 | Heartwood of Jadame | replaced | Blender | 108 |
| item316 | Dried Sunfish | replaced | Blender | 2088 |
| item321 | Ogre Ear | replaced | Smart Topology | 3263 |
| item322 | Wasp Stingers | replaced | Blender | 220 |
| pouch1 | Leather Pouch / Pouch of Bat Guano | replaced | Smart Topology | 3147 |
| pouch2 | Leather Pouch | replaced | Smart Topology | 3290 |
| pouch3 | Leather Pouch | replaced | Smart Topology | 3202 |
| rose | Rose | keep | existing relief | — |
| tooth | Tooth | replaced | Blender | 396 |
| wspwrp | Whisp wrappings | replaced | Smart Topology | 2999 |

## Production and receipts

`progress.json` contains each decision, baseline hash, selected export, review paths and installation receipt. `install_receipts.json` records all thirty source/runtime hashes and selected installer logs. The original models are preserved in `work/baseline/`; the rollback archive is untouched. `designs.json` contains worker-prefixed designs only.

Meshy source geometry and download hashes are recorded in `meshy/creature_3d_progress.json`. The sixteen untextured jobs cost five credits each; [meshy_budget.json](meshy_budget.json) records the user approval and eighty-credit total. Meshy geometry was kept near its supplied budget where decimation would save little: 2,948–3,350 triangles, except the locally repaired pirate hat at 3,652. No model exceeds the 4,000-triangle validation ceiling. No extra LODs for these already-small objects.

The first fourteen `.blend` files and exports are under `work/blender/`. The sixteen Meshy authoring scenes, unprocessed exports, baked maps and bake receipts are under `work/codex_tex/`. Their selected guides, painted views, raw sheets, metal masks and split/registration receipts live under `codex_tex/organic_*/`. Six orthographic views are packed per object for image generation and split back into the exact mesh framing. No nested Codex sessions were launched.

Images used the built-in imagegen tool. Exact prompts and selection history are in `textures/generation_runs.json`, each HD master’s `generation_runs.json`, and each texture folder’s `paint_generation.json`, `metal_generation.json` and corrective generation receipts where applicable. The approved stage added sixteen albedo sheets, seven metal-mask sheets and ten corrective sheets; Meshy supplied geometry only. Original returns and superseded sheets are retained. The old pirate-hat guide was replaced by the closed-crown guide; its receipt explicitly notes that history.

## Geometry, materials and validation

All thirty exports pass `scripts/verify_organic.py`: valid embedded PNGs, finite UVs in 0–1, no degenerate triangles, no inverted closed components, footprint centred, lowest point zero and normalized horizontal extent one. [review/validation.json](review/validation.json) contains per-model bounds, counts, UV ranges and hashes. Total: 64,234 triangles across thirty replacements. Final length axes are Blender Y / glTF Z; the final claw and pirate-hat alignments are recorded in `review/axis_alignment.json`.

The eleven simple Blender meshes use their purpose-built material atlas and separate roughness atlas. The jelly jar keeps glass on its own transparent mesh node. The other sixteen have 1024 base colour, metallic-roughness and normal maps projected from the accepted exact-mesh paintings. Seven mixed-material models have independently painted binary metal masks; nonmetal designs have zero metallic. The six source-colour calibrations are explicit glTF baseColorFactor values; the exporter’s unsupported shader multiplication was replaced with native factors. [review/pbr_validation.json](review/pbr_validation.json) verifies the masks, maps, factors and axes and records texels per normalized authoring metre.

Local shape corrections: roots, cloth, hides, heart and bags rest on their broad sides; the ear’s concha faces upward; the wrappings have the source’s narrow footprint. The pirate hat’s missing top was closed with a rounded cloth crown, then its exact guides and painting were regenerated before installation.

Eight initial albedo sheets were rejected because one or more panels changed the guide silhouette. Their one corrective pass uses the guide alone as a hard shape constraint. The quilted pouch’s mask was similarly corrected. Two extremely thin Naga Hide views still failed and are explicitly excluded from projection; its accepted top/bottom/front/right paintings supply the bake. No rejected silhouettes enter that texture. Unseen interiors/recesses use the existing projection bake’s darker filled treatment; per-model coverage is recorded in the bake receipts.

The Harpy and Phoenix feather meshes retain their baseline topology and UVs, including 36 and 9 original boundary edges; only their thickness is reduced to one quarter. The Wasp Wing is closed. The eye iris is intentionally open over the closed eyeball. No visible inverted closed surfaces were found in the above/low reviews.

## Native checks and scope

Both final isolated native runs completed with exit 0 on NVIDIA / OpenGL 3.3. Run records and complete logs are `review/native/st_outdoor_run.json`, `st_outdoor_game.log`, `st_indoor_run.json` and `st_indoor_game.log`. The outdoor tour uses the all-items MM7 save; the indoor tour drops all sixteen approved-stage icons in Agar’s Laboratory. Pillars occlude part of the grid, so these are representative shared rendering checks rather than one unobstructed frame of every object. The first attempted indoor grid was out of view and was rerun at the earlier verified positions; only the successful final records are linked here. These captures do not establish performance or drop-physics coverage.

Only assigned icon models and this worker project were changed by this worker. Shared bindings, tables, engine code, other workers’ files, settings, package rules and shared authoring scripts were left alone. Source and runtime installation used only `tools/install_model.py --world-items` with its existing lock. No whole-family installer, global cook, game build, staging, commit or release promotion. Android/release tests were not run.

## Rebuild

Run `scripts/meshy_batch.py -- prep <organic_design...>` in isolated Blender, then `scripts/paint_sheets.py pack <design>` with Python. Generate and review guide-aligned albedo/mask sheets; `paint_sheets.py split <design> paint|metal` saves the exact-frame view inputs and registration receipts. Run `meshy_batch.py -- bake <design...>` in Blender, validate, review and install selected owned icons only. Do not overwrite existing selections or submit paid repeats.

For the first group, `scripts/build_organic.py -- <icon...>` rebuilds selected Blender models. Its default covers the eleven simple models; include `7item149 item164 item174` explicitly for the three thickness corrections. It never installs models. Runtime reviews use the retained isolated-tour JSON files.
