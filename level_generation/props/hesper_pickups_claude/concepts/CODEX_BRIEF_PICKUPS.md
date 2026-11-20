# Codex brief: Hesper pickups (stat canisters, serum vats, supply satchels)

## Scope and sources

Generate original candidates for one concept sheet, `pickups.png`, with your built-in image generation tool. Each run
makes **one** candidate (the prompt names which). Write only into this directory
(`level_generation/props/hesper_pickups_claude/concepts/`); no code, builds, staging or runtime assets.

Content source (read it; print nothing from it on the art): [Pickups](../../../../design/kreegan_world/PICKUPS.md),
the user's decisions: four clickable dungeon props, each drawn **full** and **empty**.

Attached images, in order:

1. `design/kreegan_world/concepts/08_tech_gear_sheet.png`: painting style, value range and the dark sheet background.
   Its weapons are NOT part of this design.
2. `design/kreegan_world/zone1/concepts/z1_06_chests.png`: the two material languages. Top row, the **colony**
   locker: bone-white Colonial Ancient ceramic, gold edging and bands, small blue-white Ancient lights. Middle row,
   the **Kreegan** pod chest: black-violet ribbed resin, pale bone and claw edges, localized orange glow. The
   bottom (Ashrunner scrap) row is NOT part of this design.
3. `level_generation/creatures/hes_guard_claude/references_hd/00_three_quarter.png`: the colony livery: bone-white
   plates edged in gold, deep blue, a red field with the gold ring-and-stem sigil.
4. `design/kreegan_world/zone3/concepts/z3_10_fixtures.png`: how this world draws a Kreegan fixture **lit and spent**
   side by side: the same construction, the glow gone, the surface dark and dull.

These are construction and style references, not edit targets. Make original designs. No outside franchise designs
(no Fallout stimpaks, no StarCraft or Warhammer props).

## Common image contract (from `design/kreegan_world/concepts/monsters/CODEX_BRIEF_BROOD_MACHINES.md`)

- Exactly 1536 × 1024 pixels, landscape PNG; opaque, plain dark neutral charcoal background.
- Painterly late-1990s Might and Magic science-fantasy concept art: clear painted forms, strong value structure,
  restrained surface detail, natural materials and even lighting. Neither photoreal nor glossy 3D, anime or cartoon.
- Entire silhouettes inside the canvas, separated views, generous margins. Only faint contact shadows; no scenery,
  ground plane, smoke, effects, labels, lettering, numbers, logos, watermarks, UI, borders or scale bars.
- Keep glow localized so ceramic, glass, resin and cloth stay readable.
- Ivory ceramic and gold distinguish the colony; black-violet resin and pale bone distinguish the Kreegans.
- Views use independent display sizes for legibility; the sheet is not a common-scale chart. Real sizes below are
  design constraints, never printed.

## The four props

**The coloured fluid is one region.** The containers come in seven colours (red, yellow, blue, orange, green,
purple, white) that the game swaps on one model. On both containers the fluid must show through **one clearly
bounded window region** (glass panes, or the membrane and the gaps between ribs), lit evenly from inside, with no
colour bleeding onto the ceramic, gold, resin or bone. Paint the full canister's fluid **red** and the full vat's
serum **green**; nothing else on either prop is red or green.

1. **Stim canister, full** (colony and Ancient places; about 1 m tall, waist-high): an upright cylinder of
   bone-white ceramic with gold bands, standing on a low round foot. Two or three tall **glass windows** round its
   middle show the glowing stim inside, filled to near the top. A **valve** on top (a gold hand wheel on a short
   neck). A small panel with one blue-white Ancient light and a deep-blue livery stripe. Solid and simple enough to
   read at a distance; no hoses or loose parts.
2. **Stim canister, empty:** the same canister, the same pose and parts. The glass dark and smoky, the fluid gone
   (at most a thin dull film at the bottom), the blue light dead. Nothing broken.
3. **Graft-serum vat, full** (Kreegan places; about 0.8 m tall, 1.1 m across, squat): a round vat of black-violet
   resin and **ribbed walls** (vertical ribs with gaps between them where the glowing serum shows through), pale bone
   claws gripping the rim, three short splayed root feet. A **membrane lid** stretched over the top, taut,
   translucent and glowing with the serum's colour. Grown, not built.
4. **Graft-serum vat, empty:** the same vat and pose. The **membrane torn** open (ragged flaps hanging inward), the
   gaps between the ribs dark, the inside a dark dry hollow. No glow anywhere.
5. **Colony satchel, full** (colony places; about 0.5 m long, lying on the floor): a stuffed canvas supply pouch in
   faded deep blue and sand, tan straps with gold buckles, a flap closed over the top, and a small **colony patch**
   (a red field with the gold ring-and-stem sigil, no letters) sewn on the flap. Bulging with supplies.
6. **Colony satchel, empty:** the same satchel **opened and lying flat**, the flap thrown back, the straps loose, the
   canvas collapsed and creased, nothing inside.
7. **Kreegan scrap bundle, full** (Kreegan places; about 0.6 m long, on the floor): a compact bundle of looted scrap
   (a few bent ivory ceramic plates, a gold fitting, a cable end) **bound in a wrap of black-violet resin** and closed
   with a **bone clasp** (a curved claw hook through a loop). Faint orange in the resin seams only.
8. **Kreegan scrap bundle, empty:** the same resin wrap **split open and flattened**, the clasp undone and hanging,
   nothing inside, no glow.

## Layout

Two rows of four, full on the left of each pair, empty on its right; each prop in front three-quarter view, the
camera slightly above (the party looks down at these), every view the same pose as its pair.

- Top row: canister full, canister empty, vat full, vat empty (the larger props, about 60 % of the height).
- Bottom row: satchel full, satchel empty, bundle full, bundle empty.
- Candidate 1: taller slimmer canister with three windows; the vat a near-hemisphere with dense thin ribs.
- Candidate 2: stockier canister with two broad windows and a heavier foot; the vat a squat barrel shape with fewer,
  thicker ribs and bigger gaps.

## Checks per image

Eight views, each pair the same object in the same pose; the full canister red and the full vat green, the colour
confined to the window region; the empties clearly empty (dark glass, torn membrane, flat satchel, open wrap); colony
pieces ivory, gold and blue, Kreegan pieces black-violet resin and bone; no text or letters anywhere (the patch is a
picture), no scenery, no effects. 1536 × 1024 exactly.

## Output and records

- Save the candidate as `pickups_candidate_<N>.png` (N from the prompt) and every generation in `raw/`.
- Write one record per generated image to `generation_runs_pickups_c<N>.json` (runs go in parallel, one file each;
  they are merged into `generation_runs_pickups.json` after the user's pick): `id`, `file`, `prompt`, `selected`
  (false: the user selects), `reason`, `source`, dimensions and review notes.
- Copy generated PNGs without repainting, resizing or compositing; use PIL only to check dimensions.
- Retry rule: regenerate at most once, with one targeted correction, and keep the better.
