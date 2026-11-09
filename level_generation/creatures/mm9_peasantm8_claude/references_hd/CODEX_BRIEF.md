# Codex brief: HD reference views for the MM9 shopkeeper PeasantM8 (mm9_peasantm8_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_peasantm8_claude/references_hd/`. Do not
edit any other file, do not run builds, do not call Meshy. Use your built-in image generation tool. There are no native
sprites for MM9: the authority is the ORIGINAL MM9 3D model with its skin, shown in renders made from that model.

These views will be PAINTED onto an existing 3D body (built earlier for another MM9 character on the very same MM9
mesh). So the figure must have THAT body's pose, proportions and silhouette (input 4 / inputs 6-9), while the face,
hair, costume, colours and materials come from the MM9 renders (inputs 1-3).

## Inputs (attached, in order)
1. `references_hd/mm9_views.png` — renders of the ORIGINAL Might and Magic IX low-poly model with its original skin,
   five views left to right: front three-quarter from the character's RIGHT (he faces image right and toward the
   viewer), front, character's LEFT side (faces IMAGE LEFT), back, character's RIGHT side (faces IMAGE RIGHT). Flat
   grey is background. This is the design, costume and colour authority. Its faceting, blur and low resolution are
   NOT the design.
2. `references_hd/mm9_head_views.png` — close renders of the same model's head (front, left profile, three-quarter,
   right profile, back): the face and hair authority.
3. `references_hd/mm9_skin_x4.png` — the original 256x256 skin texture enlarged 4x, SURFACE MATERIAL AND COLOUR ONLY
   (face painting, blond hair, cream linen sleeves, brown wool tunic, belt, striped trousers, boots). Never the design
   or shape.
4. `mm9_forad_claude/references_hd/00_three_quarter.png` — POSE, BODY SHAPE AND SILHOUETTE AUTHORITY ONLY: the 3D body
   these views will be painted on (another person in other clothes). Copy its pose, arm angle, proportions, leg
   stance, boot shape and head size. Do NOT copy its face, dark hair, PONYTAIL, skin tone, open vest, bare chest and
   arms, bracers, necklace, sash or trousers. This man has NO ponytail (his hair is short).
5. (run 2 only) the selected `references_hd/00_three_quarter.png`.
6.-9. (run 2 only) `mm9_forad_claude/references_hd/01_front.png`, `03_left.png`, `02_back.png`, `04_right.png`: the
   same pose/silhouette authority per view (same rules as input 4; ignore their ponytail).

## Deliverables (true transparent background, unresized returns, 1536x1024 landscape so the spread arms fit)
| File | View |
|---|---|
| `00_three_quarter.png` | front three-quarter from the character's RIGHT, camera at chest height slightly above (as input 4) |
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
(skin, face, hair strands, wool weave, linen, leather grain, stitching). ONE complete figure from the top of the head
to the soles, centred, generous margins, never cropped.

Pose (identical in all views, exactly as input 4): standing upright; the arms held straight out to the sides and
slightly down as in input 4, clear air between the arms and the body; hands open and relaxed, palms facing DOWN, the
four fingers straight and close together with small gaps, the thumb separated; legs straight and slightly apart
with a clear gap between them, feet flat. Head level, looking forward.

Camera and light: near-orthographic, even soft neutral studio light, no dramatic light, no strong cast shadows on the
body; genuine transparent background, no floor, no shadow, no text.

Per-image checks (re-run before selecting): same identity, costume and colours as inputs 1–3; the pose and silhouette
of input 4 (arms out, open flat hands with five fingers, legs apart) but NO ponytail; the correct side faces the
correct image side (03: faces IMAGE LEFT; 04: faces IMAGE RIGHT); whole figure inside the frame with margins; true
transparent background; 1536x1024.

## Identity
A middle-aged HUMAN townsman, a shopkeeper (about 45-50 years old), a lean build (the body of input 4), a calm,
mild, friendly and warm face.
- Face and head (input 2): fair pale-pink skin with a little colour in the cheeks; a long oval face with a straight
  long nose, light grey-blue eyes under thin light-brown brows, faint lines round the eyes; clean-shaven (no beard,
  no moustache, no stubble shadow); thin closed lips in a relaxed, slightly kind expression. A HIGH BALDING head: the
  forehead and the whole top of the head are bare skin back to the crown; short straight dark-blond / light honey-
  brown hair covers only the sides and the back of the head, combed back, lying flat against the skull and ending in
  a neatly trimmed edge at the nape just above the collar (no ponytail, no long hair). Normal human ears, visible.
- Costume (input 1 and 3): a long-sleeved pale CREAM / oatmeal linen undershirt whose sleeves cover the whole arm
  down to the wrists (fairly close-fitting, soft creases, a simple cuff at the wrist); over it a plain warm
  CHOCOLATE-BROWN wool TUNIC (soft, slightly felted wool, a fine subtle weave, no pattern, no flecks) with short cap
  sleeves over the shoulders, closed at the front up to a round collar, a short V slit at the throat laced with a
  thin brown leather cord, the cream undershirt showing in the slit; the tunic reaches the upper thighs below the
  belt with soft vertical folds; a plain DARK BROWN leather belt at the waist with a rectangular dull iron/pewter
  buckle at the front; dark brown wool TROUSERS with a fine vertical woven rib (thin darker stripes), slightly loose,
  with a small frayed tear over each knee; tan-brown leather BOOTS to below the knee with a wide folded-down cuff
  and a small strap. Bare hands with the same fair skin as the face.

## Do NOT
- add a weapon, apron, bag, hat, cloak, necklace, earrings, jewellery, gloves or a ponytail; give him a beard,
  moustache or a full head of hair; make him old or young; paint the arms bare (they are in cream sleeves); open the
  tunic; add patterns or flecks to the tunic; change colours; change the pose; crop; make the expression stern,
  fierce or cold.
