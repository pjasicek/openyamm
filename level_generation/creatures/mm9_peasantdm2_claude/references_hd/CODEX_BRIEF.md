# Codex brief: HD reference views for the MM9 dwarf townsman PeasantDM2 (skin PeasantDM2a) (mm9_peasantdm2_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_peasantdm2_claude/references_hd/`. Do not
edit any other file, do not run builds, do not call Meshy. Use your built-in image generation tool. There are no native
sprites for MM9: the authority is the ORIGINAL MM9 3D model with its skin, shown in renders made from that model.

## Inputs (attached, in order)
1. `references_hd/mm9_views_a.png` — renders of the ORIGINAL Might and Magic IX low-poly model with its original skin,
   five views left to right: front three-quarter (he faces image right and toward the viewer), front, side facing
   IMAGE LEFT, back, side facing IMAGE RIGHT. Flat grey is background. This is the design, costume, POSE, proportions
   and colour authority. Its faceting, blur and low resolution are NOT the design.
2. `references_hd/mm9_head_views_a.png` — close renders of the same model's head (front, profile facing left,
   three-quarter, profile facing right, back): the face, beard and hair authority.
3. `references_hd/mm9_skin_x4_a.png` — the original 256x256 skin texture enlarged 4x, SURFACE MATERIAL AND COLOUR ONLY
   (face painting, white hair and braids, dark knitted tunic, braided cord belt, striped trousers with small orange
   stitched marks, brown leather boots with an orange-gold ornament on the cuffs). Never the design or shape.
4. (run 2 only) the selected `references_hd/00_three_quarter.png`.

## Deliverables (true transparent background, unresized returns, 1536x1024 landscape so the spread arms fit)
| File | View |
|---|---|
| `00_three_quarter.png` | front three-quarter, he faces image right and toward the viewer, camera at chest height slightly above (as input 1 view 1) |
| `01_front.png` | straight front; the character's RIGHT arm on IMAGE LEFT |
| `02_back.png` | straight back; the character's RIGHT arm on IMAGE RIGHT |
| `03_left.png` | pure 90-degree profile of the character's LEFT side: faces IMAGE LEFT |
| `04_right.png` | pure 90-degree profile of the character's RIGHT side: faces IMAGE RIGHT |

Run 1: generate `00_three_quarter.png` only, then stop. Arms at about 20 degrees below horizontal, and a hard-edged
opaque figure with no glow or halo around it. Run 2 (separate run): generate 01–04 with the selected 00 as an
additional input so all views are the SAME character, SAME pose, SAME proportions and colours. At most ONE corrective
regeneration per view; then select the better and note any residual fault. Keep raw returns in `raw/`.
Write `generation_runs.json` (id, prompt, inputs with sha256, output path, selected flag, reason, superseded runs)
and, after run 2, a `selected_views_review.png` contact sheet of the five selected views.

## Common prompt content (adapt per view)
TASK CONTEXT — FANTASY-GAME ASSET RESTORATION: faithful high-definition reconstruction of an EXISTING Might and
Magic IX character from the supplied renders of its original 3D model, as a 3D modelling and texturing reference.
Not a new design. A credible, fully three-dimensional character with semi-realistic game materials and sharp fine
detail (skin, wrinkles, face, beard and hair strands, braids, knitted wool, cord braid, leather grain, stitching), as if
a high-quality sculpt of the original model. ONE complete figure from the top of the head to the soles, centred,
generous margins, never cropped.

Pose (identical in all views, the model's bind pose as in input 1): standing upright; the arms held out to the sides
as in input 1: a near T-pose, the arms straight and only about 20 degrees below horizontal (the hands well above hip
height, roughly at chest-belly level; NOT a 30-45 degree A-pose), clear air between the arms and the body; hands open
and flat, palms facing DOWN, the four fingers straight and close together with small gaps, the thumb separated; legs
straight and slightly apart with a clear gap between them, feet flat. Head level, looking forward.

Camera and light: near-orthographic, even soft neutral studio light, no dramatic light, no strong cast shadows on the
body; genuine transparent background, no floor, no shadow, no text.

Per-image checks (re-run before selecting): same identity, costume and colours as inputs 1–3; dwarf proportions as
input 1; the pose above (arms out, open flat hands with five fingers, legs apart); the correct side faces the correct
image side (03: faces IMAGE LEFT; 04: faces IMAGE RIGHT); whole figure inside the frame with margins; true
transparent background; 1536x1024.

## Identity
An ELDERLY DWARF townsman (commoner) about seventy, short and stocky: a broad deep chest and wide shoulders, a large
head, thick arms, short sturdy legs (proportions exactly as input 1: the legs below the tunic are short).
- Face and head (input 2): fair ruddy weathered skin with gentle age wrinkles at the eyes and forehead, a kind
  grandfatherly face, a long straight nose, bright blue eyes OPEN with visible irises, bushy white eyebrows (one brow
  line each), a gentle closed-mouth smile; a BALDING crown: a high bare forehead and bare top front of the scalp;
  long thick WHITE hair (slightly warm, cream-white) from the sides and back of the head falling straight to the
  shoulders, covering the ears, with one thick braid on each side of the face in front of the ear, hanging to the
  jaw; a full white beard and moustache, medium length, ending a little below the chin in a soft point (to the top
  of the chest, not long).
- Costume:
  - a loose dark charcoal-brown knitted wool tunic with a fine vertical rib knit, a plain round neckline showing the
    base of the neck, LONG full sleeves reaching all the way to the wrists (no bare forearms, no cuffs or bands, the
    sleeve end just covering the wrist), reaching to mid-thigh, slightly flared below the belt;
  - a braided grey-brown cord belt (a thick plaited rope belt) at the waist, no buckle visible;
  - bare hands;
  - dark brown trousers with a fine vertical stripe and a few small orange-tan stitched mending marks on the thighs;
  - brown leather boots to below the knee with a folded-down cuff, a small orange-gold swirl ornament on the outer
    side of each cuff, flat soles.

## Do NOT
- add a weapon, tool, apron, bag, hat, headband, cloak, cape, armour, jewellery or gloves; make the beard very long;
  give him a full head of hair on top (he is bald in front); change colours (the tunic is dark charcoal-brown, the hair
  and beard white); change the pose or the dwarf proportions; crop; stylise as a cartoon.
