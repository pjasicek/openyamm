# Wilderness calibration: encounters, scenery and terrain landmarks

The [all-42-map outdoor survey](OUTDOOR_DECORATION_CALIBRATION.md) expands these selected wilderness references
with exact decoration palettes, coordinates, local coverage and subregion contrasts. Use it to choose purposeful
groves, rocky shoulders, dry/haunted scenery, working props and intentional clearings.

Read [regional-transition calibration](REGIONAL_TRANSITION_CALIBRATION.md) for the separate travel/terrain bounds,
roads continuing beyond prompts, optional terrain screening, and focused exit review. Straight open exits are valid;
curves, hills and mountain barriers are not required between neighboring maps.

The [landscape-detail follow-up](LANDSCAPE_DETAIL_CALIBRATION.md) adds full bridge/terrain contact checks, sparse
native stone-detail tiles, land-normalized scenery heatmaps, rough urban/camp props and optional buff/stat pedestals.
A deck-normal check and global decoration totals alone missed visible defects in the previous revision.

Read with [outdoor calibration](OUTDOOR_CALIBRATION.md) before populating a new outdoor map. This study answers
feedback in `test_img/1231.png` through `1235.png`, using Ravenshore (`mm8:out02`), Ravage Roaming (`mm8:out08`),
Shadowspire (`mm8:out06`) and the accepted Brackenford frontage revision as the starting comparison. Numbers describe
this checkout's imported content and merged tables. Interpretations of composition are inferences, not documented
statements by the original designers.

Evidence: [measurements](evidence/wilderness_calibration/measurements.json),
[Ravenshore plan](evidence/wilderness_calibration/out02.png),
[Ravage Roaming plan](evidence/wilderness_calibration/out08.png),
[Shadowspire plan](evidence/wilderness_calibration/out06.png),
[Brackenford before](evidence/wilderness_calibration/brackenford_before.png),
[Brackenford current](evidence/wilderness_calibration/brackenford.png).
Regenerate with `python3 level_generation/scripts/measure_wilderness.py` after writing the native map.

## Count the population that actually appears

Ravenshore has **143 fixed actor records**, but these are not 143 ordinary wilderness enemies:

- **65 town actors:** 20 guards and 45 peasants.
- **78 conditional invasion actors:** the Regnan pirates in group 10 are normally hidden. Map event 4 controls their
  appearance with campaign QBits and a timer. Do not copy this invasion into a baseline density target.
- **59 encounter spawn markers:** 43 Dire Wolf markers and 16 Centaur markers. In the current merged MapStats each
  marker creates 1–3 actors: a possible baseline of **59–177**, with **118 expected**. This is a distribution inferred
  from the current count ranges, not a measured save or a guarantee of an exact original-game population.

Use `monster_info_id` for imported actor identity when present; an actor's other raw `monster_id` field is not always
its monster table identity. Read placed spawns, fixed actors, on-load/event summons and hidden groups separately.
`OutdoorWorldRuntime::buildSpawnPointState`, `resolveEncounterSpawnCount` and initial spawn creation resolve every
placed encounter marker's family/count. Do not multiply their total by the map's rest encounter chance or slot weights.
Ravenshore also has quest-dependent summons; those are separate from ordinary initial encounters.

Behavior references: `assets_dev/worlds/mm8/events/maps/out02.lua`, event 4, and
`reference/mmext-scripts/Decompiled_Scripts/mm8orig/txt/Out02.txt`. Check these before interpreting the actor census.
Do not copy their campaign script into a new map.

Brackenford's starting comparison had only **14 wilderness enemies**, two seven-ogre camps, plus 29 town actors.
This explains large empty combat regions even though each individual cache was guarded. Match the *distribution of
encounter areas* first; stronger monsters need not match the reference's expected total headcount.

## Compose encounter areas and quiet areas together

Ravenshore's wolves form tight local patches, especially across the western/northwestern wilderness. At a 1,600-unit
connected-component radius, the 43 wolf markers form ten groups, each containing 3–5 markers. Marker nearest-neighbor
quartiles are **257 / 295 / 375 units**; group-center nearest-neighbor quartiles are about **3,777 / 4,049 / 5,293**.
A group of four markers means 4–12 actors under these MapStats, not four actors. The 1,600 radius is an analytical
choice, not an encoded native pack ID; the report includes sensitivity at 1,200 and 2,400.

Centaurs are more dispersed in the northeast: marker nearest-neighbor quartiles are **1,184 / 1,691 / 2,197 units**.
One universal pack shape/count/spacing would lose this distinction. Coordinate distances are straight-line XY;
ridges, routes, actor movement and line of sight affect experienced spacing.

For generation:

1. Mark the inhabited footprint, incoming travel anchors, main routes, quiet clearings, optional exploration areas and
   dungeon approaches on a same-scale terrain/minimap plan.
2. Assign named encounter areas to suitable hollows, woods, ridges, camps or defended approaches. Record family,
   variants/count, extent/orientation, purpose, hostility/group ownership and refill/spawn policy.
3. Vary the areas' size and shape. Let some contain several close subgroups and others a loose patrol. Leave meaningful
   gaps between areas, including some attractive places with no enemies. Do not spread packs at equal intervals over
   the whole map, or place a pack beside every landmark.
4. Fit anchors to final quantized terrain and actor radius; keep water, steep faces, buildings, arrival points and
   essential interaction approaches clear. Use deterministic sampling only inside the authored areas.
5. Inspect the overview and a few player-height approaches. Check minimum initial separation from *all* town residents,
   service doors and the inhabited boundary. This is a placement check, not proof that a wandering or pulled enemy can
   never reach town. Keep the engine's normal hostility, movement and view distance.
6. Choose either fixed actor placement or native spawn markers for each population. Avoid serializing both and doubling
   it. State how MapStats, ambient/rest encounters and event-owned summons contribute.

### An entrance does not automatically require guards

| Ravenshore entrance | Active event | Nearest regular encounter marker | Markers within 2,048 units |
| --- | ---: | ---: | ---: |
| Dire Wolf Den | 502 | 1,385 | 2 |
| Smuggler's Cove | 501 | 16,278 | 0 |
| Chapel of Eep | 507 | 5,574 | 0 |

Distances use native active-face centroids, not building labels. The wolf den also has chest BModel 2 (event 83) beside
its mouth. This supports an optional guarded-entrance reward pattern, not a rule that every guarded dungeon needs a
chest. Specify each entrance as guarded, nearby roaming activity, or deliberately quiet; inspect the resulting approach.

## Match scenery coverage and biome, not just totals

| Initially visible native sprites | Ravenshore | Ravage Roaming | Shadowspire | Brackenford before |
| --- | ---: | ---: | ---: | ---: |
| Trees | 271 | 166 | 84 | 285 |
| Low plants | 269 | 0 | 28 | 336 |
| Rocks | 207 | 85 | 159 | 96 |
| Other props | 45 | 7 | 331 | 12 |
| Lights | 15 | 8 | 2 | 0 |

These categories come from the native descriptor inventory. They exclude BModel props and textured face detail.
Zero low plants does not mean a surface has no painted grass, and light records are not a generic scenery quota.
See [Ravage inventory](evidence/mm8/out08_decorations.json) and the existing per-map inventories for names and previews.
Shadowspire's bare tree/rock/prop vocabulary and Ravage Roaming's open grassland should not inherit Ravenshore gardens.

The total of 285 Brackenford trees already exceeded Ravenshore's 271, yet the screenshot could still feel bare.
In a northwest coordinate window, Ravenshore had **77 trees / 13 rocks**, compared with **38 / 9** in Brackenford.
Tree nearest-neighbor medians there were **1,095** versus **829 units**: fewer trees covered the area, but ours were
packed more tightly where they did occur. The southeast Brackenford window had no trees, rocks or low plants at all,
only its ogre camp bones. More trees in an existing dense grove would not fix that hole.

The report's equal-coordinate windows are observation samples, not matched semantic districts. Ravenshore's southwest
window is mostly water and its southeast contains town; never treat those zeros or garden counts as wilderness
land-density targets. Use the water/terrain plan to select comparable usable land and name the sample membership.

Spread suitable woodland across chosen hill shoulders and route edges, with variable density within larger regions.
Keep a few deliberate clearings, meadow stretches and exposed slopes. Add rocks where geology/grade makes sense and
low plants where the reference uses them. Avoid identical rectangular groves, evenly spaced tree rows, or a universal
flower carpet. Inspect roots against the actual triangle, full sprite crowns against landmarks, and collision clearance
against walking and combat space. Preserve accepted town gardens when revising distant wilderness.

## Small lakes and ponds

[The driver's pond reference](../test_img/1233.png) shows a small irregular shoreline and surrounding greenery.
A pond can create a quiet destination, a route bend or a low hollow between larger landforms. Use it selectively in
fitting grassland; it is not a required component of every map or every green district.

Author the water as native terrain cells with a coherent local water elevation, a shallow shore transition and a basin
that belongs to the surrounding heightfield. Quantize first, then resolve supported water/dirt and dirt/grass tiles.
Reserve a full corner-based dirt collar; an analytical ellipse margin alone can leave water tiles adjoining grass at a
shared corner. Use the existing edge/corner validation, then inspect the actual textures and shore silhouette. Do not
make a decorative BModel plane stand in for native terrain water.

The measurement script lists connected **full-water cells** as candidate regions. Thin channels and shore tiles can
split one river into several components; this is **not a lake count**. Confirm candidates with a textured plan and view.
Keep roads, arrival points and encounters away from unplanned water crossings. A pond may intentionally be monster-free.

## Bridges: a small assembled structure

[The driver's crossing reference](../test_img/1234.png) has a plank deck, open timber posts/rails and stone supports or
abutments. Ravenshore's crossings use paired BModels **85+86** and **87+88**; inspect the assembly, not one part in
isolation. One northern assembly spans about **864 units across and 3,584 along**, with below-deck supports extending
its vertical bounds. Total bounding-box height is not rail height or player clearance.

Materials illustrate why filenames are insufficient: **HHR1P is stone**, **trimD is broad wooden planking**,
**TRIM1_16 / Trim9_32 are timber strips**. Inspect their bitmaps and native UVs before assigning a surface role.
Generate a new span fitted to the new banks, using compatible native art. Keep a level upward-facing walkable deck,
clear width between rails, credible support contact and accessible bank transitions. Thin open rails are different
from solid stone parapets. Review along the crossing and from a low side view; check the actual floor/ceiling face types.

## Cave entrances embedded in the heightfield

[The driver's den reference](../test_img/1235.png) is mostly a terrain composition: a narrow cleft and dark mouth beneath
steep flanks. Ravenshore BModel 7 (`d08entrance`) is only **576 × 896 × 576 units**, with 47 `DIRTtyl` faces and one
`solid01` face. The surrounding hill contributes the apparent scale. Its nearby chest is a separate small BModel.

Sculpt the approach and flanking native terrain first, then fit a small irregular mouth/collar into it. Let the hillside
meet the sides and roof; avoid an oversized freestanding rock arch placed on a flat pad. Keep the clickable event face,
party arrival and usable floor exposed, with clear return facing. Inspect from player height and obliquely to find
floating rock edges, visible backs, buried entrances or terrain crossing the interaction face. A nearby chest and a
pack can reinforce a defended den, while other dungeon approaches remain unguarded.

## Completion and reuse

Capture the authored encounter/quiet-area plan, scenery coverage, a woodland approach, water/bridge and cave entrance.
Use the actual written ODM for final geometry and native decoration previews; actor markers in Blender are explanatory
proxies, so inspect selected actors in the normal game view. One quick native/semantic pass should cover grounding,
water/road/building clearance, stable face/event/chest IDs, spawn duplication and preserved arrivals. Do not run a large
scenario suite for population placement. Balance remains a driver playtest task unless the brief asks otherwise.

Record both accepted changes and remaining visual limitations in the project revision notes. Feed new findings into
this guide, the main outdoor workflow, brief and review checklist so future maps start from the calibration.
