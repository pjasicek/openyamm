# Codex brief: HD reference views for the MM7 rock decoration 7rock08 (dark grey crag)

Scope: image generation only. Write ONLY into
`level_generation/decorations/mm7_3d/rocks/rock08_meshy/references_hd/`.
Do not edit any other file, do not run builds, do not call Meshy.

Use your built-in image generation tool. Attached inputs, in order:
1. `native_front_x3.png`: the ORIGINAL native MM7 sprite `7rock08` (116 x 93 px), enlarged 3x with nearest
   neighbour. It is the only native view (the game shows this same front view from every side). Magenta is
   background, not part of the rock. It sets the design, shape, proportions and palette.
2. `x2_surface_only.png`: a restored 2x frame, for surface material only (fine streaked grey stone). It never sets
   the design.

## Deliverables

Five images, true transparent background, 1536 x 1024 LANDSCAPE, returned unresized:

| File | View |
|---|---|
| `00_three_quarter.png` | The primary; generate it first. The rock from the front, camera turned about 30 degrees to the rock's right and raised about 25 degrees, so the crown, the hollow and the depth are visible. |
| `01_front.png` | The front, camera slightly above the rock's mid-height, looking a little down (as the native sprite). |
| `02_back.png` | The same rock from behind (camera turned 180 degrees round it), at the same height as 01. |
| `03_left.png` | The rock's left side: the camera turned 90 degrees to the rock's left, so the rock's front faces the image's RIGHT edge. Same height as 01. |
| `04_right.png` | The rock's right side: the camera turned 90 degrees to the rock's right, so the rock's front faces the image's LEFT edge. Same height as 01. |

Run order:
- Generate 00 first and check it.
- Then generate 01–04 with the selected 00 as an additional input, so that all five show the SAME rock with the
  SAME outline and proportions, seen from four sides.
- Regenerate a failed view at most once, with one targeted correction, then stop.

Records:
- `generation_runs.json`: id, prompt, inputs with sha256, output path, selected flag, reason and superseded runs.
- `selected_views_review.png`: a contact sheet of the five selected views.

## Prompt content (adapt per view)

**Task context.** Fantasy-game asset restoration: a faithful high-definition reconstruction of the EXISTING Might and
Magic VII outdoor decoration "7rock08" from the supplied original sprite, as a 3D modelling and texturing reference.
It is not a new design.

**Framing and light.**
- ONE free-standing natural rock, centred, with generous margins.
- Near-orthographic camera, transparent background.
- No ground, no grass, no shadow, no scenery, no text.
- Even soft neutral studio light that still shows the forms. No dramatic light.
- Credible photographic stone detail.

**Identity (from the native sprite).** A single solid crag of dark charcoal-grey stone, about 1.25 times as wide as
it is tall.
- **Body:** a broad, rounded, weathered mound whose lower sides bulge outward and flare onto the ground, so the base
  is the widest part. The silhouette sides are convex and lumpy.
- **Crown:** from the upper part of the SAME stone (grown out of the mound, not separate stones placed on it) rise
  two thick, pointed, horn-like crests that lean slightly toward each other:
  - the taller crest is just right of centre and is the highest point of the rock;
  - a shorter crest stands at the front left, reaching about 85 % of the height.
- **Hollow:** between and in front of the crests, a deep, rounded, cupped hollow is scooped into the top of the
  mound. It is dark inside.
- **Behind the crests:** the top is a lower rounded lobe.
- **Ridge:** a sharp curved ridge runs from the tall crest down the right front of the mound.
- **Surface:** dense fine-grained dark grey stone (like slate or basalt) with fine parallel streaks and striations
  running diagonally across the faces, small pale specks, a few thin cracks. Matte, slightly polished by weather on
  the ridges.
- **Colour:** charcoal grey (mid grey on the lit upper faces, a faint warm olive-grey tint), darker grey on the
  sides, near-black in the hollow and crevices.

**Do NOT:**
- add moss, grass, lichen, snow, other rocks, pebbles, a base or a floor;
- make the crests separate stones or spikes;
- make it tan, brown, blue or light grey;
- make it a tall spire or a flat slab;
- crop the rock.

**Checks per image:**
- one rock, about 1.25 : 1 width to height;
- two crests of one stone with the hollow between them, the taller on the right of the front view;
- a wide flared base;
- dark charcoal grey with fine streaks;
- nothing cropped, a true transparent background;
- the same rock as the primary.
