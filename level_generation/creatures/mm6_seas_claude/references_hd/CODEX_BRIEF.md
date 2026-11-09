# Codex brief: HD reference views for the MM6 Sea Serpent (seas)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm6_seas_claude/references_hd/`.
Do not edit any other file, do not run builds, do not call Meshy.

Use your built-in image generation, with the prompt style and record format of
`level_generation/creatures/mm6_cob_claude/references_hd/generation_runs.json`. Attached inputs:
1. `level_generation/creatures/mm6_seas/references/standing.png` — ORIGINAL native five-view sheet (magenta is
   background). Design/anatomy/palette authority.
2. `level_generation/creatures/mm6_seas/references/walk_3.png` — ORIGINAL native walk views (rising from foam,
   arched forward). Pose authority.
3. `level_generation/creatures/mm6_seas/references/attack.png` — ORIGINAL attack views: shows the head's round mouth,
   teeth and the ring of claws (for head anatomy only; do not copy the attack pose).

## Deliverables
A) Five creature views, transparent background, 1024 x 1536 portrait, unresized returns:
- `00_three_quarter.png` — front-right three-quarter (primary; generate first)
- `01_front.png`, `02_back.png`, `03_left.png` (creature's left side), `04_right.png`
Generate 01–04 with 00 as an additional input so all five are the SAME creature, SAME pose, SAME proportions.
B) `05_foam_ring.png` — 1024 x 1024, transparent background: a TOP-DOWN view (camera straight down) of a ring of
churning sea foam and splash, like the turquoise-white foam at the waterline in the native walk frames: an annulus
with an empty circular hole in the middle (hole diameter about 40% of the image), ragged irregular outer edge, bubbly
white and pale turquoise foam with a few small droplets, soft but crisp, no water surface, no creature, no shadow.
Also write `generation_runs.json` (id, prompt, inputs with sha256, output path, selected flag, reason) and a
`selected_views_review.png` contact sheet. Regenerate a view if it breaks the checks below; record superseded runs.

## Prompt content for A (adapt per view)
TASK CONTEXT — MM6 FANTASY-GAME ASSET RESTORATION: faithful high-definition reconstruction of the EXISTING Might and
Magic VI Sea Serpent from the supplied original sprites, as a 3D modelling reference. Not a new design.
Use case: faithful 3D modelling reference. ONE creature, centred, generous margins, near-orthographic camera at
mid-body height, transparent background, no water, no foam, no splash, no floor, no shadow, no scenery, no text.
Even soft neutral studio light that still shows form. Credible fully three-dimensional sculpt with semi-realistic
game materials, sharp fine detail.

Identity (from the native sprites): a huge sea worm / serpent shown only from the waterline up: a thick round
column of body, the same thickness from bottom to top, ending flat and cleanly cut at the bottom (the waterline;
nothing below it). FRONT (belly) side: pale grey-white, smooth glossy horizontal ring segments like an earthworm's
or a larva's belly, with faint grey-green tint. BACK (dorsal) side: dark olive-green scaly hide covered with rows of
short brown conical spikes, and a ragged brown crest running down the middle of the back. HEAD: a broad, rounded
armoured head shell of olive-brown plates with a crown of short upright brown spikes on top; underneath, a round
lamprey-like mouth, slightly open, showing rings of small sharp ivory teeth and a dark red interior; around the mouth
a ring of eight long curved ivory claws / mandibles hanging downward like fingers.

Pose (identical in all five views, the native walk pose): the body rises VERTICALLY out of the (invisible) water for
the lower two thirds, then the upper third arches FORWARD in a smooth curve so the head faces forward and slightly
down, its mouth and claws toward the viewer in the front view. No coils, no twists, no second body part emerging.

Do NOT: add legs, fins, wings, eyes on stalks, a tail end, water, foam, splashes or reflections; do not change
colours (pale grey ringed belly, olive spiked back, brown crest and spikes, ivory claws and teeth, red mouth).

Checks per image: whole visible body inside the frame; flat cut bottom; belly rings on the front; spikes and crest on
the back; crowned head shell; ring of eight claws; open round mouth with teeth; transparent background; same pose and
proportions as the primary.
