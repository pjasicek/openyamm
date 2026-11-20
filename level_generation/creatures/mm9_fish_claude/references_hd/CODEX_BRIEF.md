# Codex brief: HD reference views for the MM9 fish (mm9_fish_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_fish_claude/references_hd/`.
Do not edit any other file, do not run builds, do not call Meshy. Use your built-in image generation tool.
Record format as in `level_generation/creatures/mm9_wolf_claude/references_hd/generation_runs.json`.

There are no native sprites for MM9. The authority is the ORIGINAL Might and Magic IX 3D fish model with its skin,
shown in renders made from that model.

## Inputs (attached, in order)
1. `references_hd/mm9_views_tier1.png` — renders of the ORIGINAL MM9 low-poly fish with its original skin, five views
   left to right: front three-quarter from the fish's RIGHT (head toward image right), front, the fish's LEFT side
   (head faces IMAGE LEFT), back, the fish's RIGHT side (head faces IMAGE RIGHT). Flat grey is background, not
   creature. This is the design, anatomy, POSE, proportions and colour authority. Its faceting, blur and low
   resolution are NOT the design.
2. `references_hd/mm9_skin_x4.png` — the original 128x128 skin texture enlarged 4x, SCALE PATTERN, FIN RAYS AND
   COLOUR ONLY. Never the design or shape. Grey around it is background.
3. `references_hd/mm9_top_tier1.png` — top view of the same model (head toward image top), proportions only.
4. (second run only) the selected `references_hd/00_three_quarter.png`.

## Deliverables (transparent background, unresized returns)
| File | View | Canvas |
|---|---|---|
| `00_three_quarter.png` | front three-quarter from the fish's RIGHT, camera slightly above (as input 1 view 1) | 1536x1024 landscape |
| `01_front.png` | front (head toward the camera) | 1536x1024 |
| `02_back.png` | back (tail toward the camera) | 1536x1024 |
| `03_left.png` | the fish's LEFT side: head faces IMAGE LEFT (as input 1 view 3) | 1536x1024 |
| `04_right.png` | the fish's RIGHT side: head faces IMAGE RIGHT (as input 1 view 5) | 1536x1024 |

Run 1: generate `00_three_quarter.png` only, then stop. Run 2 (separate run): generate 01–04 with the selected 00 as
an additional input so all views are the SAME fish, SAME pose, SAME proportions and colours. The two side views
(03, 04) matter most: they must be TRUE side profiles (camera exactly perpendicular to the fish, the body seen flat,
every fin spread flat and fully visible). At most ONE corrective regeneration per view. Write
`generation_runs.json` (id, prompt, inputs with sha256, output path, selected flag, reason, superseded runs) and,
after run 2, a `selected_views_review.png` contact sheet.

## Prompt content (adapt per view)
TASK CONTEXT — FANTASY-GAME ASSET RESTORATION: faithful high-definition reconstruction of the EXISTING Might and Magic IX
"Fish" from the supplied renders of its original 3D model, as a 3D modelling/texturing reference. Not a new design. A
beautifully detailed, credible, fully three-dimensional freshwater fish (trout-like body, perch-like spiny dorsal
fin) with semi-realistic game materials and sharp fine scale detail, as if a high-quality sculpt of the original model.

Identity:
- Body: deep, laterally flattened, spindle-shaped body, deepest just behind the head, tapering to a narrow tail stalk;
  head with a slightly open mouth (lower jaw), a large round golden-amber eye with a black pupil, a clear gill cover.
- Colour (as inputs 1 and 2): olive-brown to bronze back densely speckled with small dark spots; a soft pink-salmon
  band along the flank; silvery white-pink belly and throat; fins bronze-olive with darker rays.
- Fins (all thin, translucent-looking membranes with clear fine rays and slightly ragged rayed edges, as in input 2):
  ONE long spiny dorsal fin along most of the back (tall at the front, as input 1); a forked/notched tail fin
  standing vertically; an anal fin under the rear belly; two pectoral fins behind the gills angled out to the sides;
  two small pelvic fins under the chest pointing down.

Pose (exactly as input 1, the model's bind pose): body straight (no bend), level, all fins spread open and fully
visible, mouth slightly open. Symmetric left/right.

Camera and light: near-orthographic, even soft neutral studio light, no dramatic light, no strong cast shadows on the
body, no specular hot spots. The whole fish inside the frame with generous margins (never crop the tail fin or fin
tips), genuine transparent background (the background must show between the fin rays where the fin edge is ragged),
no water, no bubbles, no floor, no shadow, no text.

Do NOT: make it a cartoon fish; add teeth, barbels, whiskers, extra fins or scales in other colours; bend the body;
fold the fins against the body; change the colours; crop.

## Per-image checks (re-run before selecting)
One fish, body straight; one long spiny dorsal fin, one vertical tail fin, one anal fin, two pectoral and two pelvic
fins (as many as visible from the view); golden eye; speckled olive-bronze back, pink flank band, pale belly; the
correct side faces the correct image side (03: head to image LEFT; 04: head to image RIGHT); true transparent
background; 1536x1024; nothing cropped.
