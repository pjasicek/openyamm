# Geometry upgrade concept: shared rules

The attached image is an in-game screenshot of OpenYAMM (a modern engine remake of Might and Magic VI), map New
Sorpigal. The buildings are classic 1998 "BModels": a few dozen flat polygons each, with new high-resolution textures.
We want to see what a realistic geometry upgrade of these same buildings would look like in this same real-time game.

Make two edited versions of the screenshot (an image edit of the input, not a new painting):

Hard rules for BOTH versions:
- Exact same camera position, angle, field of view, framing and composition. Overlay-compatible with the input.
- Same buildings, same footprints, same proportions, same heights, same number of storeys, same roof shapes.
- Same textures and materials as the input (same brick, plaster, stone, wood, same colours). Detail must come from
  geometry (depth, thickness, bevels, overhangs, shadows), not from new paint.
- Same sun direction, time of day, sky, terrain, trees, flowers, water, characters, colour grading and exposure.
  Do not make it look path-traced or photographic: it must still look like the same real-time game renderer
  (real-time shadows and ambient occlusion in the new crevices are fine).
- No new props, signs, banners, people, vegetation or buildings. No clutter.
- Keep the HUD (top-left bar, minimap, portrait frame at the bottom) unchanged.

Version A, file `<view>_A_target.png` (the realistic target, about 1,500–4,000 triangles per building, built in a
week per town by one artist from a modular kit):
- Walls get thickness: windows and doors recessed into the wall, with sills, lintels and frames that stick out.
- Half-timber beams, posts and corner boards stand proud of the plaster by a few centimetres.
- Roofs become slabs with real thickness, eaves overhang with fascia boards and visible rafter ends, ridge caps,
  barge boards on gables.
- Bevelled / chamfered edges on wall corners, posts and beams; a stone plinth (foundation course) at the wall base.
- Steps and porches with real treads and edges; porch posts with simple brackets.
- Stone bridges/walls: coping stones along the top, slightly irregular edge silhouette.
- Silhouettes stay mostly straight: this is clean modular detail, not a sculpt.

Version B, file `<view>_B_stretch.png` (stretch goal, about 8,000–15,000 triangles per building, hand-modelled hero
buildings):
- Everything from A, plus: individual roof tile / shingle rows modelled with a broken ragged roof silhouette, slightly
  sagging old ridges, modelled quoin stones at the corners, carved trim mouldings and cornices, leaded window frames
  modelled in depth, chimneys with caps, gutters, irregular hand-cut stone edges on walls and bridges, worn rounded
  timber ends.
- Still the same buildings, textures and composition; no extra props.

Process: generate A first, then B (B may use A as an additional input). Compare each against the input: if the
camera, the building layout or the colours drifted, regenerate that version once. Stop after one correction per
version. Save the PNGs at the paths below at the input resolution (1600x900) or the nearest your tool supports.
