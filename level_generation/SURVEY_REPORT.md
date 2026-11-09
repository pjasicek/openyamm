# Reference survey and validation record

## Current calibration — 2026-09-07

The current collection has **33 map studies** (15 indoor, 18 outdoor), including the earlier decoration/terrain
revision. The [visual calibration](VISUAL_CALIBRATION.md) adds the driver's ten facade screenshots and a
[Ravenshore catalogue](catalogues/mm8_ravenshore/README.md): 121 native BModels inventoried, 84 textured part cards,
67 parts with active entrance faces, 10 assembly views, native texture examples and equal-scale door comparison.
The catalogue links faces/events to real houses, services and initial NPC candidates; wealth/design-intent readings
are explicitly distinguished from measured evidence. All part contact sheets and the important assemblies were opened
for visual review. Blender MCP remained connected, and each render batch restored the original active scene.

The quick catalogue consistency check passed in under one second: source hashes, 109 texture keys, 78 active entrance
faces, all rendered images and local documentation links. See [validation.json](catalogues/mm8_ravenshore/validation.json).
Python syntax checks passed. No game scenario, engine build or map mutation was needed for this calibration pass.

For future generation, visual authenticity is the main gate. Ordinary outdoor content requires one quick native/wiring
check, with deeper behavioral/performance scenarios reserved for new behavior, observed defects or explicit requests.
This supersedes the older exhaustive project-review wording below and the first project's functional acceptance as
a claim of outdoor visual quality. The already playable maps were not remodeled in this pass.

## Original survey record — 2026-09-06

Date: 2026-09-06. Scope: local OpenYAMM assets and implementation, using Blender MCP for reference rendering.

Completed artifacts:

- Agent [playbook](README.md) with separate indoor and outdoor generation procedures.
- [Thirty case studies](case_studies/README.md): five indoor and five outdoor maps from each of MM6, MM7 and MM8.
- Thirty measured JSON records with local source paths/hashes, geometry/state counts, map stats, texture/tile data
  and selected direct event bindings.
- Thirty measured plans (outdoor plans include tile and height views), thirty Blender isometrics, and twelve overview
  sheets. All six plan sheets and all six Blender sheets were opened for visual inspection during this survey.
- Reproducible inspection/render/documentation scripts, authoring and scripting contracts, brief template and review gates.

The images support layout, landform, palette and structural analysis. The indoor cutaways expose cave wall bands,
architectural modules and overlap between levels. Outdoor views distinguish heightfield landforms from placed BModels.
The survey also traced selected event behavior against local Lua and readable reference scripts and inspected the
existing native import/build/runtime paths. This is not a full audit of every event branch on every map.

Important observations incorporated into the instructions:

1. d48 is a practical first complete indoor slice: three occupied sectors, two portals, one bound chest, one house and
   an exterior exit. The two exit faces do not represent two separate houses.
2. A visually simple or early-game map can have many sectors and doors. Abandoned Temple d05 contains 112 door state
   records. Control dependencies and moving geometry require explicit authoring.
3. Chest slots, directly bound chests, spawned encounters and fixed actors are different counts. Unused legacy state
   allocations and exported event templates must not inflate the feature inventory.
4. Pressure plates, secret detection and damage effects are separate semantics. Naga Vault event 76 references doors
   76/77; there is no separate event 77. The case study distinguishes those ID domains.
5. The current merged MM6 map-stat treasure values and zero-radius imported MM7 lights are observations about this
   checkout, not recommended balancing/lighting defaults for new maps.
6. Native outdoor terrain is a quantized heightfield with categorical tile behavior. Water and burn flags can overlap,
   especially in Ironsand and Plane of Fire. Roads need resolved tile transitions and route validation.
7. The current source compiler and package tools provide useful foundations but do not yet meet the complete proposed
   Blender-to-native contract. [Pipeline status](PIPELINE_STATUS.md) lists the gaps and implementation order.

Validation performed:

- Ran `inspect_references.py` over all thirty maps successfully.
- Executed `blender_reference_view.py` through Blender MCP for all thirty maps; final view metadata reports no missing
  texture keys. Resolved cross-world texture ownership through the merged development package order.
- Generated case studies and overview sheets; validated inventory, hashes, event IDs, PNG presence/dimensions, terrain
  palette coverage and local Markdown links with `validate_references.py`.
- Checked Python syntax for all scripts in this folder.

Limits: Blender lighting is neutral study lighting; actors, decoration billboards, scripted state and animated-water/
shore compositing are omitted. Magenta shore outlines in Blender are transparency preview artifacts. The 2D terrain
preview uses a documented approximation. Complex interiors still need floor slices and state-specific close-ups when
chosen for a generation project. No new native map was generated, no engine gameplay scenario was run, and no terrain
performance comparison was performed in this documentation task. Any later runtime review follows the current
visual-first policy above; a performance comparison is not a default generation gate.

Game assets and engine implementation were read as evidence; this task's persistent additions are confined to
`level_generation/`. Revalidate after changing source maps, merged tables or relevant compiler/runtime behavior.
