# Codex brief: HD reference views for the MM9 shopkeeper PeasantM5 (mm9_peasantm5_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_peasantm5_claude/references_hd/`. Do not
edit any other file, do not run builds, do not call Meshy. Use your built-in image generation tool. There are no native
sprites for MM9: the authority is the ORIGINAL MM9 3D model with its skin, shown in renders made from that model.

These views will be PAINTED onto an existing 3D body (built earlier for another MM9 character, Markel, on almost the
same MM9 mesh). So the figure must have THAT body's pose, proportions and silhouette (input 4 / inputs 6-9), while the
face, hair, costume, colours and materials come from the MM9 renders (inputs 1-3).

## Inputs (attached, in order)
1. `references_hd/mm9_views.png` — renders of the ORIGINAL Might and Magic IX low-poly model with its original skin,
   five views left to right: front three-quarter from the character's RIGHT (he faces image right and toward the
   viewer), front, character's LEFT side (faces IMAGE LEFT), back, character's RIGHT side (faces IMAGE RIGHT). Flat
   grey is background. This is the design, costume and colour authority. Its faceting, blur and low resolution are
   NOT the design.
2. `references_hd/mm9_head_views.png` — close renders of the same model's head (front, left profile, three-quarter,
   right profile, back): the face and hair authority.
3. `references_hd/mm9_skin_x4.png` — the original 256x256 skin texture enlarged 4x, SURFACE MATERIAL AND COLOUR ONLY
   (face, brown hair and beard, tan-brown linen shirt with a braided neckline trim, belt with brass buckle, charcoal
   ribbed trousers, tan boots with a folded cuff). Never the design or shape.
4. `mm9_markel_claude/references_hd/00_three_quarter.png` — POSE, BODY SHAPE AND SILHOUETTE AUTHORITY ONLY: the 3D
   body these views will be painted on (another man in other clothes). Copy its pose and arm angle, its stocky build
   with broad ROUNDED shoulders and a belly, the shirt length to the hips flaring slightly below the belt, the leg
   stance, the boots with a thick rolled cuff below the knee, the head size and the beard volume. Do NOT copy his face,
   red hair, bald crown, braid, fur mantle, gold collar, medallion, tusk pendants, placket, laces, studded belt, gold
   buckle, forearm cuffs, rings, rust colour or fur boot cuffs.
5. (run 2 only) the selected `references_hd/00_three_quarter.png`.
6.-9. (run 2 only) `mm9_markel_claude/references_hd/01_front.png`, `03_left.png`, `02_back.png`, `04_right.png`:
   the same pose/silhouette authority per view (same rules as input 4).

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
(skin, face, hair and beard strands, linen weave, knitted rib, leather grain, stitching). ONE complete figure from the
top of the head to the soles, centred, generous margins, never cropped.

Pose (identical in all views, exactly as input 4): standing upright; the arms held out to the sides and down as in
input 4, clear air between the arms and the body; hands open and relaxed, palms facing DOWN, the four fingers straight
and close together with small gaps, the thumb separated; legs straight and slightly apart with a clear gap between
them, feet flat. Head level, looking forward.

Camera and light: near-orthographic, even soft neutral studio light, no dramatic light, no strong cast shadows on the
body; genuine transparent background, no floor, no shadow, no text.

Per-image checks (re-run before selecting): same identity, costume and colours as inputs 1–3; the pose and silhouette
of input 4 (arms out, open flat hands with five fingers, legs apart, rounded shoulders, belly) but none of Markel's
fur, gold or red hair; the correct side faces the correct image side (03: faces IMAGE LEFT; 04: faces IMAGE RIGHT);
whole figure inside the frame with margins; true transparent background; 1536x1024.

## Identity
A HUMAN shopkeeper of about 40, stocky and well fed (the body of input 4: broad rounded shoulders, a belly), a calm,
warm, friendly face.
- Face and head (input 2): fair, slightly ruddy skin; a broad face with a straight nose; warm hazel-brown eyes fully
  open with visible irises under natural brown brows; a FULL head of thick wavy auburn-brown hair (no bald crown),
  combed back from a natural hairline, covering the ears' tops and ending above the collar at the nape; a FULL SHORT
  brown BEARD and moustache, trimmed close along the jaw and chin (the beard volume of input 4, not longer); lips
  closed in a gentle, warm smile. Normal human ears.
- Costume (inputs 1 and 3): a long-sleeved warm TAN-BROWN linen SHIRT (soft woven linen, soft creases) with sleeves
  down to the wrists, loose on the upper arm and fitted on the forearm, ending in a simple cuff at the wrist; a V-shaped
  neck opening edged with a narrow BRAIDED brown-and-tan woven trim that runs round the neckline; the shirt is closed,
  plain (no placket, no laces, no pattern), worn over the belt and hanging to the hips with soft folds; a plain DARK
  BROWN leather BELT at the waist with a rounded BRASS buckle; dark CHARCOAL-GREY wool TROUSERS with a fine vertical
  knitted rib, slightly loose; tan-brown leather BOOTS to below the knee with a wide folded-down leather cuff and a
  small strap with a brass clasp. Bare hands with the same skin as the face, no rings.

## Do NOT
- add a weapon, apron, bag, cloak, fur, gold collar, medallion, necklace, jewellery, rings, bracers or gloves; give him
  a bald crown, red hair, a braid or a long beard; paint the arms bare; change colours; change the pose; crop; make the
  expression stern, fierce, sad or cold; open the mouth or show teeth.
