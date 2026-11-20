# Codex brief: HD reference views for the MM9 dwarf townsman PeasantDM1 (skin PeasantDM1a) (mm9_peasantdm1_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_peasantdm1_claude/references_hd/`. Do not
edit any other file, do not run builds, do not call Meshy. Use your built-in image generation tool. There are no native
sprites for MM9: the authority is the ORIGINAL MM9 3D model with its skin, shown in renders made from that model.

## Inputs (attached, in order)
1. `references_hd/mm9_views_a.png` — renders of the ORIGINAL Might and Magic IX low-poly model with its original skin,
   five views left to right: front three-quarter from the character's RIGHT (he faces image right and toward the
   viewer), front, character's LEFT side (faces IMAGE LEFT), back, character's RIGHT side (faces IMAGE RIGHT). Flat
   grey is background. This is the design, costume, POSE, proportions and colour authority. Its faceting, blur and low
   resolution are NOT the design.
2. `references_hd/mm9_head_views_a.png` — close renders of the same model's head (front, left profile, three-quarter,
   right profile, back): the face, beard and hair authority.
3. `references_hd/mm9_skin_x4_a.png` — the original 256x256 skin texture enlarged 4x, SURFACE MATERIAL AND COLOUR ONLY
   (face painting, hair, blue wool, gold embroidery, linen undersleeves, belt, knitted leggings, boots). Never the
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

Run 1: generate `00_three_quarter.png` only, then stop. (Retry 2026-11-01: a first run 1 return had the arms about
30 degrees down and a translucent halo; it is kept in `superseded/`. Arms at 20 degrees below horizontal this time,
and a hard-edged opaque figure with no glow or halo around it.) Run 2 (separate run): generate 01–04 with the selected 00 as
an additional input so all views are the SAME character, SAME pose, SAME proportions and colours. At most ONE
corrective regeneration per view; then select the better and note any residual fault. Keep raw returns in `raw/`.
Write `generation_runs.json` (id, prompt, inputs with sha256, output path, selected flag, reason, superseded runs)
and, after run 2, a `selected_views_review.png` contact sheet of the five selected views.

## Common prompt content (adapt per view)
TASK CONTEXT — FANTASY-GAME ASSET RESTORATION: faithful high-definition reconstruction of an EXISTING Might and
Magic IX character from the supplied renders of its original 3D model, as a 3D modelling and texturing reference.
Not a new design. A credible, fully three-dimensional character with semi-realistic game materials and sharp fine
detail (skin, face, beard and hair strands, wool weave, embroidery, knitted wool, leather grain, stitching), as if a
high-quality sculpt of the original model. ONE complete figure from the top of the head to the soles, centred,
generous margins, never cropped.

Pose (identical in all views, the model's bind pose as in input 1): standing upright; the arms held out to the sides
as in input 1: a near T-pose, the arms straight and only about 20 degrees below horizontal (the hands well above hip
height, roughly at chest-belly level; NOT a 30-45 degree A-pose), clear air between the arms and the body; hands open
and flat, palms facing DOWN, the four fingers straight and close together with small gaps, the thumb separated; legs
straight and slightly apart with a clear gap between them, feet flat. Head level, looking forward.

Camera and light: near-orthographic, even soft neutral studio light, no dramatic light, no strong cast shadows on the
body; genuine transparent background, no floor, no shadow, no text.

Per-image checks (re-run before selecting): same identity, costume and colours as inputs 1–3; dwarf proportions as
input 1; the pose above (arms out, open flat hands with five fingers, legs apart); the correct side faces the correct
image side (03: faces IMAGE LEFT; 04: faces IMAGE RIGHT); whole figure inside the frame with margins; true
transparent background; 1536x1024.

## Identity
An ordinary adult DWARF townsman (commoner) about thirty-five, short and stocky: a broad deep chest and wide
shoulders, a large head, thick arms, short sturdy legs (proportions exactly as input 1: the legs below the tunic are
short).
- Face and head (input 2): fair ruddy skin, a broad face with strong cheekbones, a straight broad nose, grey-green
  eyes, auburn brows, a friendly half-smile with the mouth closed; a SHORT, close-trimmed full beard and moustache,
  ginger / strawberry-blond, following the jaw line (not long); thick ginger-blond hair to just above the shoulders,
  swept back from the forehead, covering the ears, with one thin braid on each side in front of the ear, each braid
  ending in a small silver ring clasp.
- Costume:
  - a dark slate-blue / steel-blue heavy wool tunic with a fine woven texture, short sleeves to the elbows, reaching
    to mid-thigh, slightly flared below the belt; a gold-embroidered knotwork band around the round neckline and
    across the yoke front and back, gold knotwork bands on the sleeve ends and a gold knotwork border above the hem;
    a short slit at the front of the neck;
  - a round silver medallion with a knot design on a thin leather cord on the chest;
  - on each forearm a cream-and-beige striped linen undersleeve from the elbow, a dark brown leather wrist band at
    each wrist, bare hands;
  - a wide dark brown leather belt with a square brass buckle;
  - dark brown knitted wool leggings;
  - brown leather boots with a very wide flared folded-down cuff just below the knee, a laced front with a small metal
    ornament, flat soles.

## Do NOT
- add a weapon, axe, apron, bag, hat, cloak, cape, armour or gloves; make the beard long; change colours (the tunic
  is slate-blue, the embroidery gold); change the pose or the dwarf proportions; crop; stylise as a cartoon.
