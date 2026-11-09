# Codex brief: HD modelling references for the Gate Bastion (Hesper monster 10066)

Scope: image generation only. Write ONLY into `level_generation/creatures/hes_turrets_claude/references_hd/gate_bastion/`.
Do not edit any other file, do not run builds, do not call Meshy. Use your built-in image generation tool (PIL only to
check sizes and alpha, and to remove a plain background to true transparency if the return has one).

This is a new machine of the Hesper world (an OpenYAMM world in the Might and Magic VI-VIII style), not an MM sprite:
its design authority is the user-approved concept sheet. The masters are 3D modelling references for Meshy
(image-to-3D and retexture), so the object must read as one clear, solid, fully three-dimensional machine.

## Inputs (attached in this order)

1. `concept.png`: the APPROVED concept sheet. Large right view = front three-quarter from slightly below (the thin
   blue shell around it is a SHIELD: never draw it). Upper-left = side view (barrels to image LEFT, i.e. the turret's
   LEFT side, still a little three-quarter). Lower-left = rear three-quarter view.
2. `concept_main.png`: crop of the large view (detail).
3. `concept_side.png`: crop of the side view (proportions authority: barrel length, dome, cable column, pedestal).
4. `concept_back.png`: crop of the rear three-quarter view (rear hatch, cables).
5. (run 2 only) the selected `00_three_quarter.png`.

## Deliverables

Five masters in this folder, unresized returns, **1536x1024 landscape**, true transparent background, no floor, no
shadow, no text:

| File | View |
|---|---|
| `00_three_quarter.png` | front three-quarter: the barrels point toward image LEFT and about 35° toward the camera, so we see both muzzles, the three lenses, the turret's LEFT side (the side with the grey-green patch plate) and the front of the pedestal with its banner; camera slightly ABOVE the pedestal top |
| `01_front.png` | straight front: the barrels point straight at the camera, one above the other (over-under), centred |
| `02_back.png` | straight back: the rear of the dome with its hatch and cables |
| `03_left.png` | strict 90° profile of the turret's LEFT side: barrels point to image LEFT, both visible one above the other |
| `04_right.png` | strict 90° profile of the turret's RIGHT side: barrels point to image RIGHT |

Run 1: generate `00_three_quarter.png` only, check it, at most one corrective regeneration, then stop.
Run 2 (separate invocation): 01–04 with the selected 00 as input 5. At most one corrective regeneration per view.

## Prompt content (adapt per view)

TASK CONTEXT, GAME ASSET: a faithful high-definition 3D modelling reference of an approved concept, for an MM6-8-style
first-person RPG. Not a new design. Near-orthographic camera, even soft neutral studio light (no dramatic light, no
rim light, no strong cast shadows; light is baked into the texture), painterly-realistic game materials like the
concept, sharp fine detail, a credible solid three-dimensional object.

Identity (from the concept; about 2.6 m tall in all, broad and heavy):
- PEDESTAL: a broad squat OCTAGONAL plinth of pale grey-green settler prefab composite panels in TWO steps (a wide low
  bottom step and a narrower upper step), panel seams, rivets, small brass corner blocks with bolts round the bottom
  step, a louvred vent in a side panel, and on the FRONT of the upper step a small banner plate: a short gold rod with
  a RED cloth banner bearing a gold circle-and-line glyph. On top: a heavy brushed GOLD-BRASS turning ring.
- COLUMN: above the ring a short gold neck surrounded by thick black segmented cable conduits that run from the
  underside of the head down into the ring.
- HEAD: a big DOMED white/ivory ceramic housing (a rounded helmet / beetle shape, wider than tall, panelled, gold
  bands and rivets), with a raised curved ARMOURED SHOULDER plate on EACH side standing up past the dome like a pair
  of fins, a settler patch plate of grey-green prefab panel riveted over the dome's LEFT side, and a rear access hatch.
  Under the barrels at the front: a row of THREE small round blue-white glowing sensor LENSES in a gold bar.
- BARRELS: TWIN long parallel cannon barrels mounted OVER-UNDER (one above the other, as the concept's side view shows), both level, coming out of the
  upper front of the dome: ceramic shrouds with gold collars, a section of STACKED dark COOLING FINS with a glowing
  BLUE-WHITE energy tube inside, then heavy ceramic-and-gold muzzle blocks with glowing blue-white emitters at the tips.
- Energy parts (lenses, tubes, emitters) are bright blue-white and clearly separate from the ceramic; their light does
  not spill onto the surrounding surfaces as a halo.

Pose: REST pose, both barrels exactly HORIZONTAL (level, not raised), the head level. The whole turret inside the
frame with generous margins.

Do NOT: draw the shield shell, glow halos, light rays or sparks; raise the barrels; add a third barrel, extra lenses,
legs or wheels; change the colours (ivory ceramic, brushed gold, pale grey-green pedestal and patch plate, black
cables, red banner with gold glyph, blue-white energy); add any orange; crop anything; draw a floor, shadow, background
or text.

## Per-image checks (re-run before you select a view)

Whole turret inside the frame with margins; two-step octagonal grey-green pedestal with the red banner at the front;
gold turning ring; cable column; domed ceramic head with BOTH raised shoulders and the grey-green patch plate on the
turret's LEFT; exactly two level barrels with dark cooling fins, glowing tubes and emitters; three small blue lenses
under the barrels; no shield; transparent background; 1536x1024. For 01–04: the same turret, pose, proportions and
colours as the primary (input 5). `03_left`: barrels to image LEFT, the patch plate on the near side. `04_right`:
barrels to image RIGHT, plain ceramic on the near side. `01_front`: both muzzles, the three lenses and the banner
centred. `02_back`: rounded dome rear with its hatch, cables into the ring, both shoulders.
Stop after one corrective regeneration per view and record what remains.

## Records

`generation_runs.json` in this folder: one entry per generation (id, view, prompt, input paths with sha256, output
path, selected flag, reason, superseded runs). Contact sheet `selected_views_review.png` (the five views once they
exist).

## Run 3 (correction after Claude's gate; 2026-10-22)

The 3D model built from `00_three_quarter.png` has the twin barrels on the turret's RIGHT side, not in the middle:
they come out of the dome's front at its right-hand upper corner, beside the right shoulder, over-under, and the dome's
centre front holds only the three-lens bar. The run-2 `01_front.png` and `02_back.png` drew them centred, so they do
not match the model the retexture paints. Regenerate ONLY these two views (keep the old ones in `superseded_run2/`):

- `01_front.png`: straight front. The two barrels point straight at the camera, one above the other, on IMAGE LEFT
  of centre (the turret's right), just inside the right shoulder; the dome's centre front with the three lenses,
  the pedestal banner and the ring stay centred. Same colours, materials and details as `00_three_quarter.png`.
- `02_back.png`: straight back. The barrels are hidden behind the dome except maybe their tips beyond its edge on
  IMAGE RIGHT (the turret's right); the dome's rear with its hatch and cables, both shoulders and the pedestal centred.

Inputs for this run: 1 = `00_three_quarter.png` (design, colours), 2 = `meshy_geometry_front.png`, 3 =
`meshy_geometry_back.png` (grey renders of the 3D model straight from the front and the back: AUTHORITY for the
layout and silhouette of these two views; paint them in the materials of input 1, do not copy their grey look),
4 = `03_left.png`, 5 = `04_right.png` (accepted side views, for consistency). 1536x1024, true binary alpha, no halo,
at most one corrective regeneration per view. Record the runs in `generation_runs.json` and refresh
`selected_views_review.png`.
