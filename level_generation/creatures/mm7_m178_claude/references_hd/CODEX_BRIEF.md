# Codex brief (run 2): four HD front/back/side views for the MM7 Devil (m178)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm7_m178_claude/references_hd/`.
Do not edit any other file, do not run builds, do not call Meshy. Do NOT touch `00_three_quarter.png`.

The primary `00_three_quarter.png` is ALREADY SELECTED by the orchestrator (run `m178_three_quarter_v1` in
`generation_runs.json`; earlier brief: `CODEX_BRIEF_v1_primary.md`). Do not regenerate or re-judge it. Append the new
runs to the existing `generation_runs.json` (same record format), keep raw returns under `raw/`
(`m178_front_v1.png`, ...), and at the end write `selected_views_review.png` (all five selected views side by side).

## Attached inputs, in order (paths relative to `level_generation/creatures/`)

1. `mm7_m178_claude/references_hd/00_three_quarter.png` — the selected HD primary. IDENTITY AUTHORITY for every new
   view: same devil, head, teeth, eyes, ears, spikes, plates, arms and four-fingered clawed hands, legs and feet, tail,
   colours, pose, proportions, light and render style.
2. `mm7_m178/native/m178sa0.png` — ORIGINAL native front.
3. `mm7_m178/native/m178sa2.png` — ORIGINAL native right profile (faces image right: tail, spikes, hands, feet).
4. `mm7_m178/native/m178sa4.png` — ORIGINAL native back (spikes, spine ridge, tail base).

## Deliverables (1024 x 1536 PORTRAIT like input 1, true transparent background, unresized returns)

Camera conventions (the figure faces the viewer in `01_front`; "its left" means the figure's own anatomical left):

| File | Camera | What the image must show |
|---|---|---|
| `01_front.png` | straight in front of it | face, chest plates; its RIGHT arm on IMAGE LEFT; the tail mostly hidden behind (only the raised tip may show) |
| `02_back.png` | straight behind it | spine ridge, shoulder and head spikes from behind, the tail from its base; its RIGHT arm on IMAGE RIGHT |
| `03_left.png` | at its LEFT side, pure 90-degree profile | it faces IMAGE LEFT; its LEFT arm and leg nearest the camera; the tail behind toward IMAGE RIGHT |
| `04_right.png` | at its RIGHT side, pure 90-degree profile | it faces IMAGE RIGHT; its RIGHT arm and leg nearest the camera; the tail behind toward IMAGE LEFT |

Generate each view with input 1 as the main reference. Accept a view as soon as it passes the checks below; for a
failed view do at most ONE targeted corrective regeneration, then select the better of the two and note any residual
fault in its reason. Do not chase minor differences in stains or small surface spots.

## Prompt content (adapt per view)

TASK CONTEXT — MM7 FANTASY-GAME ASSET RESTORATION: one more orthographic view of the EXACT same devil as input 1
(a faithful HD reconstruction of the existing Might and Magic VII Devil monster), as a 3D modelling reference. Not a
new design. ONE complete creature, spike tips to toe claws and tail tip, centred, generous margins (at least 60 px on
every side), near-orthographic camera at chest height, transparent background, no floor, no shadow, no scenery, no
text. Even soft neutral studio light, same render style and materials as input 1.

Identity (as in input 1): a lean upright wiry biped; small reptilian head with a wide toothy grin, glowing yellow
eyes, pointed ears, three long ivory spikes rising from the top and back of the skull; long curved ivory spikes on
each shoulder and the upper back; ochre-brown pebbled hide; dark slate-violet plated chest and abdomen down to the
groin; very long arms with a row of short ivory spikes along the outer forearm; enormous hands reaching the knees,
each with FOUR long separated bony fingers ending in long ivory hooked talons; lean legs, big clawed feet with dark
slate-violet tops, pale toe claws and a pale hooked heel spur; a long thin ochre tail with small ivory spikes along
its upper curve and a small cone spear tip, sweeping back and curling up.

Pose (identical in all views, as in input 1): standing upright, the feet apart, knees only slightly bent; the arms
hanging down and out about 35 degrees from vertical with clear air between the arms, hands and the body and legs;
fingers open and separate; the tail sweeping back and up behind the body, clear of the legs. Head facing forward.

Do NOT: add wings, armour, clothing, weapons, glow effects or extra horns; change the colours; change the pose;
change the finger count; crop the spikes, claws or tail; add a floor, shadow or text.

Checks per view:
- the camera matches the table (side and facing direction); pure front/back/profile, not three-quarter;
- same creature, proportions, pose and colours as input 1;
- whole creature including the spike tips, toe claws and tail tip inside the frame with margins, true transparent
  background, 1024 x 1536;
- four fingers per hand wherever visible;
- in profile, the arm nearest the camera hangs clear of the body and legs, and the whole tail is visible behind.
