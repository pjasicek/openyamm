# Codex brief: HD reference views for the MM9 Ewe (mm9_sheep_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_sheep_claude/references_hd/`.
Do not edit any other file, do not run builds, do not call Meshy. Use your built-in image generation tool.
Record format as in `level_generation/creatures/mm9_wolf_claude/references_hd/generation_runs.json`.

There are no native sprites for MM9. The authority is the ORIGINAL Might and Magic IX 3D model with its skin, shown
in renders made from that model.

## Inputs (attached, in order)
1. `references_hd/mm9_views_sheep1.png` — renders of the ORIGINAL MM9 low-poly sheep with its original skin
   (`sheep1.dtx`), five views left to right: front three-quarter from the sheep's RIGHT (head toward image right),
   front, the sheep's LEFT side (head faces IMAGE LEFT), back, the sheep's RIGHT side (head faces IMAGE RIGHT). Flat
   grey is background, not creature. This is the design, anatomy, POSE, proportions and colour authority. Its
   faceting, blur and low resolution are NOT the design.
2. `references_hd/mm9_skin_sheep1_x4.png` — the original 128x128 skin texture enlarged 4x, WOOL MATERIAL AND COLOUR
   ONLY (fleece tone, pale face, amber eye, tan legs, dark hooves). Never the design or shape.
3. `references_hd/mm9_top_sheep1.png` — top view of the same model (head toward image top), proportions only.
4. (second run only) the selected `references_hd/00_three_quarter.png`.

## Deliverables (transparent background, unresized returns)
| File | View | Canvas |
|---|---|---|
| `00_three_quarter.png` | front three-quarter from the sheep's RIGHT, camera slightly above (as input 1 view 1) | 1536x1024 landscape |
| `01_front.png` | front (head toward the camera) | 1536x1024 |
| `02_back.png` | back (tail toward the camera) | 1536x1024 |
| `03_left.png` | the sheep's LEFT side: head faces IMAGE LEFT (as input 1 view 3) | 1536x1024 |
| `04_right.png` | the sheep's RIGHT side: head faces IMAGE RIGHT (as input 1 view 5) | 1536x1024 |

Run 1: generate `00_three_quarter.png` only, then stop. Run 2 (separate run): generate 01–04 with the selected 00 as
an additional input so all views are the SAME sheep, SAME pose, SAME proportions and colours. At most ONE corrective
regeneration per view. Write `generation_runs.json` (id, prompt, inputs with sha256, output path, selected flag,
reason, superseded runs) and, after run 2, a `selected_views_review.png` contact sheet.

## Prompt content (adapt per view)
TASK CONTEXT — FANTASY-GAME ASSET RESTORATION: faithful high-definition reconstruction of the EXISTING Might and Magic IX
"Ewe" (a farm sheep) from the supplied renders of its original 3D model, as a 3D modelling/texturing reference. Not a
new design. A beautifully detailed, credible, fully three-dimensional domestic sheep with semi-realistic game
materials and sharp fine wool detail, as if a high-quality sculpt of the original model.

Identity: a plump domestic ewe, no horns.
- Body: a large rounded barrel of thick fleece, deep and long, with a fairly flat back line (as input 1); the fleece
  covers the body, the neck and the top of the legs down to about the elbows and knees.
- Fleece: warm cream / light beige-grey (as input 2), slightly paler and whiter on the chest and belly. Dense, compact,
  finely crimped wool with small soft curls; the wool forms ONE solid closed surface with a clean silhouette, no loose
  strands, no fluffy wisps sticking out, no separate tufts floating off the body.
- Head: a woolless, smooth-haired face in pale cream-buff (as input 1/2), a gently convex sheep profile tapering to a
  soft muzzle with small dark nostrils and a closed mouth; small amber eyes with dark horizontal pupils, set on the
  sides of the head. Two ears that stick out SIDEWAYS, nearly horizontal and slightly drooping (as input 1), pale
  outside with a slightly darker, pinkish-grey inside.
- Legs: four slim straight legs with short tan-cream hair below the fleece, and small dark grey-brown cloven hooves.
- Tail: a short, thin, woolly tail hanging down from the rump (as input 1 back view), not docked to nothing and not
  long.

Pose (exactly as input 1, the model's bind pose): standing square on all four legs, legs straight and separated, all
four hooves visible and flat on one level, the neck held forward and the head level, looking straight ahead, the ears
held out to the sides, the tail hanging down. Symmetric left/right.

Camera and light: near-orthographic, even soft neutral studio light, no dramatic light, no strong cast shadows on the
body (Meshy bakes light into the colours). The whole sheep inside the frame with generous margins (never crop ears,
tail or hooves), genuine transparent background, no floor, no shadow, no text.

Do NOT: add horns, a bell, a collar, paint marks, ear tags or a saddle; do not make the face dark or black (this is the
pale-faced ewe); do not open the mouth; do not make the fleece shaggy, stringy or matted; do not change the colours or
proportions (no lamb, no ram, no goat); do not crop.

## Per-image checks (re-run before selecting)
One head with a pale smooth face, closed mouth, two amber eyes and two sideways ears; no horns; exactly four legs, all
four hooves visible on the same level; one short hanging tail; a cream fleece body with a clean solid silhouette; the
correct side faces the correct image side (03: head to image LEFT; 04: head to image RIGHT); true transparent
background; 1536x1024; nothing cropped.
