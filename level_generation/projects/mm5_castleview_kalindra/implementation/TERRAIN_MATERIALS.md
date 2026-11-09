# Native terrain material completion

The geography, heights, water planes and travel bounds stay source-owned. Material work changes native tile
selectors and their composed registry entries; it does not replace terrain with a full BModel ground mesh.

## Acid Pond and northern scorched fringe

`terrain_materials.py` supplies a separate Acid Pond bank (`tileset 40`) and an explicit `mm5_acid_pond` water
material. Its `mm5acid` base is a byte-identical copy of MM8 `SLIMYwtr.bmp`. Twelve separately named native shore
overlays keep the pond's liquid lookup separate from the blue river. The existing static-liquid animation scrolls
the murky base below stationary shores. Ordinary water/shore flags remain; no acid damage behavior is added.

The source registry addition is `surface_materials_append.yml`. The builder composes it with the repository base
into the isolated stage's `engine/rendering/surface_materials.yml`. It preserves all existing material records and
does not overwrite the repository base or supply world-owned gameplay tables. `terrain_materials.json` records
exact donor provenance and composition. Include this fragment in the final package/dependency inventory.

All six source scorched cells lie in the outermost northern scenery row. They use MM8 `volsw`, `vols`, `volse`
to retain the neighboring scorched-biome trace and meet dark dirt. Do not add a volcano or extend these cells into
the playable region merely to make them prominent.

[Source and native local review](../review/terrain_materials_v1/native_review.json) distinguishes reviewed pond
appearance/motion/reload from the unfinished regional landscape. Native shore art retains a narrow cool-colored wet
fringe, inspected at the west bank. The broad pond remains distinctly murky. The repeated river/spill view stays blue.
The distant northern buffer remains part of the final regional composition review.

## Desert transition material

The original MM7 sand/dirt bank ends in lighter red soil. The MM8 Plane-of-Earth bank ends in orange cracked ground.
Neither endpoint matches this region's dark dirt. The original MM8 `SDdrt` bank repeats the lighter-soil artwork.

The accepted local study instead mixes unchanged MM7 `7sand` and MM8 `DIRTtyl` in a new Blender material. A periodic
noise field breaks up the corner-interpolated boundary. The shader bake uses emission, closest donor sampling and
128×128 output, preserving original detail and colors. It does not upscale the assets. Both donor endpoint bakes
match original RGB values within one 8-bit step.

The first bake failed raster-edge continuity despite a periodic continuous field. The corrected bake pins the mask's
outer pixel centers to 0/1 while keeping donor UVs unchanged. Its independent audit checks all 100 compatible tile-edge
combinations and all corner colors; the maximum recovered blend-weight discrepancy is about 0.035, including RGB
rounding, compared with 0.799 in the rejected first bake.

`implementation/art/desert_terrain/` retains the accepted twelve transitions, two endpoint checks and manifest.
`author_desert_materials.py` owns their active Blender authoring recipe; the frozen V2 recipe is also in
`review/desert_materials_v2/source_scripts/`. Canonical integration is complete. Regeneration reproduces every RGB
pixel; PNG byte hashes change because Blender embeds timestamps, camera names and render timings. The build records
the actual files' hashes, and the regeneration check separately establishes pixel identity.
[Native local views](../review/desert_materials_v2/native_review.json) show the desert/soil junction at player height.

## Efficient terrain review and completion limits

`build_desert_material_study.py` uses the editor's existing native-map-plus-terrain-metadata path for an isolated
material iteration. It checks the baseline ODM hash and every source OBJ hash before reuse, then verifies all written
BModel records, entities, spawns, heights and attributes remain identical. It does not patch binary offsets. The
current isolated study is `/tmp/openyamm-mm5-desert-material-study` and includes all 308 BModels.

This focused path proves a terrain-only iteration against its recorded baseline. Final delivery still requires the
fresh full source build required by GOAL.md. Neither the tile audit nor the two local desert views approves all
country scenery, road grades, frontages or map buffers.

The complete geometry was freshly rebuilt and audited at native hash `a18395ba2f2726ede44515f8849efee3628ee09d7ad426d39bd6cf6d807d6080`.
The reviewed sand revision was then promoted at `1dce14975ebedd1baf6dc84087eabae82586fb33d8968426a32a4a3699ffc8f6`.
The entire parsed native payload differs only in `tile_map`; all 308 BModels, scene records and heights are identical.
All composed terrain rows also match the native-reviewed study. [Promotion evidence](../review/terrain_materials_v1/desert_promotion.json)
records this relationship. There are 123 populated local terrain slots, zero unresolved categorical material boundary
cells, and zero independently classified corner mismatches. Separate cliff/space edges remain geometry-owned.
