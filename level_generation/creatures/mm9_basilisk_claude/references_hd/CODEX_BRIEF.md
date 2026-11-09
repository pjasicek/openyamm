# Codex brief: HD reference views for the MM9 Basilisk (six-legged frilled lizard) (mm9_basilisk_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_basilisk_claude/references_hd/`.
Do not edit any other file, do not run builds, do not call Meshy. Use your built-in image generation tool.
Record format as in `level_generation/creatures/mm9_dfly_claude/references_hd/generation_runs.json`.

There are no native sprites for MM9. The authority is the ORIGINAL Might and Magic IX 3D model with its skin, shown
in renders made from that model.

## Inputs (attached, in order)
1. `references_hd/mm9_views_tier1.png` — renders of the ORIGINAL MM9 low-poly model with its original skin, five
   views left to right: front three-quarter from the creature's RIGHT (head toward image right), front, creature's
   LEFT side (head faces IMAGE LEFT), back, creature's RIGHT side (head faces IMAGE RIGHT). Flat grey is background,
   not creature. This is the design, anatomy, POSE, proportions and colour authority. Its faceting, blur and low
   resolution are NOT the design.
2. `references_hd/mm9_skin_tier1_x4.png` — the original 128x128 skin texture enlarged 4x, SURFACE MATERIAL AND
   COLOUR ONLY (scale pattern, mottling, stripes). Never the design or shape.
3. `references_hd/mm9_top_tier1.png` — top view of the same model (head toward image TOP), leg layout only.
4. (second run only) the selected `references_hd/00_three_quarter.png`.

## Deliverables (transparent background, unresized returns)
| File | View | Canvas |
|---|---|---|
| `00_three_quarter.png` | front three-quarter from the creature's RIGHT, camera slightly above (as input 1 view 1) | 1536x1024 landscape |
| `01_front.png` | front (head toward camera) | 1536x1024 |
| `02_back.png` | back (tail toward camera) | 1536x1024 |
| `03_left.png` | creature's LEFT side: head faces IMAGE LEFT, tail to image right (as input 1 view 3) | 1536x1024 |
| `04_right.png` | creature's RIGHT side: head faces IMAGE RIGHT, tail to image left (as input 1 view 5) | 1536x1024 |

Run 1: generate `00_three_quarter.png` only, then stop. Run 2 (separate run): generate 01–04 with the selected 00 as
an additional input so all views are the SAME creature, SAME pose, SAME proportions and colours. At most ONE corrective
regeneration per view. Write `generation_runs.json` (id, prompt, inputs with sha256, output path, selected flag,
reason, superseded runs) and, after run 2, a `selected_views_review.png` contact sheet.

## Prompt content (adapt per view)
TASK CONTEXT — FANTASY-GAME ASSET RESTORATION: faithful high-definition reconstruction of the EXISTING Might and Magic IX
"Basilisk" monster from the supplied renders of its original 3D model, as a 3D modelling/texturing reference. Not a new
design. Beautifully detailed, credible fully three-dimensional reptile with semi-realistic game materials and sharp
fine detail (fine scales, ridged skin), as if a high-quality sculpt of the original model.

Identity: a low, long, heavy-bodied lizard about the size of a large crocodile, with SIX legs:
- Body: a long thick barrel-shaped trunk, wide and slightly flattened, a low dorsal ridge of small scutes along the
  spine. Long tail tapering from the hips to a sharp point, held straight back, touching or almost touching the ground.
- Legs: SIX short sprawling lizard legs in three pairs (front pair just behind the neck, middle pair at mid-body, rear
  pair at the hips), each bent at the elbow/knee, the elbows out to the side, the body held clear of the ground. Every
  foot has five long thin splayed clawed toes (one thumb pointing backward-inward and four forward-spreading toes)
  with dark claws, flat on the ground.
- Head: a broad blunt lizard head on a short thick neck, the jaws OPEN showing a red mouth with rows of small pale
  sharp teeth, a short horn on the nose tip, two short horns above the eyes / on the crown, small red eyes.
- Frill: a large stiff neck FRILL like a frilled lizard: two broad flat angular fan plates standing up and out on
  each side of the neck behind the head (one on the left, one on the right), dark red-brown with orange-red ribbing.
- Colour: dark olive / khaki-green scaled skin with brown and rust-orange mottling and small bright green patches,
  darker brownish stripes across the back; the frill plates dark red-brown with orange ribs; claws and horns dark.
  The UNDERSIDE (belly, chest, throat, under the tail) is paler yellow-ochre / golden with transverse scale bands
  (it shows in the back and front views and when the creature dies on its back).
- Run 2 note: keep the selected 00 exactly (two frill plates per side as drawn there, its horns), only change the view.

Pose (exactly as input 1, the model's pose): standing on all six feet, body level, head forward with the mouth open,
frill raised, tail straight back. Symmetric left/right.

Camera and light: near-orthographic, even soft neutral studio light, no dramatic light, no strong cast shadows on the
body. Whole creature inside the frame with generous margins (never crop the tail tip, toes or frill), genuine
transparent background, no floor, no shadow, no text.

Do NOT: add wings, a crest of spines along the back, extra heads, extra or missing legs (exactly six), extra toes,
armour, a long snake neck; do not close the mouth; do not drop the frill; do not change the colours; do not crop.

## Per-image checks (re-run before selecting)
Exactly six legs (three pairs) with five clawed toes each, all feet on one ground line; open-mouthed head with nose
horn and crown horns; two frill plates behind the head; long pointed tail; colours as input 1; the correct side faces
the correct image side (03: head to image LEFT; 04: head to image RIGHT); true transparent background; 1536x1024;
nothing cropped.
