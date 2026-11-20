# Geometry simplification

The authored revision removes **3,742 model triangles (8.0%)** while keeping the map layout, materials, fruit and leaf
outlines, wheel rims, chest lids, well roofs, bridge walking surfaces and all interaction identities.
Native model geometry changes from 46,814 to **43,072 triangles**, and from 26,171 to **24,331 faces**.
Including the unchanged base terrain, the total changes from 79,072 to **75,330 triangles**.

| Assembly/family | Before triangles | After triangles | Saved |
| --- | ---: | ---: | ---: |
| Skyroad rope and brace | 2,348 | 678 | 1,670 |
| Four melon patches | 3,936 | 2,976 | 960 |
| Five town chests | 1,150 | 990 | 160 |
| Kramer's caravan yard | 1,432 | 1,336 | 96 |
| Both bridges | 2,688 | 2,296 | 392 |
| Six roofed source wells | 2,232 | 1,824 | 408 |
| Four message bottles | 688 | 632 | 56 |

The rope uses one cord inside the former strand envelope and fewer segments around its coils and lashings.
Melon stems use two raised upper surfaces instead of closed boxes; all six fruit and eighteen leaves per patch
keep their geometry and positions. Wheel spoke caps inside rims/hubs and paired internal bridge-bay caps are removed.
Well buckets use a continuous open shell instead of overlapping boxes. Bottle rolls keep their open octagonal rim
with a simpler recessed interior.

Chest simplification is deliberately conservative. Native visual review of the first candidate showed a small gap
where flattened straps met the lid; the final source restores their visible edge faces and the complete hasp/hinges.
The remaining reductions remove concealed faces and flatten only the dark keyhole mark.

## Evidence

- [Before/after native views](review/geometry_simplification_v1/index.html).
- [Structural comparison with the preserved release](review/geometry_simplification_v1/validation.json).
- [Compiler parity check](review/geometry_simplification_v1/compiler_parity.json).
- [Initial audit](GEOMETRY_COST_AUDIT.md), with the original cost breakdown and review priorities.

The structural comparison verifies unchanged terrain, scenery records, non-targeted models and event identities,
identical Lua, retained fruit/leaf placements and no degenerate triangle fans. The project builder checks support,
bridge landings, winding and bindings. The Lua smoke executes all 121 status-only handlers. There are 88 semantic
BModel event records; additional scenery events account for the rest of the handler inventory.

The source snapshot and original native world are retained under `review/geometry_simplification_v1/before/`.
Earlier captures of unchanged families remain valid object-level evidence; each capture records its own native hash.
The corrected chest passed its final native capture. [Visual acceptance](review/geometry_simplification_v1/visual_review.json)
and [installed update](review/geometry_simplification_v1/installed_update.json) record release v2. Run `play.sh` and
load `castleview_start` to use the refreshed exploration save. Existing settings and other saves are preserved; the
previous starting save is archived under `local_playtest/playtest/previous_starts/`.

## Editor import cost

The initial rebuild repeatedly scanned texture directories and decoded the same image once per polygon.
`EditorDocument.cpp` now caches dimensions locally for each imported model. The cache expires when the import ends,
so subsequent imports still read current assets. No game renderer or runtime executable was changed.

Rebuilding the entire preserved original source with the updated editor produced a **byte-identical ODM**, SHA-256
`87c61c78629b56761ad46ff0280d35a5129238f6f34b3f576f5b49e107e57f24`.
The editor target builds successfully. The separate existing `outdoor-source-only-package-load` regression stops
before model import because it cannot find its generated scene supplement; its temporary files/rows were cleaned up.
The complete original-map parity build and the current native readback provide direct coverage for this import change.

These are geometry savings, not a measured game frame-rate improvement. Visual captures use an isolated Xvfb display.
