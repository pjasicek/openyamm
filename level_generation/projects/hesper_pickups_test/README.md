# The pickups test room (hes_pickups_test.blv)

A one-room colony test map for the shared dungeon pickups
([`hesper_stage/common/pickups.lua`](../hesper_stage/common/pickups.lua), design
[PICKUPS.md](../../../design/kreegan_world/PICKUPS.md)): a stim canister (event 701), a serum vat (702), three colony
satchels (751-753) and a scrap bundle (754). Map id 9109 (the integrator's zone 1 reserve) in
`hesper_stage/maps.yml`; it has no entrance, only its scenario loads it.

## Build

```sh
cd level_generation/projects/hesper_pickups_test
flock -s ../../../output/hesper_stage/locks/stage.lock blender --background --factory-startup --python author_pickups_test_blender.py
cd ../../..
flock -s output/hesper_stage/locks/stage.lock python3 level_generation/projects/hesper_pickups_test/build_pickups_test.py
flock output/hesper_stage/locks/stage.lock python3 level_generation/projects/hesper_stage/stage.py
```

`rebuild_all.sh` builds it (`MAPS`: `pickups_test`) and runs its scenario.

## Scenario

```sh
cd output/hesper_stage/scenario_run
flock -s ../locks/engine_build.lock flock -s ../locks/stage.lock ../../../build/game/openyamm --world hesper \
    --headless-run-scenario ../../../level_generation/projects/hesper_pickups_test/pickups.yml --scenario-no-color
```

[`pickups.yml`](pickups.yml) asserts the roll at first entry (canister green, vat purple: the event random numbers of a
new game, the same every run), drinking both (+2 Endurance and +2 Speed to the active character, autonotes 20 and 22,
both containers empty, a second click gives nothing), and the satchels (751 nothing, 752 and 753 an item, the bundle
754 1 744 gold at treasure level 5, a second click gives nothing).

Headless runs do not hand a clicked decoration's `evt.GiveItem` item to the party: indoors only the game view does
(`IndoorGameView::presentPendingEventFeedback`), so the scenario asserts the item satchels by their state (2), and the
item reaching the hand is checked in the desktop tour below. An engine-queue need: the scenario driver applying
granted items after an interaction, as the view does.

## Desktop check

[`review_input_pickups.yml`](review_input_pickups.yml), an input tour (its header has the command), clicks every
pickup: `review/build02/sheet.jpg` (2026-10-24). The canister green then dark glass ("+2 Endurance permanent"), the
vat purple then the torn empty vat ("+2 Speed permanent"), the satchels "Empty.", "You found 1769 gold." and "You
found something (Amulet)!" (the amulet in the hand), the bundle "Empty.". No model or Lua errors in the run's
log. The desktop's satchel rolls differ from the headless ones (the event random numbers start from the game time).

The colour and opened models load because the stage installs `hesper_stage/pickup_sprites.lua` as this map's overlay
`hes_pickups_test_pickups.lua`: a map loads only the models of what it places and of the literal `SetSprite` names
in its own scripts (`game/maps/DecorationModelManifest.cpp`), not those the shared common file computes.

## Placing pickups in a dungeon (step 3 of PICKUPS.md "Build", the map builders')

- Place each container as `hes_stim_canister` (colony and Ancient places) or `hes_serum_vat` (Kreegan places), each
  satchel as `hes_colony_satchel` or `hes_scrap_bundle`, with its own event id as both event and cog:
  `b.decoration('hes_stim_canister', x, y, z, facing, event=701, cog=701)`. Containers take 700-749, satchels
  750-789; 790 and 791 are the shared on-load event and refill hook.
- In the map's `handlers.lua`: `HesperPickups.setup({canisters = {...}, vats = {...}, satchels = {...},
  bundles = {...}})`; the stage then installs the swaps' overlay for the map. The treasure level comes from the map's
  loot class (`LOOT_CLASS` in `pickups.lua`: H1 level 3, H2 5, H3 6); a map not listed passes `treasure = n`.
- The counts and rooms are PICKUPS.md's tables; satchels never in the boss's room.
