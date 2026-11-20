# Codex brief: HD reference views for the MM9 elf townsman PeasantM1d (skin PeasantM1c) (mm9_peasantm1d_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_peasantm1d_claude/references_hd/`. Do not
edit any other file, do not run builds, do not call Meshy. Use your built-in image generation tool. There are no native
sprites for MM9: the authority is the ORIGINAL MM9 3D model with its skin, shown in renders made from that model.

## Inputs (attached, in order)
1. `references_hd/mm9_views_c.png` — renders of the ORIGINAL Might and Magic IX low-poly model with its original skin,
   five views left to right: front three-quarter from the character's RIGHT (he faces image right and toward the
   viewer), front, character's LEFT side (faces IMAGE LEFT), back, character's RIGHT side (faces IMAGE RIGHT). Flat
   grey is background. This is the design, costume, POSE, proportions and colour authority. Its faceting, blur and low
   resolution are NOT the design.
2. `references_hd/mm9_head_views_c.png` — close renders of the same model's head (front, left profile, three-quarter,
   right profile, back): the face, hair and ear authority.
3. `references_hd/mm9_skin_x4_c.png` — the original 256x256 skin texture enlarged 4x, SURFACE MATERIAL AND COLOUR ONLY
   (face painting, hair, fabric, belt, boots). Never the design or shape.
4. (run 2 only) the selected `references_hd/00_three_quarter.png`.

## Deliverables (true transparent background, unresized returns, 1536x1024 landscape so the spread arms fit)
| File | View |
|---|---|
| `00_three_quarter.png` | front three-quarter from the character's RIGHT, camera at chest height slightly above (as input 1 view 1) |
| `01_front.png` | straight front; the character's RIGHT arm on IMAGE LEFT |
| `02_back.png` | straight back; the character's RIGHT arm on IMAGE RIGHT |
| `03_left.png` | pure 90-degree profile of the character's LEFT side: faces IMAGE LEFT |
| `04_right.png` | pure 90-degree profile of the character's RIGHT side: faces IMAGE RIGHT |

Run 1: generate `00_three_quarter.png` only, then stop. Run 2 (separate run): generate 01–04 with the selected 00 as
an additional input so all views are the SAME character, SAME pose, SAME proportions and colours. At most ONE
corrective regeneration per view; then select the better and note any residual fault. Keep raw returns in `raw/`.
Write `generation_runs.json` (id, prompt, inputs with sha256, output path, selected flag, reason, superseded runs)
and, after run 2, a `selected_views_review.png` contact sheet of the five selected views.

## Common prompt content (adapt per view)
TASK CONTEXT — FANTASY-GAME ASSET RESTORATION: faithful high-definition reconstruction of an EXISTING Might and
Magic IX character from the supplied renders of its original 3D model, as a 3D modelling and texturing reference.
Not a new design. A credible, fully three-dimensional character with semi-realistic game materials and sharp fine
detail (skin, face, hair strands, fabric weave, leather grain, stitching), as if a high-quality sculpt of the original
model. ONE complete figure from the top of the head to the soles, centred, generous margins, never cropped.

Pose (identical in all views, the model's bind pose as in input 1): standing upright; the arms held out to the sides
as in input 1 (straight, about 30-35 degrees below horizontal), clear air between the arms and the body; hands open
and flat, palms facing DOWN, the four fingers straight and close together with small gaps, the thumb separated; legs
straight and slightly apart with a clear gap between them, feet flat. Head level, looking forward.

Camera and light: near-orthographic, even soft neutral studio light, no dramatic light, no strong cast shadows on the
body; genuine transparent background, no floor, no shadow, no text.

Per-image checks (re-run before selecting): same identity, costume and colours as inputs 1–3; the pose above (arms out,
open flat hands with five fingers, legs apart); the correct side faces the correct image side (03: faces IMAGE LEFT;
04: faces IMAGE RIGHT); whole figure inside the frame with margins; true transparent background; 1536x1024.

## Identity
A young adult ELF townsman (commoner), slim build of average height, a slightly round youthful face.
- Face and head (input 2): fair rosy skin, a youthful clean-shaven face with soft cheeks, light blue-grey eyes, fair
  brows; short straight BLOND (straw/honey) hair with a fringe falling over the forehead, covering the top and back of
  the head down to the nape; long POINTED ELF EARS sticking out sideways and up through the hair at both sides.
- Costume: a long-sleeved rust-orange / burnt-orange smooth suede-like tunic (fine leather or brushed felt, with soft
  folds) reaching the upper hips, a V-shaped front neck slit laced with a pale cream drawstring cord whose two ends
  hang down the chest; a narrow pale cream trim at the cuffs; a dark brown leather belt with a small brass heart- or
  ring-shaped buckle at the waist; below the belt a short flared orange-ochre tunic skirt with a thin patterned
  gold-brown hem band; dark plum/purple-brown woollen breeches, loose, tucked into the boots below the knee;
  tan-brown leather calf boots with a folded-down cuff and a small strap with a brass buckle at the ankle. Bare hands.

## Do NOT
- add a weapon, apron, bag, hat, cloak, jewellery or gloves; make him a human (the ears are long and pointed); change
  colours; change the pose; crop.
