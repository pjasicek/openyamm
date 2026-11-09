# Codex brief: HD reference views for the MM9 Jellyspore (floating spore jellyfish) (mm9_jelly_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_jelly_claude/references_hd/`.
Do not edit any other file, do not run builds, do not call Meshy. Use your built-in image generation tool.
Record format as in `level_generation/creatures/mm9_lobber_claude/references_hd/generation_runs.json`.

There are no native sprites for MM9. The authority is the ORIGINAL Might and Magic IX 3D model with its skin, shown
in renders made from that model.

## Inputs (attached, in order)
1. `references_hd/mm9_views_tier1.png` — renders of the ORIGINAL MM9 low-poly model with its original skin, five
   views left to right: front three-quarter (camera slightly above), front, left side, back, right side. The creature
   is radially symmetric, so the views look almost the same. Flat grey is background, not creature. This is the
   design, anatomy, POSE, proportions and colour authority. Its faceting, blur and low resolution are NOT the design.
2. `references_hd/mm9_skin_tier1_x4.png` — the original 256x256 skin texture enlarged 4x, SURFACE MATERIAL AND
   COLOUR ONLY (streaked green jelly pattern). Never the design or shape.
3. `references_hd/mm9_top_tier1.png` — top view of the bell (octagonal outline), layout only.
4. (second run only) the selected `references_hd/00_three_quarter.png`.

## Deliverables (transparent background, unresized returns)
| File | View | Canvas |
|---|---|---|
| `00_three_quarter.png` | front three-quarter, camera slightly above (as input 1 view 1) | 1024x1536 portrait |
| `01_front.png` | front, camera level | 1024x1536 |
| `02_back.png` | back, camera level | 1024x1536 |
| `03_left.png` | left side, camera level | 1024x1536 |
| `04_right.png` | right side, camera level | 1024x1536 |

Run 1: generate `00_three_quarter.png` only, then stop. Run 2 (separate run): generate 01–04 with the selected 00 as
an additional input so all views are the SAME creature, SAME pose, SAME proportions and colours. At most ONE
corrective regeneration per view. Write `generation_runs.json` (id, prompt, inputs with sha256, output path, selected
flag, reason, superseded runs) and, after run 2, a `selected_views_review.png` contact sheet.

## Prompt content (adapt per view)
TASK CONTEXT — FANTASY-GAME ASSET RESTORATION: faithful high-definition reconstruction of the EXISTING Might and Magic
IX "Jellyspore" monster from the supplied renders of its original 3D model, as a 3D modelling/texturing reference. Not
a new design. Beautifully detailed, credible fully three-dimensional organic creature with semi-realistic game
materials and sharp fine detail (glossy translucent-looking jelly with fine streaks and veins), as if a high-quality
sculpt of the original model. Render it OPAQUE (no see-through parts): the jelly look comes from the colour and gloss.

Identity: a floating jellyfish-like spore creature, radially symmetric, about the height of a person, top to bottom:
- Bell: a wide low dome, octagonal in outline (eight broad facets, slightly rounded), flaring out to a sharp rim,
  about twice as wide as it is tall. Saturated teal-green jelly with fine pale-green vertical streaks running down
  from the crown, a darker band near the rim; the underside of the bell is dark. No eyes, no face, no mouth.
- Neck: a short thick cylindrical stem hanging from the centre of the bell's underside, then a small diamond-shaped
  collar knot where the legs attach.
- FOUR thin jointed legs at 90 degrees to each other (front, back, left, right) spread out from the collar: each goes
  out and slightly down, bends down at a knee, then hangs straight down to a sharp pointed tip, like a spider leg or
  a tent pole. Yellow-green to lime with a fine scaly pattern, darker tips.
- Central stinger: ONE long thin straight tail hanging straight down from the collar, longer than the legs (about
  half the creature's total height), with a small diamond node a third of the way down, from which THREE short thin
  spikes point down and outward around it; the tail ends in a long sharp needle point. Teal-green, darker at the tip.

Pose (exactly as input 1, the model's pose): floating upright, bell on top, the four legs spread evenly and clear of
the stinger and of each other, the stinger vertical. Symmetric.

Camera and light: near-orthographic, even soft neutral studio light, no dramatic light, no strong cast shadows. Whole
creature inside the frame with generous margins (never crop the bell rim, leg tips or the stinger tip), genuine
transparent background, no floor, no shadow, no water, no bubbles, no text.

Do NOT: add eyes, a face, a mouth, frilly or many tentacles, extra legs (exactly four plus the one stinger), oral arms,
glow effects, water or bubbles; do not make it see-through; do not round the bell into a smooth hemisphere; do not
change the colours; do not crop.

## Per-image checks (re-run before selecting)
Octagonal low bell on top with a sharp rim; short neck and collar; exactly four jointed legs, each bent once and
hanging to a point; exactly one long central stinger with three short spikes at a node; colours as input 1; opaque;
true transparent background; 1024x1536; nothing cropped.
