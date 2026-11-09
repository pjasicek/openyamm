# MM7 Dragon v3 HD texturing masters (MM7 look on the given 3D model)

## Scope

Image generation only, with your built-in image generation tool. Write only into
`level_generation/creatures/mm7_m182_claude/references_hd_v3/`. No builds, no scripts outside this folder, no Meshy.

## Context

The game model of the Might and Magic VII Dragon (green tier, palette 183) is now an existing 3D model (an MM6 dragon
body with a new MM7 head and a new dorsal spine row). It needs a texture in the MM7 dragon's look. The five images you
make are the paint references for an automatic texturing tool that projects them onto this exact model, so each image
must show **exactly the model in the attached grey clay render of the same view, painted**. The original MM7 sprites
are the authority for colours and surface materials. The grey or magenta backgrounds of the attached images are not
part of the creature.

## Inputs (attached, in order)

1. `inputs/native_standing_views_183.png`: the original MM7 green dragon, five views (front, front three-quarter,
   right profile, rear three-quarter, back). Authority for colours and materials.
2. `inputs/native_flight_side_cycle_183.png`: original flight cycle in profile (membrane, scale and plate detail).
3. `inputs/m182sa2_183.png`: one original profile frame, larger (surface material only).
4. The clay render(s) of the model (`inputs/clay_<view>.png`): authority for the silhouette, pose, proportions and
   every part's position. Run 1 attaches `clay_00_three_quarter.png`; run 2 attaches the selected
   `00_three_quarter.png` followed by `clay_01_front.png`, `clay_02_back.png`, `clay_03_left.png`, `clay_04_right.png`.

## What to paint (green tier, from the native frames)

- **Body, neck, legs, tail top and sides:** dark forest green reptile scales with a fine darker scale pattern and
  lighter green highlights on the scale centres; matte.
- **Ventral plates:** gold-yellow segmented belly plates (transverse scutes with thin darker seams) from under the
  chin down the throat, chest and belly and along the underside of the tail.
- **Head:** dark green, finely scaled; red eyes; dark red mouth interior with small ivory teeth; the four upright
  horns ivory-white; the frill of spikes around the back of the head yellow-green to yellow.
- **Dorsal spine row** (the blades along the back of the neck, the back and the whole tail): yellow to yellow-green,
  slightly paler at the tips.
- **Wings:** membranes LIGHT GREY-GREEN (pale sage, like the native membrane), crisp and clean, with a fine
  reticulated scale pattern (small irregular cells with slightly darker borders) and a few faint warm flecks, no
  blotches, no white streaks, no blur. Wing arm and finger bones dark green; the small claws and spurs on the wing
  edge ivory.
- **Claws** on all four feet ivory.
- Even, soft studio light: no cast shadows, no strong highlights, no rim light (the light is not part of the texture).

## Silhouette rule (most important)

Paint over the clay model: keep its outline, pose, wing shape (including every scallop, finger and edge spur),
head shape and crest, spine row, legs, toes and tail exactly where they are in the clay render of the same view.
Same canvas size and the same position and scale of the creature in the frame. Do not add, remove, lengthen or
move any part. Do not redesign the wings into the native sprite's wing shape; only the colours and materials come
from the sprites.

## Deliverables

1536×1024 landscape, unresized returns, transparent background (true alpha), no floor, no shadow, no text.

| File | View | Clay guide |
|---|---|---|
| `00_three_quarter.png` | front three-quarter from slightly above (the dragon's left side and front) | `clay_00_three_quarter.png` |
| `01_front.png` | straight front | `clay_01_front.png` |
| `02_back.png` | straight back | `clay_02_back.png` |
| `03_left.png` | the dragon's LEFT side: head points to image LEFT | `clay_03_left.png` |
| `04_right.png` | the dragon's RIGHT side: head points to image RIGHT | `clay_04_right.png` |

## Procedure

- **Run 1:** generate only `00_three_quarter.png` from inputs 1–3 and `clay_00_three_quarter.png`. Check it
  (below); at most one corrective regeneration. Then stop.
- **Run 2:** generate `01`–`04`, each from the selected `00_three_quarter.png` (look and colours) plus that view's
  clay render (silhouette) and inputs 1–3. At most one corrective regeneration per view.

## Do NOT

- No colour changes: green body, gold belly plates, light grey-green membranes, dark green wing bones, ivory horns,
  claws and teeth, yellow spines, red eyes. No red, orange or blue anywhere on the body.
- No added horns, armour, rider, saddle, chains, fire, smoke, scenery, extra limbs or extra wings.
- No cropping, no ground plane, no cast shadow, no text.

## Per-image checks (re-run before selecting)

- outline matches the clay render of the same view (place both side by side: same wing tips, scallops, feet, tail
  tip, head crest, spine row at the same positions); creature inside the canvas with the same margins;
- membranes light grey-green and crisp; body dark green; belly plates gold; horns and claws ivory; spines yellow;
- transparent background (true alpha), 1536×1024; 03 head to image left, 04 head to image right.

## Records

Write `generation_runs.json` (one entry per generation: id, prompt, input file sha256 list, output path, selected
flag, reason, superseded runs) and `selected_views_review.png`, a contact sheet of the selected views next to their
clay guides.
