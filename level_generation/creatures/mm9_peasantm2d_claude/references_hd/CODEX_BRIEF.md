# Codex brief: HD reference views for the MM9 young elf shopkeeper PeasantM2d (mm9_peasantm2d_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_peasantm2d_claude/references_hd/`. Do not
edit any other file, do not run builds, do not call Meshy. Use your built-in image generation tool. There are no native
sprites for MM9: the authority is the ORIGINAL Might and Magic IX 3D model with its skin, shown in renders of that model.

These views will be PAINTED onto an existing 3D body (built earlier for another MM9 townsman on a near-identical MM9
mesh). So the figure must have THAT body's pose, proportions and silhouette (input 5 / inputs 7-10), while the face,
hair colour, costume, colours and materials come from the MM9 renders (inputs 1-4).

## Inputs (attached, in order)
1. `references_hd/mm9_views_d.png` — renders of the ORIGINAL low-poly model with its original skin, five views left to
   right: front three-quarter from the character's RIGHT (he faces image right and toward the viewer), front,
   character's LEFT side (faces IMAGE LEFT), back, character's RIGHT side (faces IMAGE RIGHT). Flat grey is background.
   Design, costume and colour authority. Its faceting, blur, low resolution and T-pose arms are NOT the design.
2. `references_hd/mm9_waist_views_d.png` — closer renders of the tunic, sleeves, belt and trousers, same five views.
3. `references_hd/mm9_head_views_d.png` — close renders of the head (front, left profile, three-quarter, right profile,
   back): face, hair and ear authority.
4. `references_hd/mm9_skin_x4_d.png` — the original 256x256 skin enlarged 4x, SURFACE MATERIAL AND COLOUR ONLY.
5. `mm9_peasantm2_claude/references_hd/00_three_quarter_clean.png` — POSE, BODY SHAPE AND SILHOUETTE AUTHORITY ONLY: the
   3D body these views will be painted on (another, older man in other clothes). Copy its pose, arm angle, hand
   shape, proportions, leg stance, the shape of the tunic (length, flare of the skirt below the belt), the WIDE
   BELL-SHAPED SLEEVES that flare open at the wrist, the boot and shoe shape, head size and the hair VOLUME (long straight
   hair falling to the shoulders, behind the shoulders at the back). Do NOT copy its face, age, beard, white hair colour,
   olive tunic, V-neck braid, checked trousers or short laced boots.
6. (run 2 only) the selected `references_hd/00_three_quarter.png`.
7.-10. (run 2 only) `mm9_peasantm2_claude/references_hd/01_front_clean.png`, `03_left_clean.png`, `02_back_clean.png`,
   `04_right_clean.png`: the same pose/silhouette authority per view (same rules as input 5).

## Deliverables (true transparent background, no floor, no shadow, no text, unresized returns, 1024x1536 PORTRAIT)
| File | View |
|---|---|
| `00_three_quarter.png` | front three-quarter from the character's RIGHT, camera at chest height slightly above (as input 5) |
| `01_front.png` | straight front; the character's RIGHT arm on IMAGE LEFT |
| `02_back.png` | straight back; the character's RIGHT arm on IMAGE RIGHT |
| `03_left.png` | pure 90-degree profile of the character's LEFT side: faces IMAGE LEFT |
| `04_right.png` | pure 90-degree profile of the character's RIGHT side: faces IMAGE RIGHT |

Run 1: generate `00_three_quarter.png` only, then stop. Run 2 (separate run): generate 01–04 with the selected 00 as
an additional input so all views are the SAME character, SAME pose, SAME proportions and colours. At most ONE
corrective regeneration per view; then select the better and note any residual fault. Keep raw returns in `raw/`.
Write `generation_runs.json` (id, prompt, inputs with sha256, output path, selected flag, reason, superseded runs)
and, after run 2, a `selected_views_review.png` contact sheet of the five selected views.

## Common prompt content (adapt per view)
TASK CONTEXT — FANTASY-GAME ASSET RESTORATION: faithful high-definition reconstruction of an EXISTING Might and
Magic IX character from the supplied renders of its original 3D model, as a 3D texturing reference. Not a new
design. A credible, fully three-dimensional character with semi-realistic game materials and sharp fine detail
(skin, face, hair strands, woven wool, linen, braid, leather grain, cord lacing). ONE complete figure from the top
of the head to the soles, centred, generous margins, never cropped.

Pose (identical in all views, exactly as input 5): standing upright, arms held down and out from the body at about
35 degrees as in input 5, clear air between the arms and the body; hands relaxed and open, five fingers; legs
straight and slightly apart with a clear gap between them, feet flat. Head level, looking forward.

Camera and light: near-orthographic, even soft neutral studio light, no dramatic light, no strong cast shadows on the
body; genuine transparent background, no floor, no shadow, no text.

Per-image checks (re-run before selecting): same identity, costume and colours as inputs 1–4; the pose and silhouette
of input 5 (arms out, bell sleeves, legs apart); the correct side faces the correct image side (03: faces IMAGE LEFT;
04: faces IMAGE RIGHT); whole figure inside the frame with margins; true transparent background; 1024x1536.

## Identity
A YOUNG ELF townsman (shopkeeper), about 25 years old, ordinary lean build (the body of input 5), a calm, friendly,
warm face with a gentle closed-mouth expression.
- Face and head (input 3): fair warm-peach skin, smooth young skin, clean-shaven (no beard, no moustache, no stubble);
  light green-grey eyes under fine light-brown brows; a straight narrow nose; closed lips. Long straight DARK-BLOND /
  honey-blond hair with a centre parting, falling straight down past the ears to the shoulders at the sides and to
  the upper back behind (the hair volume of input 5). Long POINTED ELF EARS, skin coloured, sticking out sideways and
  slightly up and back from the sides of the head THROUGH the hair, clearly visible in every view. No earrings.
- Costume (inputs 1, 2 and 4): a long-sleeved pale CREAM / oatmeal linen shirt whose wide bell sleeves cover the arms
  to the wrists, each sleeve ending in a narrow brown-and-gold woven braid cuff band; over it a SLEEVELESS dark
  forest-GREEN tunic of fine textured wool (a subtle small scale-like / speckled weave, dark green with lighter
  green-grey flecks) reaching the upper thighs and flaring slightly below the belt, its armholes open at the
  shoulders so the cream sleeves show from the shoulder down; a brown-and-gold woven braid trim round the round
  neckline, straight down the centre front as a narrow placket strip from the collar to the hem, and round the hem;
  a small oval SILVER brooch / clasp on the placket at the upper chest; a plain DARK BROWN leather belt at the waist
  with a rectangular SILVER buckle at the front; loose dark chocolate-brown TROUSERS of mottled soft leather / suede;
  tall BOOTS wrapped to just below the knee with criss-crossing tan rope cords over brown leather, a small pale
  frayed cuff at the top, plain brown leather shoes. Bare hands with fair skin.

## Do NOT
- add a weapon, apron, bag, hat, cloak, necklace, earrings, jewellery, gloves or a beard; make him old or human (the
  ears are long and pointed); make the tunic sleeves green (the sleeves are cream linen); change colours; change the
  pose; crop; make the expression stern, fierce, cold or a wide grin.
