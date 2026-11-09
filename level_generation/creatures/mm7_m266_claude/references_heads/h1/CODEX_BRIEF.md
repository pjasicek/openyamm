# Codex brief: HD HEAD masters, head 1 of the MM7 Hydra (m266)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm7_m266_claude/references_heads/h1/`.
Do not edit any other file, do not run builds, do not call Meshy.

Why: in the full-body 3D model each of the five heads got ~3% of the mesh, so the heads came out crude. These views are
for a separate head-only 3D model of THIS head (Meshy Smart Topology from the three-quarter view, then a retexture from
front/left/back/right), grafted onto the existing neck. They must show the SAME head as the accepted full-body
references, much larger and sharper.

Use your built-in image generation, record format of `../../references_hd/generation_runs.json`. Attached inputs:
1. `../crops/h1_hd_front.png` — this head cropped from the accepted full-body HD front view (neighbouring heads may
   show at the crop edges; ignore them): identity authority (shape, crest/horns/fins, colours, materials). Match it.
2. `../crops/h1_hd_quarter.png` — the same head in the accepted full-body three-quarter view.
3. `../../references_hd/01_front.png` — the accepted full-body HD front view; this head is the OUTER RIGHT head (image left in the front view).
4. `../crops/h1_native_x2.png` — the restored native MM7 sprite head: SURFACE DETAIL ONLY.

## Deliverables (5 images, transparent background, 1254 x 1254 square, unresized returns)
- `00_three_quarter.png` — front-right three-quarter: camera orbited 45 degrees to the head's anatomical right and
  slightly above eye level (primary; generate first)
- `01_front.png` — straight on (snout toward the camera)
- `02_back.png` — straight from behind
- `03_left.png` — pure profile seen from the creature's LEFT side: the snout points to SCREEN-LEFT
- `04_right.png` — pure profile seen from the creature's RIGHT side: the snout points to SCREEN-RIGHT
Generate 01–04 with your selected 00 as an additional input so all five are the SAME head, SAME expression, SAME
proportions. At most one corrective regeneration per view. Also write `generation_runs.json` (id, prompt, inputs with
sha256, output path, selected flag, reason) and a `selected_views_review.png` contact sheet.

## Prompt content (adapt per view)
TASK CONTEXT — MM7 FANTASY-GAME ASSET RESTORATION: high-definition HEAD-AND-NECK reference of one head of the EXISTING
Might and Magic VII five-headed Hydra, for a 3D head model. The head must be the SAME head as in input 1, shown large.
Not a new design.
Framing and pose: one head on a short piece of upright serpent neck, like a sculpted bust: the snout points straight
FORWARD and LEVEL (mouth line horizontal), the head sits on top of the neck the way a rearing serpent's head sits on its
raised neck; the neck section rises from below and slightly behind the skull and ends in a clean horizontal cut about
one head-length below the jaw. Head plus crest/horns/fins fill about 70% of the frame, centred, generous transparent
margins, near-orthographic camera. Transparent background, no floor, no shadow, no scenery, no text. Even soft neutral
studio light that still shows form (no strong cast shadows, no coloured rim light). Credible, fully three-dimensional
sculpt with semi-realistic game materials and sharp fine detail (individual scales, teeth, eye ridges).

Head identity: dark blue head with fine scales, TWO LARGE swept-back ribbed fins/crests rising above and behind the skull (dark blue ribs with bright blue-cyan membrane between them, like bat-wing frills), a pair of curved ivory horns on top and smaller ivory spikes at the cheeks, orange-red eyes under heavy brows, the mouth wide open with a bright red interior and rows of ivory fangs. Neck section: dark blue scales on the back and sides, pale silver segmented belly plates on its front.

Do NOT: change the expression or the mouth opening between views, add a second head, a body, shoulders, legs, wings,
glow, blood, effects or text; do not crop horns, fins, crest spikes or the neck; do not change colours.
Checks per image: whole head with every horn/fin/spike inside the frame; level snout; mouth open with distinct
individual ivory teeth; both eyes visible in front and three-quarter views; clean neck cut; transparent background
(genuine RGBA, no painted checkerboard or matte); same head as the primary and as input 1.
