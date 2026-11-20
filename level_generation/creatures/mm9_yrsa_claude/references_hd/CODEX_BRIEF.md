# Codex brief: HD reference views for Yrsa the Troll (MM9 NPC, Isle of Ashes) (mm9_yrsa_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_yrsa_claude/references_hd/`. Do not edit any other
file, do not run builds, do not call Meshy. Use your built-in image generation tool. There are no native sprites for
MM9: the authority is the ORIGINAL MM9 3D model with its skin, shown in renders made from that model.

## Inputs (attached, in order)
1. `references_hd/mm9_views.png` — renders of the ORIGINAL Might and Magic IX low-poly model with its original skin,
   five views left to right: front three-quarter from the character's RIGHT (he/she faces image right and toward the
   viewer), front, character's LEFT side (faces IMAGE LEFT), back, character's RIGHT side (faces IMAGE RIGHT). Flat
   grey is background. This is the design, costume, POSE, proportions and colour authority. Its faceting, blur, dark
   shading and low resolution are NOT the design.
2. `references_hd/mm9_head_views.png` — close renders of the same model's head (front, left profile, three-quarter):
   the face, hair and headwear authority.
3. `references_hd/mm9_skin_x4.png` — the original 256x256 skin texture enlarged 4x, SURFACE MATERIAL AND COLOUR ONLY
   (face painting, fabric, trim patterns). Never the design or shape.
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
detail (skin, face, fabric weave, stitching, trims), as if a high-quality sculpt of the original model. ONE complete
figure from the top of the head to the soles, centred, generous margins, never cropped.

Pose (identical in all views, the model's bind pose as in input 1): standing; the arms held out to the sides as in
input 1 (straight, about 15-20 degrees below horizontal), clear air between the arms and the body; hands open and flat,
palms facing DOWN, the four fingers straight and close together with small gaps, the thumb separated; legs straight
and slightly apart with a clear gap between them, feet flat. Head as in input 1.

Camera and light: near-orthographic, even soft neutral studio light (brighter than input 1, which is dark), no
dramatic light, no strong cast shadows on the body; genuine transparent background, no floor, no shadow, no text.

Per-image checks (re-run before selecting): same identity, costume and colours as inputs 1–3; the pose above (arms out,
open flat hands with five fingers, legs apart); the correct side faces the correct image side (03: faces IMAGE LEFT;
04: faces IMAGE RIGHT); whole figure inside the frame with margins; true transparent background; 1536x1024.

## Identity
Yrsa the Troll, a very old troll woman, smaller and HUNCHED: the upper back rounded and the head and neck thrust
FORWARD and low in front of the shoulders exactly as in input 1 profile views (keep this posture and her proportions:
short torso, long arms, narrow shoulders). A village wise-woman, not a monster.
- Face (input 2): a wrinkled, leathery reddish-brown face, a long hooked nose, a broad grin showing a few crooked
  yellow teeth, deep-set pale eyes under heavy grey brows, prominent cheekbones and a pointed chin; long thin
  white-grey hair framing the face, with two long pale braids/hair cords hanging down in front of the shoulders.
- Headwear: a dark brown, slightly furry/woolly cloth hood/headscarf covering the head, ending in a long pointed tail
  that hangs down her back (input 1 back and side views); a band of small gold beads and little white fangs/teeth
  across the forehead under the hood.
- Neck: a broad collar necklace of white teeth and gold beads and a silver ornate pendant on the chest.
- Dress: a long dark brown-black heavy woollen dress to the ankles with long sleeves (sleeves widen at the wrist),
  subtle darker woven pattern and faded embroidery near the hem, a thin braided cord belt at the waist, a gold-cord
  decorative loop pattern across the chest.
- Hands: bony, knuckly old hands with long fingers, reddish-brown skin. Feet: simple dark leather shoes peeking out
  under the hem.

## Do NOT
- straighten her back or lift her head upright; make her young, pretty or a green monster troll; add a staff, basket,
  cloak or weapon; change colours; change the pose; crop.
