# Dragon first-person foreleg: HD modelling masters

Scope: image generation only, with your built-in image generation tool. Write only into
`level_generation/solo_action_dragon_20261113/references_hd/`. No builds, no Meshy, no other files.

## What this is for

The player can play a Dragon in first person. On screen we show only the dragon's two forelegs, reaching into view
from the lower corners, swiping with their talons. We need one foreleg as a 3D modelling reference. It will be modelled
once and mirrored for the other side. It must be the SAME dragon as the attached MM8 Dragon (Might and Magic VIII,
monster m492). This is a faithful high-definition reconstruction of that dragon's foreleg, not a new design.

## Inputs (attached in this order)

1. `native_views.png`: the ORIGINAL low-resolution MM8 sprite views. This is the identity authority. Its
   magenta/black background is not part of the creature.
2. `01_front.png`: an accepted HD master of the whole dragon (front). Material and colour reference: copy the
   foreleg's scales, colours, talons and digit layout from here.
3. `03_left.png`: the same dragon from its left side. Same use as 2.
4. (only for the second run) `00_three_quarter.png`: your selected primary from the first run. All other views
   must show exactly this foreleg.

## The foreleg (identity)

- **Extent:** ONE RIGHT foreleg, from the shoulder joint down to the talon tips. It is cut cleanly at the shoulder:
  a flat, oval cut surface of plain dark scaled skin. No body, no chest, no wing, no neck.
- **Scales:** charcoal-black, small and tightly overlapping on the upper arm and forearm. Thin dark-red seams and
  edges between them, as on the masters. Slightly larger plates on the front of the forearm and the back of the hand.
- **Underside:** a narrow strip of gold-amber scutes runs down the back of the upper arm, matching the gold ventral
  scales of the masters, but small.
- **Wrist:** one short ivory bone spur points backward at the wrist.
- **Hand:** three long forward digits, each with three scaled segments, plus one short inner digit (a thumb or
  dewclaw) set higher on the inside of the wrist. Four digits in total.
- **Talons:** every digit ends in a long, hooked ivory-cream talon with a darker base: thick, glossy, sharp, curved
  downward, longer than the digit's last segment.
- **Palm:** dark leathery pads on the underside of the digits and the palm.
- **Proportions:** a strong muscular forearm, longer than the hand. The hand is broad with the digits spread.

## Pose and camera (the same in all five)

- **Pose:** the leg hangs straight down from the shoulder cut at the top of the image. The elbow is slightly bent, the
  forearm vertical, and the wrist straight. The hand opens downward with the three forward digits spread like a fan
  and the talons separated, so no two talons touch or overlap. The inner digit is clear of the others.
- **Canvas:** 1024×1536 portrait, transparent background, the whole leg inside generous margins. Nothing cropped,
  especially the talon tips.
- **Camera:** near-orthographic, at the height of the elbow. Soft, even, neutral studio light, with no dramatic
  shadows, no rim light and no glow: the light will be baked into the texture.
- **No:** floor, cast shadow, text, flames, scenery, ground or other body parts.

## Deliverables

| File | View |
|---|---|
| `00_three_quarter.png` | front three-quarter: the leg's front and outer side both visible, slightly from above (the primary) |
| `01_front.png` | front: facing the back of the hand and the front of the forearm |
| `02_back.png` | back: the palm side and the back of the arm with the gold scute strip |
| `03_left.png` | the leg's left side (inner side of a right leg); the inner digit faces the viewer |
| `04_right.png` | the leg's right side (outer side of a right leg) |

Left and right: in `03_left.png` the viewer looks at the leg's left side, so for a RIGHT foreleg that is the inner
side, toward where the chest would be, and the inner digit is nearest the viewer. In `04_right.png` the viewer sees
the outer side, and the inner digit is hidden behind the hand.

## Do NOT

- Add armour, rings, bracelets, gems, chains, scars or extra spikes beyond the one wrist spur.
- Add or remove digits (exactly four), or show more than one leg.
- Change the colours (no green, blue, bronze or white scales).
- Crop the shoulder cut or the talons.
- Use perspective distortion, motion blur, or dramatic lighting.

## Runs and checks

- **First run:** generate only `00_three_quarter.png`. Before saving, check it: one right foreleg, four digits,
  four talons, the wrist spur, the colours of the masters, transparent background, nothing cropped. Allow at most one
  corrective regeneration, then stop.
- **Second run:** with the selected `00` attached, generate `01`–`04`. Check each against `00` (same leg, same pose,
  same digit count, and the correct side as described above), with at most one corrective regeneration per view.
- **Records:** write `generation_runs.json` (for each generation: an id, the prompt, the input sha256 values, the
  output path, a selected flag, the reason, and any superseded runs) and a contact sheet
  `selected_views_review.png` of the selected views.
