# Rendering Notes

## Outdoor Terrain Status

Current validated state for `Out01.odm` / Dagger Wound Island:

- Outdoor terrain geometry matches the original minimap closely enough for debug validation.
- Outdoor `bmodels` are parsed from `ODM` and appear in plausible positions.
- Terrain texturing now uses original bitmap assets from `assets_dev/Data/bitmaps`.
- Terrain tile ids are resolved through `dtile.bin` / `dtile2.bin` / `dtile3.bin`.
- Terrain textures are packed into a runtime atlas and rendered with a textured bgfx pass.
- Magenta key-color pixels in the original BMPs are treated as transparent.

## Known Limitation

The current shoreline / contour rendering is still approximate.

Observed behavior:

- The earlier magenta contour artifacts were caused by source-art key color and were fixed by alpha-keying magenta.
- The current blue fringe around coastlines is the fallback water/base terrain showing through transparent transition pixels.

Interpretation:

- This is acceptable for the current debug milestone.
- This is not final-correct terrain compositing.
- The original game likely performs more nuanced shoreline / transition handling than the current single-tile textured pass.

## Likely Future Fixes

When returning to terrain rendering quality, investigate one or more of:

1. Dedicated water rendering instead of relying on the fallback base color behind transparent edge pixels.
2. Special handling for shoreline / transition tiles.
3. Proper terrain tile blending / compositing against neighboring cells.
4. Verification of any additional key colors or transparency conventions used by original terrain BMPs.

## Known Outdoor BModel Artifacts

Some visible outdoor `bmodel` faces appear to extend down into water or ground in ways that look odd from the free debug camera.

Confirmed `Out01.odm` cases:

- `bmodel=101 face=47` in `CannonA_S`, texture `gn_mtl03`
- `bmodel=102 face=47` in `CannonA_E`, texture `gn_mtl03`
- `bmodel=106 face=58` in `Dockb_W`, texture `bwooda1`
- `bmodel=107 face=2` in `Dockc_W`, texture `bwooda1`

Current interpretation:

- These are real source-model polygons present in the `ODM`, not missing textures or random renderer corruption.
- The dock faces are simple vertical quads spanning from the waterline down to `z=0`.
- The cannon faces are also vertical support-like polygons with valid geometry and UVs.
- All inspected faces had `flags=0x0000`, so there is currently no known original face flag indicating that they should be hidden or culled.

Conclusion:

- Treat these as original data quirks for now.
- Do not add ad hoc culling rules unless later evidence shows the original engine suppressed them in a principled way.

## Known Indoor Entity Gaps

Some indoor entity records do not currently resolve through the decoration billboard path.

Confirmed `D42.blv` / Arena case:

- `entity=31`
- `name=torch01`
- `dec=0`
- `tex=-`

Current interpretation:

- This is not a hidden billboard or a visibility-gating bug.
- The entity does not have a usable `ddeclist.bin` decoration id.
- The entity name `torch01` also does not resolve through `dsft.bin`.
- So the current indoor decoration billboard pipeline has no sprite-table mapping for it.

Conclusion:

- Keep the debug marker / inspect output for these unresolved indoor entities.
- Treat them as a separate indoor entity/data path to investigate later.
- Likely candidates are map-logic/light entities or geometry/face-texture-driven visuals rather than normal decoration billboards.

## Non-Blocking TODO: Indoor Mechanism Timing

Current status:

- Indoor mechanism state, scripted activation, `SetTexture`, `ToggleIndoorLight`, and `StopDoor`/`StopAnimation` behavior are working well enough for the Temple puzzle in `D05`.
- The Temple sequence now behaves mostly correctly:
  - clicking the main door starts the event
  - snake eyes turn red
  - clicking all eight snakes clears the eyes
  - the main door opens
  - the moving floor mechanisms stop

Open question to revisit later:

- The timing of some indoor mechanism motion, especially door opening, still feels somewhat slower than the original game.

What was already checked:

- OpenEnroth uses door speed as map units per real-time second.
- OpenEnroth movement formula matches the current OpenYAMM formula:
  - `distance = elapsed_ms * speed / 1000`
- Two real mismatches were already fixed:
  - indoor door state enum interpretation
  - `DLV` `timeSinceTriggered` conversion from ticks to real-time milliseconds

Current conclusion:

- This is not a blocking issue.
- If timing still feels off later, the next thing to verify is the parsed `moveLength` / `openSpeed` / `closeSpeed` field fidelity for specific indoor mechanisms, not arbitrary speed scaling.

## Current Debug Controls

- `W A S D`: pan camera target
- `R / F`: raise / lower target
- `Arrow keys`: orbit
- `Q / E`: zoom
- `1`: toggle filled terrain
- `2`: toggle terrain wireframe
- `3`: toggle bmodel overlay
- `4`: toggle bmodel wireframe
- `5`: toggle inspect mode

## Recommended Next Step

Do not spend more time polishing shoreline rendering right now unless it blocks another task.

The next stronger milestone is:

- parse and render textured outdoor `bmodels`

That should make towns, structures, and landmarks much more recognizable while preserving momentum.
