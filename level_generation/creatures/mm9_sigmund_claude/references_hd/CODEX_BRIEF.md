# Codex brief: HD reference views for MM9 Sigmund the Stressed (SIGMUND.abc, skin SIGMUND) (mm9_sigmund_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_sigmund_claude/references_hd/`. Do not
edit any other file, do not run builds, do not call Meshy. Use your built-in image generation tool. There are no native
sprites for MM9: the authority is the ORIGINAL MM9 3D model with its skin, shown in renders made from that model.

## Inputs (attached, in order)
1. `references_hd/mm9_views_a.png` — renders of the ORIGINAL Might and Magic IX low-poly model with its original skin,
   five views left to right: front three-quarter (he faces image right and toward the viewer), front, side facing
   IMAGE LEFT, back, side facing IMAGE RIGHT. Flat grey is background. This is the design, costume, POSE, proportions
   and colour authority. Its faceting, blur and low resolution are NOT the design.
2. `references_hd/mm9_head_views_a.png` — close renders of the same model's head (front, profile facing left,
   three-quarter, profile facing right, back): the face and hair authority.
3. `references_hd/mm9_skin_x4_a.png` — the original 256x256 skin texture enlarged, SURFACE MATERIAL AND COLOUR ONLY.
   Never the design or shape.
4. (run 2 only) the selected `references_hd/00_three_quarter.png`.

## Deliverables (true transparent background, unresized returns, 1024x1536 portrait)
| File | View |
|---|---|
| `00_three_quarter.png` | front three-quarter, he faces image right and toward the viewer, camera at chest height slightly above (as input 1 view 1) |
| `01_front.png` | straight front; the character's RIGHT arm on IMAGE LEFT |
| `02_back.png` | straight back; the character's RIGHT arm on IMAGE RIGHT |
| `03_left.png` | pure 90-degree profile of the character's LEFT side: faces IMAGE LEFT |
| `04_right.png` | pure 90-degree profile of the character's RIGHT side: faces IMAGE RIGHT |

Run 1: generate `00_three_quarter.png` only, then stop. Run 2 (separate run): generate 01–04 with the selected 00 as an
additional input so all views are the SAME man, SAME pose, SAME proportions and colours. At most ONE corrective
regeneration per view; then select the better and note any residual fault. Keep raw returns in `raw/`.
Write `generation_runs.json` (id, prompt, inputs with sha256, output path, selected flag, reason, superseded runs)
and, after run 2, a `selected_views_review.png` contact sheet of the five selected views.

## Common prompt content (adapt per view)
TASK CONTEXT — FANTASY-GAME ASSET RESTORATION: faithful high-definition reconstruction of an EXISTING Might and
Magic IX character from the supplied renders of its original 3D model, as a 3D modelling and texturing reference.
Not a new design. A credible, fully three-dimensional man with semi-realistic game materials and sharp fine detail
(skin, face, hair strands, riveted chain-mail rings, leather grain, braided straps, stitching, metal), as if a
high-quality sculpt of the original model. ONE complete figure from the top of the head to the soles, centred,
generous margins, never cropped.

Pose (identical in all views, the model's bind pose as in input 1): standing upright; the arms held out to the sides
as in input 1, straight, about 40 degrees below horizontal, clear air between the arms and the body; hands open and
flat, palms facing the thighs/down, the four fingers straight and close together with small gaps, the thumb separated;
legs straight and slightly apart with a clear gap between them, feet flat. Head level, looking forward.

Camera and light: near-orthographic, even soft neutral studio light, no dramatic light, no strong cast shadows on the
body; genuine transparent background, no floor, no shadow, no text.

Per-image checks (re-run before selecting): same identity, costume and colours as inputs 1–3; slim adult male
proportions as input 1; the pose above; the correct side faces the correct image side (03: faces IMAGE LEFT; 04: faces
IMAGE RIGHT); whole figure inside the frame with margins; true transparent background; 1024x1536.

## Identity
Sigmund, a Norse-styled jarl's man in his forties, tall (about 1.75 m) and slim.
- Face and head (input 2): fair weathered skin, a long narrow face with high cheekbones, a straight long nose, a
  firm clean-shaven chin (no beard, no moustache), pale blue-grey eyes OPEN with visible irises under slightly raised,
  drawn-together brows: a worried, careworn but kind expression (a man under strain, NOT angry), faint lines on the
  forehead and under the eyes, mouth CLOSED with relaxed natural lips. Thick wavy golden-blond hair parted in the
  middle, swept back from the forehead and falling over the ears to the shoulders, longer at the back (to the upper
  shoulder blades).
- Costume:
  - a grey steel CHAIN-MAIL hauberk (fine riveted rings) to mid-thigh with SHORT sleeves ending above the elbow; the
    sleeve ends and the hem have a dark blue cloth lining showing as a narrow edge; a short slit at the front hem;
  - round the neck a gold TORC collar: a broad ivory-and-gold collar of short pendant bars over the mail at the throat,
    with a round grey stone medallion hanging at the breastbone;
  - a dark red-brown leather belt with a row of round silver studs and thin cream-gold edges, a small round gold
    buckle at the front;
  - bare forearms, each with a long amber-brown braided leather BRACER wrapped from the wrist to below the elbow;
    bare hands;
  - dark brown close-fitting leather trousers; below the knees dark brown leather strips cross-gartered round the
    shins;
  - tan suede boots to mid-calf, rounded toes, flat soles.

## Do NOT
- add a weapon, shield, helmet, cloak, cape, gloves, beard or extra jewellery; make him young or old and frail; give
  him a fierce, angry or cold expression; change colours (grey mail, gold torc, blond hair, brown leathers, tan boots);
  change the pose or proportions; crop; stylise as a cartoon.
