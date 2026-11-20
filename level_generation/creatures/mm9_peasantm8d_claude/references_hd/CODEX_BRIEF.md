# Codex brief: HD reference views for the MM9 old elf commoner PeasantM8d (mm9_peasantm8d_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_peasantm8d_claude/references_hd/`. Do not
edit any other file, do not run builds, do not call Meshy. Use your built-in image generation tool. There are no native
sprites for MM9: the authority is the ORIGINAL MM9 3D model with its skin, shown in renders made from that model.

These views will be PAINTED onto an existing 3D body (built earlier for another MM9 character on the very same MM9
mesh). So the figure must have THAT body's pose, proportions and silhouette (input 4 / inputs 6-9), while the face,
hair colour, costume, colours and materials come from the MM9 renders (inputs 1-3).

## Inputs (attached, in order)
1. `references_hd/mm9_views.png` — renders of the ORIGINAL Might and Magic IX low-poly model with its original skin,
   five views left to right: front three-quarter from the character's RIGHT (he faces image right and toward the
   viewer), front, character's LEFT side (faces IMAGE LEFT), back, character's RIGHT side (faces IMAGE RIGHT). Flat
   grey is background. This is the design, costume and colour authority. Its faceting, blur and low resolution are
   NOT the design.
2. `references_hd/mm9_head_views.png` — close renders of the same model's head (front, left profile, three-quarter,
   right profile, back): the face, hair and ear authority.
3. `references_hd/mm9_skin_x4.png` — the original 256x256 skin texture enlarged 4x, SURFACE MATERIAL AND COLOUR ONLY
   (face painting, white hair, green tweed, cream linen sleeves, belt, breeches, boots). Never the design or shape.
4. `mm9_forad_claude/references_hd/00_three_quarter.png` — POSE, BODY SHAPE AND SILHOUETTE AUTHORITY ONLY: the 3D body
   these views will be painted on (another person in other clothes). Copy its pose, arm angle, proportions, leg
   stance, boot shape, head size and the hair VOLUME (hair swept back from the face and gathered in a short low
   ponytail at the nape). Do NOT copy its face, skin tone, hair colour, open vest, bare chest and arms, bracers,
   necklace, sash or leather trousers.
5. (run 2 only) the selected `references_hd/00_three_quarter.png`.
6.-9. (run 2 only) `mm9_forad_claude/references_hd/01_front.png`, `03_left.png`, `02_back.png`, `04_right.png`: the
   same pose/silhouette authority per view (same rules as input 4).

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
(skin, wrinkles, face, hair strands, tweed weave, linen, leather grain, stitching). ONE complete figure from the top
of the head to the soles, centred, generous margins, never cropped.

Pose (identical in all views, exactly as input 4): standing upright; the arms held straight out to the sides and
slightly down as in input 4, clear air between the arms and the body; hands open and flat, palms facing DOWN, the
four fingers straight and close together with small gaps, the thumb separated; legs straight and slightly apart
with a clear gap between them, feet flat. Head level, looking forward.

Camera and light: near-orthographic, even soft neutral studio light, no dramatic light, no strong cast shadows on the
body; genuine transparent background, no floor, no shadow, no text.

Per-image checks (re-run before selecting): same identity, costume and colours as inputs 1–3; the pose and silhouette
of input 4 (arms out, open flat hands with five fingers, legs apart); the correct side faces the correct image side
(03: faces IMAGE LEFT; 04: faces IMAGE RIGHT); whole figure inside the frame with margins; true transparent
background; 1536x1024.

## Identity
An OLD ELF townsman (commoner), a lean wiry build (the body of input 4), an elderly but kindly, calm and warm face.
- Face and head (input 2): fair rosy-tan weathered skin with fine wrinkles on the forehead, round the eyes and the
  cheeks; clear light blue eyes under bushy WHITE brows; a straight nose; a full white WALRUS MOUSTACHE drooping
  round the corners of the mouth; clean-shaven chin and cheeks (no beard); a calm, gentle, slightly smiling closed
  mouth. Thick WHITE / silver-grey hair swept straight back from a high forehead, covering the top and back of the
  head, gathered at the nape into a short low ponytail (the hair volume of input 4). Long POINTED ELF EARS, skin
  coloured, sticking out sideways and slightly up and back from the sides of the head, clear of the hair. No
  earrings, no beads, no braids with beads.
- Costume (input 1 and 3): a long-sleeved pale CREAM / oatmeal linen undershirt whose sleeves cover the whole arm
  down to the wrists (slightly loose, soft creases); over it a mossy olive-GREEN flecked TWEED tunic (fine
  multicoloured speckled wool, dark green with olive and ochre flecks) with short cap sleeves over the shoulders,
  closed at the front up to a round collar, a short V slit at the throat laced with a thin brown cord through small
  brass eyelets; the tunic reaches the upper thighs below the belt; a plain DARK BROWN leather belt at the waist with
  a rectangular BRASS buckle at the front; dark chocolate-brown ribbed wool BREECHES, loose, with small frayed tears
  over the knees showing skin; tall tan-brown leather BOOTS to below the knee with a wide folded-down cuff and a
  small strap. Bare hands with fair skin.

## Do NOT
- add a weapon, apron, bag, hat, cloak, necklace, earrings, jewellery or gloves; give him a beard; make him young or
  human (the ears are long and pointed); paint the arms bare (they are in cream sleeves); open the tunic; change
  colours; change the pose; crop; make the expression stern, fierce or cold.
