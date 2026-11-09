# Codex brief: HD HEAD reference views for the MM6 Flying Demon (wdm)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm6_wdm_claude/references_head/`.
Do not edit any other file, do not run builds, do not call Meshy.

Why: the full-body HD views (`../references_hd/`) give the face only ~70 px, so the 3D head came out blobby
(stretched teeth, smeared eyes). These views are for a separate head-only 3D model that will be grafted onto the
existing body at the neck, so they must show the SAME head as the body references, much larger.

Use your built-in image generation, same record format as `../references_hd/generation_runs.json`.
Attached inputs:
1. `references_hd/01_front.png` — the accepted full-body HD front view: identity authority for this head (horn shape,
   crown spike, ears, eyes, mouth, skin texture and colours). Match it.
2. `references_hd/00_three_quarter.png` — the same creature, three-quarter.
3. `level_generation/creatures/mm6_wdm/references/standing.png` — ORIGINAL native five-view sheet (magenta is
   background); anatomy authority if 1/2 are ambiguous.

## Deliverables (4 images, transparent background, 1024 x 1024 square, unresized returns)
- `00_front.png` — head straight on (primary; generate first)
- `01_three_quarter.png` — front-right three-quarter (45 degrees to the creature's anatomical right)
- `02_right.png` — the creature's right profile (pure side view, 90 degrees)
- `03_back.png` — straight from behind
Generate 01–03 with 00 as an additional input so all four are the SAME head, SAME expression, SAME proportions.
Also write `generation_runs.json` (id, prompt, inputs with sha256, output path, selected flag, reason) and a
`selected_views_review.png` contact sheet. Regenerate a view if it breaks the checks below; record superseded runs.

## Prompt content (adapt per view)
TASK CONTEXT — MM6 FANTASY-GAME ASSET RESTORATION: high-definition HEAD-AND-NECK reference of the EXISTING Might and
Magic VI Flying Demon (Devil Captain), for a 3D head model. The head must be the SAME head as in inputs 1 and 2, shown
large. Not a new design.
Framing: head and neck only, like a sculpted bust WITHOUT shoulders: the neck ends in a clean horizontal cut a little
below the jaw (no collarbones, no shoulders, no shoulder spikes, no wings). Head fills about 70% of the frame height
including the horns, centred, generous transparent margins, near-orthographic camera at eye height, head level.
Transparent background, no floor, no shadow, no scenery, no text. Even soft neutral studio light that still shows form.
Beautifully detailed, credible fully three-dimensional sculpt with semi-realistic game materials, sharp fine detail.

Head identity: demonic, bestial face; deep violet-purple skin with fine dense stippled/pebbled hide; heavy brow ridge;
bright BLUE eyes, almond-shaped, glowing irises with dark pupils, set under the brow; short snout with flared nostrils;
WIDE open grinning mouth showing rows of sharp ivory teeth with longer upper and lower fangs, dark mouth interior and
gums; strong jaw; pointed bat-like ears swept outward and slightly back; TWO thick curved ivory horns rising from the
brow, curving up and slightly outward like a crescent; a small ivory spike on the crown between them. Neck thin and
sinewy, purple. Ivory horns with subtle ring texture.

Do NOT: change the expression between views, add hair, beard, jewellery, armour, extra horns, glowing effects, blood;
do not change colours (purple skin, ivory horns/teeth, blue eyes); do not crop horns or ears.

Checks per image: both horns + crown spike fully in frame; blue eyes; open mouth with distinct individual ivory teeth
and fangs; pointed ears; neck cut cleanly below the jaw with no shoulders; transparent background; same head as the
primary and as input 1.
