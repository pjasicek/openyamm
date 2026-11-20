# greatgate status

- Phase: finished, **FAILED (does not fit the dungeon route; acceptable outcome)**. 2026-10-31.
- Finding: `GREATGATE.dat` is an open-air cutscene set (path, bridge, gatehouse, gate wall with Hanndl's peephole,
  inside a SkyMarker box with a SnowMtns sky box; no Light objects, one sun, AmbientLight 50). It is a development copy
  of the lose-game / Writ of Fate cinema that MM9 plays in Arslegard City (same Hanndl, Door0, Losecam/CameraMarker,
  Loseman, Fateman objects there, plus WritMan and ExitTrigger2). Nothing (worlds, scripts, RUDE, mm9.exe, cshell.dll,
  object.lto) names GreatGate; its own FATEMAN.scr fires `ExitTrigger2`, which exists only in Arslegard City.
- Built: nothing. Faces/rooms/portals/movers/lights/decorations/chests/actors: none. Scenarios: none. Bake: none.
  Review root untouched; old ODM import files under `assets_dev/worlds/mm9/maps/greatgate.*` untouched.
- Unmatched scripted objects: Loseman (LOSEMAN.scr), Fateman (FATEMAN.scr), Hanndl (HANNDL.scr), Losecam1-4
  (LOSECAM1/2.scr): cinema only, belong to Arslegard City's death and Writ flow.
- Record: `level_generation/projects/mm9r_greatgate/README.md` (what it is, how MM9 uses it, what a native version
  would need: carry the outcome into Arslegard City's conversion), layout sketch `work/greatgate_layout.png`.
- Not checked: no game run or capture; which engine call fires the `Lose` trigger; whether Arslegard City's current
  import plays any of the scene.
- Blockers: none.
