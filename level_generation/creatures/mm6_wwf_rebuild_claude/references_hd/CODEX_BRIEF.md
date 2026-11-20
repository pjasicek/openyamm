# Codex brief: HD reference views for the MM6 Werewolf (wfigt1), rebuild 2026-11-11

The 2026-10-09 masters (mm6_wfigt1_claude) came out as a bodybuilder, bulkier than the sprites; the installed model
was flagged for exactly that. This run must follow the SPRITE PROPORTIONS: a lean, wiry, long-limbed wolf-man.

Scope: image generation only. Write ONLY into `level_generation/creatures/mm6_wwf_rebuild_claude/references_hd/`.
Do not edit any other file, do not run builds, do not call Meshy.

Use your built-in image generation, with the prompt style and record format of
`level_generation/creatures/mm6_ttn1_claude/references_hd/generation_runs.json`. Attached inputs:
1. `level_generation/creatures/mm6_wfigt1/references/standing.png` — ORIGINAL native five-view sheet (front, front
   three-quarter, profile, rear three-quarter, back). Magenta is background, not creature. Design/anatomy/palette
   authority.
2. `level_generation/creatures/mm6_wfigt1/native/wfigt1a0.png` — ORIGINAL native front frame (transparent background).
3. `level_generation/creatures/mm6_wfigt1/native/wwalk1a1.png` — ORIGINAL native front three-quarter frame.
4. `level_generation/creatures/mm6_wfigt1/native/wwalk1a2.png` — ORIGINAL native profile frame.
5. `level_generation/creatures/mm6_wfigt1/aligned_2x/wfigt1a0.png` — restored 2x front view, for surface material
   only (fur, claw and pendant rendering). It never sets the design.

## Deliverables (5 images, transparent background, 1024 x 1536 portrait, unresized returns)
- `00_three_quarter.png` — front-right three-quarter, camera at chest height, slightly above (primary; generate first)
- `01_front.png`, `02_back.png`, `03_left.png` (the werewolf's own left side), `04_right.png` (his right side)
Generate 01–04 with 00 as an additional input so all five are the SAME werewolf, SAME pose, SAME proportions.
Also write `generation_runs.json` (id, prompt, inputs with sha256, output path, selected flag, reason) and a
`selected_views_review.png` contact sheet. Regenerate a view if it breaks the checks below; record superseded runs.

## Prompt content (adapt per view)
TASK CONTEXT — MM6 FANTASY-GAME ASSET RESTORATION: faithful high-definition reconstruction of the EXISTING Might and
Magic VI Werewolf from the supplied original sprites, as a 3D modelling reference. Not a new design.
Use case: faithful 3D modelling reference. ONE complete figure, full body from ear tips to toe claws, centred,
generous margins, near-orthographic camera, transparent background, no floor, no shadow, no scenery, no text. Even
soft neutral studio light (no dramatic lighting, no rim light, no glow) that still shows form. Credible fully
three-dimensional sculpt, semi-realistic game materials, sharp fine fur detail.

Identity (from the native sprites): a bipedal wolf-man with a LEAN, WIRY, rangy build like the sprites: a moderately
broad but not bulky chest, narrow waist, LONG lean arms reaching to mid-thigh, long lean legs; sinewy rather than
bodybuilder muscles (NO huge deltoids, biceps or pecs, no bodybuilder V-taper, no six-pack emphasis); the head is a
WOLF head about one-seventh of body height with a shaggy mane that makes the head and neck read large.
- Fur: shaggy, mostly CHARCOAL-BLACK. The chest, shoulders and upper back carry lighter ash-GREY fur with a coarse
  curly texture; the belly/waist below the chest is near-black; arms and legs are dark charcoal with short fur and
  jagged fur tufts at the elbows, the back of the calves and the shins.
- Head: wolf head with a medium muzzle (not a long snout), black nose, short pointed upright ears, a shaggy black
  mane/forelock on the crown and down the back of the neck; fierce glowing-free YELLOW eyes with dark pupils under a
  heavy frowning brow; the mouth slightly open in a snarl showing white fangs; the muzzle and cheeks are a slightly
  lighter grey.
- Neck: a heavy GOLD chain necklace, the chain lying over the collarbones, with a large round GOLD ring pendant at the
  breastbone holding a TURQUOISE/cyan gem in its centre.
- Clothing: ragged cloth SHORTS in rust-ORANGE / tan-brown (one garment, seat and both legs), from the waist to the
  knee as in the sprites (longer than briefs, loose on the thighs), with a jagged torn sawtooth hem; no belt, no shirt.
- Hands: large clawed hands with four fingers and a thumb, each ending in a long curved PALE IVORY claw; dark grey
  palms.
- Feet: big bare wolf-like paws, plantigrade and flat on the ground, with four toes each ending in a pale ivory claw.
- No tail.

Pose (identical in all five views): standing upright in an A-pose — arms straight down and away from the body at
about 30 to 35 degrees from vertical, elbows very slightly bent, hands open with the FIVE digits separated and only
slightly curled, palms facing the thighs, claws clear of the shorts and legs; back straight with only a slight
forward set of the shoulders; legs straight and slightly apart with a visible gap between the thighs and between the
calves, feet flat. Head level, looking forward, mouth slightly open.

Do NOT: make him a bodybuilder or bulky (the main fault of the previous run); add a weapon, shield, belt, shirt, armour, bracers, boots, tail, extra jewellery or a second pendant; do not
add glowing effects; do not crouch or hunch strongly; do not change colours (charcoal-black fur with ash-grey chest,
orange-brown shorts, gold chain, turquoise gem, yellow eyes, ivory claws); do not crop the ears, claws or paws; do
not draw a full human face or human feet.

Checks per image: whole figure with ear tips and toe claws inside the frame; wolf head with pointed ears, yellow
eyes, black nose and fangs; grey chest fur, near-black belly; gold chain with round gold pendant and turquoise gem;
ragged orange-brown shorts reaching the knee with a sawtooth hem; LEAN wiry build, not a bodybuilder (compare with the sprites); four fingers plus thumb with ivory claws on each
hand, hands away from the body; four clawed toes per paw; no tail; transparent background; same pose and proportions
as the primary. In the side views the left/right sides must agree with the front and back.

Side views: `03_left.png` shows the werewolf's OWN left side, so he faces image LEFT (his snout points to the left edge);
`04_right.png` shows his own right side, facing image RIGHT. Generate `00` first and check it; then generate 01-04 in a
separate pass with `00` as the first input. Stop after one corrective regeneration per view.
