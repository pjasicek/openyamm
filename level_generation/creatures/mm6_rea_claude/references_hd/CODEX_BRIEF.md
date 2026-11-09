# Codex brief: HD reference views for the MM6 Reactor (rea)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm6_rea_claude/references_hd/`.
Do not edit any other file, do not run builds, do not call Meshy. Use your built-in image generation.

Attached inputs, in order:
1. `level_generation/creatures/mm6_rea/native/reasta00.png` - ORIGINAL native front view (idle). Design, proportions
   and palette authority. Transparent background is not part of the machine.
2. `level_generation/creatures/mm6_rea/native/reaat05.png` - ORIGINAL native attack frame (arms deployed). Only to show
   what the folded arms are; the references show the IDLE state with arms retracted (not visible).
3. `level_generation/creatures/mm6_rea/aligned_2x/reasta00.png` - restored 2x front view, for surface material only.
The original game only has a FRONT view of this machine; the back and sides must be a plausible continuation.

## Deliverables (5 images, transparent background, 1024 x 1536 portrait, unresized returns)
- `00_three_quarter.png` - front-right three-quarter, camera slightly above mid-height (primary; generate first)
- `01_front.png`, `02_back.png`, `03_left.png` (machine's left side: the side that is on the IMAGE RIGHT in the front
  view), `04_right.png`
Generate 00 first and stop after at most one corrective regeneration. Then generate 01-04 with 00 as an additional
input so all five are the SAME machine, SAME state, SAME proportions.
Also write `generation_runs.json` (id, prompt, inputs with sha256, output path, selected flag, reason) and a
`selected_views_review.png` contact sheet.

## Prompt content (adapt per view)
TASK CONTEXT - MM6 FANTASY-GAME ASSET RESTORATION: faithful high-definition reconstruction of the EXISTING Might and
Magic VI "Reactor" machine (final dungeon, the Hive) from the supplied original sprite, as a 3D hard-surface modelling
reference. Not a new design. ONE complete machine, centred, generous margins, near-orthographic camera, transparent
background, no floor, no shadow, no scenery, no text. Even soft neutral studio light. Crisp, clean, credible 1990s
pre-rendered CG look with sharp fine detail: brushed silver steel, rivets, thin rust-brown panel seams.

Identity (from the native sprite), top to bottom, everything round (surfaces of revolution about one vertical axis):
- TOP CAP: a short flared silver ring/lid, panelled with vertical seams; a rectangular BLUE glowing display window on
  the front showing a thin white-blue waveform line.
- GLASS CHAMBER: a large clear glass bowl (wider at the top, rounded bottom) held by thin vertical silver struts,
  filled about three quarters with bright luminous GREEN bubbling liquid; one vertical highlight on the glass.
- Below the glass: a glowing BLUE lower bowl, then a narrow silver neck/nozzle with a small bulb, then a thin silver rod
  pointing straight down, ending in a small ball.
- A short crackling BLUE ELECTRIC ARC in the gap between that rod tip and the rod rising from the dome below. The
  upper chamber FLOATS above the dome; nothing connects them except the arc.
- LOWER DOME: a silver hemispherical dome made of riveted vertical panels with rust-brown seams; a glowing BLUE cap on
  the top with a thin silver rod rising from it; on the front a small raised rectangular CONTROL PANEL (light grey plate
  with one red round lamp, small green square lamps, little gauges/lines).
- Below the dome: a vertical cylindrical BAND (panelled, riveted) with a wide rectangular BLUE display window on the
  front showing a thin waveform; under it a wide flared conical SKIRT/base ring that rests on the ground.
- Back and sides: continue the same riveted silver panels; the back has NO displays and NO control panel, only plain
  panels and one small rectangular service hatch on the dome.

Proportions: total height about 2.3 x the dome width; glass chamber about as wide as the dome; gap between chamber
and dome about one fifth of the total height. Match the native silhouette exactly in the front view.

Do NOT: show the mechanical arms (they are retracted inside), add pipes, cables, legs, a stand, a ceiling mount,
extra lights, text or logos, change colours (silver, green, blue), or crop the top cap or base.

Checks per image: whole machine inside the frame; floating chamber with the gap and arc; correct order of parts;
control panel and both displays on the FRONT only; round cross-sections; transparent background; same state and
proportions as the primary.
