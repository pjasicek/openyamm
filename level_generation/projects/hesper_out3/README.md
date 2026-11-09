# Hesper: the Brood Spires (`hes_out3.odm`, map 9120)

The hard zone's outdoor map, built from its design
([BROOD_SPIRES.md](../../../design/kreegan_world/zone3/BROOD_SPIRES.md), BUILD-READY) into the shared
[Hesper stage](../hesper_stage/README.md). The design is the one source: the terrain functions of
`design/kreegan_world/zone3/brood_terrain.py`, every road, place, spire, decoration group and spawn point of
`brood_detail.json` (`make_brood_detail.py`) and the Acid Garden of `acid_garden_plan.json`. Modelled on
[Starport Reach](../hesper_out1/README.md), whose BModel kit (`bmodels.py`, `houses.py`) it imports.

## Build

```sh
level_generation/projects/hesper_out3/build.sh          # map (shared stage lock), scenarios, minimap, stage
flock output/hesper_stage/locks/bake.lock level_generation/projects/hesper_stage/bake.sh hesper_out3
```

1. `build_out3.py`: heights (800 + 1 500 h; the south band levelled to Starport Reach's built north row and the Crown
   gap at 1 200, both checked: the build fails if the south edge differs by more than 32 or the pass road or the gap
   is not level for 1 500 in), roads graded (`run_on` past both edges), pads levelled; tiles (lookups volcanic 198,
   swamp 270, rock 342, **tar 666** for the acid), the acid's shore tiles and Burn attribute, the eight material layers
   (the design's `terrain_materials.yml`, the two new materials' tints from their measured means); the BModels
   (`kit_out3.py`: the greenhouses, the farm wall, the sunk agri-domes, the toppled survey mast, the weather station's
   mast, the gantry with the breach face, D9's mouth, D5's grafted door; Hesk's farmhouse and Wren's post from
   `houses.py`); the decorations and the model buildings' invisible collision boxes; 12 chests; ground items; the 20
   placed groups and the Garden's people; 51 spawn points; the events (Lua); the ODM through the editor's writer,
   verified against the sources. Writes `source/`, `runtime/worlds/hesper/` and `out3_build.json` (every arrival the
   dungeons read: `arrivals.d05_root_door`, `d09_mouth` (also top level, as D9's build reads it), `d11_breach`, the edges).
2. `make_scenarios.py`: the six scenarios from the build record. `make_tour.py <name>`: the review tour.
3. `build_minimap_blender.py`, `finish_minimap.py`: Starport Reach's minimap recipe.
4. `author_standins_blender.py`: greybox stand-ins for the new decorations (`standins/`, last in the stage's
   `source_dirs`), replaced by each Meshy model as soon as its export exists. `import_terrain_materials.py`: packs the
   two new CC0 materials without touching `assets_dev` (the tool's library redirected into `work/`).

## Status (2026-10-23)

Built, staged and baked; the six scenarios pass (`brood_round_trips`, `brood_acid_rain`, `brood_nest`,
`brood_turrets`, `brood_tablets`, `brood_collision`, in `rebuild_all.sh`). Review round 2 is accepted (integrator).
Since then:
- The three ground-plant families of CR-P2-13, on the map's own 4 × 3 atlas.
- The cairn and the ag-flyer wreck as Blender hard-surface models (`hesper_decorations/scripts/build_brood_props.py`);
  no stand-ins are left.
- Night captures (`make_tour.py <name> 23:00`).

Reviews: `review/build04/sheet.jpg` and `review/build04_night/sheet.jpg`. See the builder's reports in
`design/kreegan_world/WORK_PACKAGES/requests/P2.md` ("Builder's report: the Brood Spires" and the reports after it).

## R5 Ashkites (2026-10-26)

The four Sentinel/Heavy Sentinel pairs (10055/10056) were replaced by four kite flocks of four:
A (10310) at Spinefall Pass and B (10311) on the Crown-road bluffs. The original eight actor indices remain;
eight additional flock members are appended. Two egg-field spires each carry four mixed A/B kites, groups
150/151. There are 24 kites and 89 total actors. The old plinth decorations remain as abandoned structures.

`build_out3.py` owns the placements and roost-clearance events; `make_scenarios.py` regenerates the affected
regression. The historical `brood_turrets.yml` filename stays registered in the shared queue, but its assertions
now kill kite groups without shield assumptions and check saved clearance bits 100501/100502. The turret-specific
autonote 10203 is no longer awarded. `make_tour.py` labels the pass shot as a kite roost. No terrain or bake changed.
The family scenario in `../../creatures/hes_kite_codex/integration/ashkite_family.yml` checks 30 seconds of peace
between the nearest egg-field flock and Overseer Prime, then spawns all three tiers indoors.
