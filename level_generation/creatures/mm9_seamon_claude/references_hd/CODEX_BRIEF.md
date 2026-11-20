# Codex brief: HD reference views for the MM9 Sea Monster (amphibious sea predator) (mm9_seamon_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_seamon_claude/references_hd/`.
Do not edit any other file, do not run builds, do not call Meshy. Use your built-in image generation tool.
Record format as in `level_generation/creatures/mm9_lobber_claude/references_hd/generation_runs.json`.

There are no native sprites for MM9. The authority is the ORIGINAL Might and Magic IX 3D model with its skin, shown
in renders made from that model.

## Inputs (attached, in order)
1. `references_hd/mm9_views_tier1.png` — renders of the ORIGINAL MM9 low-poly model with its original skin, five
   views left to right: front three-quarter from the creature's RIGHT (camera slightly above; head at image right),
   front (face toward camera), creature's LEFT side (head faces IMAGE LEFT), back (tail toward camera), creature's
   RIGHT side (head faces IMAGE RIGHT). Flat grey is background, not creature. This is the design, anatomy, POSE,
   proportions and colour authority. Its faceting, blur and low resolution are NOT the design.
2. `references_hd/mm9_skin_tier1_x4.png` — the original 256x256 skin texture enlarged 4x, SURFACE MATERIAL AND
   COLOUR ONLY (fine blue fish scales, olive fins, eye, teeth). Never the design or shape.
3. `references_hd/mm9_top_tier1.png` — top view of the same model (head toward image TOP, tail toward image bottom),
   limb layout only.
4. (second run only) the selected `references_hd/00_three_quarter.png`.

## Deliverables (transparent background, unresized returns)
| File | View | Canvas |
|---|---|---|
| `00_three_quarter.png` | front three-quarter from the creature's RIGHT, camera slightly above (as input 1 view 1) | 1536x1024 landscape |
| `01_front.png` | front (face toward camera) | 1536x1024 |
| `02_back.png` | back (tail toward camera) | 1536x1024 |
| `03_left.png` | creature's LEFT side: head faces IMAGE LEFT (as input 1 view 3) | 1536x1024 |
| `04_right.png` | creature's RIGHT side: head faces IMAGE RIGHT (as input 1 view 5) | 1536x1024 |

Run 1: generate `00_three_quarter.png` only, then stop. Run 2 (separate run): generate 01–04 with the selected 00 as
an additional input so all views are the SAME creature, SAME pose, SAME proportions and colours. At most ONE
corrective regeneration per view. Write `generation_runs.json` (id, prompt, inputs with sha256, output path, selected
flag, reason, superseded runs) and, after run 2, a `selected_views_review.png` contact sheet.

## Prompt content (adapt per view)
TASK CONTEXT — FANTASY-GAME ASSET RESTORATION: faithful high-definition reconstruction of the EXISTING Might and Magic
IX "Sea Monster" from the supplied renders of its original 3D model, as a 3D modelling/texturing reference. Not a new
design. Beautifully detailed, credible fully three-dimensional creature with semi-realistic game materials and sharp
fine detail (fine wet fish scales, membranous fins, glossy claws), as if a high-quality sculpt of the original model.

Identity: a lean amphibious sea predator, horse-sized, body held horizontal, a long thin tail:
- Head: a blunt, deep fish-like head with a short snout, a wide gaping mouth full of long thin needle teeth (upper and
  lower), yellow-green inside the mouth, small glowing RED eyes high on the sides of the head. No horns, no whiskers.
- Body: a compact deep chest and belly just behind the head, tapering quickly into the tail; dark blue to blue-black
  fine fish scales, slightly lighter teal on the flanks, darker on the back.
- Dorsal sail: ONE tall triangular dorsal fin rising from the back above the shoulders, swept backward, with a second
  smaller pointed lobe beside it (two sharp points in total, seen as a V from the front), dark olive/black membrane
  with olive-green patches.
- Tail: very long and thin (more than half the creature's length), straight behind the body, with a row of small
  sharp dorsal spines along its first half and a forked tail fin at the end made of three long sharp dark spines with
  olive membrane between them.
- Front limbs: TWO long thin arms from the chest under the head, reaching forward and down, bent at the elbow, ending
  in hands with FOUR long hooked dark claws.
- Hind limbs: TWO long thin legs from the belly, reaching backward and down, bent at the knee, ending in large flat
  WEBBED paddle feet with THREE long sharp spike-like claws each, the webbing between them.
- All limbs are thin and sinewy, blue-scaled like the body, darker toward the claws.

Pose (exactly as input 1, the model's bind pose): body horizontal, head forward, tail straight back and level, arms
reaching forward-down with the hands spread, legs reaching back-down with the webbed feet spread; all four limbs
clear of the body, of the tail and of each other. Symmetric left/right, the mouth open.

Camera and light: near-orthographic, even soft neutral studio light, no dramatic light, no strong cast shadows on the
body. Whole creature inside the frame with generous margins (never crop the tail fin, claws or the dorsal fin tips),
genuine transparent background, no floor, no shadow, no water, no splash, no text.

Do NOT: add horns, armour, extra limbs or extra fins, a second dorsal row of large fins, legs under the tail, scales
that look like plates, water or splashes; do not close the mouth; do not shorten the tail or thicken it into a fish
tail; do not change the colours; do not crop.

## Per-image checks (re-run before selecting)
Head with open toothy mouth and red eyes facing the correct way (03: head to image LEFT; 04: head to image RIGHT);
exactly two arms with four claws each and two legs with webbed three-claw feet, all clear; one dorsal sail with two
points; long thin tail with small spines and a three-spine forked fin; colours as input 1; true transparent
background; 1536x1024; nothing cropped.
