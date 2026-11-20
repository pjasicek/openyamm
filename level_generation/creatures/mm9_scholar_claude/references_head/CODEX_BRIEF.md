# Codex brief: HD HEAD turnarounds for the MM9 Bembridge Scholars, two faces on one body (mm9_scholar_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_scholar_claude/references_head/`. Do not edit any other file,
do not run builds, do not call Meshy. Use your built-in image generation tool. There are no native sprites for MM9: the authority is the
ORIGINAL MM9 3D model with its two skins, shown in renders of that model.

The same body carries two faces in the original game: face **A** (the Scholar: a calm man of about 40 with a long copper-ginger beard and
long copper-ginger hair under a very dark navy cap) and face **B** (the Master Scholar: a kindly old man of about 70 with a long white beard
and long white hair under a mid-blue cap). Make face A first, then face B on the SAME head shape, pose, cap shape, beard and hair shape.

## Inputs (attached, in order)
1. `references_hd/mm9_head_views_1.png`: close renders of the ORIGINAL model's head with skin A, five views (three-quarter from his right,
   front, his left side facing IMAGE LEFT, back, his right side facing IMAGE RIGHT): FACE A, HAIR, BEARD AND CAP AUTHORITY. Low resolution,
   faceting and dark shading are NOT the design.
2. `references_hd/00_three_quarter_clean.png`: the approved HD body master with face A: identity, face, cap, beard and colours of the HD look.
3. `references_hd/01_front_clean.png`: the approved HD front master (face A, front).
4. `references_hd/mm9_skin_x4_1.png`: skin A enlarged, SURFACE MATERIAL AND COLOUR ONLY (face, beard, hair and cap texels at the top left).
5. `references_hd/mm9_head_views_3.png`: the same five views with skin B: FACE B, WHITE HAIR AND BEARD, MID-BLUE CAP AUTHORITY.
6. `references_hd/mm9_skin_x4_3.png`: skin B enlarged, SURFACE MATERIAL AND COLOUR ONLY.

## Deliverables (true transparent RGBA background, 1254x1254 or the closest supported square size, unresized returns)
| File | View |
|---|---|
| `a_01_front.png` | face A: perfectly straight FRONT bust, face and shoulders square to the camera (generate FIRST) |
| `a_00_three_quarter.png` | face A: front three-quarter bust from his RIGHT side (he looks toward IMAGE RIGHT, as input 2), eye level |
| `a_02_profile.png` | face A: pure 90-degree profile of his LEFT side: the face points to IMAGE LEFT |
| `a_03_back.png` | face A: straight BACK of the head and shoulders |
| `b_01_front.png`, `b_00_three_quarter.png`, `b_02_profile.png`, `b_03_back.png` | face B, the same four views, made with the selected A view of the same name as an extra input (same framing, head shape, cap shape, beard and hair shape, stole and pose; only face, age, hair/beard colour and the cap colour change) |

Generate a_01 first; then a_00, a_02, a_03 with the selected a_01 as an extra input. Then the b_ views, each with the A view of the same
name. At most ONE corrective regeneration per view; keep raw returns in `raw/`. Write `generation_runs.json` (id, view, prompt, inputs with
sha256, output path, selected flag, reason, superseded runs, size, alpha extrema) and a `selected_views_review.png` contact sheet of the
eight selected views.

## Common prompt content
TASK CONTEXT, GAME ASSET: faithful high-definition 3D modelling and TEXTURING head reference of an EXISTING Might and Magic IX character
(inputs 1-3, 5). Not a new design. Output ONE bust only: the whole head with its cap, hair and the full beard, the neck and the top of the
shoulders with the charcoal stole and the top of its gold chain, centred with generous margins, never cropped. Near-orthographic camera at
eye level, head level, a calm warm expression, LIPS CLOSED (no teeth showing), the moustache over the upper lip and the lips just visible
between moustache and beard. Even soft neutral studio lighting, no dramatic light, no rim light, no strong shadows (the image is baked into
a texture). Sharp fine detail: skin pores, brows, lashes, lips, individual hair and beard strands, felt weave. ONE natural brow per eye, ONE
natural lip line, no pale band under the lower lids, no makeup. Clean edges between skin, hair, beard and cap: each keeps its own colour, a
soft natural hairline under the cap.

## Identity (both faces)
- CAP: a soft floppy felt scholar's cap (beret-like bonnet) sitting on top of the head and tilted back, its brim rolled, a little wider than
  the head, as input 1. Face A: very dark navy; face B: mid royal blue.
- HAIR: long thick straight hair falling from under the cap to the shoulders at the sides and down the back to the shoulder blades
  (input 1 back view); ears covered by the hair.
- BEARD: a full long beard with a moustache, reaching the upper chest in a rounded point, as input 1.
- Face A: about 40, lean kind face, fair skin, blue-grey eyes, straight brows, a straight nose; hair, brows and beard COPPER-GINGER.
- Face B: about 70, the same head shape, fair rosy skin with soft wrinkles, crow's feet, kind blue eyes, bushy white brows; hair and beard
  WHITE with a faint silver grey.

Per-image checks (re-run before selecting): the right face; the requested view (_02 faces IMAGE LEFT); lips closed; eyes open; whole head,
cap and beard inside the frame; true transparent background; square; one brow per eye.

## Do NOT
change the cap colours; make either face stern, fierce, cold or sinister; show teeth; add a hood, a crown, glasses or jewellery other than
the chain on the stole; show the ears; stylise as a cartoon; add text, a floor, a background or a shadow; crop.
