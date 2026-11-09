# Codex brief: HD reference views for the MM9 Rotter (mm9_zombie_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_zombie_claude/references_hd/`. Do not edit any
other file, do not run builds, do not call Meshy. Use your built-in image generation tool. There are no native sprites for
MM9: the authority is the ORIGINAL Might and Magic IX 3D model with its skin, shown in renders of that model.

This is a fantasy video-game undead monster, a restoration of an existing 2002 game character for a game mod. Keep the decay
stylised game art: dry leathery skin, old dark scabs and dried dark-red patches, not realistic wounds.

## Inputs (attached, in order)
1. `references_hd/mm9_views_a.png`: renders of the ORIGINAL low-poly model with its skin, five views left to right: front
   three-quarter from the figure's RIGHT (it faces image right and toward the viewer), front, figure's LEFT side (faces IMAGE LEFT),
   back, figure's RIGHT side (faces IMAGE RIGHT). Grey is background. Design, layout, POSE, proportions and colour authority.
   Faceting, blur, the shiny white streaks and low resolution are NOT the design (those streaks are render artefacts).
2. `references_hd/mm9_head_views_a.png`: close renders of head and shoulders: the face and hair authority.
3. `references_hd/mm9_shin_views.png`: close renders of the figure's RIGHT lower leg (it stands on IMAGE LEFT in a front view).
4. `references_hd/mm9_skin_x4_a.png`: the original 256x256 skin enlarged, SURFACE MATERIAL AND COLOUR ONLY.
5. (run 2 only) the selected `references_hd/00_three_quarter.png`.

## Deliverables (true transparent background, no floor, no shadow, no text, unresized returns, 1024x1536 portrait)
| File | View |
|---|---|
| `00_three_quarter.png` | front three-quarter from the figure's RIGHT, camera at chest height slightly above (as input 1 view 1) |
| `01_front.png` | straight front; the figure's RIGHT arm and the bone shin on IMAGE LEFT |
| `02_back.png` | straight back; the figure's RIGHT arm and the bone shin on IMAGE RIGHT |
| `03_left.png` | pure 90-degree profile of the figure's LEFT side: faces IMAGE LEFT; the wrapped trouser leg is nearest |
| `04_right.png` | pure 90-degree profile of the figure's RIGHT side: faces IMAGE RIGHT; the bone shin is nearest |

Run 1: generate `00_three_quarter.png` only, then stop. Run 2 (separate run): generate 01-04 with the selected 00 as an additional
input so all views are the SAME figure, SAME pose, SAME proportions and colours. At most ONE corrective regeneration per view; then
select the better and note any residual fault. Keep raw returns in `raw/`. Write `generation_runs.json` (id, prompt, inputs with
sha256, output path, selected flag, reason, superseded runs) and, after run 2, a `selected_views_review.png` contact sheet.

## Common prompt content (adapt per view)
TASK CONTEXT: faithful high-definition reconstruction of the EXISTING Might and Magic IX "Rotter" zombie from the supplied renders
of its original 3D model, as a 3D modelling and texturing reference. Not a new design. A credible, fully three-dimensional figure
with semi-realistic game materials and sharp fine detail (dry cracked leathery skin, individual hair strands, coarse woven cloth,
rope). ONE complete figure from the hair to the soles, centred, generous margins, never cropped.

Identity (exactly the layout of inputs 1-3):
- A lean, gaunt adult MALE human corpse about 1.85 m tall, shoulders a little broad, ropey muscle under dried skin: chest and
  stomach muscles visible but sunken. NOT bulky, NOT a skeleton.
- SKIN: dry yellow-olive and brown leathery skin, darker in the hollows.
- BARE TORSO: no shirt. A large dark rotted patch on his LEFT chest (IMAGE RIGHT in a front view), a short stitched or split gash on his RIGHT
  chest (IMAGE LEFT in a front view), smaller dark-red patches on the shoulders and upper arms; on the back a wide patch of dark rot across the
  shoulder blades, as in input 1.
- HEAD: shrunken, skull-like human head. Sunken dark eye sockets with small dull eyes, a shrunken nose, gaunt cheeks; lips drawn back in a
  wide rictus GRIN showing the upper and lower teeth, mouth closed or barely parted, teeth together. A tear in his LEFT cheek shows the back teeth.
  A complete human chin and jaw. Ordinary human ears hidden by the hair.
- HAIR: matted brown hair, close to the skull like a thick cap, falling straight to the nape and down over the ears to the jaw line, as in inputs 1 and 2. No bald top.
- WAIST: a rope belt tied in a knot at the front, over the top of the trousers, with a few short torn cloth tatters hanging tight against the belly and hips (no more than 10 cm, no skirt).
- TROUSERS: tight, torn dark brown coarse trousers, close-fitting on the legs like the model, patched and rotted. The cloth is missing round both knees, where
  bare olive skin shows, with a jagged edge above the knee.
- RIGHT LOWER LEG (IMAGE LEFT in a front view): a wide torn cuff ends just below the knee in long jagged cloth points. Below it the calf flesh is gone: a pale bare SHIN BONE with
  dark-red dried sinew strips clinging to it, then a jagged torn cuff at the ankle above the foot. See input 3.
- LEFT LOWER LEG (IMAGE RIGHT in a front view): the trouser continues to the ankle, with brown cloth wrappings bound round it in a crossed pattern.
- FEET: BARE decayed feet with five toes each, olive skin, a few dark bands of cloth wrapped round the instep. Toes visible.
- ARMS: bare olive skin; dark cloth bands wrapped round the forearm just above the wrist on both arms.
- HANDS: gaunt human hands with FIVE long separate fingers (four fingers and a thumb) with dark broken nails; fingers open and spread, clear air between them.
- No weapons, no armour, no extra limbs, no jewellery, no shirt.

Pose (identical in all views, the model's bind pose as in input 1): standing upright, legs straight and spread wide (feet about 80 cm apart), toes pointing forward; arms held out to the sides
just below horizontal and swung somewhat forward as in the side views of input 1, a slight bend at the elbows, palms down, clear air between arms and body. Head level, looking straight ahead.

Camera: near-orthographic, even soft studio light, no drama in the light, no cast shadows on the figure, no rim light.

Do NOT: add a shirt, armour, weapons, a skirt, long loose cloth, wings; change colours; crop any part; use the shiny white streaks; give him a modern look; add blood splatter or fresh gore.

Per-image checks (redo at most once): hair to soles in frame; true alpha; five fingers on each visible hand; bone shin on the figure's RIGHT leg; rope belt; grin with both rows of teeth; bare feet with toes.
