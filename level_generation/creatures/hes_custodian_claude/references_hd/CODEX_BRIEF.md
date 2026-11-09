# Codex brief: HD modelling references for the Custodian (Hesper monster 10100)

Scope: image generation only. Write ONLY into `level_generation/creatures/hes_custodian_claude/references_hd/`.
Do not edit any other file, do not run builds, do not call Meshy. Use your built-in image generation tool (PIL only to
check sizes and alpha, and to remove a plain background to true transparency if the return has one).

This is a new machine of the Hesper world (an OpenYAMM world in the Might and Magic VI-VIII style), not an MM sprite:
its design authority is the user-approved concept sheet. The masters are 3D modelling references for Meshy
(image-to-3D and retexture), so the machine must read as one clear, solid, fully three-dimensional object.

## Inputs (attached in this order)

1. `concept.png`: the APPROVED concept sheet. Large right view = front three-quarter (the sphere faces the viewer,
   turned slightly to image left). Upper-left = straight side view (the eye points to image LEFT: this is the machine's LEFT side). Middle-left =
   straight back view. Lower-left = front view with both arms raised out sideways (a sweep pose: NOT the rest pose).
2. `concept_main.png`: crop of the large view (detail and the REST pose to use).
3. `concept_side.png`: crop of the side view (proportions authority: arm lengths, mount height, disc size).
4. `concept_back.png`: crop of the back view (back panels, louvred vent, arm mounts).
5. (run 2 only) the selected `00_three_quarter.png`.

## Deliverables

Five masters in this folder, unresized returns, **1536x1024 landscape**, true transparent background, no floor, no
shadow, no text:

| File | View |
|---|---|
| `00_three_quarter.png` | front three-quarter as the concept's main view: the eye about 35° to image LEFT of the camera axis, so we see the eye, the red sigil field and the machine's LEFT flank and arm; camera at the eye's height, very slightly above |
| `01_front.png` | straight front: the eye centred, looking at the camera, both arms symmetric |
| `02_back.png` | straight back, as the concept's back view (louvred vent centred) |
| `03_left.png` | strict 90° profile of the machine's LEFT side: the eye points to image LEFT (as the concept's side view) |
| `04_right.png` | strict 90° profile of the machine's RIGHT side: the eye points to image RIGHT |

Run 1: generate `00_three_quarter.png` only, check it, at most one corrective regeneration, then stop.
Run 2 (separate invocation): 01–04 with the selected 00 as input 5. At most one corrective regeneration per view.

## Prompt content (adapt per view)

TASK CONTEXT, GAME ASSET: a faithful high-definition 3D modelling reference of an approved concept, for an MM6-8-style
first-person RPG. Not a new design. Near-orthographic camera, even soft neutral studio light (no dramatic light, no
rim light, no strong cast shadows; light is baked into the texture), painterly-realistic game materials like the
concept, sharp fine detail, a credible solid three-dimensional machine.

Identity (from the concept; the sphere about 2.4 m across):
- BODY: one large hovering SPHERE of bone-white Colonial ceramic panels with thin brushed-GOLD edge strips,
  chipped and cracked all over (dark cracks, missing chips, rust-brown grime in the cracks). On the upper FRONT a
  large RED field carrying the gold ring-and-stem sigil (a gold ring over a vertical stem). DEEP BLUE panels on the
  flanks and a broad deep-blue vertical band on the back with a dark LOUVRED VENT at the centre of the back. On the
  upper rear LEFT a missing panel shows dark machinery and black cable bundles.
- BELT: two broad ceramic RINGS round the middle, gold-edged, each with a V-NOTCH at the FRONT (upper ring points
  down, lower ring points up); between them a dark recessed lens belt with ONE glowing amber-orange EYE at the front.
- TOP: a short gold post carrying a small box SENSOR HEAD (ceramic, a vent grille at its back, one small blue-white
  lens at its front).
- BOTTOM: a flat ring of round thrust VENTS under the sphere, each glowing amber-orange. No legs, no wheels.
- ARMS: exactly TWO, one each side, mounted on the ring belt's flanks by a big round gold shoulder hub. Each arm: a
  gold-jointed upper arm in ceramic shell plates with exposed hydraulic pistons and black cables, an elbow hub, a
  forearm, a wrist hub, then a large circular SAW DISC (grey steel, fine serration, a gold hub) set VERTICAL with its
  flat faces toward the sides (rim pointing forward and back), about one third of the sphere's width.

Pose: the concept main view's REST pose: both arms hang down and slightly forward and outward from the shoulders,
the discs beside and below the lower half of the sphere, clearly SEPARATED from the sphere and from each other by air
gaps (no part touching the shell), discs vertical. The whole machine inside the frame with generous margins.

Do NOT: draw an energy shield, glow halos, light rays, sparks or smoke; add a third arm, extra eyes or legs; Kreegan
violet resin, chitin, bone or organic growth; change the colours (bone-white ceramic, brushed gold, deep blue, red
field with the gold sigil, amber-orange eye and vents, one blue-white sensor lens); raise the arms; crop anything;
draw a floor, shadow, background or text.

## Per-image checks (re-run before you select a view)

Whole machine inside the frame with margins; the sphere with two V-notched rings and one amber eye (front only; no
eye at the back); the red sigil field at the upper front; the sensor head on its post; the vent ring underneath;
exactly two arms in the rest pose, each ending in one vertical saw disc, with air gaps to the shell; transparent
background; 1536x1024. For 01–04: the same machine, pose, proportions and colours as the primary (input 5).
`03_left`: eye to image LEFT, the missing back panel on the near side (upper rear). `04_right`: eye to image RIGHT, no
missing panel unless the primary shows one there. `01_front`: eye and sigil centred, arms symmetric. `02_back`: the blue
back band with the louvred vent centred; no eye, no sigil.
Stop after one corrective regeneration per view and record what remains.

## Records

`generation_runs.json` in this folder: one entry per generation (id, view, prompt, input paths with sha256, output
path, selected flag, reason, superseded runs). Contact sheet `selected_views_review.png` (the five views once they
exist).
