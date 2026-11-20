# Calibrating Map Studio by rebuilding known maps

The question this answers: **if a map did not exist, what would a designer have to write down for the studio (and the
agents driving it) to build it, and how close does the result come?** We take maps whose layout, mechanisms and look
we know, pretend they do not exist, write the brief a designer would write, build from that brief, compare the result
with the original, and turn every difference into a fix: a missing field in the brief, a missing tool, a wrong
default, or a gap in the agents' instructions. Started 2026-11-12; nothing has been run yet.

## The maps

| Set | Maps | Role |
|---|---|---|
| Calibration | Ravenshore (`mm8/out02`), Harmondale (`mm7/7out02`), Temple of the Moon (`mm7/7d06`, Emerald Island), Warlord's Fortress (`mm6/6d16`) | Built repeatedly; their gaps drive the studio |
| Held out | New Sorpigal (`mm6/oute3`), Goblinwatch (`mm6/6d01`), Shadowspire (`mm8/out06`), Mad Necromancer's Lab (`mm8/d20`), Gharik's Forge (`mm6/6d18`) | Built once per milestone, never tuned on, to show the studio did not just learn four maps |
| Live | Xeen Act I: Vertigo Meadows and dungeons XD-01 to XD-05 (`devdocs/xeen/`) | A new world with no original to compare against; judged by you |

Existing evidence for the calibration set: case studies `level_generation/case_studies/outdoor/mm8_out02.md`,
`mm7_7out02.md`, `indoor/mm7_7d06.md`; the Ravenshore building catalogue `level_generation/catalogues/mm8_ravenshore/`;
the measured JSONs in `level_generation/evidence/`; the Xeen map-craft census and its scripts in
`devdocs/xeen/research/map_craft/`.

## Three roles, kept apart

- **Designer** writes the brief from the original. It may read everything about the map, but writes at design level:
  what a level designer hands over, not a description of the file (rules below).
- **Builder** builds from the brief with the studio's tools only. It never sees the original map, its case study or
  its evidence files. The asset catalogue hides the target map's own BModels; the general kits, textures and
  calibration bands stay available. Its transcript is checked for reads of the hidden paths.
- **Evaluator** compares the build with the original in a fresh context, runs the metrics and the fixed cameras, and
  files the gaps. It never edits either map.

## The brief, in levels

Each map gets briefs at four levels of detail. Building from each level shows how much a designer must specify:
the smallest level that reaches the target is what the studio's Plan stage must ask for.

| Level | Contents | Like |
|---|---|---|
| L0 Pitch | One paragraph: what the place is, who lives there, how it is played, its mood | A design-doc entry |
| L1 Plan | `plan.yml`: zones or rooms with purpose and size class, the road graph or room graph, critical path, locks and keys, points of interest, landmarks, exits and neighbours, height bands | A bubble diagram with notes |
| L2 Specification | L1 plus kits and palettes per zone or room, a building list by type and service, a mechanism inventory (doors by kind, levers, traps, puzzles as rules), population targets per zone, atmosphere | A production brief |
| L3 Sketch | L2 plus a to-scale sketch on the 512-unit grid: room outlines or district footprints, road lines, water, key heights | An architect's floor plan |

Rules for every level: no coordinates finer than the plan grid, no face or vertex lists, no texture names per face, no
copied geometry. Kits, themes and palettes are named from the shared library (for example "Ravenshore town kit, rich
and medium tiers"), not from the target map's own files.

### What a brief specifies

**Outdoor**: identity and purpose; neighbours, travel and arrivals; landform (height bands, relief, water, coast);
road graph with purposes; districts with spacing and density; buildings by type, tier and service; landmarks and
sightlines; decoration palette per zone and deliberate open spaces; encounter zones (map slots, tiers, density);
points of interest with their behaviour (wells, fountains, shrines); dungeon entrances; atmosphere.

**World** (for worlds with many linked maps): faces and layers, the travel graph, the main-quest steps placed on maps, level and treasure bands. See PLAN.md section 4, "World projects".

**Indoor**: identity and purpose; entrance and exits; room graph with size classes and heights; critical path, loops
and shortcuts; locks, keys and where keys come from; set pieces and puzzles as rules (inputs, states, solution);
mechanism inventory; theme per room or wing; light density; population per room or wing; verticality bands; secrets.

The brief's fields become the schema of `plan.yml` and its companions in the project format (PLAN.md section 4).
When a calibration round shows a brief could not express something the build needed, the field is added there.

## What is compared

Metrics run on the original and on the build through the same core code (import, checks, flow graph). The targets
are bands, not equality: a rebuilt Ravenshore should be Ravenshore-like, not Ravenshore.

| Kind | Indoor | Outdoor |
|---|---|---|
| Structure | Room graph edit distance; room count and area spread; critical path length; loops and shortcuts; verticality bands | Road graph length and junctions; district count; exits and arrivals |
| Scale | Corridor widths, door sizes, ceiling heights, map bounds used | Building footprints, door metrics, nearest-building gaps, relief range |
| Mechanisms | Doors by kind, levers, traps, puzzles; event presets by kind | Services by kind, points of interest by behaviour |
| Density | Spawns and treasure per room; lights per area | Decorations by role per area; spawns per zone; open-space share |
| Palette | Texture and theme overlap | Tile and decoration type overlap; building kit tiers |
| Play | Reachability; critical path solvable; walk time along it in a playtest | Reachability; landmark visibility; travel time between key places |
| Look | Fixed camera sets side by side, scored on a closed rubric by the evaluator | Same |

The Xeen map-craft scripts (`measure_indoor.py`, `measure_outdoor.py`) and the case-study measurements are the first
implementations to port into the core's metrics.

## Turning differences into fixes

Every difference the evaluator files is classed as one of:

1. **Brief gap**: the brief could not say it. Add a field to the brief and the project format.
2. **Tool gap**: the builder could not do it. Add an operation, preset or tool to the studio backlog.
3. **Default gap**: the tool did it, with the wrong default. Change the calibration data (`calibration.yml`, kits).
4. **Builder gap**: the tools allowed it, the agent did not do it. Change the `map-studio` skill or tool descriptions.
5. **Metric gap**: the metric measured the wrong thing. Fix the metric.

Gaps go into `openyamm-studio/calibration/GAPS.md` with the map, round, class and status. A round ends with a report
per map (`openyamm-studio/calibration/<map>/round-N/report.md`, `metrics.json`, the camera sheets). A map is
calibrated when its metrics sit inside their bands at the lowest brief level that gets there, and you accept the
side-by-side views.

## When it starts

Writing briefs needs no studio: the designer role can write L0–L3 briefs for the four maps now, and those briefs are
the first real requirements for the plan format and the Plan stage. Measuring the originals needs the import and
metrics (milestone S1). Builds start with the operations (S2) for overlay-level work and with S3 and S4 for full
indoor and outdoor rebuilds; both come before the browser editor (S5), so calibration drives the authoring tools
while they are built. Before any of that, S0 builds one small new dungeon end to end (the vertical slice in PLAN.md
section 12) to test the project format itself.
