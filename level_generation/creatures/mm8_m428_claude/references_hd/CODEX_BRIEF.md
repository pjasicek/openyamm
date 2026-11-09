# MM8 female Dark Elf peasant (m428) HD reference brief

Scope: image generation only. Write only into `level_generation/creatures/mm8_m428_claude/references_hd/`.
No builds, no Meshy, no other files.

## Inputs (attached in this order)

1. `../../mm8_m428/references/identity.png`: the ORIGINAL native five-view sprite sheet (front, three-quarter
   front, side, three-quarter back, back). Design authority for identity, proportions, costume and colours.
   The transparent/white background is not part of the character.
2. `../../mm8_m428/aligned_2x/m428sa0.png`: a restored 2x front frame. Surface material reference ONLY (cloth
   sheen, lacing, buckle). It never sets the design.
3. (Run 2 only) `00_three_quarter.png`: the selected primary, identity and costume authority for views 01-04.

## Deliverables

Unresized image-generation returns, transparent background, 1024x1536 portrait, one figure each:

| File | View |
|---|---|
| `00_three_quarter.png` | front three-quarter showing the character's right side (~35 degrees from front), camera at upper-chest height, very slightly above |
| `01_front.png` | exactly front |
| `02_back.png` | exactly back |
| `03_left.png` | character's LEFT side: her nose points to IMAGE LEFT |
| `04_right.png` | character's RIGHT side: her nose points to IMAGE RIGHT |

## Prompt content (primary)

Use case: stylized-concept. Asset: faithful 3D modelling reference. Faithful high-definition reconstruction of the
EXISTING Might and Magic VIII FEMALE DARK ELF PEASANT from the attached original native sprite sheet; not a new
design. One adult woman, slender average build, natural human proportions, dark warm brown skin (not blue, grey or
purple), soft oval face with a straight nose and full lips, light grey eyes, long pointed elven ears that stand out
from the hair. Very long straight silver-white hair with a short straight fringe; it falls BEHIND the shoulders down
the back to the middle of the back, ending in a soft point; two narrow side locks frame the face and end at the
collarbones, lying on the upper chest, not over the arms.

Costume (keep exact coverage and colours): a floor-length dark forest-green dress. Fitted green bodice with two
vertical rows of small gold eyelets and orange-brown criss-cross lacing down the centre front; low square neckline
showing a pale grey linen chemise. The green bodice has narrow straps over the shoulders and a green band around
each upper arm; full puffed pale-grey linen chemise sleeves from the shoulder to the middle of the forearm, gathered
at the end into a short ruffled cuff; the lower forearms and hands are bare. Wide black leather belt at the natural
waist with a square gold buckle at the front. Below the belt the long green skirt is open in a narrow vertical split
at the centre front, showing the pale grey underskirt; the grey underskirt hem shows a hand-width below the green
hem all round, ending just above the floor. Simple black flat shoes, only the toes visible under the hem. Fine
linen weave, soft wool dress fabric with natural folds, subtle leather, individual hair strands; detailed believable
game-character sculpt.

Pose: FULL BODY neutral symmetrical A-pose, arms approximately 35 degrees away from vertical, elbows nearly straight,
palms forward, all five fingers on each hand open and visibly separated, hands well clear of the skirt; feet flat
and about hip-width apart, so the skirt hangs in a clean bell with a small gap between the hem and the floor.
Head upright, looking straight forward. No weapon or sheath: the native dagger and scabbard are modelled separately.

Camera and image: near-orthographic camera, even soft neutral studio lighting (no dramatic shadows), exactly ONE
figure, portrait 1024x1536 with generous complete margins around the hair, both hands and the hem. Genuine
transparent background with alpha 0 outside the figure and opaque figure; no floor, cast shadow, haze, lettering,
scenery or inset views.

Do NOT: add armour, jewellery, a hat, a weapon, a scabbard, extra belts or pouches, embroidery, a cape; change the
colours; shorten the dress or show the legs; make the hair cover the arms; glowing eyes; exaggerated ears, bust or
muscles; crop any part; fuse or drop fingers.

Views 01-04 use the same text with "Image 1 is the selected HD primary (exact identity and costume authority),
image 2 is the native sprite sheet (proportions and back-of-costume details)" and the view line from the table.
For `02_back`: back of the head, the long hair down the back ending in a point at mid-back, the bodice back plain
green with the belt horizontal, the skirt back closed (no split), backs of both open hands visible, no face.
For the side views: tell left from right by the nose direction given in the table; the arms stay in the same
A-pose, so the near arm is in front of the skirt and both hands are visible.

## Per-image checks (re-run before selecting a view)

- One figure, full body, nothing cropped, 1024x1536, true alpha (0 outside, opaque body).
- Five separated fingers on each hand, two pointed ears.
- Dress floor-length, green bodice with gold eyelets and orange lacing, grey puffed sleeves to mid-forearm,
  black belt with gold buckle, front split showing the grey underskirt, grey hem band.
- Hair long, white, behind the shoulders; side locks end at the collarbones.
- Same pose and proportions as the primary (views 01-04).
- Stop after ONE corrective regeneration per view.

## Records

`generation_runs.json`: per run the id, prompt (or prompt file), input paths with sha256, output path and sha256,
selected flag, reason, superseded runs. After all five pass, a `selected_views_review.png` contact sheet
(five views side by side on a mid-grey background with labels).
