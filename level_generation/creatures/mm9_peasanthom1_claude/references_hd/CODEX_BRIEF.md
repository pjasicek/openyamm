# Codex brief: HD reference views for the MM9 half-orc townsman PeasantHOM1 (skin PeasantHOM1a) (mm9_peasanthom1_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_peasanthom1_claude/references_hd/`. Do not
edit any other file, do not run builds, do not call Meshy. Use your built-in image generation tool. There are no native
sprites for MM9: the authority is the ORIGINAL MM9 3D model with its skin, shown in renders made from that model.

## Inputs (attached, in order)
1. `references_hd/mm9_views_a.png` — renders of the ORIGINAL Might and Magic IX low-poly model with its original skin,
   five views left to right: front three-quarter from the character's RIGHT (he faces image right and toward the
   viewer), front, character's LEFT side (faces IMAGE LEFT), back, character's RIGHT side (faces IMAGE RIGHT). Flat
   grey is background. This is the design, costume, POSE, proportions and colour authority. Its faceting, blur and low
   resolution are NOT the design.
2. `references_hd/mm9_head_views_a.png` — close renders of the same model's head (front, left profile, three-quarter,
   right profile, back): the face, hair, horn, tusk and ear authority.
3. `references_hd/mm9_skin_x4_a.png` — the original 256x256 skin texture enlarged 4x, SURFACE MATERIAL AND COLOUR ONLY
   (face painting, hair, fabric, belt, boot wraps). Never the design or shape.
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
detail (skin pores, face, hair strands, horn ridges, fabric weave, leather grain, stitching), as if a high-quality
sculpt of the original model. ONE complete figure from the horn tips to the soles, centred, generous margins, never
cropped.

Pose (identical in all views, the model's bind pose as in input 1): standing upright; the arms held out to the sides
as in input 1 (straight, about 30-35 degrees below horizontal), clear air between the arms and the body; hands open
and flat, palms facing DOWN, the four fingers straight and close together with small gaps, the thumb separated; legs
straight and slightly apart with a clear gap between them, feet flat. Head level, looking forward.

Camera and light: near-orthographic, even soft neutral studio light, no dramatic light, no strong cast shadows on the
body; genuine transparent background, no floor, no shadow, no text.

Per-image checks (re-run before selecting): same identity, costume and colours as inputs 1–3; the pose above (arms out,
open flat hands with five fingers, legs apart); two horns, two pointed ears, the small lower tusks; the correct side
faces the correct image side (03: faces IMAGE LEFT; 04: faces IMAGE RIGHT); whole figure inside the frame with margins;
true transparent background; 1536x1024.

## Identity
An adult HALF-ORC townsman (commoner): a stocky, broad-shouldered, thick-necked man of human height, a heavy, slightly
pot-bellied build, big hands.
- Face and head (input 2): a broad, fleshy, coarse human-like face with ruddy pink-orange skin, heavy brow ridge,
  small deep-set eyes, a broad flat nose, full cheeks and a wide grinning mouth showing uneven teeth and two short
  pointed lower TUSKS (fangs) rising from the lower jaw at the corners of the mouth; clean-shaven. Large POINTED EARS
  that stick straight out sideways from the sides of the head (wide, flat, triangular, skin-coloured). Thick straight
  chestnut-brown hair cut in a heavy bowl shape that covers the top, sides and back of the head down to the nape and
  sits low on the forehead in a fringe. Two smooth tan-ochre HORNS growing from the top of the head, one each side
  above the temples: each rises up and curves outward and then down like a hook, tips pointing down and slightly out,
  each about the length of the head.
- Costume: a long-sleeved loose cream-beige linen shirt (coarse weave, a dark embroidered band at the cuffs), its
  front showing in a narrow vertical strip down the chest and below the vest; a sleeveless dark brown-plum woollen
  VEST (tweed-like, flecked dark red/brown) with a rust-brown leather border, open at the front, reaching the upper
  thighs; a narrow brown leather belt with a small brass buckle under the vest; the shirt's pointed front tail hangs
  below the belt; dark red-brown woollen trousers, loose, straight; on the shins thick wrapped leggings of pale cream
  cloth criss-crossed by dark brown leather straps from the ankle to below the knee; soft brown leather shoes. Bare
  hands.

## Do NOT
- add a weapon, apron, bag, hat, cloak, jewellery or gloves; drop the horns, tusks or pointed ears; make him green or a
  monstrous orc (his skin is ruddy human pink-orange); change colours; change the pose; crop.
