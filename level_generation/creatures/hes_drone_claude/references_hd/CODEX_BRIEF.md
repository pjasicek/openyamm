# Codex brief: HD modelling references for the Hesper Drones (Seeker / Hunter / Reaver)

Scope: image generation only. Write ONLY into `level_generation/creatures/hes_drone_claude/references_hd/`. Do not
edit any other file, do not run builds, do not call Meshy. Use your built-in image generation tool (PIL only to check
sizes and alpha).

This is a new creature of the Hesper world (an OpenYAMM world in the Might and Magic VI-VIII style), not an MM
sprite: its design authority is the user-approved concept sheet `references_hd/concept.png`.

## Inputs (attached in this order)

1. `references_hd/concept.png` — the APPROVED concept sheet. The LARGE view on the right is tier A (the Seeker Drone),
   front three-quarter: design, proportions, materials and colour authority. The small lower-left view is tier A in
   strict side profile (lens to image LEFT). The two small upper-left views are tiers B and C (darker colours, extra
   gear): use them ONLY for the gear reference image, never for the five body views. Reproduce the tier-A drone
   faithfully; do not redesign. The dark background and the contact shadow are not part of the creature.
2. `references_hd/material_reference.png` — the Sentinel Turret of the same faction: surface material reference only
   (white/bone Ancient ceramic with fine cracks and gold trim, black-violet Kreegan resin, ribbed chitin, bone spurs,
   orange glow). It never sets the drone's design.
3. (run 2 only) the selected `references_hd/00_three_quarter.png`.

## Deliverables

Body masters in `references_hd/`, the tier-A drone alone, unresized returns, 1536x1024 LANDSCAPE, true transparent
background, no floor, no shadow, no text:

| File | View |
|---|---|
| `00_three_quarter.png` | front three-quarter like the concept's large view: lens toward image LEFT and turned about 35° toward the camera, so we see the lens face and the drone's LEFT flank; camera slightly ABOVE the drone's mid-height (we see a little of the top spine, and the vent ring underneath only in perspective) |
| `01_front.png` | straight front: the lens in the centre, looking straight at the camera |
| `02_back.png` | straight back: the rear end facing the camera |
| `03_left.png` | strict 90° profile of the drone's LEFT side: the lens points to image LEFT |
| `04_right.png` | strict 90° profile of the drone's RIGHT side: the lens points to image RIGHT |

Gear reference in `references_hd/` (run 2): `gear.png`, 1536x1024 landscape, transparent background, two separate
objects side by side with air between them, each seen exactly from its side, no drone body:
left, tier B's **second emitter barrel** alone (a short ceramic-and-gold barrel with a glowing orange-red lens at its
front end, lens pointing image LEFT, the same diameter as the main lens collar); right, tier C's **shield emitter ring**
alone, seen at a 30° angle from above (a flat blackened band with gold trim and a row of small glowing orange-white
rectangular cells, as round the middle of the concept's tier-C view).

Run 1: generate `00_three_quarter.png` only, check it, at most one corrective regeneration, then stop.
Run 2 (separate invocation): 01–04 and `gear.png`, with the selected 00 as input 3. At most one corrective
regeneration per view.

## Prompt content (adapt per view)

TASK CONTEXT — GAME ASSET: a faithful high-definition 3D modelling reference of an approved creature concept, for an
MM6-8-style first-person RPG. Not a new design. Use case: 3D modelling reference sheet view. Near-orthographic camera,
even soft neutral studio light (no dramatic lighting, no rim light, no strong shadows, no glow halo spilling onto the
casing or into the air: light is baked into the texture), painterly-realistic game materials like the concept, sharp
fine detail, a credible fully three-dimensional object.

Identity (from the concept, tier A Seeker Drone): a hovering Colonial Ancient survey drone overgrown by the Kreegans,
about 0.8 m long. BODY: a rounded elongated ceramic casing (a lozenge / flattened egg, about 1.6 times as long as it
is tall, slightly narrower than tall), its front end a round lens housing. LENS: ONE large round forward emitter lens
glowing orange in a ring of gold and dark segmented collars at the front. CASING: bone-white / ivory Ancient ceramic
plates with fine cracks, edged in brushed gold, with a few gold rivets; one plate wraps each flank behind the lens.
OVERGROWTH: black-violet Kreegan resin and ribbed chitin tubes grown over the REAR HALF and along the top, with small
orange glow showing between the resin tubes; the overgrowth reaches further forward on the drone's RIGHT flank
(almost to the lens collar) than on its LEFT flank (where the ceramic plate behind the lens stays clear, as in the
concept's large view). SPINE: a single row of 7-8 curved bone ribs / spurs along the top centre line, curving
backward, largest in the middle. REAR: the casing ends in a ceramic tail cap with two short curved bone hooks pointing
back-down, as in the concept. UNDERSIDE: a round ring of small thrust vents under the belly (a gold and dark ring
with a row of glowing orange slots), centred under the middle of the body. TENDONS: exactly THREE short segmented
black cable tendons hanging from the underside behind the vent ring, each ending in a small curved bone-white tip,
hanging DOWN and slightly BACKWARD, separated from each other and from the body by clear air.

Pose: level hover, the body horizontal (not tilted), tendons hanging relaxed straight down-back, not curled under the
body, not touching each other. The whole drone inside the frame with generous margins (tendon tips and spine ribs
not cropped).

Do NOT: add legs, wings, arms, weapons, a second lens or barrel, a ring band round the middle, a shield shell, a glow
halo or light rays; change the colours (bone-white ceramic, gold trim, black-violet resin, orange glow); draw more or
fewer than three tendons; crop anything; draw a floor, shadow, background or text.

## Per-image checks (re-run before you select a view)

Whole drone inside the frame with margins; one orange lens at the front in gold collars; bone-white ceramic plates
with gold edging; black-violet resin over the rear half and top, further forward on the RIGHT flank; 7-8 bone ribs
along the top; tail cap with two bone hooks; vent ring with orange slots under the middle; exactly three separate
tendons; no extra gear; transparent background and 1536x1024. For 01–04: the same drone, pose, proportions and colours
as the primary (input 3). Side views: in `03_left` the lens points to image LEFT and the flank shows mostly clear
ceramic behind the lens; in `04_right` the lens points to image RIGHT and the resin reaches almost to the lens collar.
`01_front`: the lens centred and round, the spine ribs visible as a ridge on top, the vent ring and tendons below.
`02_back`: the tail cap and hooks centred, the resin mass, the spine ribs on top, tendons below; no lens visible.
Stop after one corrective regeneration per view and record what remains.

## Records

`references_hd/generation_runs.json`: one entry per generation (id, view, prompt, input paths with sha256, output
path, selected flag, reason, superseded runs). Contact sheet `references_hd/selected_views_review.png` (the five views
and the gear reference once they exist).

## Run 2 note (after Claude's gate of run 1)

`00_three_quarter.png` (the corrected return) is ACCEPTED and frozen. Its tendons came back as four short curled
segmented cables with bone tips; that is accepted (the rig replaces the tendons with its own), so in 01–04 draw the
tendons as the primary shows them (same count and look) rather than the three in the brief: consistency with the
primary matters more. The faint alpha halo is acceptable; keep backgrounds truly transparent.
