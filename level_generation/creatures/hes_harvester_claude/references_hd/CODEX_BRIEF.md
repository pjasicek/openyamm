# Codex brief: HD modelling references for the Harvester (Hesper boss 10104)

Scope: image generation only. Write ONLY into `level_generation/creatures/hes_harvester_claude/references_hd/`.
Do not edit any other file, do not run builds, do not call Meshy. Use your built-in image generation tool (PIL only to
check sizes and alpha, and to remove a plain background to true transparency if the return has one).

This is a new machine of the Hesper world (an OpenYAMM world in the Might and Magic VI-VIII style), not an MM sprite:
its design authority is the approved concept sheet (`design/kreegan_world/concepts/monsters/boss_harvester.png`,
candidate 2, approved 2026-10-23). The masters are 3D modelling references for Meshy (image-to-3D and retexture), so
the machine must read as one clear, solid, fully three-dimensional object with clean separable parts.

## Inputs (attached in this order)

1. `concept.png`: the APPROVED concept sheet. Large right view = front three-quarter (drill toward the viewer at image
   lower left, the machine's LEFT flank visible). Upper left = true side profile (drill to image LEFT: the machine's
   LEFT side). Middle left = rear three-quarter (drill to image right, sprayer at image left, the RIGHT flank).
   Bottom left = the dig state (vents open): NOT the pose of these masters.
2. `concept_main.png`: crop of the large view (detail authority).
3. `concept_side.png`: crop of the side profile (proportions authority: hull length, track length, drill size,
   fin row, core housing and sprayer positions).
4. `concept_back.png`: crop of the rear three-quarter view (sprayer, rear hull, rear of the tracks).
5. (run 2 only) the selected `00_three_quarter.png`.

## Deliverables

Five masters in this folder, unresized returns, **1536x1024 landscape**, true transparent background, no floor, no
shadow, no text:

| File | View |
|---|---|
| `00_three_quarter.png` | front three-quarter like the concept's main view: the drill points toward image LEFT and about 35° toward the camera; we see the drill, the armoured front plates either side of it, the machine's LEFT flank with its track and bucket chain, and the top (fins, core housing, sprayer) from a camera slightly ABOVE the hull top |
| `01_front.png` | straight front: the drill points straight at the camera, centred, the two armoured front plates and both tracks symmetric either side, the vent hatches and the fins above |
| `02_back.png` | straight back: the rear of the hull and both tracks, the sprayer's nozzle pointing straight at the camera above them, centred |
| `03_left.png` | strict 90° profile of the machine's LEFT side: drill to image LEFT |
| `04_right.png` | strict 90° profile of the machine's RIGHT side: drill to image RIGHT |

Run 1: generate `00_three_quarter.png` only, check it, at most one corrective regeneration, then stop.
Run 2 (separate invocation): 01–04 with the selected 00 as input 5. At most one corrective regeneration per view.

## Prompt content (adapt per view)

TASK CONTEXT, GAME ASSET: a faithful high-definition 3D modelling reference of an approved concept, for an MM6-8-style
first-person RPG boss. Not a new design. Near-orthographic camera, even soft neutral studio light (no dramatic light,
no rim light, no strong cast shadows; light is baked into the texture), painterly-realistic game materials like the
concept, sharp fine detail, a credible solid three-dimensional machine.

Identity (from the concept; a colossal mining machine about three times as long as it is tall, low and heavy):
- RUNNING GEAR: two long armoured CRAWLER TRACKS, one each side, running nearly the whole length: dark segmented
  track links, a row of gold road wheels, chipped ivory ceramic track guards along their upper outer face.
- HULL: a long, hunched hull of chipped ivory/white ceramic armour plates with aged gold trim and rivets, bound by
  thick ribbed BLACK-VIOLET RESIN cables that fill the gaps between plates. A row of five or six pale BONE FINS,
  curved and swept backward, along the spine.
- DRILL: one big CONICAL SPIRAL DRILL at the front (dark steel cone with raised gold-edged spiral flights, a sharp dark
  tip) in a round drill housing, on a short thick boom with a round GOLD HINGE HUB on each side of the housing: the
  drill tilts down on that hinge. Level and straight ahead in these masters.
- ARMOURED FRONT: two large thick ivory ceramic plates with gold edges, one each side of the drill, reaching down
  over the front of the tracks: the heaviest armour of the machine.
- HEAT VENTS: two louvred ivory vent hatches with gold frames on the upper front flanks, one each side, just behind
  and above the drill housing. CLOSED and dark in these masters.
- BUCKET CHAIN: a chain of open gold-brass bucket scoops running along each lower flank between the hull and the
  track, from the drill housing back toward the rear.
- CORE HOUSING: a ring-banded ivory drum housing on the upper rear hull with a narrow vertical slot glowing
  WHITE-GOLD (clearly different from the orange).
- SLAG SPRAYER: at the very rear top, a squat gooseneck nozzle on a gold turning ring, its round nozzle pointing
  BACKWARD over the rear, glowing orange inside its throat; a thick resin feed hose curving into it.
- Orange glow only in a few narrow seams between plates, in the nozzle's throat and in small lamps; it does not
  spill onto the surrounding surfaces as a halo.

Pose: REST, the drill level and straight, the vents closed, the sprayer pointing straight back. The whole machine
inside the frame with generous margins.

Do NOT: draw the dig state or open vents; tilt the drill; add a second drill, a second sprayer, legs, arms, a head,
a face, wheels on spokes or extra fins beyond the concept's row; draw sparks, smoke, glow halos or light rays; change
the colours (chipped ivory ceramic, aged gold, black-violet resin, dark steel drill and track links, pale bone fins,
orange seams, white-gold core slot); crop anything; draw a floor, shadow, background or text.

## Per-image checks (re-run before you select a view)

Whole machine inside the frame with margins; two crawler tracks with gold road wheels and ivory guards; one conical
spiral drill at the front on its gold hinge hubs; the two armoured front plates either side of it; two closed louvred
vent hatches on the upper front flanks; a bucket chain along each visible lower flank; the bone fin row; the drum core
housing with a white-gold slot; ONE gooseneck sprayer at the rear top pointing backward; transparent background;
1536x1024. For 01–04: the same machine, pose, proportions and colours as the primary (input 5). `03_left`: drill to
image LEFT. `04_right`: drill to image RIGHT, the sprayer at image LEFT. `01_front`: drill centred and pointing at
the camera. `02_back`: sprayer nozzle centred and pointing at the camera, the drill hidden behind the hull.
Stop after one corrective regeneration per view and record what remains.

## Records

`generation_runs.json` in this folder: one entry per generation (id, view, prompt, input paths with sha256, output
path, selected flag, reason, superseded runs). Contact sheet `selected_views_review.png` (the five views once they
exist).

## Run 3 (correction after Claude's gate; 2026-10-23)

The 3D model built from `00_three_quarter.png` differs at the rear from the run-2 `02_back.png` (kept as
`02_back_run2.png`): the slag sprayer's gooseneck stands on the machine's RIGHT side (IMAGE RIGHT in a straight back
view, about a quarter of the hull width right of centre, its round nozzle pointing straight at the camera), not
centred; the core drums sit at the hull's flanks (one each side, mostly hidden from behind), not in the middle; the rear
centre is a dense bundle of thick resin cables with one big vertical hose down the middle between the two track ends.
Regenerate ONLY `02_back.png`, a straight back view:

- Inputs: 1 = `00_three_quarter.png` (design, materials, colours), 2 = `meshy_geometry_back.png` (a grey render of the
  3D model straight from the back: AUTHORITY for the layout and silhouette; paint it in the materials of input 1, do
  not copy its grey look), 3 = `02_back_run2.png` (the previous attempt: its painting style and material detail),
  4 = `03_left.png`, 5 = `04_right.png` (accepted side views, for consistency).
- Match input 2's outline and part positions: the two track ends at the bottom left and right with their ivory
  guards, the cable mass and the central hose between and above them, the fin row's tips at the top centre, the
  sprayer's gooseneck and glowing orange nozzle at the upper IMAGE RIGHT.
- 1536x1024, true binary alpha, no halo, no background, at most one corrective regeneration. Record the run in
  `generation_runs.json` and refresh `selected_views_review.png`.
