# inventastorca — overnight status

- Phase: DONE (2026-10-30). No background processes, no locks held.
- Record: `level_generation/projects/mm9r_inventastorca/README.md`; props: `level_generation/props/mm9_inventastorca_claude/README.md`.

## Summary
- Faces 9 057 (14 972 vertices), rooms 27 (28 sectors), portal faces 29 (12 UserPortals, 10 archway cuts, 6 door
  leaves, 1 rectangle), movers 88 (59 rotate, 23 dat, 5 sink, 1 slide), 1 ladder, lights 71 BLV (+13 bake-only,
  8 skipped: in rock / under the water), decorations 108, loot containers 5 (3 chests, 2 treasure bags), actors 39
  (9 dead adventurers), pads 13 (+ the cavern's water pad), perception hints 11 brushes (cogs 320-330).
- Scenarios: doors_exits PASS, chests PASS, scripted PASS (real clicks; bags and floor chests behind moved panels by
  their events).
- Audit: no actor region cut off (no reach probes needed); steps = MM9 spiral exit stair and the cave's rock ledges;
  5 "unreachable" = desk/table tops.
- Fix round (orchestrator, 22:25 rule): bake calibrated to the DAT lightmaps. Zone luminance ours/MM9: west hall 1.26,
  long hall 1.16, north 0.92, green party hall 1.72, reading 0.94, south 0.93, lower library 0.96, cave 1.11; hue matches
  in all 8 zones. Cave shaft: 6 map-local bake-only lights from MM9's cave lightmaps (cave_lights.py + bake.py; no
  converter change), cave lightmap (0.519, 0.455, 0.436) vs MM9 (0.469, 0.407, 0.393). Black tables traced: the engine
  subtracts the frame ambient (0.345 at sector light 20) from a decoration's baked room light; the hall's fill-only actor
  ambient was below it. Fixed in the map: sector minimum light 31 (bake floor kept the same: ambient_scale 0.671); table
  top (8,6,4) -> (31,28,21). Engine-side fix noted, not made. Capture ratio (info only): 68.5/66.4 = 1.03.
- Unmatched scripted objects: `AxeTrap` (every DoubleDoor's OpenTrigger target; not in the DAT). MM9 anim sounds missing
  from the audio import (lichkingTaunt, gopherwince, dragonflyhattackair1, harpyflap): substituted or skipped.
- Sheets: review/v07_compare.jpg (capture | native, 36 views), review/lighting_v07_compare.jpg (capture | unbaked | baked, 12), review/cave06_compare.jpg,
  review/open01_sheet.jpg, review/hints01_sheet.jpg, review/flames01_sheet.jpg, review/v01_compare.jpg.
- Not checked: the dresser/drawer motions individually; every orb (one clicked); the ladder from the top down; MM9
  monsters' 3D models (stand-ins); the long tables reading near-black in baked light (not traced);  real-hardware performance.
