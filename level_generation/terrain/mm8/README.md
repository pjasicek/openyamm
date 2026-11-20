# MM8 restored terrain

Current installed revision: [v13 shared cobble material and continuous diagonals](roads/v13/README.md). Fixes the material mismatch and repeated dirt bites reported in1304. All eight diagonals reuse accepted straight-road pixels; 28 other roads are unchanged. [Final comparison](roads/v13/exact_pose_comparison.png). Pattern discontinuities at road bends remain explicitly accepted limitations; this is not an all-seams-pass revision.

Historical revision: [v12 NE2 edge and join repair](roads/v12/README.md). Only the dirt/grey-dirt NE2 diagonals changed; every straight road remains unchanged. [Exact-pose before/after](roads/v12/exact_pose_comparison.png). Rounded stone contours replace the clipped upper edge and lower ghost fragment; lower grout is aligned to the straight neighbour. Launcher and installed hashes verified. Broad gallery/ZIP/audit are historical snapshots.

Historical revision: [v11 exact1302-pose diagonal repair](roads/v11/README.md). Only eight diagonal variants changed; all straight/junction tiles remain byte-identical to v10. [Exact-pose before/after](roads/v11/exact_pose_comparison.png). Material calibrated to accepted stone pixels, and the visible NE2 east join repaired on the diagonal side only. Broad gallery/ZIP/audit remain historical snapshots.

Historical revision: [v10 clean road connections](roads/v10/README.md). Fixes the Alvar smears from1300/1301 by restoring28 non-diagonal roads byte-for-byte to v7 and repairing eight diagonal endpoints to match. [Straight-road comparison](roads/v10/straight_comparison.png). v8/v9 acceptance is superseded for these roads. Broad gallery/ZIP/audit remain historical snapshots.

Historical revision: [v9 stone material — GOOD](roads/v9/README.md). Eight diagonal variants use sharper artwork matched to accepted cobbles, retaining the approved v8 masks and boundary pixels. [Focused connections](roads/v9/connections.png). The broad gallery, ZIP and previous completion audit remain v8 snapshots; they were not rebuilt for this focused update.

Historical road update: [v8 native diagonal reconstruction](roads/v8/README.md). This revision is superseded by v12. [Original / v7 / v8 path comparison](roads/v8/assembled_paths.png).

The complete export contains **239 textures at256×256**:197 used static names and42 animation frames,
covering all14 outdoor maps. It preserves the original painted palette, feature scale, shaded/interleaved
banks and separate orange stepping stones. Native incompatible map placements remain unchanged.

[Comparison gallery](review.html) · [Maps to try](MAPS.md) · [Handoff](HANDOFF.md) ·
[Exact export and source provenance](complete_runtime_x2/manifest.json) ·
[Review acceptance](reports/acceptance.json) · [Installation audit](reports/integration.json).

The reviewed pack includes the `roads/v7` joined-stone and border-colour correction for the road reported in1297.
[Exact-pose before/after comparison](roads/v7/index.html) · [Reproduce that view](roads/v7/README.md). Run from the repository root:

```sh
./level_generation/terrain/mm8/play.sh enhanced
./level_generation/terrain/mm8/play.sh original
./level_generation/terrain/mm8/play.sh enhanced out04.odm
./level_generation/terrain/mm8/play.sh enhanced out06.odm
```

Default map: Dagger Wound Island. `out04.odm` is Ironsand Desert; `out06.odm` is Shadowspire.
The same pack serves every MM8 outdoor map. Change only terrain quality with enhanced/original;
other enhanced categories retain the current settings. Each launch copies settings/saves into an isolated
run and remains open until closed. Optional `tools/run_game.sh` arguments follow the map, for example
`--seconds 15`, `--save path/to/save.oysav`, or camera overrides. The launcher uses the current development
executable and does not build it. It verifies installed terrain hashes before an enhanced run.

Installation adds `assets_dev/worlds/mm8/terrain_x2/` and preserves originals in
`assets_dev/engine/terrain/` and `assets_dev/worlds/mm8/textures/`, plus all other enhanced content.
The shareable [runtime ZIP](mm8_complete_terrain_x2.zip) contains the world directory, export manifest,
acceptance record and installation notes. Extract its `worlds/` into `assets_dev/` on another checkout.

Reproduce the exact export from retained, hash-checked source artwork:

```sh
python3 level_generation/terrain/mm8/assemble_pack.py
python3 level_generation/terrain/mm8/check_complete_pack.py
python3 level_generation/terrain/mm8/build_gallery.py
python3 level_generation/terrain/mm8/write_map_list.py
python3 level_generation/terrain/mm8/install.py
python3 level_generation/terrain/mm8/package.py
```

The export manifest keeps its immutable candidate-assembly status; the subsequent acceptance and integration
records establish review/installation. Avoid mixing historical `runtime_x2/` with the complete union: the former
is a partial build input. `reports/candidate_stage.json` identifies every final override and its retained source.
Changing source art requires renewed review and acceptance; scripts fail on changed hashes.

Evidence includes24,428 compatible edge checks across the exact export/all liquid phases,13 selected flat-land
views,18 original/enhanced bank animation captures, eight grounded cobble routes, eight original/enhanced
stepping routes, four paired cobble loop/diagonal comparisons, and representative native-map pilots.
The gallery's animation preview complements measured native captures; Xvfb results are not GPU benchmarks.
See the handoff for authoring recipes, the85 retained imagegen calls, masks, shading, source receipts and lessons.
The raw historical inventory misses a Shadowspire scene override; use `effective_inventory.json` for coverage.
