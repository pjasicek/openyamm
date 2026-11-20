# Codex brief: HD reference views for the Lich (MM9 monster, rows Lich and Power Lich) (mm9_lich_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_lich_claude/references_hd/`. Do not edit
any other file, do not run builds, do not call Meshy. Use your built-in image generation tool. There are no native
sprites for MM9: the authority is the ORIGINAL MM9 3D model with its skin, shown in renders made from that model.

## Inputs (attached, in order)
1. `references_hd/mm9_views.png`: flat-lit renders of the ORIGINAL Might and Magic IX low-poly model with its original
   skin, five views left to right: front three-quarter (figure faces image right and toward the viewer), front, side
   facing IMAGE LEFT, back, side facing IMAGE RIGHT. Flat grey is background. This is the design, costume, POSE,
   proportions and colour authority. Its faceting, blur and low resolution are NOT the design.
2. `references_hd/mm9_head_views.png`: close renders of the head and collar (front, side facing image left, three-quarter):
   skull, eyes, hood, collar, pendant authority.
3. `references_hd/mm9_hand_views.png`: close renders of the belt, apron and skeletal hands.
4. `references_hd/mm9_skin_x4.png`: the original 256x256 skin texture enlarged 4x, SURFACE MATERIAL AND COLOUR ONLY
   (trim patterns, weave, bandage wraps, skull face). Never the design or shape.
5. (run 2 only) the selected `references_hd/00_three_quarter.png`.

## Deliverables (true transparent background, unresized returns, 1024x1536 portrait)
| File | View |
|---|---|
| `00_three_quarter.png` | front three-quarter as input 1 view 1 (faces image right and toward the viewer), camera at chest height, slightly above |
| `01_front.png` | straight front, as input 1 view 2 |
| `02_back.png` | straight back, as input 1 view 4 |
| `03_left.png` | pure 90-degree profile, faces IMAGE LEFT, as input 1 view 3 |
| `04_right.png` | pure 90-degree profile, faces IMAGE RIGHT, as input 1 view 5 |

Run 1: generate `00_three_quarter.png` only, then stop. Run 2 (separate run): generate 01-04 with the selected 00 as an
additional input so all views are the SAME figure, SAME pose, SAME proportions and colours. At most ONE corrective
regeneration per view; then select the better and note any residual fault. Keep raw returns in `raw/`. Write
`generation_runs.json` (id, prompt, inputs with sha256, output path, selected flag, reason, superseded runs) and, after
run 2, a `selected_views_review.png` contact sheet of the five selected views.

## Common prompt content (adapt per view)
TASK CONTEXT, FANTASY-GAME ASSET RESTORATION: faithful high-definition reconstruction of an EXISTING Might and Magic IX
character from the supplied renders of its original 3D model, as a 3D modelling and texturing reference. Not a new
design. A credible, fully three-dimensional figure with semi-realistic game materials and sharp fine detail (bone,
woven cloth, braided trim, leather, tooled boots), as if a high-quality sculpt of the original model. ONE complete
figure from the hood peak to the soles, centred, generous margins, never cropped.

Pose (identical in all views, the model's bind pose as in input 1; do not tidy it): upright, a short walking stance with
the feet apart, one foot a short step forward and the other a short step back as in the side views of input 1; both arms
hang out from the shoulders inside wide bell sleeves, elbows slightly bent, forearms angled forward and the skeletal
hands held at hip height in FRONT of and beside the thighs, fingers hooked like claws, palms facing inward and down.
Clear air between each hand and the thigh, and between each sleeve and the torso.

Camera and light: near-orthographic, even soft neutral studio light, no dramatic light, no cast shadows on the body;
genuine transparent background, no floor, no shadow, no text.

Per-image checks (re-run before selecting): same identity, costume and colours as inputs 1-4; the pose above; skull
visible inside the hood; five long separate bone fingers on each hand with air between them; the correct side faces the
correct image side (03 IMAGE LEFT, 04 IMAGE RIGHT); whole figure inside the frame with margins; true transparent
background; 1024x1536.

## Identity
A lich: a tall, gaunt undead sorcerer in a hooded robe. Costume from top to bottom:
- Head: a real human SKULL, ivory-bone coloured, deep eye sockets with a burning red-orange ember glow, a nose cavity,
  teeth, and a lower jaw hanging slightly open, a dark hollow mouth. It sits deep in the hood. Input 2 is the authority:
  proportions of a true skull, not a cartoon.
- Hood: a tall, slightly peaked hood of coarse dark olive-brown woven cloth with a soft forward point above the brow,
  dark inside, framing the skull.
- Cowl and collar: a shoulder cape of the same olive-brown cloth, trimmed in a braided golden-tan Celtic knot border, a
  thin silver chain across the upper chest ending at a round silver skull pendant in the centre of the collar.
- Torso: a dark navy-black corset with faint tarnished embroidery, a V of braided trim above it.
- Belt: a wide rust-red leather belt with two pale rope edges, small silver studs, a small bone skull buckle at the front.
- Below the belt: a long tapering navy-black apron with a thin tan piping, in FRONT of a long open olive-brown robe that
  hangs at the front and back to mid-shin; the robe's lower edge is torn and ragged. The robe is open at the sides,
  showing the legs.
- Sleeves: very wide bell sleeves of the same olive-brown cloth, lower edges darker and TORN into jagged tatters and
  notches, as in the skin in input 4. Forearms inside are thin, wrapped in dark brown fur or rags.
- Hands: fully SKELETAL, long thin ivory-green phalanges with clear joints, five fingers, long pointed finger tips.
- Thighs: wound in tight horizontal strips of pale tan linen bandage with dark gaps between the wraps.
- Boots: tall black leather boots to just under the knee, with pointed front and back flares at the top and a faint
  tooled skull-face relief. Over dark brown leather foot wraps.
- Feet: the leather ends at the toes; bare ivory bone toes show at the front of each foot.

## Do NOT
- add a staff, weapon, crown, armour, wings or extra limbs; change colours; make it clean or new-looking; straighten the
  pose or make the figure symmetrical; put hands together or against the body; add flesh to the skull or hands; crop.
