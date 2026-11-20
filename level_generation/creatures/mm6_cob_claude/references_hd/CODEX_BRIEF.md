# Codex brief: HD reference views for the MM6 Cobra (cob)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm6_cob_claude/references_hd/`.
Do not edit any other file, do not run builds, do not call Meshy.

Use your built-in image generation, with the prompt style and record format of
`level_generation/creatures/mm6_wdm_claude/references_hd/generation_runs.json`. Attached inputs:
1. `level_generation/creatures/mm6_cob/references/standing.png` — ORIGINAL native five-view sheet (front, front
   three-quarter, profile, rear three-quarter, back; magenta is background, not creature). Design/anatomy/palette
   authority. The profile (top middle) shows the target pose.
2. `level_generation/creatures/mm6_cob/aligned_2x/cobwalc0.png` — restored 2x profile, for surface material only.

## Deliverables (5 images, transparent background, 1536 x 1024 landscape, unresized returns)
- `00_three_quarter.png` — front-right three-quarter (primary; generate first)
- `01_front.png`, `02_back.png`, `03_left.png` (creature's left side), `04_right.png`
Generate 01–04 with 00 as an additional input so all five are the SAME snake, SAME pose, SAME proportions.
Also write `generation_runs.json` (id, prompt, inputs with sha256, output path, selected flag, reason) and a
`selected_views_review.png` contact sheet. Regenerate a view if it breaks the checks below; record superseded runs.

## Prompt content (adapt per view)
TASK CONTEXT — MM6 FANTASY-GAME ASSET RESTORATION: faithful high-definition reconstruction of the EXISTING Might and
Magic VI Cobra from the supplied original sprites, as a 3D modelling reference. Not a new design.
Use case: faithful 3D modelling reference. ONE complete snake, head to tail tip, centred, generous margins,
near-orthographic camera at the height of the raised hood, transparent background, no floor, no shadow, no scenery,
no text. Even soft neutral studio light that still shows form. Credible fully three-dimensional sculpt with
semi-realistic game materials, sharp fine detail.

Identity (from the native sprites): a large cobra. Body thick and muscular in the middle, tapering to a long thin
pointed tail. Dorsal colour dark blue-grey / slate teal with fine, dense, clearly separated overlapping scales; a few
pale grey-white transverse bands spaced along the back and tail. Ventral side: pale grey-green broad belly scutes in
horizontal bands, visible on the front of the raised neck from below the head down to the ground. Hood: wide, flat,
spread like a shield, pale grey-green on the FRONT face (belly side) with scute bands, dark blue-grey on the BACK face
with a bold pale cream-white SPECTACLE marking (two connected rings / a V-shaped spectacle, exactly as on the native
back view). Head: broad, flat, wedge-shaped, dark blue-grey with large smooth head plates, small dark eyes with a
glint, mouth slightly open showing two curved ivory fangs in the upper jaw and a dark mouth interior.

Pose (identical in all five views, the native profile pose): the rear two-thirds of the body lie on the ground in ONE
STRAIGHT LINE directly behind the snake (no curves, no coils, no loops), tail tip at the far end; the front third
rises VERTICALLY from the ground in a smooth bend, neck upright, head at the top tilted forward and level, looking
straight ahead; hood fully spread and facing forward (front face toward the viewer in the front view). Nothing
overlaps: the raised neck is clearly separate from the ground body.

Do NOT: coil the body, curve the ground part, add a rattle, frills, horns, legs, wings, extra heads, glowing effects,
blood, a forked tongue; do not change colours (slate blue-grey back, pale grey-green belly and hood front, cream
spectacle on the hood back, pale bands, ivory fangs); do not crop the tail tip.

Checks per image: whole snake including the tail tip inside the frame; straight ground body; raised vertical front
third; spread hood; spectacle marking on the hood back (visible in back and three-quarter views where the back
shows); pale belly scutes on the neck front; two fangs; transparent background; same pose/proportions as the
primary.
