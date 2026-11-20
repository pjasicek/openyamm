# Codex brief: HD reference views for the MM9 Markel the Great (skin MARKEL) (mm9_markel_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_markel_claude/references_hd/`. Do not
edit any other file, do not run builds, do not call Meshy. Use your built-in image generation tool. There are no native
sprites for MM9: the authority is the ORIGINAL MM9 3D model with its skin, shown in renders made from that model.

## Inputs (attached, in order)
1. `references_hd/mm9_views.png` — renders of the ORIGINAL Might and Magic IX low-poly model with its original skin,
   five views left to right: front three-quarter from the character's RIGHT (he faces image right and toward the
   viewer), front, character's LEFT side (faces IMAGE LEFT), back, character's RIGHT side (faces IMAGE RIGHT). Flat
   grey is background. This is the design, costume, POSE, proportions and colour authority. Its faceting, blur and low
   resolution are NOT the design.
2. `references_hd/mm9_head_views.png` — close renders of the same model's head (front, left profile, three-quarter,
   right profile, back): the face and hair authority.
3. `references_hd/mm9_skin_x4.png` — the original 256x256 skin texture enlarged 4x, SURFACE MATERIAL AND COLOUR ONLY
   (face painting, hair, beard, tunic cloth, fur mantle, placket, gold collar, belt, cuffs, hands, trousers, boots).
   Never the design or shape.
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
detail (skin, face, beard and hair strands, fur, wool weave, leather grain, stitching, gold metal), as if a
high-quality sculpt of the original model. ONE complete figure from the top of the head to the soles, centred,
generous margins, never cropped.

Pose (identical in all views, the model's bind pose as in input 1): standing upright; the arms held out to the sides
as in input 1 (straight, about 35 degrees below horizontal), clear air between the arms and the body; hands open
and flat, palms facing DOWN, the four fingers straight and close together with small gaps, the thumb separated; legs
straight and slightly apart with a clear gap between them, feet flat. Head level, looking forward.

Camera and light: near-orthographic, even soft neutral studio light, no dramatic light, no strong cast shadows on the
body; genuine transparent background, no floor, no shadow, no text.

Per-image checks (re-run before selecting): same identity, costume and colours as inputs 1–3; the pose above (arms out,
open flat hands with five fingers, legs apart); the correct side faces the correct image side (03: faces IMAGE LEFT;
04: faces IMAGE RIGHT); whole figure inside the frame with margins; true transparent background; 1536x1024.

## Identity
Markel the Great, a wealthy, jovial HUMAN Norse merchant-lord of about fifty: stocky and well fed, broad chest and a
slight belly, upright and confident.
- Face and head (inputs 2, 3): fair skin with warm rosy cheeks and nose, a broad friendly face, clear light BLUE eyes
  fully open with visible irises, relaxed natural brows (not knitted, not angry), fine laughter lines at the eyes, a
  pleasant closed-mouth half smile, natural lips (no pout). HAIR: bald on the crown and high forehead (deeply receding
  hairline, skin on the top of the head), with thick wavy coppery RED-ginger hair at the sides and back falling to the
  nape, gathered at the back into a short braid. A FULL thick copper-red beard and moustache, wavy, trimmed to the jaw,
  with two small gold beads in the beard at the chin.
- Costume:
  - a long-sleeved rust-brown (red-brown) knitted wool tunic reaching to the upper thigh, its hem bordered with a
    narrow twisted gold rope trim;
  - a cream-white FUR mantle over the shoulders and upper arms: shaggy long pale fur covering the shoulders and the
    upper chest and upper back, ending in ragged pointed tufts on the chest, the back (a V down to the shoulder blades)
    and over the upper arms to just above the elbows;
  - down the centre front a cream linen placket with two black laces crossed over it, bordered on both sides by a
    vertical gold braided band;
  - a gold collar/torc at the neck with cream-gold boar-tusk pendants and an oval GOLD embossed medallion hanging on
    the upper chest;
  - a wide ornate gold-trimmed belt: dark band with a row of small cream and gold studs between gold edge lines, and a
    large oval gold buckle with a cream inner ring and a small red-gold gem at the centre;
  - on each forearm, a dark brown leather cuff with fine gold scrollwork from mid-forearm to the wrist; bare hands with
    a few GOLD RINGS on the fingers;
  - dark brown vertically ribbed (striped) wool trousers, straight;
  - tall light-brown leather boots to mid-calf with a turned-down cream-white fur cuff at the top, flat soles.

## Do NOT
- add a weapon, cloak, crown, helmet, hat, bag, book or gloves; drop the fur mantle, placket, medallion, belt or
  cuffs; change colours (the tunic is rust-brown, the fur cream-white, the hair and beard copper-red); give him a full
  head of hair on top or make him young; angry or squinting eyes; change the pose; crop; stylise as a cartoon.
