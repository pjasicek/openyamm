# Codex brief: HD modelling references for the Ashrunners (Hesper)

Scope: image generation only. Write ONLY into `level_generation/creatures/hes_ashrunner_claude/references_hd/` and
`level_generation/creatures/hes_ashrunner_claude/references_head/`. Do not edit any other file, do not run builds, do
not call Meshy. Use your built-in image generation tool.

This is a new character family of the Hesper world (an OpenYAMM world in the Might and Magic VI-VIII style), not an
MM sprite: its design authority is the user-approved concept sheet
`design/kreegan_world/concepts/monsters/fam_ashrunners.png` (copied as `references_hd/concept.png`). The large figure
on the right is tier A (the one to model); upper left is tier B (darker cloak, a rifle and an extra chest plate),
middle left is tier C (sand cloak, a dark carbine with orange glow and a round buckler emitter on the forearm), lower
left is tier A from the back. All three tiers share ONE body; the weapons, the chest plate and the buckler are separate
props, so the body masters show NONE of them.

## Inputs (attached in this order)

1. `references_hd/concept.png` — the APPROVED concept sheet. Design, proportions, materials and colour authority.
   Reproduce this exact character faithfully; do not redesign. The dark background is not part of the character.
2. (runs 2 and H only) the selected `references_hd/00_three_quarter.png`.

## Deliverables

Body masters in `references_hd/`, one figure each, full body from the top of the hood to the soles, unresized
returns, 1024x1536 PORTRAIT, true transparent background, no floor, no shadow, no text:

| File | View |
|---|---|
| `00_three_quarter.png` | front three-quarter, body turned about 35° (we see the front and the figure's RIGHT side), camera at chest height slightly above |
| `01_front.png` | front |
| `02_back.png` | back |
| `03_left.png` | the figure's LEFT side: a strict 90° profile, the face points to image LEFT, the left shoulder nearest the camera |
| `04_right.png` | the figure's RIGHT side: a strict 90° profile, the face points to image RIGHT, the right shoulder nearest the camera |

Prop references in `references_hd/` (run P), each ALONE, transparent background, no hands, no glow halo beyond the
glowing parts themselves, whole prop inside the frame with margins, even light, the same painterly-realistic finish:

| File | Canvas | Prop and view |
|---|---|---|
| `pistol.png` | 1536x1024 | tier A's Ancient **blaster pistol** from the concept's main view, seen exactly from its RIGHT side (muzzle to image RIGHT, grip down): a chunky white/ivory ceramic body with gold trim, a raked brown-and-gold grip, a trigger guard, a blue-white glowing power-cell window along the side, a dark metal emitter muzzle; about 30 cm long; scavenged: chipped, scratched, dusty |
| `carbine.png` | 1536x1024 | tier C's stolen **Kreegan pulse carbine** from the concept (middle left), seen exactly from its RIGHT side (muzzle to image RIGHT, pistol grip down): about 0.85 m, a black-violet resin body with ivory bone plates and ridges, orange-glowing slots and a glowing orange emitter at the muzzle, a pistol grip under the rear, a straight round fore-grip section in the middle where the left hand holds it, a short stock |
| `buckler.png` | 1254x1254 | tier C's stolen **buckler emitter** (concept middle left, on the left forearm), seen exactly FACE-ON: a round device about 32 cm across, a dark grey-violet resin disc with an ivory bone rim, two concentric orange glowing rings and an orange-glowing centre; flat and shallow (about 4 cm deep) |
| `chest_plate.png` | 1254x1254 | tier B's extra **salvage chest plate** (concept upper left), seen exactly FROM THE FRONT as worn (no body): one curved white Ancient ceramic plate covering the upper chest from collarbone to the bottom of the ribs, about 40 cm wide, gold-edged, cracked and patched, a few rivets, two leather straps with buckles at its upper corners and sides |

Head turnaround in `references_head/` (run H), bust only (head, hood, goggles, scarf, neck and the top of the
shoulders), 1254x1254 (or the closest square size), transparent background, the SAME person as the body masters,
neutral expression: `01_front.png`, `00_three_quarter.png`, `02_profile.png` (the figure's right side, face toward
image right), `03_back.png`. The face shows only between the hood and the scarf: the eyes, brows, the bridge of the
nose, weathered tanned skin.

Run 1: generate `00_three_quarter.png` only, check it, at most one corrective regeneration, then stop.
Run P (may run at the same time as run 1): the four prop references. Run 2 (separate invocation): 01–04 with the
selected 00 as an input. Run H (separate invocation): the head turnaround with the selected 00 as an input.
At most one corrective regeneration per image.

## Prompt content (adapt per view)

TASK CONTEXT — GAME ASSET: a faithful high-definition 3D modelling reference of an approved character concept, for an
MM6-8-style first-person RPG. Not a new design. Use case: 3D character modelling reference sheet view.
Near-orthographic camera, even soft neutral studio light (no dramatic lighting, no rim light, no strong shadows: the
light is baked into the texture), painterly-realistic game materials like the concept, sharp fine detail, a credible
fully three-dimensional figure.

Identity (tier A, the concept's large right figure): a lean, hard, weathered adult human surface scavenger.
- HOOD and CLOAK: a hooded **ash-grey** cloak, the hood UP over the head; the cloak lies over both shoulders, is OPEN
  at the front (the clothes, belt and legs show between its edges) and falls behind the arms to mid-calf at the back
  and sides. Ragged, torn hem in long pointed tatters (as in the concept), worn and dusty. The cloth itself is SOLID:
  wear spots and small holes are painted as darker patches, not cut through (no see-through holes).
- FACE: a **rust-orange** scarf wrapped over the nose, mouth and neck, one torn tail hanging down the chest; brass-
  rimmed welding **goggles** pushed up onto the hood's brow; between hood and scarf the eyes, brows and weathered
  tanned skin are visible.
- UNDER-CLOTHES: a dark charcoal-brown layered tunic reaching mid-thigh with a ragged hem, loose dark grey-brown
  trousers; **rust-orange cloth wraps** around both forearms and both shins; dark fingerless gloves.
- SCRAP PLATE: cracked **white Ancient ceramic plates with gold edging** strapped on with leather: one on each
  shoulder, one on each knee and shin.
- GEAR: a brown leather chest strap; a wide brown leather **salvage belt** with pouches, metal canisters, keys and a
  rope coil hanging from it; sturdy brown **wrapped boots** with straps; a brown leather-and-canvas **pack** on the
  back, worn OVER the cloak (straps over the shoulders), with tubes and a canister hanging from it (see the back view).

Pose (identical in all five body views): A-pose, arms straight down and away from the body about 40° from vertical
so there is clear air between the arms and the body and the cloak falls BEHIND the arms (no cloth over the arms or
hands, the hands well clear of the cloak). BOTH hands are loose FISTS with the fingers curled around EMPTY space as if
holding a gun grip, knuckles forward-down. EMPTY HANDS. Legs straight, feet a little more than hip-width apart with a
clear gap between the legs, soles flat. Head level, looking forward.

Do NOT: draw any weapon, pistol, rifle, carbine, knife, buckler, shield or energy shell; add the tier B chest plate;
change the colours (ash-grey cloak, rust-orange scarf and wraps, white-and-gold ceramic plates, charcoal-brown
clothes, brown leather); make it a monk robe or a closed cloak; cut holes through the cloak; crop the hood, hands,
cloak tips or feet; draw a floor, shadow, background or text.

## Per-image checks (re-run before you select a view)

Full figure inside the frame with margins (cloak tips included); hood up, goggles on the brow, rust scarf over the
lower face; open ash-grey cloak behind the arms with a ragged hem; white ceramic plates with gold edging on both
shoulders and both knees/shins; rust wraps on both forearms and shins; belt with pouches, canisters and rope; pack on
the back over the cloak; both hands empty fists clear of the cloak; A-pose with air between arms and body and between
the legs; transparent background; for 01–04 the same figure, pose, proportions and colours as the primary; side
views: in `03_left` the face points to image LEFT, in `04_right` to image RIGHT, strict profiles (one eye visible, the
far arm mostly hidden). For the props: the stated view, nothing cropped, no hands. Stop after one corrective
regeneration per image and record what remains.

## Records

`references_hd/generation_runs.json` and `references_head/generation_runs.json`: one entry per generation (id, view,
prompt, input paths with sha256, output path, selected flag, reason, superseded runs). Contact sheets
`references_hd/selected_views_review.png` (the five body views and the four props, once all exist) and
`references_head/selected_views_review.png`.
