# Props worker — 2026-10-18

All **142 owned icons examined** against their restored inventory icons and the original source-model renders.
**123 replacements installed/cooked for desktop, 19 suitable reliefs retained, no deferred icons.** This is an isolated development WIP, not release promotion or final user art acceptance.

## Review and per-icon results

- [Per-icon ledger, CSV](ledger.csv) / [full JSON with validation](ledger.json).
- [Comparison 01](review/comparison_01.jpg), [02](review/comparison_02.jpg),
  [03](review/comparison_03.jpg), [04](review/comparison_04.jpg),
  [05](review/comparison_05.jpg), [06](review/comparison_06.jpg),
  [07](review/comparison_07.jpg), [08](review/comparison_08.jpg).
  Each cell is **source icon / above / low three-quarter**, in ownership order.
  Replacements use `review/revised/`; retained entries use `review/baseline/`.
- [Twelve sculptural replacements](review/meshy_final_comparison.jpg): source icon / above / low three-quarter.
- [New indoor capture](review/native_meshy_indoor/props_meshy_indoor.png) and
  [new outdoor gallery](review/native_meshy_outdoor_contact.jpg).
- [Native outdoor gallery](review/native_outdoor_contact.jpg), from the existing MM7 all-items save.
- [Native indoor display](review/native_indoor/props_indoor.png), Agar's Laboratory, MM6.
- Original model renders and source hashes are preserved under `review/baseline/` and
  [baseline_source_hashes.json](review/baseline_source_hashes.json).

Regular objects use local Blender builders: faceted cuts, ore volumes, turned vessels, scroll rolls and spirals,
three-strand rope coils, boarded/stencilled crates, open jar/ingredient cases, cards, books, instruments, lamp spouts,
hourglass frame/bulbs, and individual quest-prop constructions. Names were not used as shape authority: the
“Worn Belt” remains a rope coil, Mercury has separate flask/puddle designs, and reagents retain their containers.
Small sculptural details on these manually built props are simplified for ground viewing; compare the art sheets.

## Validation

- [Export checks](review/validation.json): 123 models, **116,316 triangles total**, maximum **3,200**.
  Zero inverted closed parts or degenerate triangles; finite positions/UVs, UVs in 0–1, embedded PNG references,
  baked node transforms, centred footprint, minimum height zero and longest footprint side along Blender Y.
- [Installed checks](review/installed_validation.json): source/runtime hashes and all 80 referenced cooked textures
  verified; 19 retained source models remained byte-identical to the captured baseline.
- All replacements re-imported into isolated Blender and rendered from above and a low three-quarter angle.
  [Crate checker](review/checker/7item400_low.png), [scroll checker](review/checker/item199_low.png),
  [ore checker](review/checker/7item353_low.png); crate wood uses consistent physical UV scale.
- [Texel density](review/texel_density.json) records each textured material before runtime binding scale.
  Repeated boards/parts intentionally share material UV space. Atlas cells are separate material textures,
  preventing cross-cell mip bleed; source PNGs are 256, 512 or 1024 square with embedded glTF images.
  The twelve sculptural models use area-normalized UV islands, 1024-square PBR maps, dilated gutters,
  and hard edges aligned with UV seams; [mesh audit](review/meshy_geometry_audit.json).
  Existing per-icon binding lengths are preserved.
- Metal and dielectric components use separate materials. Gold/silver in painted puzzle, drum and book templates
  use explicit metallic/roughness maps. Glass has its own blended mesh node. No single-metallic mixed-material bake.
  Native checks retain binary metal values; no engine-specific partial-metal exception was needed.
- Native desktop checks use the existing `build/game/openyamm`, NVIDIA vendor `0x10de`, OpenGL 3.3, Wayland.
  No item-model load errors. These are visual checks, not comparative performance measurements.
  Dense legacy test-map rows overlap some larger props and use elevated item positions; the indoor display uses spaced drops clear of the wall.
  The first new outdoor scatter crossed uneven terrain and was rejected; final captures use established save positions.
- LODs omitted for these already small static props. No renderer changes, global cook/build, Android test,
  release packaging, staging or commits were performed.

## Artwork and reproducibility

Four painted UV atlases for the Blender models were generated with the **built-in imagegen tool**, then their measured grid cells were
cropped/resized into PNG materials. No inventory-icon projection is used for these replacement volumes.
The [generation receipts](generation_runs.json) retain hashes, chosen output paths, prompts and derivation.

| Atlas | Selected image | Exact prompt |
|---|---|---|
| Shared materials and six ore types | [image](references/material_atlas_v1.png) | [prompt](references/material_atlas_prompt.txt) |
| Organic/mineral surface detail | [image](references/detail_atlas_v1.png) | [prompt](references/detail_atlas_prompt.txt) |
| Six stencils, cards and book cover | [image](references/panels_atlas_v1.png) | [prompt](references/panels_atlas_prompt.txt) |
| Instrument, magic-stone and nacre identity | [image](references/identity_atlas_v1.png) | [prompt](references/identity_atlas_prompt.txt) |

`designs.json` contains only worker-prefixed owned designs. `.blend` files are under `blends/`; unprocessed
exports are `work/exports/props_<icon>_export.glb`. [Install receipts](install_receipts.json) record source/runtime
hashes. Installation used only `tools/install_model.py --world-items --name item_<icon>.glb`, with its shared lock.

```sh
/snap/bin/blender --background --factory-startup --python level_generation/props/items_wip_props/scripts/build_props.py -- <icon>
python3 level_generation/props/items_wip_props/scripts/validate_props.py
/snap/bin/blender --background --factory-startup --python level_generation/props/items_wip_props/scripts/render_review.py -- revised <icon>
python3 level_generation/props/items_wip_props/scripts/make_review_sheets.py
python3 level_generation/props/items_wip_props/scripts/install_reviewed.py
```

The installer helper accepts only owned icons in `review/reviewed_models.json` whose exports match the validation
hashes, and resumes using its receipts. After any art edit, inspect fresh renders before updating that review list.
Native capture recipes are under `work/native_*`; final run records and logs are under `review/`.

## Completed approved Meshy batch

The user approved the [concrete proposal](meshy_batch.json) with “meshy approval granted”.
**12 initial Smart Topology jobs × 5 credits = 60 credits consumed; all succeeded; no paid retries.**
Five golem components (`7item368`, `7item371`–`7item374`), `harp`, `horn`, `item267`, `item276`, `memcryst`,
`lockpick`, and `amber` are now installed. The worker's Meshy claim was released after all results were downloaded.
[API receipts and request/input hashes](meshy/creature_3d_progress.json), [coordinator handoff](handoff.json).

Every object has its own icon-derived HD master under `meshy/props_<icon>/references_hd/` and six grey mesh guides,
painted views, exact prompts and generation receipts under `codex_tex/props_<icon>/`. Six-view sheets are cropped
into separated silhouette bands, preserving the unresized raw return. Painting is projected with visibility tests
onto newly unwrapped UVs. The torso, harp, horn, sarcophagus and pouch have binary metallic masks, separating metal
from cloth, wood, horn, stone or leather. The remaining models use uniform metallic or dielectric values.
The torso mask's first return misclassified bronze and was rejected; its selected correction and exact prompt are retained.
The pouch's two end views were corrected individually after its sheet substituted side views. No paid shape retries.

Memory-crystal Smart Topology contained intersecting interior sheets. A local 0.008-unit voxel exterior repair and
reduction to 3,200 triangles removed them while preserving the face and rim. Its pre-cleanup guides remain archived;
the same selected paintings were registered onto the repaired guides. The current bake covers essentially 100% of
its surface. Other hollow props have intentionally unobserved inner surfaces; their bake reports expose coverage.
[Checker views](review/checker/memcryst_low.png), source/low/above comparisons, exported winding/UV checks and native captures are the review evidence.

The sculptural `.blend` files and unprocessed PBR exports are under `work/codex_tex/`; canonical reviewed exports
are also retained under `work/exports/`. Reproduce one item with:

```sh
/snap/bin/blender --background --factory-startup --python level_generation/props/items_wip_props/scripts/codex_texture.py -- prep props_<icon>
python3 level_generation/props/items_wip_props/scripts/paint_atlas.py prep props_<icon>
# Use the built-in imagegen tool with the saved prompts and guide/master inputs; retain raw returns.
python3 level_generation/props/items_wip_props/scripts/paint_atlas.py split props_<icon> <painted-atlas.png> paint
# Mixed models also need the selected binary mask atlas split with kind metal.
/snap/bin/blender --background --factory-startup --python level_generation/props/items_wip_props/scripts/codex_texture.py -- bake props_<icon>
```

Binding lengths remain unchanged, including the intentionally large 393.3-unit sarcophagus. No shared binding,
settings, table, renderer or package changes are part of this worker's output. WIP art awaits the user's review;
Android, release packaging and global cooking/building remain coordinator work.
