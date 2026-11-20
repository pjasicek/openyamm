# Codex brief: HD reference views for the MM9 Lesser Demon (mm9_stage1demon_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_stage1demon_claude/references_hd/`. Do not
edit any other file, do not run builds, do not call Meshy. Use your built-in image generation tool. There are no native
sprites for MM9: the authority is the ORIGINAL Might and Magic IX 3D model with its skin, shown in renders of that model.

This is a fantasy video-game demon monster, a restoration of an existing 2002 game character for a game mod. Stylised, no gore.

## Inputs (attached, in order)
1. `references_hd/mm9_views.png`: renders of the ORIGINAL low-poly model with its skin, five views left to right: front
   three-quarter from the figure's RIGHT (it faces image right and toward the viewer), front, figure's LEFT side (faces image
   left), back, figure's RIGHT side (faces image right). Grey is background. Design, layout, POSE, proportions and colour
   authority. Faceting, blur, shine streaks and low resolution are NOT the design.
2. `references_hd/mm9_head_views.png`: close renders of the head and shoulders: front, three-quarter, left profile, back.
   Head, horn and crest authority.
3. `references_hd/mm9_hand_foot_views.png`: close renders: top row the right hand from above, front and three-quarter
   (gauntlet, thumb and three long clawed fingers); bottom row the right foot from the front, side and three-quarter.
4. `references_hd/mm9_skin_x4.png`: the original 256x256 skin enlarged, SURFACE MATERIAL AND COLOUR ONLY.
5. (run 2 only) the selected `references_hd/00_three_quarter.png`.

## Deliverables (true transparent background with hard edges and no soft halo, no floor, no shadow, no text, unresized returns, 1024x1536 portrait)
| File | View |
|---|---|
| `00_three_quarter.png` | front three-quarter from the figure's RIGHT, camera at chest height slightly above (as input 1 view 1) |
| `01_front.png` | straight front |
| `02_back.png` | straight back |
| `03_left.png` | pure 90-degree profile of the figure's LEFT side: faces IMAGE LEFT |
| `04_right.png` | pure 90-degree profile of the figure's RIGHT side: faces IMAGE RIGHT |

Run 1: generate `00_three_quarter.png` only, then stop. Run 2 (separate run): generate 01-04 with the selected 00 as an
additional input so all views are the SAME figure, SAME pose, SAME proportions and colours. At most ONE corrective
regeneration per view; then select the better and note any residual fault. Keep raw returns in `raw/`. Write
`generation_runs.json` (id, prompt, inputs with sha256, output path, selected flag, reason, superseded runs) and, after
run 2, a `selected_views_review.png` contact sheet.

## Common prompt content (adapt per view)
TASK CONTEXT: faithful high-definition reconstruction of the EXISTING Might and Magic IX "Lesser Demon" from the supplied
renders of its original 3D model, as a 3D modelling and texturing reference. Not a new design. A credible, fully
three-dimensional figure with semi-realistic game materials and sharp fine detail (fine reptilian scales, layered forged
steel plates with worn edges, polished bone horns). ONE complete figure from the horn tips to the toe claws and the tail
tip, centred, generous margins, never cropped.

Identity (exactly the layout of inputs 1-3):
- BODY: a huge hulking demon about 2.6 m tall to the horn tips, hunched forward: massive rounded shoulders and a thick
  muscular upper back that rise above the head, a deep chest, a narrower muscular waist with a defined abdomen, thick
  arms longer than a man's, powerful thighs. Heavy but not fat.
- SKIN: deep crimson and maroon reptilian hide with fine pebbled scales, darker brown-black in the hollows, with
  smouldering orange-red streaks on the shoulders and upper arms, as in input 4. Matte with a slight sheen. No wounds,
  no blood.
- HEAD: a long reptilian, dragon-like head carried low and forward of the shoulders. A long snout, scaly crimson face,
  a heavy angry brow ridge in a V, two narrow slanted glowing yellow-orange eyes set close together under it. The MOUTH
  hangs OPEN: a gaping lower jaw, a red-pink mouth, rows of sharp ivory fangs along both jaws, a red tongue inside.
- HORNS: two thick pale bone-grey RAM horns, ridged, growing from the back of the skull behind the eyes, curving out
  sideways and forward in a wide C, the tips pointing forward and up level with the brow, a short sharp spur on each.
- NAPE CREST: behind the head, over the back of the neck, a dark steel crest of jagged plates with two tall dark steel
  horns that sweep up and back like a lyre, and a single tall steel spike in the middle between them.
- ARMOUR (dark gunmetal steel with silver-grey highlights, forged as layered jagged scale plates with dark outlines):
  - a jagged collar/bib of layered steel scale plates over the upper chest under the jaw, ending in points above the
    abdomen; the abdomen and lower chest are bare red skin;
  - a long back plate of layered steel scales down the spine from the nape to the waist, with a row of short steel
    spikes standing out along each shoulder blade and down the sides of the back;
  - a thin dark belt with small steel studs at the waist;
  - an armoured loin of layered jagged steel plates covering hips, buttocks and the front of the thighs to mid-thigh,
    like plated shorts; the inner and lower thighs show red scaly hide;
  - smooth black steel gauntlets from the elbow to the wrist, each with a fan of sharp steel flanges at the wrist;
  - dark steel greaves from below the knee to the ankle, jagged at the top, with a small spike at the back of the heel.
- HANDS: red scaly hands with FOUR digits: a thumb and three very long, thin, tapering fingers that end in sharp
  claw points, like long talons. Fingers open and slightly spread, hanging forward, clear air between them.
- FEET: big red scaly feet with THREE forward toes, each ending in a large curved pale ivory-tan claw. Flat on the
  ground plane.
- TAIL: a long thin red tail from the base of the spine, hanging down behind the legs nearly to the ground, ending in
  an orange-red arrowhead (spade) tip.
- No wings, no weapons, no cape, no cloth.

Pose (identical in all views, the model's bind pose as in input 1): standing, legs apart (feet about 60 cm apart), knees
slightly bent, toes forward; the torso leans forward a little with the shoulders hunched; arms held out to the sides and
down about 40 degrees below horizontal, a slight bend at the elbows, the long fingers hanging; clear air between arms and
body; head low and forward, looking straight ahead.

Camera: near-orthographic, even soft studio light, no drama in the light, no cast shadows on the figure, no rim light.

Do NOT: add wings, weapons, a cape, cloth or fur; change the colours; crop any part; add blood or gore; add a soft halo;
close the mouth; give the hands five fingers.

Per-image checks (redo at most once): horn tips to toe claws and tail tip in frame; true alpha; open mouth with fangs;
both ram horns and the steel nape crest; four digits with long talons on each visible hand; three clawed toes; tail with
arrowhead tip.
