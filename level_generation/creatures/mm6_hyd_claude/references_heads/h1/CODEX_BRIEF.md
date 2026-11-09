# Codex brief: HD HEAD masters, head 1 (OLIVE) of the MM6 Hydra (hyd)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm6_hyd_claude/references_heads/h1/`.
Do not edit any other file, do not run builds, do not call Meshy.

Why: in the full-body model each of the five heads got ~3% of the mesh and ~150 reference pixels, so the heads came
out crude and blurry. These views are for a separate head-only 3D model of THIS head (Meshy Smart Topology from the
three-quarter view, then a retexture from front/left/back/right), grafted onto the existing neck. They must show the
SAME head as the accepted full-body references, much larger and sharper.

Use your built-in image generation, record format of `../../references_hd/generation_runs.json`. Attached inputs:
1. `../crops/h1_hd_front.png` — this head cropped from the accepted full-body HD front view: identity authority
   (shape, crest/horns/fins, colours, materials). Match it.
2. `../../references_hd/00_three_quarter.png` — the accepted full-body HD three-quarter view; this head is the OUTERMOST LEFT head in the front view (lowest, left).
3. `../crops/h1_native_front.png` — the ORIGINAL MM6 sprite head (enlarged pixels; palette authority only).
4. `../../../mm6_hyd/references/standing.png` — ORIGINAL native five-view sheet (magenta is background, not creature);
   anatomy authority if 1 and 2 are ambiguous.

## Deliverables (5 images, transparent background, 1254 x 1254 square, unresized returns)
- `00_three_quarter.png` — front-right three-quarter: camera orbited 45 degrees to the head's anatomical right and
  slightly above eye level (primary; generate first)
- `01_front.png` — straight on (snout toward the camera)
- `02_back.png` — straight from behind
- `03_left.png` — pure profile seen from the creature's LEFT side: the snout points to SCREEN-LEFT
- `04_right.png` — pure profile seen from the creature's RIGHT side: the snout points to SCREEN-RIGHT
Generate 01–04 with 00 as an additional input so all five are the SAME head, SAME expression, SAME proportions.
Also write `generation_runs.json` (id, prompt, inputs with sha256, output path, selected flag, reason) and a
`selected_views_review.png` contact sheet. Regenerate a view that breaks the checks; record superseded runs.

## Prompt content (adapt per view)
TASK CONTEXT — MM6 FANTASY-GAME ASSET RESTORATION: high-definition HEAD-AND-NECK reference of one head of the EXISTING
Might and Magic VI five-headed Hydra, for a 3D head model. The head must be the SAME head as in input 1, shown large.
Not a new design.
Framing and pose: one head on a short piece of upright serpent neck, like a sculpted bust: the snout points straight
FORWARD and LEVEL (mouth line horizontal), the head sits on top of the neck the way a rearing serpent's head sits on
its raised neck; the neck section rises from below and slightly behind the skull and ends in a clean horizontal cut
about one head-length below the jaw. Head plus crest/horns/fins fill about 70% of the frame, centred, generous
transparent margins, near-orthographic camera. Transparent background, no floor, no shadow, no scenery, no text. Even
soft neutral studio light that still shows form (no strong cast shadows, no coloured rim light). Credible, fully
three-dimensional sculpt with semi-realistic game materials and sharp fine detail (individual scales, teeth, eye
ridges).

Head identity: olive yellow-green head with fine pebbled scales, a ring of short brown-orange horn spikes round the back and top of the skull, bright yellow eyes with dark slit pupils under heavy brows, an open mouth with a dark red interior, rows of small ivory fangs with longer upper fangs, and two long thin golden barbels (whisker tendrils) hanging down from the chin. The neck section: dark green scales on the back and sides, pale grey-white horizontal belly
rings on its front, like the rest of the hydra.

Do NOT: change the expression or the mouth opening between views, add a second head, a body, shoulders, legs, wings,
glow, blood, effects or text; do not crop horns, fins, crest spikes or barbels; do not change colours.
Checks per image: whole head with every horn/fin/spike inside the frame; level snout; mouth open with distinct
individual ivory teeth; both yellow eyes visible in front and three-quarter views; clean neck cut; transparent
background (genuine RGBA, no painted checkerboard or matte); same head as the primary and as input 1.
