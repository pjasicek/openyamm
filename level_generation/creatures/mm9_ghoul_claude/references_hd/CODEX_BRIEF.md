# Codex brief: HD reference views for the MM9 Ghast (mm9_ghoul_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_ghoul_claude/references_hd/`. Do not edit any
other file, do not run builds, do not call Meshy. Use your built-in image generation tool. There are no native sprites for
MM9: the authority is the ORIGINAL Might and Magic IX 3D model with its skin, shown in renders of that model.

This is a fantasy video-game undead monster, a restoration of an existing 2002 game character for a game mod.

## Inputs (attached, in order)
1. `references_hd/mm9_views_a.png`: renders of the ORIGINAL low-poly model with its skin, five views left to right: front
   three-quarter from the figure's RIGHT (it faces image right and toward the viewer), front, figure's LEFT side, back, figure's RIGHT side.
   Grey is background. Design, layout, POSE, proportions and colour authority. Faceting, blur and low resolution are NOT the design.
2. `references_hd/mm9_head_views_a.png`: close renders of head and shoulders: front, three-quarter, left profile, back. Face, ear and hair authority.
3. `references_hd/mm9_hand_foot_views.png`: close renders: top row a hand from the back and side, with the claws; bottom row a foot.
4. `references_hd/mm9_loin_views.png`: close renders of belt and loincloth: front, three-quarter, side.
5. `references_hd/mm9_skin_x4_a.png`: the original 256x256 skin enlarged, SURFACE MATERIAL AND COLOUR ONLY.
6. (run 2 only) the selected `references_hd/00_three_quarter.png`.

## Deliverables (true transparent background with hard edges and no soft halo, no floor, no shadow, no text, unresized returns, 1024x1536 portrait)
| File | View |
|---|---|
| `00_three_quarter.png` | front three-quarter from the figure's RIGHT, camera at chest height slightly above (as input 1 view 1) |
| `01_front.png` | straight front |
| `02_back.png` | straight back |
| `03_left.png` | pure 90-degree profile of the figure's LEFT side: faces IMAGE LEFT |
| `04_right.png` | pure 90-degree profile of the figure's RIGHT side: faces IMAGE RIGHT |

Run 1: generate `00_three_quarter.png` only, then stop. Run 2 (separate run): generate 01-04 with the selected 00 as an additional
input so all views are the SAME figure, SAME pose, SAME proportions and colours. At most ONE corrective regeneration per view; then
select the better and note any residual fault. Keep raw returns in `raw/`. Write `generation_runs.json` (id, prompt, inputs with
sha256, output path, selected flag, reason, superseded runs) and, after run 2, a `selected_views_review.png` contact sheet.

## Common prompt content (adapt per view)
TASK CONTEXT: faithful high-definition reconstruction of the EXISTING Might and Magic IX "Ghast" from the supplied renders
of its original 3D model, as a 3D modelling and texturing reference. Not a new design. A credible, fully three-dimensional figure
with semi-realistic game materials and sharp fine detail (fine wrinkled hide, individual hair strands, grained leather, polished metal studs).
ONE complete figure from the ear tips to the soles, centred, generous margins, never cropped.

Identity (exactly the layout of inputs 1-4):
- A lean, sinewy, tall humanoid ghoul about 1.95 m tall, wide shoulders, narrow waist, long limbs: defined chest and stomach muscles, visible ribs on the back and spine knobs. NOT bulky, NOT a skeleton.
- SKIN: yellow-olive hide with darker olive-brown hollows, as in input 5. Smooth, slightly wrinkled and matte. No wounds, no blood, no scabs, no scales.
- HEAD: bald-faced ghoul with a long face, heavy angry brow ridge, deep dark eye sockets with small amber eyes, hollow cheeks, a long narrow nose with a broad tip, a strong complete chin. The lips are gone or drawn far back around the mouth: a wide mouth with long thin sharp ivory teeth, upper and lower rows interlocked, set in a dark gap. Two pale ridges of bare gum under the nose. The mouth is fixed in this snarl.
- EARS: very large pointed ears, like a bat or a goblin, standing out from the sides of the head and swept up and back, about 22 cm long, leaf shaped, each with a real inner hollow. Both ears are the same size and shape.
- HAIR: dark brown-black straight hair. A short widow's peak at the top of the forehead, a band running back over the top of the crown, then falling straight down the back of the skull as one thick flat mass, behind the ears, to the top of the back between the shoulder blades, ending in a few ragged locks. The sides of the head and the ears are bare. It reads as one thick mass with clumped locks, as a 3D modeller would sculpt it. No loose flying strands.
- BELT: a wide belt from under the ribs down to the hips, of dark red-brown leather in two parallel bands, edged with thin brass strips, with round polished silver studs along each band. In the centre front of the upper band a round silver plate with a relief of a skull; below it, on the lower band, a small rectangular silver plate with a woven pattern. It goes round the whole waist; the back carries studs only.
- SHORTS AND LOINCLOTH: skin-tight dark leather shorts, ending at mid thigh, with banded folds of tan and dark brown leather on the outside of the hips and thighs. In front a smooth dark leather triangular flap hangs from the belt down between the thighs, its point about 30 cm below the crotch of the belt; behind, a matching triangular flap. Both flaps are thick stiff leather, narrow, and close to the body. No skirt, no fur, no tatters, no loose cloth.
- BRACERS: wide dark brown leather wraps on the forearms, from mid forearm to just above the wrist, tight to the arm, in horizontal bands.
- GREAVES: wide dark brown leather wraps on the lower legs, from under the knee to just above the ankle, tight to the leg, in horizontal bands, with a reddish lower edge.
- HANDS: long gaunt hands with FIVE separate digits (four fingers and a thumb), knobbly joints, each digit ending in a long straight tapering black claw, about 7 cm, pale at the base, sharply pointed. Fingers open and spread, clear air between them.
- FEET: large long bare feet, olive skin, five toes with short dark nails. Toes point forward. Flat on the ground plane.
- No weapons, no armour plates, no extra limbs, no shirt, no cape, no necklace.

Pose (identical in all views, the model's bind pose as in input 1): standing upright, legs straight and spread wide (feet about 80 cm apart), toes pointing forward and a little outward; arms held out to the sides about 20 degrees below horizontal, a slight bend at the elbows, palms down, clear air between arms and body. Head level, looking straight ahead.

Camera: near-orthographic, even soft studio light, no drama in the light, no cast shadows on the figure, no rim light.

Do NOT: add a shirt, armour, weapons, a skirt, long loose cloth, wings; change colours; crop any part; give him a modern look; add blood or gore; add a soft halo.

Per-image checks (redo at most once): ear tips to soles in frame; true alpha; five digits with long claws on each visible hand; both big pointed ears; skull plate on the belt; front and back flaps; interlocked teeth; bare feet with toes.
