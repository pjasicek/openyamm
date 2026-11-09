# Codex brief: HD reference views for MM9 Ebora (mm9_ebora_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_ebora_claude/references_hd/`. Do not edit any
other file, do not run builds, do not call Meshy. Use your built-in image generation tool. There are no native sprites for
MM9: the authority is the ORIGINAL Might and Magic IX 3D model with its skin, shown in renders of that model.

This is a fantasy video-game character: Ebora, a demon queen (an adult female demon with red skin, small horns and a
black armoured corset), a restoration of an existing 2002 game character for a game mod. Fully clothed, non-sexual,
a dignified villain portrait for a 3D modelling reference.

## Inputs (attached, in order)
1. `mm9_body_views_ebora.png`: renders of the ORIGINAL low-poly model with its skin, WINGS REMOVED, five views left to
   right: front three-quarter from the figure's RIGHT, front, figure's LEFT side, back, figure's RIGHT side. Grey is
   background. Design, layout, proportions and colour authority. The faceting, blur and low resolution are NOT the
   design. The T-pose of the input is NOT the pose wanted.
2. `mm9_head_views_ebora.png`: close renders of head, hair, horns and neck, same five views.
3. `mm9_chest_views_ebora.png`: close renders of the corset, breast cups, belt and arms, same five views.
4. `mm9_legs_views_ebora.png`: close renders of the legs and boots, same five views.
5. `mm9_hand_views.png`: the hand. TOP ROW ONLY is Ebora (black glove, long claws); ignore the bottom row.
6. `mm9_skin_x4_ebora.png`: the original 256x256 skin enlarged, SURFACE MATERIAL AND COLOUR ONLY.
7. (run 2 only) the selected `references_hd/00_three_quarter.png`.

## Deliverables (true transparent background, no floor, no shadow, no text, unresized returns, 1024x1536 PORTRAIT)
| File | View |
|---|---|
| `00_three_quarter.png` | front three-quarter from the figure's RIGHT, camera at chest height slightly above (as input 1 view 1) |
| `01_front.png` | straight front |
| `02_back.png` | straight back |
| `03_left.png` | pure 90-degree profile of the figure's LEFT side: she faces IMAGE LEFT |
| `04_right.png` | pure 90-degree profile of the figure's RIGHT side: she faces IMAGE RIGHT |

Run 1: generate `00_three_quarter.png` only, then stop. Run 2 (separate run): generate 01-04 with the selected 00 as an
additional input so all views are the SAME figure, SAME pose, SAME proportions and colours. At most ONE corrective
regeneration per view; then select the better and note any residual fault. Keep raw returns in `raw/`. Write
`generation_runs.json` (id, prompt, inputs with sha256, output path, selected flag, reason, superseded runs) and, after
run 2, a `selected_views_review.png` contact sheet.

## Common prompt content (adapt per view)
TASK CONTEXT: faithful high-definition reconstruction of the EXISTING Might and Magic IX "Ebora" from the supplied renders
of its original 3D model, as a 3D modelling and texturing reference. Not a new design. A credible, fully three-dimensional
figure with semi-realistic game materials and sharp fine detail (smooth skin, polished black leather, engraved dark
silver, individual hairs). ONE complete figure from the horn tips to the soles, centred, both hands inside the frame with
margin, never cropped.

Identity (exactly the layout of inputs 1-5):
- An athletic adult FEMALE demon about 1.80 m tall, slim waist, long legs, ordinary proportions. Skin a smooth saturated
  ORANGE-RED (like input 2, about RGB 225,70,30 in light), the same red on face, neck, shoulders and upper arms.
- HEAD: a beautiful, cold, haughty face of about 30, high cheekbones, arched black brows, fully WHITE eyes with no visible
  pupils (as input 2), dark plum lips, closed mouth, complete chin and jaw. Ears hidden by the hair.
- HAIR: thick straight glossy BLACK hair, a long side-swept fringe over the forehead, falling past the shoulders to the
  shoulder blades at the back, framing the face, as input 2. Hair lies on the head and shoulders, not blowing.
- HORNS: two slim curved horns, dark grey-black with pale ridged rings, rising from the top of the head through the hair,
  curving up and slightly back, about 14 cm tall, as input 2.
- CORSET: a black leather corset from the bust to the hips, with two rigid dark-silver engraved BREAST CUPS, each with a
  small silver SKULL embossed at the centre and a short silver spike at its outer top, and the belly covered by
  overlapping horizontal dark-silver scale plates down the front, as input 3. Black leather shoulder straps. The upper
  chest and shoulders are bare red skin. At the back the corset is black leather laced up the spine with a silver spine
  ridge, as input 3 view 4.
- BELT AND LOINS: a thin gold-and-silver chain belt at the hips, and below it a front panel of dark silver plate with a
  silver skull emblem, as input 3.
- LEGS: tight glossy black-blue leather leggings, and on the FRONT of each thigh and shin a vertical band of pale bone-like
  silver studs and plates (as input 4), ending in black high-heeled ankle boots with a slim heel and pointed toe.
- ARMS: bare red upper arms; long black leather GLOVES from just below the elbow to the fingertips.
- HANDS: slender gloved hands with FIVE long separate fingers (four fingers and a thumb), each ending in a long sharp
  black CLAW, relaxed and slightly curled, clear air between the fingers, as input 5 top row. Nothing in the hands.
- NO WINGS: the original has bat wings on her back. Leave them OUT completely (they are modelled separately). The back is
  clean: hair and corset only, no wing stubs.
- No cape, no weapons, no jewellery beyond the skulls, no extra limbs, no tail.

Pose (identical in all views; NOT the T-pose of input 1): standing upright and symmetrical, facing the camera direction
of the view, feet apart (about 30 cm between the heels), toes forward, legs straight; arms straight, out to the sides and
down at about 40 degrees from vertical, palms facing the thighs, slightly forward, elbows nearly straight, wrists
straight, clear air between the arms and the body. Head level, looking straight ahead.

Camera: near-orthographic, even soft studio light, no drama in the light, no cast shadows on the figure, no rim light.

Do NOT: add wings, a tail, weapons or a cloak; change the skin colour from orange-red; give her pupils; crop any part;
copy the blur or faceting; make the outfit more revealing than input 3.

Per-image checks (redo at most once): horns to soles in frame; both hands in frame; true alpha; five clawed fingers on
each visible hand; two horns; white eyes; black hair to the shoulder blades; two breast cups with skulls; scale plates on
the belly; studded bands on the front of the legs; high-heeled boots; no wings.
