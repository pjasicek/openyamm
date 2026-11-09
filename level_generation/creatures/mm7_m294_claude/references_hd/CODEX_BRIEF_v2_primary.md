# Codex brief (run 2): HD primary three-quarter view for the MM7 Necromancer (m294), covered outfit

User decision 2026-10-20: the first faithful brief (run 1) was refused by the image service (sexual). The user allows
a reworded, NON-SEXUALISED reference: a dignified sorceress in a fully covered version of the native outfit. This is a
deliberate design deviation from the native sprite's cut-outs.

Scope: image generation only. Write ONLY into `level_generation/creatures/mm7_m294_claude/references_hd/`.
Do not edit any other file, do not run builds, do not call Meshy.

This run produces ONLY the primary `00_three_quarter.png`. APPEND to the existing `generation_runs.json` (same
record format; keep the run-1 record). Attached inputs, in order (paths relative to `level_generation/creatures/`):

1. `mm7_m294/native/m294sa4.png` — ORIGINAL native BACK frame (long white hair over the long ragged black cape).
2. `mm7_m294/native/m294sa2.png` — ORIGINAL native PROFILE frame (silhouette, cape length, boots).
3. `mm7_m294/native/m294sa0.png` — ORIGINAL native FRONT frame: use it ONLY for the head, hair, circlet, cape,
   colours and silhouette. Do NOT copy its garment cut; the garment is described below and is fully covered.

## Deliverable

`00_three_quarter.png`: 1024 x 1536 portrait, genuine transparent background, unresized return; raw returns under
`raw/`. Accept the first image that passes the checks; at most ONE targeted corrective regeneration for a failed
image (for image faults such as framing, pose or colour), then select the better and note residual faults. If the
image tool declines a request, do NOT rephrase or retry it yourself: stop, record the exact refusal text in
`generation_runs.json` and in your last message.

## Prompt content

TASK CONTEXT — FANTASY-GAME 3D MODELLING REFERENCE: a high-definition character reference of the Might and Magic VII
"Necromancer", a dignified, sinister undead sorceress, based on the supplied original game sprites for her head, hair,
cape, colours and silhouette. Output: exactly ONE 1024 x 1536 portrait PNG, genuine transparent background. ONE
complete figure, full body from the top of the head down to the boot soles, centred, about 80% of the canvas height
with about 140 px of transparent space above and below, generous side margins. Near-orthographic camera, no floor,
no shadow, no scenery, no text. Even soft neutral studio light. Credible fully three-dimensional sculpt,
semi-realistic game materials, sharp fine detail.

Character:
- An adult sorceress with very pale grey-white skin, a narrow stern face with a neutral expression, and pale glowing
  white eyes.
- HAIR: long, straight WHITE hair parted in the middle, falling behind the shoulders and down the back to the waist.
- CIRCLET: a thin black band across the forehead with a small round GOLD ornament set with a pale jewel at the brow.
- NECK: a black choker.
- OUTFIT (fully covered, opaque): a dark PURPLE long-sleeved tunic-bodysuit with a high neckline and long sleeves to
  the wrists, of heavy matte fabric, decorated with angular BLACK and darker-purple inset panels and diagonal black
  straps across the torso (these panels stand where the original sprite has openings). The tunic reaches the upper
  thighs.
- LEGS: opaque matte BLACK leggings, and tall glossy BLACK heeled boots up to just above the knee with a pointed GOLD
  chevron trim at each knee.
- CAPE: a long RAGGED BLACK cape hanging from the shoulders behind the arms down to the floor, opening at the front
  into two long panels on either side of the legs like a split overskirt, the hem torn into long irregular strips.
  Opaque matte charcoal-black cloth.
- HANDS: pale, slender, with long dark pointed fingernails, EMPTY.

Pose (the pose for every later view as well): a neutral reference A-pose: standing upright, weight even, feet about
shoulder width apart with a gap between the legs; arms hanging down and out from the body at about 40 degrees from
vertical, elbows very slightly bent, a clear gap of air between each arm and the body and cape, the arms in FRONT of
the cape; both hands open, fingers separated, palms toward the body. Head level, looking forward.

Do NOT: draw a weapon, staff or any held object; add armour, a hood, a crown, extra jewellery or extra limbs; show
bare torso, bare legs or any openings in the outfit; change the colours (white hair, pale grey skin, purple tunic with
black panels, black cape, black leggings and boots, gold details); let the cape or the hair cover the arms or hands;
crop the head or the boots; add a floor, shadow, glow, sparkles, spell effect or text.

INPUT ROLES (put these in the prompt): inputs 1–3 are original low-resolution game frames for the head, hair,
circlet, cape, colours and silhouette only; their magenta/transparent background is not part of the character; the
outfit follows the written description, not the sprite's garment cut.

Camera for this PRIMARY view: a TRUE FRONT THREE-QUARTER view, 40–45 degrees to one side of straight front, at chest
height and slightly above, near-orthographic, showing the front and one flank of the body and cape. Head aligned with
the torso.

## Checks (re-run before selecting)

- true three-quarter camera (40–45 degrees), not near-frontal;
- whole figure inside the frame (head, hair, cape hem, boots), true transparent alpha, 1024 x 1536;
- white hair, circlet with gold ornament, black choker, long-sleeved high-necked purple tunic with black panels, black
  leggings, black boots with gold knee chevrons, ragged black split cape to the floor;
- neutral A-pose, arms clear of the body and cape; both hands open and empty; gap between the legs.
