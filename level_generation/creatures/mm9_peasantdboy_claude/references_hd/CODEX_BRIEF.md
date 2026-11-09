# Codex brief: HD reference views for the MM9 dwarf boy PeasantDboy1 (skin DWARFBOY1) (mm9_peasantdboy_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_peasantdboy_claude/references_hd/`. Do not
edit any other file, do not run builds, do not call Meshy. Use your built-in image generation tool. There are no native
sprites for MM9: the authority is the ORIGINAL MM9 3D model with its skin, shown in renders made from that model.

## Inputs (attached, in order)
1. `references_hd/mm9_views_a.png` — renders of the ORIGINAL Might and Magic IX low-poly model with its original skin,
   five views left to right: front three-quarter (he faces image right and toward the viewer), front, side facing
   IMAGE LEFT, back, side facing IMAGE RIGHT. Flat grey is background. This is the design, costume, POSE, proportions
   and colour authority. Its faceting, blur and low resolution are NOT the design.
2. `references_hd/mm9_head_views_a.png` — close renders of the same model's head (front, profile facing left,
   three-quarter, profile facing right, back): the face and hair authority.
3. `references_hd/mm9_skin_x4_a.png` — the original 128x128 skin texture enlarged, SURFACE MATERIAL AND COLOUR ONLY
   (face painting, brown hair, rust-orange patterned wool tunic with blue-and-cream key-pattern embroidered bands, cream
   linen shirt with red-brown lacing, dark brown checked wool trousers, brown leather boots). Never the design or shape.
4. (run 2 only) the selected `references_hd/00_three_quarter.png`.

## Deliverables (true transparent background, unresized returns, 1536x1024 landscape so the spread arms fit)
| File | View |
|---|---|
| `00_three_quarter.png` | front three-quarter, he faces image right and toward the viewer, camera at chest height slightly above (as input 1 view 1) |
| `01_front.png` | straight front; the character's RIGHT arm on IMAGE LEFT |
| `02_back.png` | straight back; the character's RIGHT arm on IMAGE RIGHT |
| `03_left.png` | pure 90-degree profile of the character's LEFT side: faces IMAGE LEFT |
| `04_right.png` | pure 90-degree profile of the character's RIGHT side: faces IMAGE RIGHT |

Run 1: generate `00_three_quarter.png` only, then stop. Run 2 (separate run): generate 01–04 with the selected 00 as an
additional input so all views are the SAME boy, SAME pose, SAME proportions and colours. At most ONE corrective
regeneration per view; then select the better and note any residual fault. Keep raw returns in `raw/`.
Write `generation_runs.json` (id, prompt, inputs with sha256, output path, selected flag, reason, superseded runs)
and, after run 2, a `selected_views_review.png` contact sheet of the five selected views.

## Common prompt content (adapt per view)
TASK CONTEXT — FANTASY-GAME ASSET RESTORATION: faithful high-definition reconstruction of an EXISTING Might and
Magic IX character from the supplied renders of its original 3D model, as a 3D modelling and texturing reference.
Not a new design. A credible, fully three-dimensional DWARF CHILD with semi-realistic game materials and sharp fine
detail (skin, face, hair strands, wool weave, embroidery, linen, leather grain, stitching), as if a high-quality sculpt
of the original model. ONE complete figure from the top of the head to the soles, centred, generous margins, never
cropped.

Pose (identical in all views, the model's bind pose as in input 1): standing upright; the arms held out to the sides
as in input 1: the arms straight and about 25 degrees below horizontal (the hands well above hip height, NOT a 35-45
degree A-pose), clear air between the arms and the body; hands open and flat, palms facing DOWN, the four fingers
straight and close together with small gaps, the thumb separated; legs straight and slightly apart with a clear gap
between them, feet flat. Head level, looking forward.

Camera and light: near-orthographic, even soft neutral studio light, no dramatic light, no strong cast shadows on the
body; genuine transparent background, no floor, no shadow, no text.

Per-image checks (re-run before selecting): same identity, costume and colours as inputs 1–3; stocky dwarf-child
proportions as input 1; the pose above (arms out, open flat hands with five fingers, legs apart); the correct side
faces the correct image side (03: faces IMAGE LEFT; 04: faces IMAGE RIGHT); whole figure inside the frame with margins;
true transparent background; 1536x1024.

## Identity
A medieval DWARF BOY about eight years old: short (about 1.0 m) and sturdy with a dwarf child's proportions as input 1
(a large head, a broad compact chest, short thick arms and short legs, big feet in large boots).
- Face and head (input 2): fair skin with rosy cheeks and a few faint freckles, a calm, warm, friendly face with a gentle
  closed-mouth smile, green-hazel eyes OPEN with visible irises, light brown eyebrows (one brow line each), a small
  rounded nose, a soft rounded chin; thick straight medium chestnut-brown hair in a page-boy BOB with a fringe across the
  forehead, falling straight to the jaw line at the sides and back, cut level, over the tops of the ears.
- Costume:
  - a rust-orange patterned wool TUNIC (mottled orange and brown weave) with ELBOW-length wide sleeves, reaching to
    mid-thigh, with a stand-up collar; dark blue bands with a cream key/scroll embroidered pattern edge the collar and
    yoke, the sleeve ends, a band around the chest below the yoke and the hem;
  - at the chest front an opening showing a cream linen shirt with red-brown criss-cross lacing;
  - a broad cream linen band (the shirt) around the waist above a thin brown leather belt with a small round buckle;
    the orange tunic skirt flares below the belt;
  - bare forearms with a thin dark leather band round each wrist; bare hands;
  - dark brown checked (small woven grid) wool trousers;
  - big brown leather boots to mid-calf with a wide folded-down cuff, rounded toes, flat soles.

## Do NOT
- add a beard, a weapon, tool, apron, bag, hat, cloak, cape, armour, jewellery or gloves; make him an adult, a teenager
  or a human child of normal proportions; give him a fierce, cold or sad expression; change colours (the tunic is
  rust-orange with blue bands, the hair chestnut brown); change the pose or proportions; crop; stylise as a cartoon or
  chibi.
