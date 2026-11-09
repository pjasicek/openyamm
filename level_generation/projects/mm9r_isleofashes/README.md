# MM9 rework: Isle of Ashes (`isleofashes.odm`)

**Superseded, no longer builds (2026-11-06).** The isle is the BLV of
[`../mm9r_isleofashes_blv/`](../mm9r_isleofashes_blv/README.md), whose map Lua is a hand port (`regionlua.py`).
`story.py` stays here for that build (the story actors it places, the book's cinematic) but writes no Lua any more:
the generic story runtime (`story.lua`, the generated `Isle.*` tables, the compiled RUDE hooks) is gone, so
`convert.py` exits at its start. The notes below describe the pilot as it was.

The pipeline pilot of the [MM9 rework](../../../devdocs/mm9_rework/README.md): MM9's Isle of Ashes converted from its
original DAT world into a native ODM. Built into the isolated review root `output/mm9_rework/assets_dev`
([`../mm9r_common/review_root.py`](../mm9r_common/review_root.py)); `assets_dev` is not written.

## Build and review

```sh
python3 level_generation/projects/mm9r_isleofashes/convert.py   # terrain, tiles, ODM, install, weights (about 10 s)
python3 level_generation/projects/mm9r_isleofashes/make_tour.py terrain03                  # the new map's tour
python3 level_generation/projects/mm9r_isleofashes/make_tour.py terrain03 --original       # same views, old map
./tools/run_game.sh --isolated mm9isle --world mm9 --map isleofashes.odm \
    --assets "$PWD/output/mm9_rework/assets_dev" --position -3840 -13056 2272 --yaw-radians 0 --pitch-degrees 0 \
    --warmup 3 --seconds 90 --set debug.screenshot_tour_path=$PWD/level_generation/projects/mm9r_isleofashes/review_tour_terrain03.yml
```

The original map forbids saving, which the isolated launcher needs; its comparison tour runs against
`output/mm9_rework/assets_original` (a second hard-linked mirror whose only change is `allow_save_game: true` in the
old `isleofashes.scene.yml`).

`convert.py` also installs the MM9 world's terrain material file (`../mm9r_common/terrain_materials_world.yml` as
`worlds/mm9/terrain_materials/world.yml`: MM8's tile table and tile art, per-map shades) and writes the map's
weights with `tools/terrain_materials.py weights --assets`.

## What the conversion does

- Terrain: the visible terrain world models (terrain-folder textures; water volumes, the VisBSP helper and the
  PhysicsBSP collision hull excluded), transformed `x = LT.x * 2.56 - offset_x`, `y = LT.z * 2.56 - offset_y`,
  `z = (LT.y - sea) * 2.56` (`work/transform.json`; offsets centre the terrain on a cell boundary, the sea is the top
  of the water volume, LT -64). Node heights are the top surface at each 512-unit node.
- Seabed: the heights below sea level are kept in `work/seabed_heights.npy` for the diving decision (plan, Water
  and diving); the ODM clamps them to the sea.
- Coast: a node is dry when MM9 land lies within 128 units of it (so spits and ridges narrower than a cell
  survive); wet nodes lie at the sea. Each cell's tile follows its wet corners as MM8's shore tiles do (four wet:
  water; two adjacent: an edge, `wtrdrN` = water to the south; three: an inner corner; one: an outer corner); a
  diagonal pair, which has no tile, dries the wet node with most dry neighbours. Shore cells keep their land-side
  corners (native shores do: Dagger Wound's reach 1632). The first rule, a cell is water when under half of it is
  land with every shore corner sunk to the sea, erased the narrow ridge under the north castle.
- Tiles: one per land cell from the MM9 terrain texture covering most of its land samples (`ashcliff`, `ashrock2`,
  `NWROCK` rock; `ashrock`, `MainGrass` grass; `ashdirt3` dirt), through the lookups grass 90, rock 342, volcanic
  198 (unused), water 126.
- Structures: from the current imported map's BModels (the DAT world models with texture aliases and texel UVs),
  moved into this frame: every face of the PhysicsBSP (MM9's main static world: the castle, ruins, wooden bridges and
  walkways, floors), the fort walls, world objects and the doors; the non-terrain faces of the terrain models
  (Terrain3's fort wall). Grouped into BModels by shared vertices (8-unit tolerance), coplanar faces merged by the
  editor: 45 structures and one invisible collision BModel (MM9's `firethrough` blockers), 4 428 faces in all.
  MM9's sea floor plane (`ashfloorsea`, wider than the map) is left out for the diving decision. Not yet taken: the
  script-linked invisible brushes, AI barriers, perception brushes, the props, the chests.
- Exits: the review root's `worlds/mm9/data_tables/map_transitions.txt` gets the isle's rows in this frame (exit
  volumes on the isle and arrivals onto it), computed from the assets_dev originals; other maps' rows are kept as the
  review root has them. The exit to Sturmford lies far out at sea (about 43 000 west): MM9's boat leg.
- Ground materials: the MM9 world's material file (rock `rock_ground` with a tan shade, grass with a dry olive
  shade, MM8's shore, slope and cliff rules), weights from `tools/terrain_materials.py` (`--assets`).
- Cut-outs: MM9 cuts its terrain mesh open under the castle on the middle island (a 2 000-unit opening; the castle's
  floors are the ground) and at the tunnel's east mouth. Enclosed openings are land: each fine sample takes the lowest
  structure floor over it minus 8 (`fill_cutouts`). Before this they were read as sea: water pits and gaps under the
  castle walls (user review 2026-11-01).
- Gating: `work/gating.png` and `work/gating.json` (green MM9-walkable, red steep in MM9 but walkable on the grid,
  orange walkable in MM9 but a slide cell on the grid, magenta route cuts, cyan route joins). Route grading
  ([outdoor playbook](../mm9r_common/OUTDOOR_PLAYBOOK.md), step 6): trail cells from MM9's painted map and connectivity
  cuts per walkable component (multi-cell breaks included) are graded to the path crossing them, all solved together,
  structure nodes pinned (`work/route_fixes.json`: 98 cells, 63 from trails; 3 cuts left beside pinned or sea nodes).
  Trail walk (`make_trail_walk.py`): Yrsa's hut up the valley and round the north-east mountain, 31 of 32 segments
  pass; the last clips a steep cell's corner and passes walked round it. Terrain only.
- Party: the review copy of `worlds/mm9/world.yml` drops MM9's `partyMovement` (eye 152), so the engine defaults
  apply (eye 176, radius 37, height 192): see the [checks](../../../devdocs/mm9_rework/CHECKS.md).

## Status (2026-10-29)

Terrain, coast, structures, route cuts and exits built and reviewed: `review/terrain02_compare.jpg` (terrain, old
against new), `review/struct01_compare.jpg` and `review/castle_compare.jpg` (structures), `review/coast04_sheet.jpg`
(after the coast rework). 1 183 land and 530 shore cells.

Props (2026-10-29): 59 decoration entities from `props.json` (`../../props/mm9_isleofashes_claude/`: 16 converted
MM9 props installed as `mm9_deco_*` engine models; the 25 MM9 trees as the MM8 pines `tree29`/`tree30`). Their 17
decoration rows, sprites and bindings exist only in the review root (`tables.py --apply --assets
output/mm9_rework/assets_dev`): appending them to assets_dev would shift the ids Hesper's stage relies on (it
expects the engine table to end at row 673). Review: `review/props01_sheet.jpg`; the pines read bright lime against
MM9's dark spruces, and the trees lack MM9's per-placement scales (map entities carry none).

Chests (2026-10-29): MM9's three chests keep their own baked models (the old map's `MM9_chest_*` BModels, every
face clickable, event 40 + n) and their loot records from the old scene (treasure type, level, trap, repopulation),
moved into this frame; the map Lua opens them (`evt.OpenChest`). Check: `make_chests_scenario.py` writes `chests.yml`
(headless, from `output/mm9_rework/scenario_run`, whose settings.ini points at the review root): passes.

Floors: our terrain stays under every structure floor MM9 shows (an upward face on or above MM9's terrain):
`clamp_under_floors` lowers the dry nodes within a cell of such a floor to 8 under it (99 nodes; the castle courtyard
had terrain through its floor). Floors MM9 buries are left alone.

Doors (2026-10-29): the bunker's pair (BunkerDoor1/2, DAT 498/499) and Yrsa's hut door (RotatingDoor8, DAT 769) are
BModels of their own (faces kept, not merged) and rotating-door mechanisms on the classic scene
([classic mechanisms](../../../devdocs/mm9/MM9_ODM_BMODEL_WORLD_GOAL.md#mechanisms-on-classic-odm-scenes)), with MM9's
pivots, angles, times and sounds from the old scene moved into this frame (`story.py` `mechanisms()`). The bunker
stays locked without the Turret Key (`DoorLock.scr 568 1`, below); the hut door toggles (MM9 closes it again after 5 s:
not reproduced). The light bake treats doors as closed.

Placement check: `check_placement.py` compares MM9's surfaces with ours (lost and added land, every structure's
foundation gap over both grounds; `work/placement.png`, `work/placement.json`). Foundations that met MM9's ground
are fitted (`fit_foundations`, 65 nodes).

Boat arrivals: the three `transport_routes.txt` rows to the isle (StartPoint0) still carry the old frame's arrival
(-18 984, 492, 492), not moved by `convert.py` (found 2026-11-01). Not yet: the tunnel (blocked by the hill's terrain; options in the [outdoor playbook](../mm9r_common/OUTDOOR_PLAYBOOK.md#tunnels-and-caves-under-terrain-open)), the general population (spawn density; only the chain's actors are placed), the beach band on steep shore slopes (beach material across raised shore
cells), the minimap (still the old map's), a sky theme.

## Story chain (2026-10-29)

`story.py` (called by `convert.py`) builds the chain from MM9's data, bound by DAT object names; `story.lua` holds
the authored handlers, each with its source lines; `make_story_scenario.py` writes `story.yml` (headless, from
`output/mm9_rework/scenario_run`, like `chests.yml`).

The chain as the sources give it (RUDE rows are `NPC<n>.rude` lines; keys are raw MM9 keys, QBit 90000 + key):

1. Forad Darre stands at the bridge. Using him (FORAD.scr:23-41 OnUse: key 480, 800 xp; the DoRude property opens
   NPC2): node 2 line 5 "Our boat crashed" -> line 15 "No. Who is that?" (key 477, journal "Find Yrsa the Troll").
   OnRudeExit (FORAD.scr:46-86): key 368 and 4000 xp once. He does not walk up by himself here: his OnAppear
   (FORAD.scr:121-129, OnFoundPlayer 256 -> within 16 -> DoRude 2) runs on an "Appear" message no isle object sends
   (ARGUMENT.scr sends it in Thronheim).
2. Yrsa in her hut (YRSA.scr:75-102 OnUse: keys 480 and 365, 800 xp): NPC1 line 21 "Who are you?" (forbids 27)
   gives key 7 ("Help Yrsa the Troll": the dragonflies beyond the tunnel).
3. The dragonflies: 12 flyers (DragonFly0-2, DragonFlyMite5-11, FireDragonFly0-1) have DeathTriggerTarget
   KillControl / OneDown; KillControl runs tm_Hardrock.scr "8 27 200" (29-54): the eighth death gives key 27 and
   200 xp.
4. Yrsa: line 6 "Who are you?" (needs 27, forbids 1) -> destiny -> line 3 gives key 1. OnRudeExit (YRSA.scr:15-70):
   key 27 -> 2000 xp + key 366; key 1 -> 2000 xp + key 367.
5. Forad: line 8 "Yrsa sent us" (needs 1) -> ... -> line 13 "Welcome Aboard." (hire, -10: keys 29 and 371;
   journal "Kill the Bone Thrashers ... behind the locked door"). OnRudeExit: with key 29 he leaves the map (joins).
6. Yrsa: line 25 "How do we through that door?" (needs 29) gives key 469; OnRudeExit Key (YRSA.scr:24-37): item
   568, the Turret Key.
7. The bunker (DoorLock.scr:22-48 on BunkerDoor1/2, "568 1"): the key opens the sticky pair and is taken. In front of
   it Trigger2 raises BoneThrasher1-3 (AutoResurrect.scr).
8. The book on the lectern (IsleAshesBook.scr; the lectern Prop159 forwards Use, PropTrigger.scr "Book Use"): with
   key 29 and without 28 the cinema runs (OnUse 29-54 ... FadeOut2 218-226): the bunker's FortWall breaks, Shooter
   fires out, Shooter0 fires at the islet's FortWall0, whose death triggers TriggerEffects (five explosions, the
   Lich King's end), the islet sinks, the boat appears, key 28 and 5200 xp, then ExitTrigger1: Sturmford StartPoint0,
   4 travel days.
9. Afterwards (key 28) Annud Redeye (DAT 747, HideModel.scr "28 unhide", NPC138, Fre's Rain) stands at the dock and
   sells passage to Sturmford (line 3, -5; `transport_routes.txt` dock 138: Tue-Thu, Sat, Sun; closed while key 5017
   is set, 20:00-6:00 by FORADWORLD.scr, which `story.lua` runs). Forad (DeleteCheck) is gone on any later
   visit once key 29 is set. Yrsa (YRSA.scr Init) leaves with key 29 only after the cinema (key 28): MM9 forbids
   saves on the isle, so it never reloads the map between Forad joining and the Turret Key; here a reload in that
   window would have hidden her and locked the bunker for good (2026-10-30). The Lich and FortWall0 go after key 28.

Implementation: the scene actors are the old scene's DAT records of the chain's objects (3 NPCs, 12 flyers, the
3 bunker Bone Thrashers, the Lich), moved into this frame onto the floor below (flyers keep their height). The
dialogue callbacks (OnRudeExit, and each DoRude object's Use rewards followed by its dialogue) are compiled by
`tools/mm9_import_discovery/mm9_scr_to_lua.py` (`compile_rude_exit(..., dorude_id=NPCNbr)`). The generated data
(`Isle.*` in the map Lua) carries actor indices by DAT name, death triggers, the story triggers' boxes and messages,
points with their aim, script parameters and the Sturmford exit row. `story.lua` dispatches DAT messages (trigger
targets, death triggers), runs the cinema on a 0.25 s timer, polls the trigger boxes, and sets presence on map entry.
Missing sounds at the scripts' paths (`spells/ebolt01.wav`, `spells/eblast03.wav`) are copied from MM9's sound files
into the review root.

Check: `story.yml` (161 steps) walks the whole chain: both conversations with Forad and three with Yrsa by RUDE
row, eight dragonfly kills (key 27 on the eighth), the bunker locked without the key and both doors open with it
(the key taken), the lectern, key 28 at OnSink, Sturmford after 17 s; then a later visit: Yrsa and Forad gone, Annud
present, passage taken to Sturmford. Passes, and `chests.yml` still passes (2026-10-29). Headless runs do not
advance outdoor map timers (the scene frame update belongs to the game view), so the scenario runs the story timer
(event 31000) once per 0.25 s tick, and it uses the lectern's event directly (headless runs do not load the model
triangles decorations are picked by). The cinema's look, the lectern click and the Trigger2/TriggerStarters boxes
(both timer driven) still need a desktop check.

Engine gaps (logged once as `[MM9Unsupported]`): cinema cameras, pans, fades and letterbox (the party keeps
control during the 17 s); the islet cannot sink (Terrain3 is part of the height map); the boat cannot sail (it shows
at its berth); ExitTrigger1 runs as `AdvanceGameMinutes` + `MoveToMap` (time and timed states pass, but not the
travel's food and rest); the hire service itself (Forad as a follower) is not implemented, only its keys; the
earthquake objects are not shaken; the hut door does not close by itself; ContainerCheck (the party on an AI rail) is
taken as true. Yrsa vanishes on re-entry once Forad has joined (YRSA.scr Init); MM9 forbids saving here, so
it never reloads between steps 5 and 6, and the remade map would lose the bunker key. story.lua hides her only after the
cinema too (keys 29 and 28).
