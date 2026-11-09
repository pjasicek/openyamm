# Codex brief: HD reference views for the MM9 Jarl Sven Svenssen ("Sven Forkbeard") (mm9_sven_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_sven_claude/references_hd/`. Do not
edit any other file, do not run builds, do not call Meshy. Use your built-in image generation tool. There are no native
sprites for MM9: the authority is the ORIGINAL MM9 3D model with its skin, shown in renders made from that model.

## Inputs (attached, in order)
1. `references_hd/mm9_views.png` — renders of the ORIGINAL Might and Magic IX low-poly model with its original skin,
   five views left to right: front three-quarter from the character's RIGHT (he faces image right and toward the
   viewer), front, character's LEFT side (faces IMAGE LEFT), back, character's RIGHT side (faces IMAGE RIGHT). Flat
   grey is background. This is the design, costume, POSE, proportions and colour authority. Its faceting, blur and low
   resolution are NOT the design.
2. `references_hd/mm9_head_views.png` — close renders of the same model's head (three-quarter, front, left profile,
   back, right profile): the face and hair authority.
3. `references_hd/mm9_skin_x4.png` — the original 256x256 skin texture enlarged 4x, SURFACE MATERIAL AND COLOUR ONLY
   (face painting, hair with braids, chain mail, red quilted vest, fur trim, belt, bracer, breeches, boots). Never the
   design or shape.
4. (run 2 only) the selected `references_hd/00_three_quarter.png`.

## Deliverables (true transparent background, unresized returns, 1536x1024 landscape so the spread arms fit)
| File | View |
|---|---|
| `00_three_quarter.png` | front three-quarter from the character's RIGHT, camera at chest height slightly above (as input 1 view 1) |
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
Magic IX character from the supplied renders of its original 3D model, as a 3D modelling and texturing reference.
Not a new design. A credible, fully three-dimensional character with semi-realistic game materials and sharp fine
detail (skin, face, beard and hair strands, chain-mail rings, quilted cloth, fur, leather grain, engraved metal), as if
a high-quality sculpt of the original model. ONE complete figure from the top of the head to the soles, centred,
generous margins, never cropped.

Pose (identical in all views, the model's bind pose as in input 1): standing upright; the arms held out to the sides
as in input 1 (straight, about 30-35 degrees below horizontal), clear air between the arms and the body; hands open
and flat, palms facing DOWN, the four fingers straight and close together with small gaps, the thumb separated; legs
straight and slightly apart with a clear gap between them, feet flat. Head level, looking forward.

Camera and light: near-orthographic, even soft neutral studio light, no dramatic light, no strong cast shadows on the
body; genuine transparent background, no floor, no shadow, no text.

Per-image checks (re-run before selecting): same identity, costume and colours as inputs 1–3; the pose above (arms out,
open flat hands with five fingers, legs apart); the correct side faces the correct image side (03: faces IMAGE LEFT;
04: faces IMAGE RIGHT); whole figure inside the frame with margins; true transparent background; 1536x1024.

## Identity
Sven Svenssen, called Sven Forkbeard, Jarl of Arslegard: a big, powerful HUMAN Norse warrior-chieftain of about
forty-five, tall with broad shoulders, a deep chest and thick muscular bare arms; upright and confident.
- Face and head (input 2): fair weathered skin with a warm tan and ruddy cheeks, a broad strong face, a straight
  strong nose, light blue eyes with laugh lines at their corners, thick brown brows; a hearty, friendly expression: a
  warm broad smile with the LIPS CLOSED (cheeks raised, no teeth showing); a FULL brown beard and moustache, thick and
  trimmed, a little longer at the chin; long thick wavy brown hair parted in the middle, falling past the ears to the
  shoulders, with a thin plaited BRAID at each side of the face in front of the ears (as input 3).
- Costume:
  - a sleeveless knee-length jerkin of dark crimson-maroon cloth with a fine quilted/knit diamond texture, open at the
    front, worn over a grey steel CHAIN-MAIL shirt that shows in a wide front panel from the neck down to the upper
    thighs; the jerkin has no sleeves, the arms are bare from the shoulders;
  - a thick tawny-gold FUR mantle collar lying over both shoulders front and back; the jerkin's front edges and hem
    are bordered with tawny fur and a thin gold line; at the front the hem dips to a point at each side of the mail;
  - a collar necklace of amber-gold plaques / bear teeth around the neck, and two round GOLD embossed brooches at the
    upper chest fastening the jerkin over the mail;
  - a wide dark red leather belt with small silver studs, a large round embossed GOLD buckle at the front and a grey
    braided-metal plate beside it;
  - on each wrist a wide engraved STEEL bracer (silver-grey with spiral scrollwork, white rim at each edge); bare hands;
  - brown leather breeches with a soft suede sheen and a narrow ORANGE braided stripe down the outer side of each leg;
  - mid-calf brown leather boots with a tawny fur cuff at the top, steel chevron plates on the shin front and crossed
    dark leather straps over the instep; flat soles.

## Do NOT
- add a weapon, shield, helmet, horns, cloak, cape, bag or gloves; add sleeves (the arms are bare); drop the necklace,
  brooches, bracers or fur; change colours (the jerkin is crimson-maroon, the mail steel grey, the fur tawny); make him
  thin, young or bald; change the pose; crop; stylise as a cartoon.
