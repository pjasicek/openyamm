# Codex brief: HD references for the two Honk goose hats (MM9 props HonkHat.abc and ElderHonkHat.abc)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_honkmale_claude/hats/references/`. Do not edit any
other file, do not run builds, do not call Meshy. Use your built-in image generation tool. Authority: renders of the
ORIGINAL Might and Magic IX low-poly props with their skins.

## Inputs (attached, in order)
1. `mm9_hats.png`: renders of the original props. Top row: the GOOSE HAT (three views). Bottom row: the ELDER HAT (three
   views). Flat grey is background. Design and proportion authority; the faceting and blur are not the design.
2. `mm9_hat_skins.png`: left, the elder hat's 256x256 skin; right, the goose hat's skin, SURFACE MATERIAL AND COLOUR ONLY.
3. `level_generation/creatures/mm9_honkfemale_claude/v2/references_head/00_three_quarter.png` and 4. `.../02_profile.png`:
   the approved HD look of the goose hat on a priestess: the HD style authority for BOTH hats (hammered silver scale
   feathers, embossed folded wings, gold knotwork brim, polished gold goose head).

## Deliverables (true transparent RGBA background, 1254x1254 or the closest supported square, unresized returns; one hat per
image, no head, no hair, no person, no stand, centred with generous margins)
| File | Hat and view |
|---|---|
| `goose_00.png` | GOOSE HAT, front three-quarter from the right, slightly above: the goose head and beak at the top, beak pointing toward IMAGE RIGHT and the viewer |
| `elder_00.png` | ELDER HAT, same view |
| `elder_01_front.png` | ELDER HAT straight from the front |
| `elder_02_back.png` | ELDER HAT straight from the back |
| `elder_03_left.png` | ELDER HAT pure profile, the beak points to IMAGE LEFT |
| `elder_04_right.png` | ELDER HAT pure profile, the beak points to IMAGE RIGHT |

Generate `goose_00` and `elder_00` first; make the other four with the selected `elder_00` as an extra input so all are the SAME
hat. At most ONE corrective regeneration per view. Keep raw returns in `raw/`. Write `generation_runs.json` and a
`selected_views_review.png` contact sheet.

## Goose hat
A rigid conical hat for a cult of the goose, as tall as a head, hollow underneath: a ring-shaped gold brim band with an olive
gold knotwork strip; above it the plump body of a stylised sitting goose in hammered silver scale feathers with a folded
embossed wing on each side, narrowing upward; on top a clearly formed gold neck curving up and forward into a gold goose
head with a bead eye and a long pointed beak pointing FORWARD and slightly down. The neck is as thick as two fingers, about a
third of the hat's height, and the head and beak are big enough to read at a distance. As in input 1 top row.

## Elder hat
The same family, grander, as in input 1 bottom row: the same gold brim band; the silver goose body with its gold neck and head and
forward beak; two large silver WINGS raised up and back from the shoulders of the goose, spread like a V seen from behind,
with long separated flight feathers at the tips, standing clear of the neck with air between; below the brim at the BACK a tall
stiff gold sheet of hammered gold falling to the nape of the neck, split into two broad lobes with a notch between them at the
bottom, and short gold cheek guards at the sides. As in input 1 bottom row.

Even soft studio light, near-orthographic camera, no shadows, no floor, no text. Rigid metal, no cloth.
