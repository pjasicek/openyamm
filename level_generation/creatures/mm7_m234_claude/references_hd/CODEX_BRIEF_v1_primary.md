# Codex brief (run 1): HD three-quarter primary for the MM7 Gargoyle (m234)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm7_m234_claude/references_hd/`.
Do not edit any other file, do not run builds, do not call Meshy.

This run produces ONLY the primary `00_three_quarter.png`. The four orthographic views are a later, separate run.

Use your built-in image generation. Record format: `level_generation/creatures/mm7_m398_claude/references_hd/
generation_runs.json` (id, family `m234`, role `primary`, prompt, inputs with sha256, output path, selected flag,
reason, superseded runs). Keep raw returns under `raw/` (`m234_three_quarter_v1.png`, ...).

## Attached inputs, in order (paths relative to `level_generation/creatures/`)

1. `mm7_m234/native/m234sa0.png` — ORIGINAL native front frame (transparent background). Design, proportions and
   palette authority.
2. `mm7_m234/native/m234sa1.png` — ORIGINAL native front three-quarter frame.
3. `mm7_m234/native/m234sa2.png` — ORIGINAL native side profile (horns, snout, tail, feet).
4. `mm7_m234/native/m234sa4.png` — ORIGINAL native back (wing membranes from behind, tail root).
5. `mm7_m234/native/m234wf0.png` — ORIGINAL native front flight frame with the wings SPREAD (the wing pose to use).
6. `mm7_m234/aligned_2x/m234sa1.png` — restored 2x three-quarter view, for SURFACE MATERIAL ONLY (stone texture,
   membrane veins). It never sets the design, pose or proportions.

## Deliverable

| File | View |
|---|---|
| `00_three_quarter.png` | front-right three-quarter (camera 40–45° toward the figure's own RIGHT side), camera at chest height, slightly above; 1536 x 1024 landscape, true transparent background, unresized return |

If the first return fails a check below, do ONE targeted corrective regeneration, then select the better of the two
and note any residual fault in its reason. Do not chase minor differences.

## Prompt content

TASK CONTEXT — MM7 FANTASY-GAME ASSET RESTORATION: faithful high-definition reconstruction of the EXISTING Might and
Magic VII Gargoyle monster from the supplied original sprites, as a 3D modelling reference. Not a new design.
Output: exactly ONE 1536 x 1024 landscape PNG with a genuine transparent background. ONE complete figure, from the
horn tips to the toe claws, both complete wings to their tips and the whole tail to its tip, centred, generous
margins, near-orthographic camera, no floor, no shadow, no scenery, no text. Even soft neutral studio light (no
dramatic lighting, no rim light, no glow) that still shows form. Credible, fully three-dimensional sculpt,
semi-realistic game materials, sharp fine detail.

Identity (from the native sprites): a living stone gargoyle, a lean muscular demonic humanoid made of slate-grey
stone.
- HEAD: a short bestial muzzle with a heavy brow, small glowing red eyes, a wide mouth with small fangs, pointed
  swept-back ears, and two large RAM HORNS curling back and around from the top of the head.
- BODY: slate grey to blue-grey weathered stone skin with fine cracks and speckle, defined chest and abdominal
  muscles, no clothing, no genitals (smooth groin).
- ARMS: muscular arms with large four-fingered clawed hands plus a thumb (five digits), long dark curved talons.
- LEGS: bestial DIGITIGRADE legs: muscular thighs, the heel raised high off the ground (a backward-pointing hock),
  long feet standing on three long clawed toes with dark talons.
- TAIL: a long thin whip tail from the base of the spine, ending in a small dark arrowhead (spade) tip.
- WINGS: two large BAT WINGS attached at the upper back behind the shoulders: dark grey-black bony struts (an arm bone
  and four long finger struts) with a small hooked claw at the wrist, and GREEN leathery membranes with darker green
  vein patterns, scalloped trailing edge between the strut tips.
- COLOUR AND MATERIAL: slate/blue-grey stone body, horns and talons darker grey, red eyes, green wing membranes, dark
  wing struts.

Pose: a neutral A-pose for rigging (NOT the native hunch). Standing upright, weight even, legs nearly straight and
apart with a clear gap between the legs and between the feet, standing on the toes with the heels raised (digitigrade),
toes forward. Arms hang down and out to the sides at about 35 degrees from vertical, elbows very slightly bent, a clear
gap of air between each arm and the torso; hands open, the five clawed digits spread, palms facing the thighs. Head
level, looking forward. WINGS spread wide and raised in a high open V exactly like the native front flight frame
(input 5), membranes fully open and flat, the struts fanned out; the lower edges of the membranes stay ABOVE the hands
and do not touch the arms, the head, the tail or the other wing. TAIL hanging down behind the legs and curving out to
the figure's RIGHT side on the ground plane, clear of both legs, its tip fully visible.

Do NOT: add armour, clothing, a loincloth, jewellery, weapons; add extra horns, extra limbs or extra wings; turn the
feet into human feet; change the colours (the body stays slate grey, the membranes stay green); add glow, aura, fire
or magic effects; make it cartoonish; crop the wing tips, the horns, the tail or the feet; add a floor, shadow or text.

INPUT ROLES: Inputs 1–4 are the native standing views (front, front three-quarter, side, back): design, proportions
and palette authority; input 5 sets the spread-wing pose; magenta/black/transparent pixels are background. Input 6 is
SURFACE MATERIAL ONLY.
CAMERA: FRONT-RIGHT THREE-QUARTER, camera 40–45 degrees toward the figure's anatomical RIGHT from straight front, chest
height slightly above. The face and toes point diagonally toward SCREEN-LEFT. FRAMING / ALPHA: the whole figure, both
wings and the tail inside the frame with generous transparent margins, genuine RGBA alpha outside the silhouette and in
the air gaps. No painted checkerboard. Return exactly 1536 x 1024 unresized.

## Checks before selecting

- front-right three-quarter camera at chest height, near-orthographic, whole figure, wing tips and tail tip inside the
  frame with margins, 1536 x 1024, true transparent background;
- ram horns, pointed ears, red eyes, fanged muzzle; slate-grey stone skin, no clothing;
- five clawed digits per hand, digitigrade legs with raised heels and clawed toes;
- bat wings attached behind the shoulders, spread in a raised V, green membranes, not touching the arms or head;
- tail clear of the legs with its arrowhead tip visible;
- A-pose with the stated gaps.
