# Geometry upgrade concept: shared rules

The attached image is an in-game screenshot of OpenYAMM (a modern engine remake of Might and Magic VI); the map is
named in the prompt. The buildings are classic 1998 "BModels": a few dozen flat polygons each, with new high-resolution textures.
We want to see what a realistic geometry upgrade of these same buildings would look like in this same real-time game.

Make one edited version of the screenshot (an image edit of the input, not a new painting):

Hard rules:
- Exact same camera position, angle, field of view, framing and composition. Overlay-compatible with the input.
- Same buildings, same footprints, same proportions, same heights, same number of storeys, same roof shapes.
- Same textures and materials as the input (same brick, plaster, stone, wood, same colours). Detail must come from
  geometry (depth, thickness, bevels, overhangs, shadows), not from new paint.
- Same sun direction, time of day, sky, terrain, trees, flowers, water, characters, colour grading and exposure.
  Do not make it look path-traced or photographic: it must still look like the same real-time game renderer
  (real-time shadows and ambient occlusion in the new crevices are fine).
- No new props, signs, banners, people, vegetation or buildings. No clutter.
- Keep the HUD (top-left bar, minimap, portrait frame at the bottom) unchanged.

The version, file `<shot>_A.png` (the realistic target, about 1,500–4,000 triangles per building, built in a
week per town by one artist from a modular kit):
- Walls get thickness: windows and doors recessed into the wall, with sills, lintels and frames that stick out.
- Half-timber beams, posts and corner boards stand proud of the plaster by a few centimetres.
- Roofs become slabs with real thickness, eaves overhang with fascia boards and visible rafter ends, ridge caps,
  barge boards on gables.
- Bevelled / chamfered edges on wall corners, posts and beams; a stone plinth (foundation course) at the wall base.
- Steps and porches with real treads and edges; porch posts with simple brackets.
- Stone bridges/walls: coping stones along the top, slightly irregular edge silhouette.
- Silhouettes stay mostly straight: this is clean modular detail, not a sculpt.

Process: generate only version A. Compare it against the input: if the camera, the building layout or the
colours drifted, regenerate once. Stop after one correction. Save the PNG at the path below at the input resolution
(1600x900) or the nearest your tool supports.

Also applies to non-buildings in the view (town walls, gate pillars, piers, ship, fountains, wells, signs): the same
kind of modest modular detail (coping stones, chamfered posts with bases and caps, rails, plank edges, stone courses).
