# darkpassageway status

- Phase: DONE (2026-10-31 ~03:00, after the dark-corridor fix round)
- Faces 4 424, rooms 29 (30 sectors), portal faces 22 (18 doorways, 4 archway cuts incl. path_tube), movers 44, lights 76 BLV + 44
  bake-only + 11 DirLights, decorations 113 (props project level_generation/props/mm9_darkpassageway_claude/: 16 built,
  5 reused, rows 2383-2403), chests 7, actors 44 (41 monsters at MM9 sizes + Wyrde RUDE 338, adventurer, hidden Njam),
  3 ladders, water as wading surfaces (lake, tube room, ocean) + a dive box tube -> ocean.
- Scenarios (real clicks): doors_exits PASS (106 steps), chests PASS (117), scripted PASS (243); reach probes PASS
  (work/reach_monsters.yml: control, pillar-ledge terror, pit Terror). Audit: 8 unreachable = worlds joined only by
  teleporters (MM9's design), steps = desert dunes / island shore / pillar platforms.
- Brightness (fix round after orchestrator review): lightmaps matched first (lit zones x0.89-1.19 lightmap-exact), then
  a per-room ambient floor stands in for MM9's PlayerLightOn (convert.py ROOM_LEVELS: levels 0/8/15 vs 30, profile
  ambient_scale 0.22; revert: ROOM_LEVELS = [] and ambient 0.2). With it: forest 1.10, desert 1.12, curve 0.91,
  Wyrde 0.98, tube 1.33, lake 1.44, ocean 1.50, canyon 2.15, start 2.56 of the lightmaps. Baked screen mean 21.5
  (capture 79.6, x0.27, information only); per-view minimum 9.6 (k03 desert teleporter alcove), next 11.4-13.1.
- Bake current: stale_bakes --check does not list the map. model_lighting on (compared, work/model_lighting_props.txt).
- Unmatched: swimming, mirrors' visible rotation, carpet steering, Spikes1 damage, laser visuals beyond evt.Beam,
  statue/Njam animations, AmbientSound, fireflies, PlayerLight.
- Sheets (looked at): level_generation/projects/mm9r_darkpassageway/review/v02_pages_p01-p08.jpg (capture | unbaked |
  baked, 47 views), review/v02_compare.jpg, review/v01_pages_p01-p08.jpg, review/props01_pages_p01.jpg,
  review/model_lighting_compare_p01.jpg, review/teleport/lake_after.png.
- Not checked: MM9 actor art, desktop playthrough with real input (puzzles by hand, carpet ride, fights on the water,
  warrior/sea-monster deaths), save/load mid-puzzle, arrivals seen from Arslegard/Guberland, Android.
- Blockers: none. No engine or shared converter change. Playbook gained "Lessons from Dark Passageway" and a table row.
- Props README: claw torches without a flame and opaque ice statues noted as open items (not fixed).
