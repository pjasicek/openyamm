# Ogre review and reproduction

Accepted offline restoration: all 60 native unique source frames (59 referenced plus unused ogrdief0).
Five stored standing/walking views, native mirrors, front-only actions, repeated attack binding,
per-palette timing, logical scale and anchoring are retained in the manifest.

Reviewed every native/raw sheet, all-base and all-mask contacts, native/restored comparisons,
ordered action sheets, all three standing palettes, enlarged edges and offline viewer samples:
walk mirrored view 6 / palette 783 / frame 4 and death / palette 785 / frame 4.
These are ordered-sequence and paused-viewer checks, not an engine performance test.

The initial blue selector caught isolated neutral contour pixels and missed cyan spike highlights.
The final enhanced-art R8 mask selects coherent blue/cyan spike components (12-pixel minimum,
three-pixel neighborhood), protecting skin, leather, main silver plates, blade and gold details.
Variants use deterministic native palette fits; no separate AI variant artwork.
Fixed RGB gain 0.90 restores native tonal weight across all views/actions.
A narrow green-fringe correction removes extraction spill on claws/blade; alpha is preserved.
Final automated checks pass, including source/provenance hashes, exact crop/atlas reconstruction,
all native sequences, variant alpha and zero-mask protection. Magenta candidates: zero at cleaned,
exported and atlas-extracted stages. Final light/dark edges and viewer composition are acceptable.

The enhanced skull medallion, tusks, claws and blade edge are clearer and somewhat more pronounced
than native pixel art; fine surface shading is approximate. No gameplay installation was performed.

Rebuild from retained raw checkpoints (commands from repository root):
```
python3 level_generation/creatures/mm6_ogr/process.py
python3 level_generation/creatures/mm6_peasants/package_family.py ogr
python3 level_generation/creatures/mm6_peasants/build_viewer.py ogr
```
A rebuild resets visual acceptance; review changed output before accepting again.
Raw images, exact submitted prompts, reference hashes and registration settings are retained.
