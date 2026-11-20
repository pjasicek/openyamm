# Codex brief (run 1): HD three-quarter primary for the MM7 Ghost (m242)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm7_m242_claude/references_hd/`.
Do not edit any other file, do not run builds, do not call Meshy.

This run produces ONLY the primary `00_three_quarter.png`. The four orthographic views are a later, separate run.
Use your built-in image generation. Record format: `level_generation/creatures/mm7_m398_claude/references_hd/
generation_runs.json` (id, family `m242`, role `primary`, prompt, inputs with sha256, output path, selected flag,
reason, superseded runs). Keep raw returns under `raw/` (`m242_three_quarter_v1.png`, ...).

## Attached inputs, in order (paths relative to `level_generation/creatures/`)

1. `mm7_m242/native/m242sa0.png` — ORIGINAL native front frame (transparent background). Design, proportions and
   palette authority.
2. `mm7_m242/native/m242sa1.png` — ORIGINAL native front three-quarter frame.
3. `mm7_m242/native/m242sa2.png` — ORIGINAL native side profile (the robe is thin front to back; the hood peaks).
4. `mm7_m242/native/m242sa3.png` — ORIGINAL native rear three-quarter.
5. `mm7_m242/native/m242sa4.png` — ORIGINAL native back (the robe's back with its ragged hem points).
6. `mm7_m242/aligned_2x/m242sa1.png` — restored 2x three-quarter, for SURFACE MATERIAL ONLY (cloth, bone finish).

## Deliverable

| File | View |
|---|---|
| `00_three_quarter.png` | front-right three-quarter (camera 40-45 deg toward the figure's own RIGHT side), chest height, slightly above; 1024 x 1536 portrait, true transparent background, unresized return |

If the first return fails a check, do ONE targeted corrective regeneration, then select the better of the two and note
any residual fault in its reason. Do not chase minor differences.

## Prompt content

TASK CONTEXT — MM7 FANTASY-GAME ASSET RESTORATION: faithful high-definition reconstruction of the EXISTING Might and
Magic VII Ghost monster from the supplied original sprites, as a 3D modelling reference. Not a new design.
Output: exactly ONE 1024 x 1536 portrait PNG with a genuine transparent background. ONE complete figure from the hood
peak to the lowest robe tatters, centred, generous margins, near-orthographic camera, no floor, no shadow, no
scenery, no text. Even soft neutral studio light (no dramatic lighting, no rim light, no glow, no mist) that still
shows form. Credible, fully three-dimensional sculpt, semi-realistic game materials, sharp fine detail.

Identity (from the native sprites): a floating undead spectre: a human SKELETON wrapped in a large, ragged, hooded
dark umber-brown robe, with NO legs and NO feet — below the waist there is only the robe, hanging empty.
- HEAD: a yellowed ivory human SKULL (no skin, no eyes): large black hollow eye sockets, black nasal opening, a full
  row of teeth, closed jaw, inside a deep pointed brown HOOD that frames the face.
- TORSO: the robe falls open at the front from the neck to the waist, showing the yellowed ivory RIBCAGE, sternum and
  spine; the robe's two front edges hang on each side of the ribs.
- ARMS: the robe drapes over the shoulders and the upper arms like a cape; from the elbows the bare bony FOREARMS and
  long skeletal HANDS emerge: five long bony fingers per hand, like claws.
- ROBE: one heavy coarse woollen robe, worn, stained and moth-eaten, dark umber brown, falling from the shoulders in
  long folds to a deeply TATTERED hem of many long pointed shreds; the lowest points hang where the feet would be.
  Thin from front to back (as in input 3), wide at the shoulders, tapering slightly downward.
- COLOUR AND MATERIAL: dark umber-brown cloth with lighter worn edges, yellowed ivory bone, black sockets.

Pose: a neutral rigging pose, floating upright. The arms are held OUT and slightly forward, at about 40 degrees from
vertical, elbows slightly bent, with a clear gap of air between the bony forearms/hands and the robe; both hands open,
the five long bony fingers spread apart, palms facing down and slightly inward. Head level, looking forward. The robe
hangs straight down, still, its shreds not blowing.

Do NOT: draw legs, feet or bones below the pelvis; add a scythe, weapon, chains, lantern, belt, rope or jewellery; add
skin, flesh or eyes; add glow, smoke, mist or magic effects; change the colours (robe stays dark umber brown, bone stays
yellowed ivory); cross the hands; cover the ribcage; crop the hood or the hem; add a floor, shadow or text.

INPUT ROLES: Inputs 1-5 are the native standing views (front, front three-quarter, side, rear three-quarter, back):
design, proportions and palette authority; magenta/black/transparent pixels are background. Input 6 is SURFACE
MATERIAL ONLY. CAMERA for this primary: FRONT-RIGHT THREE-QUARTER, 40-45 degrees toward the figure's anatomical RIGHT
from straight front, chest height slightly above: the skull and the robe front point diagonally toward SCREEN-LEFT.
FRAMING / ALPHA: the whole figure occupies about 85 % of the height with generous transparent margins, genuine RGBA
alpha outside the silhouette and in the air gaps between the arms and the robe. No painted checkerboard.

## Checks before selecting

- front-right three-quarter at chest height, whole figure inside the frame, 1024 x 1536, true transparent background;
- skull inside a pointed hood, open robe front showing the ribcage;
- arms out at ~40 degrees, bony forearms and five-fingered skeletal hands clear of the robe;
- no legs, no feet, a tattered robe hem; no weapon or effects; colours as stated.
