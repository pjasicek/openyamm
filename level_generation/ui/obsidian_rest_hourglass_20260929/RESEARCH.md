# Rest hourglass: consistency study for 2136

Historical first-pass investigation. The current [refinement 02](README.md) replaces the initial vector artwork;
the [first proof screenshot](revisions/motion_v1/preview.png) preserves that earlier appearance.

Prepared 2026-09-29 in response to the request to bring back an hourglass without the restored sequence's wobble.
Open [the animated comparison](index.html). This is a browser motion/placement proof and an implementation proposal;
it does not install the vector drawing or re-enable the old hourglass in the game.

## Findings

- The original `assets_legacy/icons_20260926/engine/icons/hglas001.bmp` through `hglas120.bmp` are 72 × 114,
  paletted, opaque images with a textured light panel baked around and through the glass. The MM6-prefixed series
  has a dark panel instead. Neither is a clean foreground sequence. Upscaling these pixels alone preserves the
  unwanted backing. Removing the exterior would still leave the panel seen through the transparent glass.
- The installed `assets_dev/engine/icons_x2/hglas*.png` restoration separates the exterior, but adjacent frames
  have differing painted caps, columns, highlights and glass shapes. Upright samples 060, 061 and 090 demonstrate
  this; common 144 × 228 canvases do not make the artwork identical. Normalizing each frame's bounds would move
  the rest of the object and cannot repair internal geometry or inconsistent glass.
- There is also a playback discontinuity: the removed `formatRestHourglassTextureName` in the tracked renderer
  looped 060–119 over four seconds. Frame 119 is partly turned; frame 060 is upright. Fixing the range removes
  that jump, but would not repair the restored artwork. The comparison can show either the full 001–120 series
  or that former subset; playback is slowed to the new nine-second proof cycle for inspection.
- The current `GameplayScreenController::updateRestOverlayProgress` already advances
  `RestScreenState::hourglassElapsedSeconds`. The current rest renderer and YAML omit the hourglass. There is no
  missing gameplay timer or reason for indoor/outdoor-specific implementations.
- `obsidian_journal_icon_story.png` is an existing, separate Obsidian hourglass illustration. It is a good material
  reference, but its sand and glass are flattened together. Reusing it unchanged gives a static hourglass, not
  an animated sand reservoir.

## Recommended production route: one layered 2D master

Author **one** brass/obsidian frame with empty glass, separated into a back layer and transparent front highlights.
Use the Story icon as the material/style reference. Render sand reservoirs and a narrow falling stream between
those layers. The frame, glass, camera and pixel registration remain identical; no independently regenerated
animation drawings are needed.

The proof uses original SVG geometry to make that mechanism reviewable without producing replacement bitmap art.
Sand drains for eight seconds, then the complete object makes a smooth one-second planar half-turn. Completed
orientations are retained so material highlights do not snap back on the next cycle. This is illustrative timing
and sand geometry, not a physically simulated glass vessel. A final painted shell would replace the vector shell;
the shape stability comes from sharing that same shell throughout the animation.

Native integration can stay in the shared rest renderer: the existing elapsed timer supplies phase, the YAML gives
one fixed rectangle, and ordinary UI triangles/quads draw the two sand shapes and highlights. Alternatively, bake
the composition to a modest fixed-canvas RGBA sprite sequence and use normal frame playback. Do not crop/recenter
individual output frames. Neither route needs a live 3D scene or special per-world behavior.

The placement proof reserves roughly **72 × 114 logical pixels** for the hourglass. Its calendar block starts at
`(364,151)` and is `260 × 133`, leaving twelve logical pixels after the actions block and room for the turn's wider
silhouette. Date text sits to the right, with a fine separator. Rest/wait actions retain their current positions;
the exit button is centred beneath the wider calendar block. The page reconstructs the workspace from
real mounted assets/fonts; only the bottom portrait region of 2136 is displayed as an unchanged screenshot crop.
The source screenshot's red annotation is outside that crop.

## Other viable routes

| Route | Suitability |
| --- | --- |
| One 3D hourglass rendered offline to RGBA frames | Strong choice if the original perspective tumble is essential. A fixed model, camera, scale and lighting solve geometry drift. More authoring work than a layered illustration; runtime still draws ordinary 2D sprites. |
| Restore the native animation with consistent mattes | Preserves the original motion. Requires background reconstruction and careful glass/edge treatment, then upscale and temporal review. The original backing seen through refracting glass makes simple colour removal insufficient. |
| Generate each frame independently again | Poor fit for the stated requirement: canvas locking cannot guarantee identical internal geometry/materials. Do not repeat this route. |

No new imagegen or ESRGAN run was made, no archived source was modified, and no runtime layout was changed for this
research task. The proof and the Story material reference are separate from production asset acceptance.

## Review

- `node --check app.js` passed.
- Headless browser captures were reviewed for sand/glass layering, the date-panel fit and transparent exterior.
- The full comparison uses the original BMPs and installed PNGs directly; the source images are not altered.
- `?phase=0.42` pauses the proof for a repeatable still. The cycle slider, play/pause control, light backdrop and
  old/full playback switch allow interactive comparison.
