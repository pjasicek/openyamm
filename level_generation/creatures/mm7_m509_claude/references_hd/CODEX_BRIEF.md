# Codex brief: HD modelling references for the MM7 Dog (m509)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm7_m509_claude/references_hd/`.
Do not edit any other file, do not run builds, do not call Meshy. Use your built-in image generation tool.

## Inputs (attached in this order)

1. `references_hd/native_views.png` — ORIGINAL native MM7 sprite standing views, enlarged 4x with nearest neighbour,
   left to right: front (head-on), front three-quarter, its right profile (facing image right), rear three-quarter,
   back. Magenta is background, not animal. Design, anatomy, proportions and colour authority (one palette, 545).
2. `references_hd/native_actions.png` — native walk frames (profile) and the death (rears up, falls on its back).
   Anatomy evidence only.
3. `level_generation/creatures/mm7_m509/aligned_2x/m509sa1.png` — restored 2x three-quarter frame, SURFACE MATERIAL
   ONLY. Never sets the design.
4. (second run only) the selected `references_hd/00_three_quarter.png`.

## Deliverables

Five images in `references_hd/`, one dog each, the whole animal from nose to tail tip and ear tips to paws, unresized
returns, 1536x1024 LANDSCAPE, true transparent background, no floor, no shadow, no text:

| File | View |
|---|---|
| `00_three_quarter.png` | front three-quarter from its RIGHT side (head toward image right-front), camera slightly above its back |
| `01_front.png` | front (head-on) |
| `02_back.png` | back (tail toward the camera) |
| `03_left.png` | its LEFT side, exact profile: the nose points to image LEFT |
| `04_right.png` | its RIGHT side, exact profile: the nose points to image RIGHT |

Run 1: generate `00_three_quarter.png` only, check it, at most one corrective regeneration, then stop.
Run 2 (a separate invocation): 01–04 with the selected 00 as an input so all five show the same dog, pose and
proportions. At most one corrective regeneration per view. Front and back views show the whole animal.

## Prompt content (adapt per view)

TASK CONTEXT — MM7 FANTASY-GAME ASSET RESTORATION: a faithful high-definition reconstruction of the EXISTING Might and
Magic VII town dog from the supplied original sprites, as a 3D modelling reference. Not a new design. Near-orthographic
camera, even soft neutral studio light (no dramatic lighting, no rim light: the light is baked into the texture),
semi-realistic game materials, a credible fully three-dimensional animal with clear fur detail.

Identity (from the native sprite): a lean medium-large dog of German-shepherd type: tall erect pointed ears, a long
wedge-shaped muzzle with a black nose, dark eyes, a deep chest and tucked belly, a long bushy tail hanging low with a
slight curve, straight slim legs with compact paws. Short dense coat of DARK GREY-OLIVE / charcoal fur with slightly
lighter, brownish-grey highlights on the back, flanks and legs; no markings, no collar.

Pose (identical in all five views, a neutral modelling pose from the native standing sprite): standing square on all
four legs, legs straight with clear gaps between them and between left and right, paws flat; head raised forward,
mouth closed; the tail hanging down and slightly back, clear of the hind legs.

Do NOT: add a collar, harness, saddle, extra limbs or markings; change the colour (no tan-and-black shepherd saddle, no
brown or white dog); open the mouth; crop the tail, ears or paws.

## Per-image checks (re-run before you select a view)

Whole dog inside the frame with margins; four separated straight legs with paws flat; erect pointed ears; dark
grey-olive coat; long low bushy tail; transparent background; for 01–04 the same dog, pose and proportions as the
primary; side views: in `03_left` the nose points to image LEFT, in `04_right` to image RIGHT. Stop after one
corrective regeneration per view and record what remains.

## Records

`references_hd/generation_runs.json`: one entry per generation (id, view, prompt, input paths with sha256, output
path, selected flag, reason, superseded runs). After run 2, a contact sheet `references_hd/selected_views_review.png`.
