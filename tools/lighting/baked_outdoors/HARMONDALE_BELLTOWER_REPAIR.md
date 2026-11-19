# Harmondale bell tower lighting repair, 2026-11-19

Map: `worlds/mm7/maps/7out02.odm`, Temple3_N models 94 and 96.
Their first 62 faces occupy identical surfaces with matching material UVs.
Cycles previously received both copies, causing coincident surfaces to occlude
each other and making the open bell tower appear almost entirely black.

The lighting producer now shares a chart for identical oriented surfaces with
matching texture sampling. Cyclic vertex rotations are supported; opposite
winding and different texture coordinates remain distinct. Every native model
and face retains its receiver record, events and collision. No ODM changes.

Installed `7out02.lighting` and `7out02.bake.json` were generated together using
the existing profile: 64 samples, 315-degree azimuth, unchanged sun/sky strengths,
Blender 5.3.0 CPU. Original files and review intermediates remain in the ignored
`output/wilner-lighting/` directory.

Validation:

- Nine geometry/compression unit tests passed, including surface identity coverage.
- For 3892 interior samples on each tower copy, fully black samples decreased
  from 2993/2996 to 72/72; mean sky response increased from about 0.0098 to 0.1173.
  This is a numerical bake check, not final visual acceptance.
- Native geometry hash and all 197 lighting dependency hashes matched.
- Existing Windows executable loaded Harmondale headlessly with exit code zero.
- Repository-wide stale-bake check found only an unrelated existing change in
  `7out06.scene.yml`; the repaired Harmondale bake is current.
- No game build or new desktop screenshot was made. Reload the map to inspect
  the updated lightmap in an already running game.

## Remaining black sill, follow-up

The next quicksave preview exposed a black rectangle below the left edge of the
bell platform. Model 95 (`Temple3_N_1`), face 26, overlapped the upper 64-by-128
section of tower face 57 on models 94/96. This partial overlap has different
materials and is outside the exact-surface sharing rule.

`tools/lighting/fix_harmondale_belltower.py` trims only the covered top of wall
face 26. The tower sill retains that surface, so the combined wall has no hole.
The tool checks the original coordinates and both covering faces, retains face
ids and remaining UVs, and verifies that no other face changes. It produces a
review copy and rejects an already repaired source.

Installed the repaired ODM with a fresh 64-sample lighting/recipe pair. On each
copy of face 57, fully black interior samples decreased from 55/56 to 0/56.
Geometry identity and all 197 dependencies passed, and the existing executable
loaded the repaired map headlessly with exit code zero. Review files and prior
installed assets are retained under `output/wilner-lighting/sill-repair/`.
No game build, save modification or final desktop visual acceptance was performed.
