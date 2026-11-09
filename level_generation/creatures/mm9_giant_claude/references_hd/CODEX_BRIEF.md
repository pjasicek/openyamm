# Codex brief: HD reference views for the MM9 Giant (mm9_giant_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_giant_claude/references_hd/`. Do not edit any other file, do not run
builds, do not call Meshy. Use your built-in image generation tool. There are no native sprites for MM9: the authority is the ORIGINAL Might and
Magic IX 3D model with its skin, shown in renders of that model.

This is a fantasy video-game character: the "Forest Giant", a huge barbarian man, a restoration of an existing 2002 game creature for a game mod.

## Inputs (attached, in order)
1. `mm9_views_b.png`: renders of the ORIGINAL low-poly model with its skin, five views left to right: front three-quarter from the figure's RIGHT,
   front, figure's LEFT side (faces IMAGE LEFT), back, figure's RIGHT side (faces IMAGE RIGHT). Grey is background. Design, layout, POSE, proportions
   and colour authority. Faceting, blur and low resolution are NOT the design.
2. `mm9_torso_views_b.png`: close renders of the torso (front, left side, back, three-quarter).
3. `mm9_leg_views_b.png`: close renders of the legs (front, left side, back, three-quarter).
4. `mm9_head_views_b.png`: close renders of the head (front, three-quarter, left side, back).
5. `mm9_hand_views_b.png`: close renders of the hands and leather wrist bracers.
6. `mm9_skin_x4_b.png`: the original 256x256 skin enlarged, SURFACE MATERIAL AND COLOUR ONLY.
7. (run 2 only) the selected `references_hd/00_three_quarter.png`.

## Deliverables (true transparent background, no floor, no shadow, no text, unresized returns, 1536x1024 LANDSCAPE: the arms reach far out)
| File | View |
|---|---|
| `00_three_quarter.png` | front three-quarter from the figure's RIGHT, camera at chest height slightly above (as input 1 view 1) |
| `01_front.png` | straight front |
| `02_back.png` | straight back |
| `03_left.png` | pure 90-degree profile of the figure's LEFT side: faces IMAGE LEFT |
| `04_right.png` | pure 90-degree profile of the figure's RIGHT side: faces IMAGE RIGHT |

Run 1: generate `00_three_quarter.png` only, then stop. Run 2 (separate run): generate 01-04 with the selected 00 as an additional input so all views are
the SAME figure, SAME pose, SAME proportions and colours. At most ONE corrective regeneration per view; then select the better and note any residual fault.
Keep raw returns in `raw/`. Write `generation_runs.json` (id, prompt, inputs with sha256, output path, selected flag, reason, superseded runs) and, after run 2,
a `selected_views_review.png` contact sheet.

## Common prompt content (adapt per view)
TASK CONTEXT: faithful high-definition reconstruction of the EXISTING Might and Magic IX "Forest Giant" from the supplied renders of its original 3D model,
as a 3D modelling and texturing reference. Not a new design. A credible, fully three-dimensional figure with semi-realistic game materials and sharp fine
detail (skin pores, leather grain, stitching, fur tufts, hammered steel). ONE complete figure from the top of the head to the soles, centred, generous
margins, never cropped.

Identity (exactly the layout of inputs 1-6):
- A huge, heavily muscled barbarian man with heroic proportions: broad shoulders, deep chest, defined abdominal muscles, thick arms and legs, tanned
  warm-brown skin. Normal human proportions otherwise (head about 1/8 of the height).
- HEAD (input 4): long loose dark-brown hair to the shoulders, parted at the centre, a full short dark-brown beard and moustache with grey-brown flecks,
  a rugged broad face with heavy brows, a straight nose, blue-grey eyes, mouth CLOSED in a grim line. Small gold ring earrings in both ears.
- SHOULDERS and COLLAR (inputs 2, 6): a mantle of shaggy tan-and-cream fur across both shoulders and upper chest and upper back; on top of each shoulder a
  round domed steel pauldron engraved with a Celtic knot pattern; a necklace of large curved ivory animal fangs and small dark steel disks across the
  collarbones, with a small double-axe-shaped steel pendant at the centre of the chest.
- TORSO: BARE muscular chest and stomach (pectorals and abs clearly visible), tanned skin. On the back, below the fur, a dark-brown leather harness panel
  across the shoulder blades carrying three large round engraved steel disks (input 2 back view); the lower back is bare skin.
- BELT: a very wide belt of dark-brown leather with three parallel steel bands and rows of steel rivets, with a large round dark-red and steel boss
  (a round buckle) at the front centre.
- HIPS: under the belt a short loincloth of tan fur and dark leather with ivory claws and steel rivets over the front, the sides and the buttocks,
  ending high on the thigh. It is tight to the body (like shorts), NOT a flaring skirt.
- LEGS (input 3): BARE muscular thighs with a narrow dark-brown leather strap with a round steel ring buckle around each upper thigh; a curved steel
  knee cop on each knee; the shins wrapped in dark-brown leather and tan fur bands with two thin polished-steel bands round each calf; simple
  dark-brown leather shoes.
- ARMS: bare muscular arms, wide dark-brown leather bracers on the wrists (input 5). Big strong human hands, RELAXED and slightly open, NOT fists,
  four separate fingers and a separate thumb, fingers slightly apart so each one reads.
- No weapon, no cape, no helmet, no shield. The hands hold nothing.

Pose (identical in all views, the model's bind pose as in input 1): standing upright, legs straight and apart (feet about 40 cm apart), feet pointing
forward; arms straight out to the sides and down at about 25 degrees BELOW horizontal, elbows very slightly bent, palms facing down and slightly back,
clear air between the arms and the body and between the legs. Head level, looking straight ahead along the body.

Camera: near-orthographic, even soft studio light, no drama in the light, no cast shadows on the figure, no rim light.

Do NOT: add a weapon, clothes on the chest or thighs, a cape or a helmet; change colours; crop any part; close the hands into fists; show teeth; copy
faceting or the render's dark sheen; turn the loincloth into a long kilt.

Per-image checks (redo at most once): head to soles in frame; true alpha; both hands open with four fingers plus thumb; bare chest and bare thighs;
round steel pauldrons; wide steel-banded belt with the round boss; closed mouth with a complete chin and beard.
