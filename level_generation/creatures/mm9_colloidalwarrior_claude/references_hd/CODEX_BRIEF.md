# Codex brief: HD reference views for the MM9 Colloidal Warrior (mm9_colloidalwarrior_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_colloidalwarrior_claude/references_hd/`. Do not edit any other
file, do not run builds, do not call Meshy. Use your built-in image generation tool. There are no native sprites for MM9: the authority is the
ORIGINAL Might and Magic IX 3D model with its skin, shown in renders of that model.

This is a fantasy video-game monster: a hulking humanoid made of living green slime and mud (a "colloidal" golem), a restoration of an existing
2002 game creature for a game mod. It has no genitals and no clothes: the groin is a smooth fold of slime under the belly.

## Inputs (attached, in order)
1. `mm9_views_b.png`: renders of the ORIGINAL low-poly model with its skin (tier "Colloidal Warrior", green), five views left to right: front
   three-quarter from the figure's RIGHT, front, figure's LEFT side (faces IMAGE LEFT), back, figure's RIGHT side (faces IMAGE RIGHT). Grey is
   background. Design, layout, POSE, proportions and colour authority. Faceting, blur, stretched texture and low resolution are NOT the design.
2. `mm9_head_views_b.png`: close renders of the head: face authority (front, three-quarter, left side, back).
3. `mm9_hand_views_b.png`: close renders of the right hand.
4. `mm9_skin_x4_b.png`: the original 256x256 skin enlarged, SURFACE MATERIAL AND COLOUR ONLY (it holds the face, top left, and body patches).
5. (run 2 only) the selected `references_hd/00_three_quarter.png`.

## Deliverables (true transparent background, no floor, no shadow, no text, unresized returns, 1024x1536 portrait)
| File | View |
|---|---|
| `00_three_quarter.png` | front three-quarter from the figure's RIGHT, camera at chest height slightly above (as input 1 view 1) |
| `01_front.png` | straight front |
| `02_back.png` | straight back |
| `03_left.png` | pure 90-degree profile of the figure's LEFT side: faces IMAGE LEFT |
| `04_right.png` | pure 90-degree profile of the figure's RIGHT side: faces IMAGE RIGHT |

Run 1: generate `00_three_quarter.png` only, then stop. Run 2 (separate run): generate 01-04 with the selected 00 as an additional input so all
views are the SAME figure, SAME pose, SAME proportions and colours. At most ONE corrective regeneration per view; then select the better and note
any residual fault. Keep raw returns in `raw/`. Write `generation_runs.json` (id, prompt, inputs with sha256, output path, selected flag, reason,
superseded runs) and, after run 2, a `selected_views_review.png` contact sheet.

## Common prompt content (adapt per view)
TASK CONTEXT: faithful high-definition reconstruction of the EXISTING Might and Magic IX "Colloidal Warrior" from the supplied renders of its
original 3D model, as a 3D modelling and texturing reference. Not a new design. A credible, fully three-dimensional creature with semi-realistic
game materials and sharp fine detail. ONE complete figure from the top of the head to the feet, centred, generous margins, never cropped.

Identity (exactly the layout of inputs 1-4):
- A squat, very heavy, hunched humanoid about 2 m tall made of thick glossy olive-green slime: a huge round pot BELLY that hangs over the groin,
  heavy sagging man-breasts, very broad sloping shoulders, short thick column legs set wide apart, long thick arms whose hands hang beside the
  knees. The silhouette is pear-shaped and wide at the hips.
- HEAD (input 2): NO NECK. A rounded dome of slime rising straight out of the shoulders and upper chest like a hood, slightly pointed on top.
  The face sits low on the front of this dome: a heavy ridged brow with small horn-like nubs along the top, two narrow slanted glowing ORANGE
  slit eyes in dark deep sockets, a short hooked beak-like nose, a very wide evil GRIN with rows of small yellowish pointed teeth between dark lips,
  cheeks in thick folds. Under the mouth a stack of three or four thick horizontal folds of slime (a layered throat like a toad's) runs down to the chest.
- SURFACE (input 4): wet, glossy, gelatinous slime with soft specular highlights, olive and yellow-green with darker mossy blotches and spots on the
  belly, chest, back and thighs (like algae under the surface), lighter yellow-green on the arms, soft lumpy folds and drips; NOT fur, NOT
  scales, NOT rock. Opaque.
- HANDS (input 3): big, thick slimy hands, RELAXED and slightly curled, NOT fists: four long thick separate fingers and a thick separate thumb,
  blunt rounded fingertips, no nails. Fingers slightly apart so each finger reads.
- FEET: large flat webbed feet like a toad's or a frog's: three to four thick rounded toes joined by webbing that spreads into a wide flipper
  in front of the leg, soles flat on the ground.
- No tail. No clothes, no belt, no armour, no jewellery, no weapons, no hair.

Pose (identical in all views, the model's bind pose as in input 1): standing upright with a slight forward hunch of the upper back, legs straight
and wide apart, feet pointing forward; arms held away from the body and down at about 35 degrees from vertical, elbows slightly bent, palms facing
backward and slightly inward, clear air between arms and body, clear air between the legs. Head level, looking straight ahead.

Camera: near-orthographic, even soft studio light, no drama in the light, no cast shadows on the figure, no rim light.

Do NOT: add clothes or weapons; add a tail or hair; make it translucent; change colours; crop any part; close the hands into fists; give it a
neck; copy faceting, stretched texture or the render's dark sheen.

Per-image checks (redo at most once): head to feet in frame; true alpha; no neck, face low on the dome with two orange slit eyes, beak nose and a
toothy grin; throat folds; pot belly; open hands with four fingers plus thumb; webbed toad feet; glossy green slime with darker mottling.
