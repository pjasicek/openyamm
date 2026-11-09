# Codex brief: HD reference views for the MM9 Dwarf (mm9_dwarf_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_dwarf_claude/references_hd/`. Do not edit any other file, do not run
builds, do not call Meshy. Use your built-in image generation tool. There are no native sprites for MM9: the authority is the ORIGINAL Might and
Magic IX 3D model with its skin, shown in renders of that model.

This is a fantasy video-game character, an adult male dwarf warrior in leather and mail, a restoration of an existing 2002 game character for a game mod.

## Inputs (attached, in order)
1. `mm9_views.png`: renders of the ORIGINAL low-poly model with its skin, five views left to right: front three-quarter from the
   figure's RIGHT, front, figure's LEFT side (faces IMAGE LEFT), back, figure's RIGHT side (faces IMAGE RIGHT). Grey is background. Design, layout,
   proportions and colour authority. The faceting, blur and low resolution are NOT the design.
2. `mm9_waist_views.png`: close renders of the tunic, arms and boots, same five views.
3. `mm9_head_views.png`: close renders of head and chest, same five views. Face, helmet, horns and collar authority.
4. `mm9_skin_x4.png`: the original skin enlarged, SURFACE MATERIAL AND COLOUR ONLY.
5. (run 2 only) the selected `references_hd/00_three_quarter.png`.

## Deliverables (true transparent background, no floor, no shadow, no text, unresized returns, 1024x1024 SQUARE)
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
TASK CONTEXT: faithful high-definition reconstruction of the EXISTING Might and Magic IX "Dwarven Guard" from the supplied renders of its original 3D model,
as a 3D modelling and texturing reference. Not a new design. A credible, fully three-dimensional figure with semi-realistic game materials and sharp fine
detail (mail rings, stitching, studs, worn leather, hair strands). ONE complete figure from the horn tips to the soles, centred, both hands inside the frame with margin, never cropped.

Identity (exactly the layout of inputs 1-3):
- A short, very stocky adult male DWARF about 1.3 m tall to the helmet top: broad chest and shoulders, thick arms, short thick legs, big feet, head large for the body. Not fat, not a child.
- HEAD: a rugged man about 50, ruddy pale skin, broad nose, heavy brows, pale grey-blue eyes, a full short red-auburn beard and moustache ending in a blunt point on the chest, mouth closed under the moustache.
- HELMET: a plain polished steel-grey helmet covering the crown, the sides of the head and the whole back of the neck down to the collar (a rounded shell like a bucket from behind), an opening for the face only. The face opening and the lower rim are edged with a narrow dark band set with small gold studs and diagonal gold marks, as in input 3.
- HORNS: three ivory horns on the helmet, each with a brown wrapped base: one short straight spike on top of the crown, and two long horns curving out and up from the sides at temple height, as in input 3.
- COLLAR: a tan rough cloth yoke round the neck with a square-toothed gold-edged lower border on the chest and upper back. Small polished steel plates with gold edges and a stud or two lie on top of each shoulder.
- TUNIC: a sleeveless thick red-brown leather tunic with a soft hide nap, scattered small silver studs on the chest, closed all round, belted at the waist, gathered below the yoke at the back.
- BANDOLIER: one dark brown studded leather strap diagonally across the chest from the figure's LEFT shoulder (IMAGE RIGHT in a front view) to the belt, with a large pale square spiral buckle at mid chest. Front only, as in input 2: do not invent more straps.
- BELT: a brown leather belt with silver studs and a large pale round knotwork buckle at the front.
- SKIRT: below the belt the tunic continues as a short skirt to the upper thigh, slightly flared, standing clear of the thighs, a closed tube round the hips. Its hem is a wide band of grey chain mail edged in gold, higher at the sides and dipping in a shallow inverted V at the centre front as in input 2.
- SLEEVES: short grey chain-mail sleeves to above the elbow, ending in a gold zigzag border and a tan and gold patterned band.
- FOREARMS: bare, thick muscular forearms with pale skin, a broad brown and gold bracer with a round gold boss at the wrist.
- HANDS: strong hands in plain dark brown leather gloves with FIVE separate fingers (four fingers and a thumb), relaxed and slightly curled, clear air between the fingers. No weapons in them.
- LEGS: short very dark brown trousers, only a little visible below the skirt, ending inside the boots.
- BOOTS: heavy brown leather boots to below the knee: a tan rolled cuff at the top, a gold band with pale round studs under it, a wrapped ribbed leather shaft, and a big rounded smooth toe cap with a thick dark sole.
- No cape, no hood, no pouches, no scabbard, no shield, no weapons, no extra limbs.

Pose (identical in all views): standing upright, feet apart (about 35 cm between the feet), toes pointing forward; arms hanging out from the shoulders at about 35 degrees from vertical, elbows slightly bent, wrists straight, clear air between arms and body and between the hands and the skirt.

Camera: near-orthographic, even soft studio light, no drama in the light, no cast shadows on the figure, no rim light.

Do NOT: add weapons, a shield, a cloak or extra armour; change colours; crop any part; copy the blur or faceting; give him a modern look; add a nose guard or a visor; make the beard long or braided.

Per-image checks (redo at most once): horn tips to soles in frame; both hands in frame; true alpha; five fingers on each visible hand; three horns; the steel shell down to the collar at the back; bandolier on the correct side; closed skirt with mail hem; boots with cuff and gold band.
