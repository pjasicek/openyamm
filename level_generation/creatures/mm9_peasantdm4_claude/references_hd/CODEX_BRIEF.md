# Codex brief: HD reference views for the MM9 dwarf townsman PeasantDM4 (skin PeasantDM4a) (mm9_peasantdm4_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_peasantdm4_claude/references_hd/`. Do not
edit any other file, do not run builds, do not call Meshy. Use your built-in image generation tool. There are no native
sprites for MM9: the authority is the ORIGINAL MM9 3D model with its skin, shown in renders made from that model.

## Inputs (attached, in order)
1. `references_hd/mm9_views_a.png` — renders of the ORIGINAL Might and Magic IX low-poly model with its original skin,
   five views left to right: front three-quarter (he faces image right and toward the viewer), front, side facing
   IMAGE LEFT, back, side facing IMAGE RIGHT. Flat grey is background. This is the design, costume, POSE, proportions
   and colour authority. Its faceting, blur and low resolution are NOT the design.
2. `references_hd/mm9_head_views_a.png` — close renders of the same model's head (front, profile facing left,
   three-quarter, profile facing right, back): the face, cap, beard and hair authority.
3. `references_hd/mm9_skin_x4_a.png` — the original 256x256 skin texture enlarged 4x, SURFACE MATERIAL AND COLOUR ONLY
   (face painting, red hair and beard, ochre woven cloth, blue bands with gold knotwork, the silver knot emblem, cream
   linen shirt and undersleeves, brown leather belt, dark trousers, brown boots with a gold ornament). Never the design
   or shape.
4. (run 2 only) the selected `references_hd/00_three_quarter.png`.

## Deliverables (true transparent background, unresized returns, 1536x1024 landscape so the spread arms fit)
| File | View |
|---|---|
| `00_three_quarter.png` | front three-quarter, he faces image right and toward the viewer, camera at chest height slightly above (as input 1 view 1) |
| `01_front.png` | straight front; the character's RIGHT arm on IMAGE LEFT |
| `02_back.png` | straight back; the character's RIGHT arm on IMAGE RIGHT |
| `03_left.png` | pure 90-degree profile of the character's LEFT side: faces IMAGE LEFT |
| `04_right.png` | pure 90-degree profile of the character's RIGHT side: faces IMAGE RIGHT |

Run 1: generate `00_three_quarter.png` only, then stop. Arms at about 20 degrees below horizontal, and a hard-edged
opaque figure with no glow or halo around it. Run 2 (separate run): generate 01–04 with the selected 00 as an
additional input so all views are the SAME character, SAME pose, SAME proportions and colours. At most ONE corrective
regeneration per view; then select the better and note any residual fault. Keep raw returns in `raw/`.
Write `generation_runs.json` (id, prompt, inputs with sha256, output path, selected flag, reason, superseded runs)
and, after run 2, a `selected_views_review.png` contact sheet of the five selected views.

## Common prompt content (adapt per view)
TASK CONTEXT — FANTASY-GAME ASSET RESTORATION: faithful high-definition reconstruction of an EXISTING Might and
Magic IX character from the supplied renders of its original 3D model, as a 3D modelling and texturing reference.
Not a new design. A credible, fully three-dimensional character with semi-realistic game materials and sharp fine
detail (skin, face, beard and hair strands, woven wool, embroidered knotwork bands, linen, leather grain, stitching),
as if a high-quality sculpt of the original model. ONE complete figure from the top of the cap to the soles, centred,
generous margins, never cropped.

Pose (identical in all views, the model's bind pose as in input 1): standing upright; the arms held out to the sides
as in input 1: a near T-pose, the arms straight and only about 20 degrees below horizontal (the hands well above hip
height, roughly at chest-belly level; NOT a 30-45 degree A-pose), clear air between the arms and the body; hands open
and relaxed, palms facing DOWN, the four fingers straight and close together with small gaps, the thumb separated;
legs straight and slightly apart with a clear gap between them, feet flat. Head level, looking forward.

Camera and light: near-orthographic, even soft neutral studio light, no dramatic light, no strong cast shadows on the
body; genuine transparent background, no floor, no shadow, no text.

Per-image checks (re-run before selecting): same identity, costume and colours as inputs 1–3; dwarf proportions as
input 1; the pose above (arms out, open hands with five fingers, legs apart); the correct side faces the correct
image side (03: faces IMAGE LEFT; 04: faces IMAGE RIGHT); whole figure inside the frame with margins; true
transparent background; 1536x1024.

## Identity
A middle-aged DWARF townsman about fifty, short and stocky: a broad deep chest and wide shoulders, a large head, thick
arms, short sturdy legs (proportions exactly as input 1: the legs below the tunic are short).
- Face and head (input 2): fair skin with rosy cheeks, a broad friendly face, a broad nose, calm warm green-grey eyes
  OPEN with visible irises (relaxed, kindly; never staring, fierce or cold), one natural ginger eyebrow line over each
  eye, a gentle closed-mouth smile under the moustache; NO visible ears: thick copper-red (ginger) hair falls straight
  from under the cap over the ears to the shoulders at the sides and back; a full copper-red beard and moustache,
  thick and wavy, medium length, ending a little below the chin (to the top of the chest). The hair and beard are plain
  hair strands: NO beads, rings, ties, clasps or braid ornaments anywhere in the hair or beard.
- Cap: a snug rounded skullcap (a low brimless cap with a slightly peaked crown) of ochre-brown woven wool, with a band
  around its lower edge of dark blue cloth embroidered with a gold-tan running knotwork pattern, and a small silver
  Celtic-knot medallion on the front of the crown above the forehead.
- Costume:
  - an ochre-brown (golden-brown) woven wool tunic with wide elbow-length sleeves with puffed shoulders, each sleeve
    ending in a dark blue band with gold knotwork; over the chest an open-fronted vest panel edged in the same blue
    knotwork band and laced across a cream linen shirt with dark brown crossed laces;
  - a band of the cream linen shirt showing at the waist above the belt;
  - a brown leather belt with a small silver rectangular buckle;
  - below the belt the tunic skirt to mid-thigh, slightly flared, with a blue knotwork band at the hem;
  - cream linen undersleeves covering the forearms to the wrists, with a thin dark leather band at each wrist;
  - bare hands;
  - dark brown trousers;
  - brown leather boots to below the knee with a wide folded-down cuff and a small gold swirl ornament on each cuff,
    flat soles.

## Do NOT
- add a weapon, tool, apron, bag, cloak, cape, armour, gloves or extra jewellery; show the ears; put beads, rings or ties
  in the hair or beard; make the beard very long or braided into ropes; change colours (the tunic and cap are
  ochre-brown with dark blue bands, the hair and beard copper-red); change the pose or the dwarf proportions; crop;
  stylise as a cartoon; give him a fierce, frowning or cold expression.

## Run 1 result (Claude, 2026-11-02)
Selected `00_three_quarter.png` = `raw/run1_initial.png` with the halo removed (`scripts/clean_alpha.py`): arms 20 degrees
below horizontal as MM9's bind. Codex's own pick (`raw/run1_correction.png`, arms near horizontal) is kept in
`raw_codex/`. For run 2, keep the arms exactly as in input 4 (about 20 degrees below horizontal) and a hard-edged opaque
figure with no glow or halo.

Run 2 (Claude): all four selected returns accepted; halos removed by scripts/clean_alpha.py (Codex files in raw_codex/).
