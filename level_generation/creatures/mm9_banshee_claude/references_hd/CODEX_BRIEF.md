# Codex brief: HD reference views for the Banshee body (MM9 monster, rows Fright, Dread, Terror) (mm9_banshee_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_banshee_claude/references_hd/`. Do not edit any other file, do not run builds,
do not call Meshy. Use your built-in image generation tool. There are no native sprites for MM9: the authority is the ORIGINAL MM9 3D model with its skin.

## Inputs (attached, in order)
1. `references_hd/mm9_views_body_E.png`: flat-lit renders of the ORIGINAL Might and Magic IX low-poly model, five views left to right: front three-quarter (figure faces image right
   and toward the viewer), front, side facing IMAGE LEFT, back, side facing IMAGE RIGHT. Grey is background. Her cloak-wings and hair spikes are removed from these renders on purpose.
   This is the design, costume, POSE, proportions and colour authority. Its faceting, blur and low resolution are NOT the design. The head region is damaged in this render: ignore it, use input 2.
2. `references_hd/mm9_views_head_A.png`: the same views, close on head, neck and collar (with the spiked hair that you must NOT draw).
3. `references_hd/mm9_skin_x4_E.png`: the original 256x256 skin enlarged 4x, SURFACE MATERIAL AND COLOUR ONLY (linen pleats, gold embroidery, ribs seen through the brown side panels,
   knotwork forearm guards, hand skin with thin red scratches). Never the design or shape.
4. (run 2 only) the selected `references_hd/00_three_quarter.png`.

## Deliverables (true transparent background, unresized returns, 1024x1536 portrait)
| File | View |
|---|---|
| `00_three_quarter.png` | front three-quarter as input 1 view 1 (faces image right and toward the viewer), camera at chest height, slightly above |
| `01_front.png` | straight front, as input 1 view 2 |
| `02_back.png` | straight back, as input 1 view 4 |
| `03_left.png` | pure 90-degree profile, faces IMAGE LEFT, as input 1 view 3 |
| `04_right.png` | pure 90-degree profile, faces IMAGE RIGHT, as input 1 view 5 |

Run 1: generate `00_three_quarter.png` only, then stop. Run 2 (separate run): generate 01-04 with the selected 00 as an additional input so all views are the SAME figure, SAME pose, SAME
proportions and colours. At most ONE corrective regeneration per view; then select the better and note any residual fault. Keep raw returns in `raw/`. Write `generation_runs.json` (id, prompt,
inputs with sha256, output path, selected flag, reason, superseded runs) and, after run 2, a `selected_views_review.png` contact sheet of the five selected views.

## Common prompt content (adapt per view)
TASK CONTEXT, FANTASY-GAME ASSET RESTORATION: faithful high-definition reconstruction of an EXISTING Might and Magic IX undead woman from the supplied renders of its original 3D model, as a 3D
modelling and texturing reference. Not a new design. A credible, fully three-dimensional figure with semi-realistic game materials and sharp fine detail. ONE complete figure from the crown of the
head to the tips of the dress, centred, generous margins, never cropped. Render it SOLID and OPAQUE: a modelling reference, so no transparency, no glow, no mist, no smoke, no aura.

Pose (identical in all views, the model's bind pose as in input 1; do not tidy it): a legless floating woman, slim, upright torso, a thin long neck leaning forward with the head held out in front of the
chest. Both arms straight out and down from the shoulders about 35 degrees below horizontal, well clear of the body, in slim long sleeves. Hands open. Below the waist one long closed tapered dress with
NO legs and NO feet inside it: it sweeps down and BACKWARD about 30 degrees from vertical, as in the side views of input 1, wider toward the hem, ending in a few long sharp points.

Camera and light: near-orthographic, even soft neutral studio light, no dramatic light, no cast shadows on the body; genuine transparent background, no floor, no shadow, no text.

Per-image checks (re-run before selecting): same costume and colours as inputs 1 and 3; the pose above; no legs; dress sweeping back; both arms clear of the body; correct side faces the correct image
side (03 IMAGE LEFT, 04 IMAGE RIGHT); hands with four digits each; whole figure inside the frame with margins; true transparent background; 1024x1536.

## Identity, top to bottom
- Head: a woman's face with an open screaming mouth; red-brown hair pulled tightly back from the forehead into a SMOOTH close-fitting cap with no loose strands and no spikes. (The head is modelled separately later, so keep it simple.)
- Neck: long, thin, pale. A tall stand-up collar at the back of the neck in banded cream and gold cloth; a thin gold necklace with a small flame-shaped pendant in the V of the neck.
- Bodice front: a long pale cream pleated linen panel running from the neck down over the belt to mid-thigh, like a long apron, its neckline a deep V edged with gold beaded embroidery, its hem a gold embroidered band.
- Gold bands: broad orange-gold brocade bands down both sides of the linen panel, from the shoulder past the belt to the apron's hem.
- Sides and back of the torso: tan-brown cloth with the darker RIBCAGE showing through it like a stain, ribs curving round the sides and a spine down the back, as in input 1 view 4 and input 3.
- Belt: a narrow gold embroidered band at the waist.
- Sleeves: slim, tan-gold cloth. The forearm carries a long pointed gold knotwork guard from the elbow to the wrist, with a thin gold edge, and a soft cream ruffle at the wrist.
- Hands: long and bony, pale pink-cream skin with thin red scratches. EXACTLY FOUR digits on each hand, three very long fingers and one thumb, each ending in a long narrow pointed dark claw. Digits spread wide apart, never touching.
- Dress: mauve-brown cloth with long soft dark vertical streaks, darker at the very bottom; a few long sharp points at the hem, the same front and back.

## Do NOT
add legs, feet, a hood, a cloak, wings, drapes from the arms, hair spikes, a crown, armour, weapons or extra limbs; change colours; add glow or see-through effects; straighten the dress to hang vertically; put hands against
the body; give a hand five digits; crop.
