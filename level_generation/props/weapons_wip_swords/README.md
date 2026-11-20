# Sword ground-item production

This is the 68-icon sword assignment from [the production job](../items_claude/weapons_parallel_20261018/01_swords.txt).
**Finished: all 68 swords rebuilt, reviewed and installed; zero deferred or unresolved items.**
The [per-icon review ledger](LEDGER.md), [machine-readable ledger](ledger.json) and [completed handoff](handoff.json)
record each replacement. The base meshes total 187,932 triangles (1,642–6,424 per sword); eight have three additional
LOD levels. There are 57 design groups and 11 matching variants. Meshy spend was 15 credits across three jobs.
Development-only distribution and release exclusion are required by that job; they do not imply pending artwork.

## Construction

The restored icons constrain each blade's outline and proportions, not its surface paint. Blades are closed lofts
with finite cutting edges, a raised ridge or a recessed fuller, and deliberate cross-sections. The reavers have
separate fork-tip branches with a real central gap. Each guard, grip, collar, pommel and ornament is a physical
component with a complete back. Sword-specific scan limits exclude quillons from blade outlines. Small outline
noise is simplified while preserving the flamberges, curves and deep cutlass/reaver notches.

Regular components use Blender. Iron Feather, Dragonning Blade and the matching Headsman's Reaver/Finality/
Sword of Whistlebone hilts use fitted Meshy Smart Topology sculptures. Original downloads and receipts remain in
`meshy/`; mesh repair closes scan/socket boundaries, recalculates outward normals and checks manifold geometry.
Each final `.blend` is editable under `blends/`.

There are three successful Meshy jobs, **15 credits total**, under the job's unlimited authorization. An initial
sandbox-blocked request was reconciled against the task list and confirmed not created before retrying. The worker's
lease is released. Geometry is reused only for recorded matching design variants; the physical blade remains specific
to its inventory icon.

## Materials

[Imagegen receipts](references/generation_receipts.json) preserve four images and their hashes: a purpose-built
[surface atlas](references/surface_painted.png), and [Iron Feather](references/iron_feather_hilt_hd.png),
[skull](references/bone_hilt_hd.png) and [dragon](references/dragon_hilt_hd.png) hilt masters.
The atlas [UV template](references/surface_uv_template.png) and [prompt](references/surface_prompt.txt), plus the
three adjacent `*_hilt_prompt.txt` files, preserve the exact built-in `image_gen.imagegen` inputs.

Painted illumination is removed from the material albedo and interpreted as restrained roughness/normal detail.
Metal, leather, bone, ivory, enamel and gemstones have distinct masks and roughness. Rust has an explicit oxide/
exposed-metal mask. Puck's red ladder is an authored enamel inlay. No original inventory painting is projected
unchanged onto the mesh. Fire-coloured blades use patterned metal within the existing PBR renderer.

Each sword packs its surfaces into **one material**, with 1024² embedded PNG base colour, metallic/roughness and
OpenGL tangent-normal maps. Colour uses sRGB; roughness and normals remain linear data throughout packing.
Material tiles have six-pixel gutters. Surface UV area is normalized to physical area before packing, giving an
average density of approximately 174 or 357 texels per authoring metre depending on tile count; the ladder graphic
has its own deliberate mapping. Matching repeated surfaces may overlap. Detailed normal maps use the same UVs.

## Resting pose and detail levels

The origin is at the footprint centre and the lowest real contact is at zero. Blender +Y is the long horizontal
axis, exported as glTF -Z; glTF +Y is vertical. The support angle is solved independently from the blade and hilt
geometry. Existing binding lengths and item IDs are preserved.

Simple swords retain their economical base meshes. Models above 4,000 triangles have static LODs at approximately
50%, 25% and 12.5% of the base, linked through the existing `openyamm_lods` contract. They share the same material
and textures. No renderer changes or binding corrections are required.

## Review and validation

The nine sheets ([1](review/comparison_01.jpg), [2](review/comparison_02.jpg), [3](review/comparison_03.jpg),
[4](review/comparison_04.jpg), [5](review/comparison_05.jpg), [6](review/comparison_06.jpg),
[7](review/comparison_07.jpg), [8](review/comparison_08.jpg), [9](review/comparison_09.jpg)) compare all inventory icons, preserved baseline models,
neutral clay and four textured views: above, three-quarter, low side and underside. Individual renders remain in
`review/baseline/`, `review/clay/` and `review/replacement/`. Baseline source GLBs and hashes are retained in
`references/baseline_models/` and [baseline receipts](references/baseline_receipts.json).

[Validation](work/validation.json) checks the exact ownership set, finite positions/unit normals, triangle indices,
nondegenerate geometry and normal-map UVs, outward positive-volume components, embedded power-of-two PNGs,
texture encoding, albedo ranges, applied transforms, centring, grounding, axes and decreasing LOD chains. Builder
assertions also check closed manifold components. The final install receipts, visual ledger and native run records
are linked from the handoff. Native checks are visual validation, not performance measurements.

All 68 exact-model desktop cook checks passed with zero problems. Final source/runtime hashes, preserved baseline
hashes and unchanged binding lengths passed the [final integrity check](work/final_integrity.json).
The [cook verification](work/cooked_verification.json), [installation receipts](work/install_receipts.json),
[texture totals](work/texture_totals.json) and [LOD comparison](review/lod_comparison.jpg) retain the evidence.
Each sword has three 1024² source maps; shared surfaces reduce the batch to 120 unique source images/runtime textures.

The final NVIDIA/OpenGL 3.3 native runs passed outdoors in MM7 `out10.odm` and indoors in MM6 `6d19.blv`.
The [outdoor contact sheet](review/native_outdoor_contact.jpg) covers all 68 swords and eight low-angle views;
full-size examples include [Iron Feather](review/native_final_outdoor/21-7item218_low.png) and
[Headsman's Reaver](review/native_final_outdoor/23-item010_low.png).
Sixteen representative swords cover the construction and material types in indoor
[group 1](review/native_final_indoor_1/indoor_group_1.png),
[group 2](review/native_final_indoor_2/indoor_group_2.png),
[group 3](review/native_final_indoor_3/indoor_group_3.png) and
[group 4](review/native_final_indoor_4/indoor_group_4.png).
Blades remain thin, guards and hilts have complete backs and volume, and the mixed materials remain legible in the
dim interior. No engine-driven material adjustment was needed. Selected captures, binary hashes, settings and logs
are indexed in [native run records](work/native_runs.json); all five final runs exited successfully.

Only this worker's icon GLBs are installed, through `tools/install_model.py --world-items --name`; the shared
installer serializes source writes and scoped desktop cooking. Shared bindings, tables, engine/game code, settings,
other projects and package rules are outside this worker's write scope. No full build/cook or release promotion is
part of the job. Android cooking/device testing is not included.

## Reproduction

Run these sequentially from the repository root:

```sh
python3 level_generation/props/weapons_wip_swords/scripts/prepare_designs.py
python3 level_generation/props/weapons_wip_swords/scripts/prepare_surfaces.py
/snap/bin/blender --background --factory-startup --python level_generation/props/weapons_wip_swords/scripts/build_swords.py
python3 level_generation/props/weapons_wip_swords/scripts/link_exports.py
python3 level_generation/props/weapons_wip_swords/scripts/validate_exports.py
/snap/bin/blender --background --factory-startup --python level_generation/props/weapons_wip_swords/scripts/render_swords.py -- clay
/snap/bin/blender --background --factory-startup --python level_generation/props/weapons_wip_swords/scripts/render_swords.py -- replacement
python3 level_generation/props/weapons_wip_swords/scripts/make_sheets.py
```

The reviewed install helper requires fresh clay and textured views and an explicit per-icon visual decision.
It retains original source models and never installs an unassigned icon or rewrites bindings. Regenerating a model
requires renewed visual review before installing it.
