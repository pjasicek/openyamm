# Codex brief: HD HEAD reference views for the MM7 Medusa (mm7_m282_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm7_m282_claude/references_head/`.
Do not edit any other file, do not run builds, do not call Meshy.

Why: the full-body HD views (`../references_hd/`) give the face only ~70 px. These views texture the 3D head's own 1K
texture set (a head-only retexture of the existing head mesh), so they must show the SAME head and face as the body
references, much larger.

Use your built-in image generation, same record format as `../references_hd/generation_runs.json`. Attached inputs:
1. `references_hd/01_front.png` — the accepted full-body HD front view: identity authority for this head (face, skin,
   eyes, hair snakes, gold collar). Match it.
2. `references_hd/00_three_quarter.png` — the same medusa, three-quarter.
3. `references_hd/03_left.png` — the same medusa from her left side.
4. `references_hd/native_views.png` — ORIGINAL native MM7 sprite views (magenta is background); identity authority if
   1-3 are ambiguous.

## Deliverables (4 images, transparent background, 1254 x 1254 square or the nearest supported square, unresized)
- `00_front.png` — head straight on (primary; generate first)
- `01_three_quarter.png` — front three-quarter from her RIGHT (she faces toward image LEFT-front)
- `02_profile.png` — her LEFT profile (pure side view, she faces image LEFT)
- `03_back.png` — straight from behind
Generate 01-03 in a second step with 00 as the first input so all four are the SAME head, SAME expression, SAME
proportions, SAME hair snakes. At most one corrective regeneration per view. Also write `generation_runs.json` and a
`selected_views_review.png` contact sheet.

## Prompt content (adapt per view)
TASK CONTEXT — MM7 FANTASY-GAME ASSET RESTORATION: high-definition HEAD reference of the EXISTING Might and Magic VII
Medusa for a 3D head texture. The head must be the SAME head as in inputs 1-3, shown large. Not a new design.
Framing: a bust of the head, neck and the gold collar, cut cleanly just below the collar (no shoulders, no breastplate,
no arms, no quiver). Head fills about 65 % of the frame height, the hair snakes included and not cropped, centred,
near-orthographic camera at eye height, head level, neutral calm expression, mouth closed. Transparent background, no
floor, no shadow, no scenery, no text, no glow or halo. Even soft neutral studio light that still shows form.
Beautifully detailed, credible fully three-dimensional sculpt with semi-realistic game materials, sharp fine detail.

Head identity: a calm, fine-featured, almost mask-like female face with smooth pale BLUE-GREY / lavender-grey skin,
high cheekbones, small straight nose, small closed mouth with grey-lilac lips, glowing pale WHITE-BLUE eyes without
pupils, thin dark eyebrows. NO human hair: about 14 thick hair SNAKES grow from the scalp, olive-grey and green with
BRONZE / GOLD bands and undersides and fine scales, each ending in a small dark snake head with tiny eyes; two frame
the face on each side, the rest fall behind and beside the head. A narrow polished GOLD collar band at the base of
the neck.

Do NOT: add human hair, a crown, earrings, makeup colours, open mouth or fangs, extra snakes on the face, glowing
effects beyond the eyes, blood; do not change colours; do not crop the snakes.

Checks per image: same face and skin colour as input 1; pupil-less pale glowing eyes; snakes not hair; gold collar;
neck cut below the collar; transparent background; same head as the primary.
