# Jewellery ground-item batch — finished

Finished the assigned artwork: **88 replacements installed, 3 satisfactory mounted gems retained, 0 deferred**.
All 91 icons have been examined. The job's required WIP designation applies to development-only distribution and
release exclusion, not to pending artwork. No Meshy jobs or credits were used.

| Family | Replaced | Kept |
|---|---:|---:|
| Belts | 18 | 0 |
| Rings | 41 | 0 |
| Gems, including the Dimension Door book | 29 | 3 |

The retained icons are `7item146`, `7item154` and `7item264`: satisfactory shallow mounted-jewellery reliefs.
The replacements have real open ring shanks, separate settings and ornaments; cut stones, crystal prisms,
faceted orbs and rose cuts; solid belt straps with separate hardware and lining; and a closed purple spellbook.
The large jade rings have broad shanks, and the Angel's Ring pair has open lattice shanks. Identical inventory
designs share their construction; different cuts, settings and hardware have explicit icon-specific definitions.

The completed surface pass adds chased bands, engraved plaques, sun-face medallions, woven belt trim and scarab
enamel. These use a purpose-painted UV atlas baked into flat albedo, separate metallic/roughness masks and tangent
normals. Square, emerald-cut and marquise stones have matching polygonal bezels. Gemstones use glossy tinted
blended shells over saturated solid cores, kept on a separate mesh node; pearls and jade retain their own materials.
All replacements are within the 3200-triangle target: **32–3168 triangles**, 90,520 total.

## Review

- [Per-icon ledger](LEDGER.md), [machine-readable ledger](ledger.json), [coordinator handoff](handoff.json).
- Gems: [1](review/replacement_gems_01.jpg), [2](review/replacement_gems_02.jpg),
  [3](review/replacement_gems_03.jpg), [4](review/replacement_gems_04.jpg).
- Rings: [1](review/replacement_rings_01.jpg), [2](review/replacement_rings_02.jpg),
  [3](review/replacement_rings_03.jpg), [4](review/replacement_rings_04.jpg),
  [5](review/replacement_rings_05.jpg).
- Belts: [1](review/replacement_belts_01.jpg), [2](review/replacement_belts_02.jpg).

Each row shows the inventory reference, an above render and a low three-quarter render. Corresponding
`review/baseline_*` sheets preserve the original models. Individual full-resolution renders are under
`review/baseline/` and `review/replacement/`.

Native checks used the existing desktop build on NVIDIA/OpenGL through isolated runs:

- [Finished outdoor belts](review/native_material_outdoor/01-belts_8300.png),
  [rings](review/native_material_outdoor/05-rings_7300.png),
  [gems](review/native_material_outdoor/08-gems_7490.png)
  in MM7 `out10.odm`, using `saves/Ground items test.oysav`.
- [Finished indoor representative collection](review/native_material_indoor/finished_materials_indoor.png)
  in MM6 `6d19.blv`.
- Earlier captures remain in `review/native_outdoor/`, `review/native_indoor/` and `review/native_final_rings/`.

The native runs exited successfully. The indoor representative items loaded, settled and rendered.
The metals darken with the room's lighting but remain visible. No model-load errors appeared in either run.
Native run JSON, logs, immutable launch settings and preparation records are preserved in `work/native_records/`.
These are visual checks, not a performance benchmark.

## Authoring and installation

- `scripts/build_jewellery.py`: explicit cut/colour/proportion definitions and ring construction.
- `scripts/build_belts_book.py`: solid straps, separate hardware/lining and the book.
- `scripts/prepare_textures.py`: packs the two imagegen paintings into purpose-built UV textures.
- `scripts/prepare_engraving.py` and `scripts/surface_detail.py`: bake and map the painted engraving atlas.
- `blends/jewellery_<icon>.blend`: editable authoring scenes.
- `work/exports/jewellery_<icon>_export.glb`: unprocessed exports, embedded PNGs and standard PBR factors.
- [Imagegen prompts and receipts](references/generation_receipts.json): built-in `image_gen.imagegen`, three images:
  a flat purple book cover, neutral leather swatch and purpose-built engraving atlas. The atlas uses
  [this UV guide](references/jewellery_trim_uv_template.png) and [this exact prompt](references/trim_prompt.txt).
  Raw paintings stay in `references/`; packed textures in `textures/`. No inventory painting is stretched around a
  replacement mesh. Painted illumination is removed from engraving albedo and interpreted as relightable surface detail.
- `references/baseline_models/`: original source copies of the 88 replaced models.
- `references/first_pass_models/` and `review/first_pass/`: preserved geometry and sheets from before material finishing.
- [Install receipts](work/install_receipts.json) and `work/install_logs/`: hashes, preserved binding lengths and
  the install/cook output for each icon.

Only owned source and runtime icon models were installed, through `tools/install_model.py --world-items --name`.
Shared bindings, item tables, main-project scripts/designs, engine code, settings and package rules were not edited.
No scale or binding changes are requested from the coordinator. The rollback archive is unchanged.

## Validation and limits

[Validation results](work/validation.json) cover every replacement: finite positions and unit normals, valid
triangle indices, no degenerate triangles, UVs within 0–1, embedded power-of-two PNGs, applied transforms,
footprint-centred resting pose, glTF Y-up with its lowest point at zero and the longest horizontal side along Z,
and outward closed-component winding, including the blended shells. Normal-mapped triangles have nondegenerate UVs;
constant albedo factors stay within sRGB 30–243. Opaque and blended materials are on separate mesh nodes.
All GLBs were re-imported for the two review views. The builder also asserts closed manifold components before export.
Three retained source hashes and all 88 installed source/runtime hashes
were checked against their receipts.

The read-only desktop verification reported **911 development models, 751 textures, zero problems**. No global cook or
build was run. Metal uses metallic=1 and non-metal uses metallic=0; the book has a separate binary metal mask.
No dim-room partial-metal workaround was necessary. Uniform surfaces use PBR factors, so their UV overlap has no
texture consequence. Belt UVs unwrap around the strap with 1024×128 grain strips; approximately 370 texels per
authoring metre around the loop and 530–850 vertically. The book uses a 1024² cover and 1024×128 page-edge map.

The glass uses the existing renderer's blended PBR materials with a coloured core, rather than a ray-tracing or
screen-refraction extension. The engraving has 512² material maps and 1024×128 repeated band strips; it adds surface
detail without micro geometry. No additional LODs are needed for these small rigid props. The first pass's oversized
bezel and medallion geometry was reduced, bringing every asset within the normal triangle budget.
Release promotion and Android release/device checks are outside the supplied job's development-only scope.

To reproduce, run these sequentially from the repository root:

```sh
python3 level_generation/props/items_wip_jewellery/scripts/prepare_textures.py
python3 level_generation/props/items_wip_jewellery/scripts/prepare_engraving.py
/snap/bin/blender --background --factory-startup --python level_generation/props/items_wip_jewellery/scripts/build_jewellery.py
/snap/bin/blender --background --factory-startup --python level_generation/props/items_wip_jewellery/scripts/build_belts_book.py
/snap/bin/blender --background --factory-startup --python level_generation/props/items_wip_jewellery/scripts/render_batch.py -- replacement
python3 level_generation/props/items_wip_jewellery/scripts/validate_exports.py
python3 level_generation/props/items_wip_jewellery/scripts/make_review_sheets.py replacement
```

After reviewing changed exports, `scripts/install_reviewed.py` installs only this ownership list. It requires the
visual-review ledger, checks that renders are newer than exports, retains the originals and uses the shared installer
lock for each icon. It never runs a blanket family install or writes bindings.
