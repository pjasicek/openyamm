# Codex brief: HD modelling references for the Ward Turret (Hesper monster 10065)

Scope: image generation only. Write ONLY into `level_generation/creatures/hes_turrets_claude/references_hd/ward_turret/`.
Do not edit any other file, do not run builds, do not call Meshy. Use your built-in image generation tool (PIL only to
check sizes and alpha, and to remove a plain background to true transparency if the return has one).

This is a new machine of the Hesper world (an OpenYAMM world in the Might and Magic VI-VIII style), not an MM sprite:
its design authority is the user-approved concept sheet. The masters are 3D modelling references for Meshy
(image-to-3D and retexture), so the object must read as one clear, solid, fully three-dimensional machine.

## Inputs (attached in this order)

1. `concept.png`: the APPROVED concept sheet. Large right view = front three-quarter from slightly below (the thin
   blue shell around it is a SHIELD: never draw it). Upper-left = side view (barrel to image LEFT, i.e. the turret's
   LEFT side). Lower-left = back view.
2. `concept_main.png`: crop of the large view (detail).
3. `concept_side.png`: crop of the side view (proportions authority: barrel length, yoke arm, pedestal).
4. `concept_back.png`: crop of the back view.
5. (run 2 only) the selected `00_three_quarter.png`.

## Deliverables

Five masters in this folder, unresized returns, **1536x1024 landscape**, true transparent background, no floor, no
shadow, no text:

| File | View |
|---|---|
| `00_three_quarter.png` | front three-quarter: the barrel points toward image LEFT and about 35° toward the camera, so we see the muzzle end, the turret's LEFT side (the side with the big blue sensor lens and the pennant) and the front of the pedestal with its hazard hatch; camera slightly ABOVE the pedestal top (we see the top of the gold ring a little) |
| `01_front.png` | straight front: the muzzle points straight at the camera, centred |
| `02_back.png` | straight back, as the concept's back view |
| `03_left.png` | strict 90° profile of the turret's LEFT side: barrel points to image LEFT (as the concept's side view) |
| `04_right.png` | strict 90° profile of the turret's RIGHT side: barrel points to image RIGHT |

Run 1: generate `00_three_quarter.png` only, check it, at most one corrective regeneration, then stop.
Run 2 (separate invocation): 01–04 with the selected 00 as input 5. At most one corrective regeneration per view.

## Prompt content (adapt per view)

TASK CONTEXT, GAME ASSET: a faithful high-definition 3D modelling reference of an approved concept, for an MM6-8-style
first-person RPG. Not a new design. Near-orthographic camera, even soft neutral studio light (no dramatic light, no
rim light, no strong cast shadows; light is baked into the texture), painterly-realistic game materials like the
concept, sharp fine detail, a credible solid three-dimensional object.

Identity (from the concept; about 1.8 m tall in all):
- PEDESTAL: a squat TAPERED block of pale grey-green settler prefab composite panels (wider at the bottom, slightly
  rounded corners, about as tall as the head assembly above it), vertical darker grey-green ribbed seam strips at the
  corners and between panels, brass rivets, a small rectangular access hatch on the FRONT with yellow-and-black hazard
  stripes; it stands on a low SQUARE base plate of the same panels with FOUR big brass hex bolts on square blocks at
  the corners. On top: a heavy riveted brushed GOLD-BRASS turning ring, then a slim dark turntable disc.
- YOKE: from a gold bracket at the FRONT of the turntable a thick angled white-ceramic ARM rises up and BACK to a
  large round gold ELBOW HUB under the middle of the head; black segmented cables loop from the head down behind the
  arm to the turntable.
- HEAD: a sleek, smoothly CURVED white/ivory ceramic gun housing: a rounded egg / helmet shape at the rear that flows
  forward and tapers into the barrel shroud (one continuous swept form, not a drum, not a box), panelled with brushed
  gold trim strips, light wear and a few small scorch flecks. On its LEFT side a big round BLUE-WHITE glowing sensor
  LENS in a gold ring. At the upper rear a short gold pole sticks out to the turret's LEFT carrying a RED cloth pennant
  with a gold circle-and-line glyph, hanging straight down with a ragged lower edge.
- BARREL: ONE long energy rifle, about as long as the head: a ceramic shroud with gold collars, then an exposed
  glowing BLUE-WHITE energy coil / tube section (visible between the shroud and the front sleeve), then a ceramic front
  sleeve and a gold-and-ceramic muzzle with a glowing blue-white emitter at the tip.
- Energy parts (lens, coil, emitter) are bright blue-white and clearly separate from the ceramic; their light does
  not spill onto the surrounding surfaces as a halo.

Pose: REST pose, the barrel exactly HORIZONTAL (level, not raised), the head level, the pennant hanging straight down.
The whole turret inside the frame with generous margins.

Do NOT: draw the shield shell, glow halos, light rays or sparks; raise the barrel; add a second barrel, extra lenses,
legs or wheels; turn the head into a cylinder or a box; change the colours (ivory ceramic, brushed gold, pale
grey-green pedestal, yellow-black hazard hatch, red pennant with gold glyph, blue-white energy); add any orange; crop
anything; draw a floor, shadow, background or text.

## Per-image checks (re-run before you select a view)

Whole turret inside the frame with margins; tapered grey-green pedestal on a square plate with four corner bolts;
hazard-striped hatch on the pedestal front (visible in 00 and 01, not in 02); gold ring and turntable; the angled yoke
arm with the gold elbow hub; one curved ceramic head flowing into one long level barrel with a visible glowing coil
and emitter; one big blue lens on the turret's LEFT side; red pennant with a gold glyph on the LEFT rear; no shield;
transparent background; 1536x1024. For 01–04: the same turret, pose, proportions and colours as the primary
(input 5). `03_left`: barrel to image LEFT, lens and pennant on the near side. `04_right`: barrel to image RIGHT, the
lens and pennant are on the far side (the pennant may show behind the head; no lens on this side unless the primary
shows one). `01_front`: muzzle emitter centred, pedestal hatch visible below. `02_back`: the rounded rear of the head
with cables, the pennant at image LEFT, no hatch.
Stop after one corrective regeneration per view and record what remains.

## Records

`generation_runs.json` in this folder: one entry per generation (id, view, prompt, input paths with sha256, output
path, selected flag, reason, superseded runs). Contact sheet `selected_views_review.png` (the five views once they
exist).
