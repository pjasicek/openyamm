# Codex brief: HD reference views for MM9 Skraelos (mm9_skraelos_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_skraelos_claude/references_hd/`. Do not edit any other
file, do not run builds, do not call Meshy. Use your built-in image generation tool. There are no native sprites for MM9: the authority
is the ORIGINAL Might and Magic IX 3D model with its skin, shown in renders of that model.

This is a fantasy video-game character: Skraelos, an undead priest of the Afterworld in Might and Magic IX (he hears confessions and
grants absolution): a hooded figure in long dark robes with a bare SKULL for a face and SKELETAL bone hands. A restoration of an existing
2002 game character for a game mod. He is solemn and calm, not a monster in attack.

## Inputs (attached, in order)
1. `mm9_views.png`: renders of the ORIGINAL low-poly model with its skin, five views left to right: front three-quarter, front,
   a side view, back, the other side view. Grey is background. Design, layout, proportions and colour authority. The faceting, blur and
   low resolution are NOT the design. IGNORE the long pale bone staff and the small skull held in one hand: they are separate props and
   must NOT appear in your images.
2. `mm9_chest_views.png`: closer renders of the hood, skull face, bone necklace, tabard and sleeves, same five views (ignore the staff).
3. `mm9_head_views.png`: close renders of the skull in its hood, same five views.
4. `mm9_skirt_views.png`: close renders of the lower robe and its hem, same five views.
5. `mm9_skin_x4.png`: the original 256x256 skin enlarged, SURFACE MATERIAL AND COLOUR ONLY (skull face, jaw bone, black tooled robe
   cloth, rust-brown tabard with a ragged blood-stained lower edge, bone necklace, red eye). Never the shape.
6. (run 2 only) the selected three-quarter master `00_three_quarter_clean.png`. For 01-04 produce a TRUE transparent background with NO
   glow or halo around the figure.

## Deliverables (true transparent background, no floor, no shadow, no text, unresized returns, 1536x1024 LANDSCAPE so the spread arms fit)
| File | View |
|---|---|
| `00_three_quarter.png` | front three-quarter from the figure's RIGHT (he faces image left-of-centre and toward the viewer), camera at chest height slightly above |
| `01_front.png` | straight front; the figure's RIGHT arm on IMAGE LEFT |
| `02_back.png` | straight back; the figure's RIGHT arm on IMAGE RIGHT |
| `03_left.png` | pure 90-degree profile of the figure's LEFT side: he faces IMAGE LEFT |
| `04_right.png` | pure 90-degree profile of the figure's RIGHT side: he faces IMAGE RIGHT |

Run 1: generate `00_three_quarter.png` only, then stop. Run 2 (separate run): generate 01-04 with the selected 00 as an additional input so
all views are the SAME figure, SAME pose, SAME proportions and colours. At most ONE corrective regeneration per view; then select the better
and note any residual fault. Keep raw returns in `raw/`. Write `generation_runs.json` (id, prompt, inputs with sha256, output path, selected
flag, reason, superseded runs) and, after run 2, a `selected_views_review.png` contact sheet of the five selected views.

## Common prompt content (adapt per view)
TASK CONTEXT, FANTASY-GAME ASSET RESTORATION: faithful high-definition reconstruction of the EXISTING Might and Magic IX character
Skraelos from the supplied renders of its original 3D model, as a 3D modelling and texturing reference. Not a new design. A credible, fully
three-dimensional figure with semi-realistic game materials and sharp fine detail (heavy black wool with a dark grey-teal tooled /
embossed brocade pattern, coarse rust-brown wool, aged ivory bone). ONE complete figure from the top of the hood to the hem on the floor,
centred, both hands inside the frame with margin, never cropped.

Identity (exactly the layout of inputs 1-5):
- A tall, gaunt figure of about 1.75 m, standing upright, completely covered by his robes except the skull face and the bone hands.
- HEAD: a bare aged-ivory human SKULL (no skin, no flesh, no lips, no eyelids): smooth cranium hidden under the hood, deep round eye
  sockets each holding a small glowing red-orange ember, a pear-shaped nose cavity, cheekbones, the jaw CLOSED with both rows of teeth
  meeting in a calm, even, long grin (input 3 front). Real skull proportions, not a cartoon; calm, solemn, not snarling or screaming.
- HOOD: a deep BLACK hood covering the top, sides and back of the skull, its front edge framing the face closely, rising behind to a soft
  backward point (input 3 side views); it falls onto the shoulders.
- NECKLACE: a collar of long pale bone teeth / fangs strung round the neck, with a small bone skull pendant at the centre of the chest
  (input 2 front).
- ROBE: a long BLACK robe to the floor with long, slightly widening black sleeves covering the arms to the wrists, the cloth showing a dark
  grey-teal tooled / embossed ornamental pattern (input 5); the hem wide on the floor like a long cone, a little longer at the back. No feet
  visible.
- TABARD: over the black robe a long sleeveless RUST-BROWN wool over-robe (tabard), covering the shoulders and back, OPEN down the front
  from the neck so a wide strip of the black robe shows in the middle; its two front panels and back hang straight to about knee height,
  where the brown ends in a RAGGED, TORN, uneven lower edge with dark dried-red stains (inputs 1, 4, 5). Below it the black robe continues
  to the floor.
- HANDS: SKELETAL hands of aged ivory bone (no skin): five long separate bony fingers each (four fingers and a thumb) with visible knuckle
  joints, relaxed and slightly curled, open, clear air between the fingers, palms down. Nothing in them.
- COLOUR: as inputs 1 and 5: black hood and robe with dark teal-grey tooling, rust-brown tabard, ivory bone, red-orange ember eyes. Flat
  even studio light, no baked shadows (the image is baked into a texture).
- No staff, no held skull, no weapon, no book, no crown, no wings, no extra limbs, no visible spine or ribs.

Pose (identical in all views): standing upright, feet hidden under the hem; arms out to the sides sloping down about 30 degrees below
horizontal, the sleeves hanging from them, elbows nearly straight, wrists straight, clear air between the sleeves and the body. Head level,
looking ahead.

Camera: near-orthographic, even soft studio light, no drama in the light, no cast shadows on the figure, no rim light.

Do NOT: add flesh or a face to the skull; open the jaw wide or make him scream or snarl; let the hood hide the face; make the tabard a
different colour or close it over the front; show feet or legs; add a staff, a skull in the hand or anything held; add glowing magic,
smoke or particles; change the colours; crop any part; copy the blur or faceting.

Per-image checks (redo at most once): hood top to hem in frame; both hands in frame; true alpha; five bony fingers on each visible hand; a
bare skull with closed jaw and two small red ember eyes; black hood with a back point; bone-fang necklace with a skull pendant; open
rust-brown tabard ending in a ragged stained edge at the knees over a black floor-length robe; the side views show the figure facing the
stated image direction.
