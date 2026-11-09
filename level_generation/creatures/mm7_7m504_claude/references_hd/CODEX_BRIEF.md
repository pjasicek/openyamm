# Codex brief: HD modelling references for the MM7 Chicken (7m504)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm7_7m504_claude/references_hd/`.
Do not edit any other file, do not run builds, do not call Meshy. Use your built-in image generation tool.

## Inputs (attached in this order)

1. `references_hd/native_views.png` — ORIGINAL native MM7 sprite standing views, enlarged 4x with nearest neighbour,
   left to right: front (head-on), front three-quarter, its right profile (facing image right), rear three-quarter,
   back. Magenta is background, not animal. Design, anatomy, proportions and colour authority (one palette, 545).
2. `references_hd/native_actions.png` — native walk frames (profile) and the death (the wings flap open, it falls on its side with the legs out).
   Anatomy evidence only.
3. `level_generation/creatures/mm7_7m504/aligned_2x/7m504sa1.png` — restored 2x three-quarter frame, SURFACE MATERIAL
   ONLY. Never sets the design.
4. (second run only) the selected `references_hd/00_three_quarter.png`.

## Deliverables

Five images in `references_hd/`, one hen each, the whole bird from beak to tail feathers and comb to toes, unresized
returns, 1536x1024 LANDSCAPE, true transparent background, no floor, no shadow, no text:

| File | View |
|---|---|
| `00_three_quarter.png` | front three-quarter from its RIGHT side (head toward image right-front), camera slightly above its back |
| `01_front.png` | front (head-on) |
| `02_back.png` | back (tail toward the camera) |
| `03_left.png` | its LEFT side, exact profile: the beak points to image LEFT |
| `04_right.png` | its RIGHT side, exact profile: the beak points to image RIGHT |

Run 1: generate `00_three_quarter.png` only, check it, at most one corrective regeneration, then stop.
Run 2 (a separate invocation): 01–04 with the selected 00 as an input so all five show the same hen, pose and
proportions. At most one corrective regeneration per view. Front and back views show the whole animal.

## Prompt content (adapt per view)

TASK CONTEXT — MM7 FANTASY-GAME ASSET RESTORATION: a faithful high-definition reconstruction of the EXISTING Might and
Magic VII farm chicken from the supplied original sprites, as a 3D modelling reference. Not a new design.
Near-orthographic camera, even soft neutral studio light (no dramatic lighting, no rim light: the light is baked into
the texture), semi-realistic game materials, a credible fully three-dimensional bird with clear feather detail.

Identity (from the native sprite): a plump WHITE domestic hen: pure white feathers all over with faint pale-grey
shading in the feather layers, a small RED single comb and small red wattles, a short yellow-orange beak, small dark
eyes, a full rounded breast, a short upturned tail of white feathers, and bare PINK-ORANGE / pale flesh-coloured
scaly legs with four thin toes each (three forward, one back).

Pose (identical in all five views, a neutral modelling pose from the native standing sprite): standing upright on
both legs, the legs straight with a clear gap between them (feet a little apart, toes spread flat), the wings FOLDED
neatly against the body (no feather tips sticking out), the neck upright and the head level looking forward, beak
closed; the tail raised behind.

Do NOT: add a rooster's big comb or long tail feathers, coloured feathers, spurs, extra legs or toes; spread or lift
the wings; change the colour (white bird, red comb, pink-orange legs); crop the comb, tail or toes.

## Per-image checks (re-run before you select a view)

Whole hen inside the frame with margins; two separated legs with four toes each, flat; white feathers; small red comb;
wings folded; short raised tail; transparent background; for 01–04 the same hen, pose and proportions as the
primary; side views: in `03_left` the beak points to image LEFT, in `04_right` to image RIGHT. Stop after one
corrective regeneration per view and record what remains.

## Records

`references_hd/generation_runs.json`: one entry per generation (id, view, prompt, input paths with sha256, output
path, selected flag, reason, superseded runs). After run 2, a contact sheet `references_hd/selected_views_review.png`.
