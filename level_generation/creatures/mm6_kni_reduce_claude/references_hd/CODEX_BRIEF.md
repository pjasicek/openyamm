# Codex brief: HD reference views v2 for the MM6 Knight (KnightPlate, kni)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm6_kni_reduce_claude/references_hd/`.
Do not edit any other file, do not run builds, do not call Meshy.

Why v2: the v1 masters (`../mm6_kni_codex/references_hd/`) replaced the original helmet with a closed T-visor great
helm and turned the black chrome armour into matte grey with muted blue. The user wants the ORIGINAL helmet, the
original saturated colours and crisp skull details. The body armour layout of v1 stays, because the existing 3D
mesh was built from it and the new views are projected onto that mesh.

## Attached inputs (in this order)

1. `native_standing_sheet.png` — the ORIGINAL MM6 sprite, standing, five views left to right: front, front
   three-quarter, profile, rear three-quarter, back (enlarged 3x, nearest neighbour). Grey is background, not
   creature. **Authority for the helmet, the colours and the materials.**
2. `native_helmet_sheet.png` — the same five views cropped to head and shoulders (6x). **Authority for the helmet.**
3. `../../mm6_kni/aligned_2x/knistaa0.png` — restored 2x front frame, **surface material only** (chrome finish).
4. `../../mm6_kni_codex/references_hd/00_three_quarter.png` — the v1 primary master. **Authority for pose,
   proportions and the body armour layout below the neck** (it matches the existing 3D mesh). Not for the helmet
   or colours.

## Run 1 deliverable

`00_three_quarter.png` only: front-right three-quarter, 1024 x 1536 portrait, transparent background, unresized
return. Stop after it; the other views are a separate run with the selected primary as input.

## Prompt content

TASK CONTEXT — MM6 FANTASY-GAME ASSET RESTORATION: faithful high-definition reconstruction of the EXISTING Might and
Magic VI Plate Knight (black knight) from the supplied original sprites, as a 3D modelling reference. Not a new
design. ONE complete figure head to feet, centred, generous margins, near-orthographic camera at chest height,
transparent background, no floor, no shadow, no text. Even soft studio light (no dramatic lighting); the chrome
finish is shown by crisp highlights on edges and curved plates, not by a light setup.

Pose and armour layout exactly as image 4: A-pose, arms about 35 degrees from the body, hands open with five
separated armoured fingers, legs straight and slightly apart, feet flat. Same banded breastplate with the central
round dark-violet gem, same skull pauldrons, upper-arm bands, elbow cops, spiked gauntlets (spikes on the outer
forearm), plate fauld with a chainmail skirt between the thighs, belt with the heart/eye emblem, knee cops, plate
greaves and sabatons. Body only: no sword, no shield, no cape.

HELMET, from images 1-2 (the most important change): a rounded black chrome helmet whose face is an open SKULL
MASK: a polished chrome skull face with deep dark eye sockets, a nose cavity and bared teeth, clearly readable.
A narrow vertical crest strip runs over the brow with a small violet rivet. Two slim dark chrome horns rise upward
from the top sides of the helmet and curve inward like a crescent. Two large CURLED RAM HORNS in saturated
blue-violet wrap at the sides of the head at ear level (one full spiral each). Long straight black hair falls from
the top of the helmet down the back to the waist.

PAULDRONS: each shoulder carries a large sculpted skull face (deep dark eye sockets, nose cavity, teeth) that stands
out clearly from the plate, with a few short violet spikes rising behind it.

COLOURS AND MATERIALS, from images 1 and 3: deep black polished chrome steel, high contrast: near-black plates with
crisp bright silver-white highlights along edges, ridges and curved surfaces and cool blue reflections. Saturated
blue-violet (like the sprite, vivid, not grey-blue) on the ram horns, the collar band, the upper-arm bands, the
elbow and knee cops, the belt emblem and the pauldron spikes. The chest gem is dark violet. Black hair. The armour
must NOT look grey, matte, dusty or washed out.

SYMMETRY: left and right halves are mirror images (armour, horns, pauldrons, spikes).

Do NOT: a closed great helm or T-shaped visor; a human face; a muscle cuirass (keep the banded plates of image 4);
extra horns, spikes or skulls beyond those listed; cape, sword or shield; glow effects; grey or desaturated armour;
cropping.

## Checks before selecting

- Skull-mask face clearly readable; two upward horns; two violet ram-horn spirals; hair down the back.
- Pauldron skulls readable at a glance.
- Armour layout and pose match image 4; five fingers per hand; symmetric.
- Black chrome with bright edges and saturated violet, not grey.
- Transparent background, full figure inside the frame, 1024 x 1536.
Regenerate at most once with one targeted correction.

## Records

`generation_runs.json` (id, prompt, inputs with sha256, output path, selected flag, reason, superseded runs).

## Run 1b: one targeted correction (cuirass)

Read files with `cat` or `python3` (there is no `python`). Inputs: 1 `00_three_quarter_run1.png` (the run-1
primary: keep it), 2 `../../mm6_kni_codex/references_hd/00_three_quarter.png` (v1: torso armour reference).
Regenerate `00_three_quarter.png` as image 1 with ONE change: replace the sculpted muscle cuirass (abs and pectorals)
with the smooth banded plate breastplate of image 2 (overlapping horizontal lames, central dark-violet gem, collar
band), so it fits the existing 3D mesh. Keep everything else of image 1 exactly: the skull-mask helmet, horns, hair,
skull pauldrons, colours, chrome finish, pose, proportions, gauntlets, legs. Transparent background, 1024 x 1536.
Record it in `generation_runs.json`.

## Run 2: the other views (after the primary is selected)

Read files with `cat` or `python3`. Inputs: 1 the selected `00_three_quarter.png` (authority for everything: the
same knight, pose, proportions, armour, colours), 2 `native_standing_sheet.png` (original views, for what the back
and sides look like: the hair covers the back down to the waist), 3 `native_helmet_sheet.png`.
Generate, each 1024 x 1536, transparent background, the same A-pose and the same figure as image 1:
- `01_front.png` — front orthographic;
- `02_back.png` — back orthographic (long black hair down the back over the armour);
- `03_left.png` — the knight's LEFT side faces the camera, so the knight looks toward image LEFT;
- `04_right.png` — the knight's RIGHT side faces the camera, so the knight looks toward image RIGHT.
Then the helmet turnaround for a separate 3D helmet model, each 1254 x 1254, transparent background:
- `h1_front.png`, `h2_left.png` (helmet's left side faces the camera), `h3_back.png`, `h4_right.png`.
  The HELMET ALONE as an object, exactly as in image 1: the rounded black chrome helmet with the skull-mask face
  (eye sockets, nose cavity, teeth), the brow crest strip with its violet rivet, the two upward horns and the two
  violet curled ram horns attached at its sides. Nothing else: no hair, no neck, no collar, no body, no stand.
  Near-orthographic, centred, filling about 80 % of the frame, even studio light.
Checks: same design in every view; left/right not swapped; symmetric; nothing cropped; true alpha.
One corrective regeneration per view at most. Record every run in `generation_runs.json` and write a
`selected_views_review.png` contact sheet of the nine selected images.
