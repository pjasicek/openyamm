# Codex brief: HD reference views for the MM9 half-orc townswoman PeasantHOF1 (skin PeasantHOF1a) (mm9_peasanthof_claude, design A)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_peasanthof_claude/references_hd/a/`. Do not
edit any other file, do not run builds, do not call Meshy. Use your built-in image generation tool. There are no native
sprites for MM9: the authority is the ORIGINAL MM9 3D model with its skin, shown in renders made from that model.

## Inputs (attached, in order)
1. `references_hd/mm9_views_phof1a.png` — renders of the ORIGINAL Might and Magic IX low-poly model with its original skin,
   five views left to right: front three-quarter (she faces image right and toward the viewer), front, side facing IMAGE
   LEFT, back, side facing IMAGE RIGHT. Flat grey is background. This is the design, costume, POSE, proportions and colour
   authority. Its faceting, blur and low resolution are NOT the design.
2. `references_hd/mm9_head_views_phof1a.png` — close renders of the same model's head (front, profile facing left,
   three-quarter, profile facing right, back): the face, ears and hair authority.
3. `references_hd/mm9_skin_x4_phof1a.png` — the original 256x256 skin texture enlarged 4x, SURFACE MATERIAL AND COLOUR ONLY
   (face painting, auburn hair, braids, teal-blue wool bodice with gold embroidered neckline and red front lacing, brown
   knitted shawl, cream linen sleeves, olive-brown shoulder caps, cream apron with an embroidered border, dark brown skirt,
   brown leather belt with a silver buckle, brown boots). Never the design or shape.
4. (run 2 only) the selected `references_hd/a/00_three_quarter.png`.

## Deliverables (true transparent background, unresized returns, 1536x1024 landscape so the spread arms fit)
| File | View |
|---|---|
| `00_three_quarter.png` | front three-quarter, she faces image right and toward the viewer, camera at chest height slightly above (as input 1 view 1, with BOTH arms fully inside the frame) |
| `01_front.png` | straight front; the character's RIGHT arm on IMAGE LEFT |
| `02_back.png` | straight back; the character's RIGHT arm on IMAGE RIGHT |
| `03_left.png` | pure 90-degree profile of the character's LEFT side: faces IMAGE LEFT |
| `04_right.png` | pure 90-degree profile of the character's RIGHT side: faces IMAGE RIGHT |

Run 1: generate `00_three_quarter.png` only, then stop. Run 2 (separate run): generate 01–04 with the selected 00 as an
additional input so all views are the SAME character, SAME pose, SAME proportions and colours. At most ONE corrective
regeneration per view; then select the better and note any residual fault. Keep raw returns in `raw/` (inside a/).
Write `generation_runs.json` (id, prompt, inputs with sha256, output path, selected flag, reason, superseded runs)
and, after run 2, a `selected_views_review.png` contact sheet of the five selected views. A hard-edged opaque figure with
no glow, halo or soft fringe around it.

## Common prompt content (adapt per view)
TASK CONTEXT — FANTASY-GAME ASSET RESTORATION: faithful high-definition reconstruction of an EXISTING Might and
Magic IX character from the supplied renders of its original 3D model, as a 3D modelling and texturing reference.
Not a new design. A credible, fully three-dimensional character with semi-realistic game materials and sharp fine
detail (skin, face, hair strands, wool weave, knitted shawl, linen folds, lacing, leather grain, stitching), as if a
high-quality sculpt of the original model. ONE complete figure from the top of the head to the soles, centred, generous
margins, never cropped.

Pose (identical in all views, the model's bind pose as in input 1): standing upright; the arms held out to the sides,
straight, about 35 degrees below horizontal, clear air between the arms and the body; hands open and relaxed, palms
facing DOWN, the four fingers straight and close together with small gaps, the thumb separated; legs straight and
slightly apart, feet flat. Head level, looking forward.

Camera and light: near-orthographic, even soft neutral studio light, no dramatic light, no strong cast shadows on the
body; genuine transparent background, no floor, no shadow, no text.

Per-image checks (re-run before selecting): same identity, costume and colours as inputs 1–3; the tall sturdy
proportions of input 1; the pose above (arms out ~35 degrees below horizontal, open hands with five fingers, legs apart);
the correct side faces the correct image side (03: faces IMAGE LEFT; 04: faces IMAGE RIGHT); whole figure inside the frame
with margins; true transparent background; 1536x1024.

## Identity
A HALF-ORC townswoman (commoner) about thirty, tall, sturdy and strong: broad shoulders, strong arms, a full bust, a
solid waist, a slightly large head (proportions exactly as input 1; the skirt ends just below the knee and the boots
reach up the calf).
- Face and head (input 2): warm light skin with a faint natural flush, a broad friendly face, a short straight slightly
  broad nose, grey-blue eyes OPEN with visible irises, one fine eyebrow line each, natural soft lips (not lipstick).
  Mouth CLOSED in a calm, warm, faint smile; two SMALL ivory lower tusks (the lower canines) rise from the lower jaw and
  show just over the upper lip near the mouth corners, short and neat. Expression WARM and gentle: never fierce, snarling,
  cold, staring or sad.
- Ears: pointed half-orc ears, a little longer than human and pointing up and back, skin-coloured, standing out of the
  hair at the sides of the head (as input 2).
- Hair: thick auburn / chestnut-red hair, a short straight fringe across the forehead, the rest smoothly drawn back over
  the head in a close rounded volume; two plaited braids hang from behind the ears in FRONT of the shoulders down to the
  upper chest, ending in a small tie; a third braid hangs down the middle of the back to the shoulder blades. No loose
  flyaway strands.
- Costume (input 1 / 3):
  - a fitted teal-blue wool bodice with a scooped neckline edged in a narrow gold embroidered border, laced up the centre
    front with a red cord over a white chemise;
  - a brown knitted shawl over both shoulders, crossed and knotted in front of the chest, its ends hanging to the waist;
  - short sleeves: olive-brown cloth caps on the shoulders over cream linen sleeves that end just below the elbow with a
    narrow embroidered band; the forearms are BARE, with a thin brown cord bracelet at each wrist;
  - a brown leather belt with a small silver buckle at the waist;
  - a knee-length dark brown skirt with soft vertical folds and, over it, a cream linen apron to just above the hem with
    an embroidered border near its bottom, lying FLAT and close against the skirt;
  - brown leather calf boots with turned-down cuffs and a small gold clasp, flat soles.

## Do NOT
- add a hood, hat, headscarf, cloak, belt pouch, weapon, tool, basket, jewellery beyond the wrist cords, or gloves; give
  her long sleeves; let the apron or skirt flare away from the body; big boar tusks or an orc snout; green skin; loose hair
  strands; change colours (the bodice is teal-blue, the shawl and skirt brown, sleeves and apron cream, the hair auburn);
  change the pose or proportions; crop; stylise as a cartoon; a fierce, cold, staring or sad expression; an open mouth.
