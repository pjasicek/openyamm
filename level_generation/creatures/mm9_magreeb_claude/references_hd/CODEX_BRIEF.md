# Codex brief: HD reference views for the MM9 Magreeb (four-legged mantis monster with pincer claws) (mm9_magreeb_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_magreeb_claude/references_hd/`.
Do not edit any other file, do not run builds, do not call Meshy. Use your built-in image generation tool.
Record format as in `level_generation/creatures/mm9_dfly_claude/references_hd/generation_runs.json`.

There are no native sprites for MM9. The authority is the ORIGINAL Might and Magic IX 3D model with its skin, shown
in renders made from that model.

## Inputs (attached, in order)
1. `references_hd/mm9_views_tier1.png` — renders of the ORIGINAL MM9 low-poly model with its original skin, five
   views left to right: front three-quarter from the creature's RIGHT, front, creature's LEFT side (head and claws
   point to image LEFT), back, creature's RIGHT side (head and claws point to image RIGHT). Flat grey is background,
   not creature. This is the design, anatomy, POSE, proportions and colour authority. Its faceting, blur and low
   resolution are NOT the design.
2. `references_hd/mm9_skin_tier1_x4.png` — the original 256x256 skin texture enlarged 4x, SURFACE MATERIAL AND
   COLOUR ONLY (olive and yellow-green segmented chitin, the red eye, the teeth, the orange-red claw pattern with
   green tips). Never the design or shape.
3. `references_hd/mm9_top_tier1.png` — top view of the same model (front toward image bottom), leg and claw layout.
4. (second run only) the selected `references_hd/00_three_quarter.png`.

## Deliverables (transparent background, unresized returns)
| File | View | Canvas |
|---|---|---|
| `00_three_quarter.png` | front three-quarter from the creature's RIGHT, camera slightly above (as input 1 view 1) | 1536x1024 landscape |
| `01_front.png` | front (head and claws toward the camera) | 1536x1024 |
| `02_back.png` | back | 1536x1024 |
| `03_left.png` | creature's LEFT side: head and claws point to IMAGE LEFT (as input 1 view 3) | 1536x1024 |
| `04_right.png` | creature's RIGHT side: head and claws point to IMAGE RIGHT (as input 1 view 5) | 1536x1024 |

Run 1: generate `00_three_quarter.png` only, then stop. Run 2 (separate run): generate 01–04 with the selected 00 as
an additional input so all views are the SAME creature, SAME pose, SAME proportions and colours. At most ONE corrective
regeneration per view. Write `generation_runs.json` (id, prompt, inputs with sha256, output path, selected flag,
reason, superseded runs) and, after run 2, a `selected_views_review.png` contact sheet.

## Prompt content (adapt per view)
TASK CONTEXT — FANTASY-GAME ASSET RESTORATION: faithful high-definition reconstruction of the EXISTING Might and Magic IX
"Magreeb" monster (an insect-like mantis beast) from the supplied renders of its original 3D model, as a 3D
modelling/texturing reference. Not a new design. Beautifully detailed, credible fully three-dimensional creature with
semi-realistic game materials and sharp fine detail (segmented chitin plates, fine scales), as if a high-quality
sculpt of the original model.

Identity (exactly as input 1):
- Body: a raised, forward-tilted insect body: a plump segmented abdomen at the back, angled up, with a row of
  dark grey triangular dorsal spines/fins along its back (about eight, largest in the middle), olive and yellow-green
  chitin plates with orange-red patches on the underside; a narrower thorax in front rising to a short neck.
- Head: a small reptile-insect head on the neck, a long narrow snout with a row of small white teeth along the
  mouth, a small red eye on each side, and ONE long curved horn/crest rising up and back from the top of the head,
  banded olive and red toward its tip.
- Arms: TWO front arms (one each side of the thorax, below the head), held forward and bent, each ending in a large
  crab-like PINCER claw of two curved pointed blades, the claws orange-red with a flame-like pattern and green tips.
- Legs: FOUR long, very thin, jointed insect legs (two each side), olive green with dark joints and sharp dark tips:
  the front pair stands under the thorax, nearly vertical; the rear pair is longer and reaches far back and out.
  The legs stand on the ground on their tips.
- No wings, no tail sting, no extra legs, no antennae.

Pose (exactly as input 1, the model's pose): standing on its four legs, the body tilted with the abdomen raised, the
head up and looking forward, both pincer arms held forward, every leg and claw clear of the body and of each other.
Symmetric left/right.

Camera and light: near-orthographic, even soft neutral studio light, no dramatic light, no strong cast shadows on the
body. Whole creature inside the frame with generous margins (never crop leg tips, claw tips or the horn), genuine
transparent background, no floor, no shadow, no text.

Do NOT: add wings, antennae, extra legs (exactly four legs plus two pincer arms), a scorpion tail, armour, or a
mammal face; do not thicken the legs; do not change the colours; do not crop.

## Per-image checks (re-run before selecting)
Exactly FOUR thin legs standing on the ground plus TWO pincer arms (each a two-bladed claw); one head with a toothed
snout, red eyes and ONE curved horn; a row of dorsal spines on the raised abdomen; colours as input 1; the correct side
faces the correct image side (03: head to image LEFT; 04: head to image RIGHT); true transparent background;
1536x1024; nothing cropped.
