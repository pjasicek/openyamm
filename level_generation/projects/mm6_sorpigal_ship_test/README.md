# Ravenshore ship in New Sorpigal

Playable test copy, 2026-09-29. The ordinary MM8 Ravenshore wooden ship replaces New Sorpigal's `SHP` billboard.
It retains the Odyssey service with Captain Bryan. The main asset root, original MM6/MM8 maps and normal saves
are unchanged; all test content is under this project.

From the repository root, run:

```sh
./level_generation/projects/mm6_sorpigal_ship_test/run_test.sh
```

This opens an isolated fresh game on the pier, looking at the ship, and runs until you close the window.
Walk down the pier and through the ship's boarding opening. Turn right toward the stern and use or click the
cabin door to open Odyssey. Only that door has the interaction; the hull, deck, rails and mast do not.
The existing **E** nearby-target selection is retained, so it can still select the door when aiming beside it.
The existing travel timetable applies; a fresh game's date can show “Sorry, come back another day.”
The launcher prints its temporary directory, which contains that run's private settings, saves and logs.

## Files

- [Native map](build/oute3.odm) and [scene state](build/oute3.scene.yml).
- [Changed-assets ZIP](build/ship_overlay.zip): 28 files, with paths relative to an asset root.
  Contains the ODM, scene, lighting, bake recipe, 12 logical-size BMPs and 12 existing x2 PNGs.
  It is an overlay for a **separate asset copy**, not a self-contained world or a registered runtime mod.
- [Package checksums](build/package.json) and [import report](build/report.json).
- [Placement/source manifest](source/ship.json), [native port helper](source/port_ship.cpp), and
  [builder](build_test.py).
- [Packed Blender reimport](source/ship_and_pier.blend): the final five ship BModels and original pier, textured,
  with native face indices. It omits terrain and billboards. The JSON/C++ import remains the reproducible build source.
- `playtest/assets_dev/`: complete development asset snapshot used by the launcher. Unchanged files are hardlinks;
  the builder replaces changed files atomically. Do not edit shared files in this snapshot in place.

The isolated copy deliberately keeps the `oute3.odm` map key so existing map events, house IDs, travel destinations,
arrival positions and world metadata remain valid. It adds no engine code or runtime import step.

## Placement and import

MM8 `out02.odm` BModels 111–115 become MM6 BModels 85–89. Native scale is retained, with an exact -90-degree
rotation around `(8256, -14286, 0)` and placement at `(2168, -9936, -104)`. The ship is lowered by 104 units,
matching the difference between Ravenshore's 264-unit pier and New Sorpigal's 160-unit pier. Its boarding opening
is centered on the pier at `y=-10208`, and the hull meets the pier tip at `x=1768`. The entrance lip is at
`z=152–156`, and the main deck at `z=88`. The native invisible boarding ramp is retained, allowing walking in
both directions without jumping. The earlier copy's 32-unit horizontal gap is closed.

Decoration slot 477 is retired as an empty marker, preserving all other decoration indices. Only cabin door face
87:42 (donor 113:42, `bdoorb`) uses MM6 event 29 / house 496; all other ship faces have their clickable flag and
event cleared. Donor MM8 quest groups and events are cleared. Original terrain arrays, BModels,
other decorations and spawns are checked unchanged. Existing scene actors and events are retained.

The twelve imported texture keys are `ns8s00`–`ns8s11`, confined to the test MM6 content. Native UVs and logical
texture sizes are preserved. `t05a10` and `t05a11` lacked native BMPs in this checkout, so their logical-size BMPs
were downsampled from the existing x2 PNGs; all twelve x2 PNGs are exact copies.

Five fully covered coplanar donor faces are invisible/untouchable in the copy to remove observed depth fighting:
111:22, 111:62, 114:34, 114:35 and 114:36. Their face slots remain intact. The original donor is untouched.
The map has a fresh lighting bake, including decoration shadows with the retired billboard removed.

## Review

- [Pier approach](review/final/01-dock_approach.png)
- [Ship and pier](review/final/02-ship_and_pier.png)
- [Hull close-up](review/final/03-hull_detail.png)
- [Offshore view](review/final/04-offshore.png)
- [Boarding opening from the pier](review/final/05-boarding_from_pier.png)
- [Return to the pier](review/final/06-return_to_pier.png)
- [Cabin door](review/final/07-cabin_door.png)
- [Odyssey dialogue](review/interaction/odyssey_dialogue.png)
- [Validation record](review/validation.json)

The focused scenario walks from the pier onto the deck and back up the ramp without jumping, checks save/load,
and directly picks cabin door face 87:42 to activate event 29. The independent import check verifies that all
other ship faces have no event or clickable flag. A separate runtime ray-pick probe aimed at the cabin window
finds no activatable target. Native desktop captures use OpenGL on NVIDIA/Wayland and include door activation and
the inert hull. These checks cover this berth and interaction, not a full campaign or performance benchmark.
See the validation record for the final results.

## Rebuild

Requires the pinned local game assets, a C++20 compiler, Python with Pillow/PyYAML, and Blender for lighting.
From the repository root:

```sh
python3 level_generation/projects/mm6_sorpigal_ship_test/build_test.py
```

This compiles the small authoring helper against the existing native ODM reader/writer, validates the source
hashes and output, prepares the isolated asset root, and installs the map and textures. It removes the isolated
copy's stale lighting. If geometry and textures are unchanged, restore the retained bake with:

```sh
python3 level_generation/projects/mm6_sorpigal_ship_test/build_test.py --install-lighting
```

After changing geometry, rebake before installing lighting:

```sh
ship_project="$PWD/level_generation/projects/mm6_sorpigal_ship_test"
/snap/bin/blender --background --factory-startup --python-exit-code 1 \
  --python "$ship_project/playtest/tools/lighting/bake_outdoor.py" -- \
  --profile "$ship_project/source/bake_profile.json" --output "$ship_project/bake"
python3 "$ship_project/build_test.py" --install-lighting
python3 "$ship_project/build_test.py" --package
```

The bake scripts are unchanged copies of the repository's normal producers, using the isolated root.
`source/reimport_blender.py` regenerates the packed Blender inspection scene through Blender MCP while preserving
other open scenes. `source/final_tour.yml` and `source/interaction_tour.yml` reproduce the native captures through
the desktop launcher's screenshot and menu-input tour settings. `source/collision_smoke.yml` runs with
`--headless-run-scenario` from an isolated run directory whose settings point at the test asset root.
