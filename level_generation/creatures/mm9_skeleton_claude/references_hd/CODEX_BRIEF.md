# Codex brief: HD reference views for the MM9 Skeleton (mm9_skeleton_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_skeleton_claude/references_hd/`.
Do not edit any other file, do not run builds, do not call Meshy. Use your built-in image generation tool. There are no
native sprites for MM9: the authority is the ORIGINAL Might and Magic IX 3D model with its skin, shown in renders made
from that model.

## Inputs (attached, in order)
1. `references_hd/mm9_views_skel2.png` — renders of the ORIGINAL MM9 low-poly model with its original skin, five views left
   to right: front three-quarter from the figure's RIGHT (it faces image right and toward the viewer), front, figure's LEFT
   side (faces IMAGE LEFT), back, figure's RIGHT side (faces IMAGE RIGHT). Flat grey is background. This is the design,
   clothing layout and colour authority. Its faceting, blur, spindly tube limbs and low resolution are NOT the design.
2. `references_hd/mm9_head_views_skel2.png` — close renders of the head: front, three-quarter, left profile, back.
3. `references_hd/mm9_torso_views_skel2.png` — close renders of the torso and pelvis: front, three-quarter, back.
4. `references_hd/mm9_skin_x4.png` — the original 256x256 skin enlarged 4x. It shows the painted detail: skull with one
   glowing green eye and one cracked empty socket, a separate lower jaw with a gold tooth, the torn leather vest with
   rope collar, ring, studded diagonal strap and buckle over the ribs; pelvis with a rope belt and two hanging leather
   scraps; a femur or shin bone with a torn brown leather wrap and dark leather bands; forearm bones with a crossed
   linen bandage, a dark leather wrist cuff; a five-finger bone hand; a bone foot with separate toes.
5. (run 2 only) the selected `references_hd/00_three_quarter.png`.

## Deliverables (true transparent background, unresized returns, 1024x1536 portrait)
| File | View |
|---|---|
| `00_three_quarter.png` | front three-quarter from the figure's RIGHT, camera at chest height slightly above (as input 1 view 1) |
| `01_front.png` | straight front; the figure's RIGHT arm on IMAGE LEFT |
| `02_back.png` | straight back; the figure's RIGHT arm on IMAGE RIGHT |
| `03_left.png` | pure 90-degree profile of the figure's LEFT side: faces IMAGE LEFT |
| `04_right.png` | pure 90-degree profile of the figure's RIGHT side: faces IMAGE RIGHT |

Run 1: generate `00_three_quarter.png` only, then stop. Run 2 (separate run): generate 01–04 with the selected 00 as an
additional input so all views are the SAME figure, SAME pose, SAME proportions and colours. At most ONE corrective
regeneration per view; then select the better and note any residual fault. Keep raw returns in `raw/`. Write
`generation_runs.json` (id, prompt, inputs with sha256, output path, selected flag, reason, superseded runs) and, after
run 2, a `selected_views_review.png` contact sheet of the five selected views.

## Common prompt content (adapt per view)
TASK CONTEXT — FANTASY-GAME ASSET RESTORATION: faithful high-definition reconstruction of the EXISTING Might and Magic
IX "Skeleton" monster from the supplied renders of its original 3D model and its painted skin, as a 3D modelling and
texturing reference. Not a new design. A credible, fully three-dimensional figure with semi-realistic game materials and
sharp fine detail (aged bone with cracks and pits, worn stitched leather, rough rope, tarnished iron). ONE complete figure
from the top of the skull to the soles, centred, generous margins, never cropped. It is a real SKELETON: no skin, no
muscle, no flesh anywhere; separate rigid bones with clear air between them wherever the clothing stops.

Identity (exactly the layout of inputs 1–4):
- Tall and gaunt, about 1.9 metres, slim long limbs, a slightly large head.
- SKULL: a human skull with a HIGH, large domed cranium swelling backward, of aged ochre-ivory bone with a brownish patina.
  The figure's RIGHT eye socket holds a glowing GREEN eye; the figure's LEFT socket is an empty dark hole with a crack
  running from the brow through the socket to the cheek. Triangular nasal hole, cheekbones, upper teeth with one small
  gold tooth. A SEPARATE lower jaw, the mouth OPEN about 3 cm, a full row of lower teeth, with a gap of air between the
  upper and lower teeth.
- NECK: bare neck vertebrae.
- VEST: a sleeveless, open-fronted torn brown LEATHER VEST over the ribcage, from the shoulders down to the lower ribs,
  with a raised rope-twist collar edge at the neck, and frayed ragged lower edges with ragged holes. In front it hangs
  open down the middle so the breastbone and ribs show between its two sides; the rib cage is visible through the torn
  holes and the open front. At the back it covers the upper back, then is torn away so that the spine and lower ribs show.
- STRAP: a dark leather diagonal strap across the chest from the figure's RIGHT shoulder to its LEFT lower ribs, with
  iron studs, a square iron buckle in the middle and a round iron ring at the collar.
- RIBCAGE: real separate ribs with air gaps under the vest, a sternum in front, spine at the back.
- WAIST: NO clothing between the vest and the pelvis: a bare bone spine of a few vertebrae with clear air on both sides.
- PELVIS: a real bone pelvis (hip blades, sacrum) with a thin twisted brown ROPE belt round the hips and two SHORT torn
  leather scraps hanging from the belt on the hips, each no longer than a hand; they stop above mid-thigh.
- LEGS: a single femur each with knee, a shin (tibia and fibula) of bare aged bone; the outer side of each thigh has a
  narrow torn brown leather wrap, tight to the bone, and just above each ankle two or three tight dark leather bands.
  NO skirt, NO trousers, NO loincloth.
- ARMS: bare bone upper arm (a single humerus each), forearm of two bones (radius and ulna) with a crossed pale LINEN
  bandage wrapped tight round the elbow joint, and a dark leather wrist cuff, frayed at the edges.
- HANDS: bone hands with FIVE separate fingers each, each finger three separate joints, no flesh.
- FEET: bone feet with five separate toes.

Pose (identical in all views): an A-pose standing upright, arms straight out to the sides about 50 degrees from vertical
with a very slight bend at the elbow and clear air between the arms and the body; the bone hands open with the five
fingers separated and slightly curved (NOT fists), palms facing down and forward; legs straight and wide apart as in
input 1 with a clear gap between them, feet flat, toes forward. Head level, looking forward.

Camera and light: near-orthographic, even soft neutral studio light (brighter than input 1, which is dark), no dramatic
light, no strong cast shadows on the figure; genuine transparent background, no floor, no shadow, no text.

Do NOT: add a weapon, dagger, shield, cape, helmet, flesh, skin, muscle, tendons or extra armour; do not close the mouth;
do not fill the waist gap; do not cover the ribs with an unbroken vest; do not make the vest long; do not change the
colours; no fire and no glow except the green eye; do not crop the skull or the feet.

## Per-image checks (re-run before selecting)
High domed skull; green eye in the figure's RIGHT socket (on IMAGE LEFT in the front view), the other socket dark and
cracked; open mouth with a visible gap and separate jaw; torn open brown leather vest with ribs showing; diagonal studded
strap with square buckle; bare spine at the waist with air beside it; bone pelvis with thin rope belt and short scraps;
bare femur and shin bones with a narrow leg wrap and ankle bands; crossed bandage at the elbows, wrist cuffs; FIVE
separated bone fingers on each hand and toes on each foot; no weapon; the pose above; the correct side faces the correct
image side (03: faces IMAGE LEFT; 04: faces IMAGE RIGHT); whole figure inside the frame with margins; true transparent
background; 1024x1536.
