# FighterChain production lessons

- Inspect native equipment before adopting a family nickname. figc is described as a swordsman,
  but holds a right-hand double axe and left-hand kite shield; the sword stays sheathed at the left hip.
- Meshy's left mail sleeve and bracer were one connected component. Keep anatomical shoulder/elbow
  blending on the sleeve and a rigid forearm region on the bracer instead of weighting the whole
  component rigidly. Fit hand rest axes from the knuckles before solving both grips.
- Use native matched-pixel palette samples, but separate region hue from the monotonic luminance ramp.
  Crossed palette groups otherwise put yellow highlights into the Veteran's orange fabric.
  Body/head metal values and the collar's neutral chainmail need explicit consistency checks.
- Nearest-face normal signs alone falsely classified the open armpit/hem as a solid interior.
  Final arm/prop contact candidates also require a three-ray majority inside test. Record that method
  and its 5-cm candidate search; do not silently widen the 2-mm acceptance threshold.
- Gear drops need the actual blade/shield surface plane. PCA of the prop face provides a flat landing
  orientation; a guessed axis left the shield standing on its rim. Gate contacts after this correction.
- Populate every reused review manifest model's sha256. The viewer's remembered-pose lookup can
  match undefined against an undefined hash and silently select tier A for a tier-C URL.
- Check exported subframes as well as keyed frames. This asset differs from the authoring mesh by
  0.0233 mm on integer frames and up to 4.17 mm between them because dense floor keys export at 30 fps.
  Rig/contact/motion gates therefore ran on the reimported GLB, not only the authoring scene.
- Final LOD0 is 11,823 triangles including equipment. This is an explicit armoured-actor budget
  choice preserving hands, face and plate boundaries; it does not meet a generic 10k triangle target.

## Review round 1

Held gear needs actual shaped cutting bits, bevels, a socket and grip surface, plus the native shield face
layout—not uniform colour swatches. A dedicated 1K atlas with low-amplitude forged grain, scratches, pigment
wear, wood grain and leather seams provides surface detail without adding dense geometry. This round adds
778 triangles across both props, with 23 visible shield studs and no buried stud stems. Give bevel UVs real
area: copying the same outer and inner UVs collapses their tangent basis. Steel hue and exposure must be
consistent across tiers; native palette highlight gains produced bright white/yellow armour in game.
