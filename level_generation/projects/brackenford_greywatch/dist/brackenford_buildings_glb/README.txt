BRACKENFORD BUILDINGS AND BMODELS

41 self-contained GLB (glTF 2.0) files; all textures embedded as PNG.
Open in Blender or another glTF-compatible viewer without OpenYAMM installed.

buildings/: 29 buildings, each including its separate door mesh.
structures/: assembled castle (12 BModels), bridge (5), and cave entrance (4).
props/: 8 placed props: 4 chests, 2 wells, fountain, and obelisk.
brackenford_all_bmodels_in_place.glb: all 87 BModels at original relative map positions.
Each BModel remains a named, separate mesh, with its runtime index in custom properties.
Individual assets are centered horizontally and grounded at their lowest vertex.
Map orientation is preserved. Scale: one glTF unit = 128 native game units.
glTF uses Y up: native (X,Y,Z) becomes (X,Z,-Y), divided by 128.
manifest.json records original placement offsets, materials, counts, checks, and hashes.

Scope: exterior BModel geometry and materials only. Terrain, vegetation, actors,
interiors, game logic, animated water, and runtime lighting are not included.
Materials retain the authored texture UVs, nearest filtering, and rough surfaces.

Provenance: building/structure geometry was generated for Brackenford, calibrated
against MM8 Ravenshore architecture. Textures are existing MM8 artwork. The chests,
wells, fountain, and obelisk reuse MM8 out02.odm geometry; exact source BModel indices
are recorded in the manifest. This archive does not grant a new license to MM8 assets.
