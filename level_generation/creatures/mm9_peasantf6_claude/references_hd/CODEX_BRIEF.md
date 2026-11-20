# Codex brief: HD reference views for the MM9 elf townswoman PeasantF6, skin A (mm9_peasantf6_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_peasantf6_claude/references_hd/`. Do not edit any other
file, do not run builds, do not call Meshy. Use your built-in image generation tool. There are no native sprites for MM9: the authority is
the ORIGINAL Might and Magic IX 3D model with its skin, shown in renders of that model.

These views will be PAINTED onto an existing 3D body (built earlier for another MM9 townswoman on a near-identical MM9 mesh, with a new
head: hair, braid and elf ears). So the figure must have THAT body's pose, proportions and silhouette (input 5 and, in run 2, inputs 8-11)
and the head shape of input 6, while the face, hair colour, costume, colours and materials come from the MM9 renders (inputs 1-4).

## Inputs (attached, in order)
1. `references_hd/mm9_views_a.png`: renders of the ORIGINAL low-poly model with its original skin A, five views left to right: front
   three-quarter from the character's RIGHT (she faces image right and toward the viewer), front, character's LEFT side (faces IMAGE
   LEFT), back, character's RIGHT side (faces IMAGE RIGHT). Flat grey is background. Design, costume and colour authority. Its faceting,
   blur, low resolution and T-pose arms are NOT the design.
2. `references_hd/mm9_chest_views_a.png`: closer renders of the upper body (bodice, lacing, sleeves, belt, hair and braid), same five views.
3. `references_hd/mm9_head_views_a.png`: close renders of the head (front, left profile, three-quarter, right profile, back): face, hair,
   braid and ear authority.
4. `references_hd/mm9_skin_x4_a.png`: the original 256x256 skin enlarged 4x, SURFACE MATERIAL AND COLOUR ONLY.
5. `../mm9_peasantf5_claude/references_hd/00_three_quarter_clean.png`: POSE, BODY SHAPE AND SILHOUETTE AUTHORITY ONLY: the 3D body these
   views will be painted on (another woman in other clothes). Copy its pose, arm angle, hand shape, proportions, the shape of the bodice,
   the ROUNDED GATHERED SLEEVE HEADS at the shoulders, the SLIM close-fitting arms below them, the skirt and apron shape and length, the
   shoes. Do NOT copy her face, age, coif, high embroidered collar, blue pinafore, brooches, bare forearms or bracelets.
6. `references_hd/shape_head_clay.png`: grey clay renders of the NEW 3D head these views will be painted on (front, left side, three-quarter,
   right side, back): HEAD SHAPE AUTHORITY ONLY. The hair is a smooth rounded bob that covers the top, sides and back of the head down to
   the jaw line, close round the face, fuller at the back; a single thick plait (braid) leaves the hair at the nape and hangs down the
   upper back to between the shoulder blades; two long pointed elf ears come out of the hair above and behind the cheeks, pointing out,
   up and back. Paint exactly this hair outline, braid and ear placement.
7. (run 2 only) the selected `references_hd/00_three_quarter.png`.
8.-11. (run 2 only) `../mm9_peasantf5_claude/references_hd/01_front_clean.png`, `03_left_clean.png`, `02_back_clean.png`,
   `04_right_clean.png`: the same pose/silhouette authority per view (same rules as input 5).

## Deliverables (true transparent background, no floor, no shadow, no text, unresized returns, 1024x1536 PORTRAIT)
| File | View |
|---|---|
| `00_three_quarter.png` | front three-quarter from the character's RIGHT, camera at chest height slightly above (as input 5) |
| `01_front.png` | straight front; the character's RIGHT arm on IMAGE LEFT |
| `02_back.png` | straight back; the character's RIGHT arm on IMAGE RIGHT |
| `03_left.png` | pure 90-degree profile of the character's LEFT side: faces IMAGE LEFT |
| `04_right.png` | pure 90-degree profile of the character's RIGHT side: faces IMAGE RIGHT |

Run 1: generate `00_three_quarter.png` only, then stop. Run 2 (separate run): generate 01-04 with the selected 00 as an additional input so
all views are the SAME character, SAME pose, SAME proportions and colours. At most ONE corrective regeneration per view; then select the
better and note any residual fault. Keep raw returns in `raw/`. Write `generation_runs.json` (id, prompt, inputs with sha256, output path,
selected flag, reason, superseded runs) and, after run 2, a `selected_views_review.png` contact sheet of the five selected views.

## Common prompt content (adapt per view)
TASK CONTEXT - FANTASY-GAME ASSET RESTORATION: faithful high-definition reconstruction of an EXISTING Might and Magic IX character from the
supplied renders of its original 3D model, as a 3D texturing reference. Not a new design. A credible, fully three-dimensional character
with semi-realistic game materials and sharp fine detail (skin, face, hair strands, plaited braid, woven wool, linen, embroidery, cord
lacing, leather grain). ONE complete figure from the top of the head to the soles, centred, generous margins, never cropped.

Pose (identical in all views, exactly as input 5): standing upright, arms held down and out from the body at about 35 degrees as in input
5, clear air between the arms and the body; hands relaxed and open, five fingers; feet under the long skirt. Head level, looking forward.

Camera and light: near-orthographic, even soft neutral studio light, no dramatic light, no strong cast shadows on the body; genuine
transparent background, no floor, no shadow, no text.

Per-image checks (re-run before selecting): same identity, costume and colours as inputs 1-4; the pose and silhouette of input 5 (arms out,
gathered sleeve heads, slim lower sleeves, skirt and apron); the head shape of input 6 (rounded bob, braid at the back, elf ears); the
correct side faces the correct image side (03: faces IMAGE LEFT; 04: faces IMAGE RIGHT); whole figure inside the frame with margins;
true transparent background; 1024x1536.

## Identity
A YOUNG ELF townswoman, about 25 years old, ordinary slim build (the body of input 5), a calm, friendly, warm face with a gentle closed-lip
smile, eyes open and relaxed.
- Face and head (input 3): fair warm-peach skin, smooth young skin, a few faint freckles, blue eyes under fine light-brown brows, a small
  straight nose, natural soft pink lips (not red lipstick), closed mouth. HONEY-BLOND / golden-blond hair parted in the middle and swept
  back over the head into the rounded bob shape of input 6, gathered at the nape into ONE thick three-strand PLAIT that hangs down the
  upper back (input 3 back view). Long POINTED ELF EARS, skin coloured, coming out of the hair at the sides and pointing out, up and back,
  clearly visible in every view. No earrings.
- Costume (inputs 1, 2 and 4):
  - an OCHRE-BROWN / mustard-brown wool gown, long sleeves of the same brown from the shoulders (the rounded gathered sleeve heads of input
    5 are this brown wool) down to just below the elbows, and a full-length brown skirt to the ankles;
  - under it a CREAM linen chemise: it shows at the neck as a plain round collar with a short slit and a small tie at the front of the
    neck (the neck itself is bare skin, NO high collar), and from below the elbows to the wrists as loose cream sleeves ending in a narrow
    cream band at each wrist;
  - over the gown a fitted DARK BROWN BODICE / VEST open at the front, its edges bordered with a narrow dark band of tiny red and gold
    flowers (input 2), laced across the front over the cream chemise with criss-crossing cream cords; the vest back is the brown gown;
  - a BLACK leather belt at the waist with a small dark buckle at the front and two small pale bone/metal clips on it at the hips;
  - a long CREAM / off-white linen APRON from the belt to below the knees in front (as input 5's apron);
  - plain brown leather shoes. Bare hands with fair skin, no rings, no bracelets.

## Do NOT
- add a weapon, bag, hat, coif, scarf, hood, cloak, necklace, earrings, rings, bracelets, gloves; make her old or human (the ears are long
  and pointed); make the hair loose or long down the back (only the braid hangs down); give her a high collar; change colours; change the
  pose; crop; make the expression stern, fierce, cold or a wide grin; paint red lipstick.
