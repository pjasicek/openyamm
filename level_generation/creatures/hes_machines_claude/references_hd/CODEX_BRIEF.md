# Codex brief: HD modelling references for the colony and Lattice machines

Project `level_generation/creatures/hes_machines_claude/` (Round 3, Claude C). Each Codex run handles **one subject**
(its prompt names it: `starport_turret`, `capacitor_column` or `throne_conduit`) and **one run kind** (run 1: the
primary only; run 2: the four side views).

## Scope

- Image generation only, with your built-in image generation tool. Python (PIL) only to check sizes and alpha, and
  to turn a plain flat background into true transparency if the return has one.
- Write only into `level_generation/creatures/hes_machines_claude/references_hd/<subject>/`. No other file, no
  builds, no Meshy.
- These are new machines of the Hesper world (an OpenYAMM world in the Might and Magic VI–VIII style). The design
  authority is the user-approved concept sheet `concept.png` in the subject's folder. The masters are 3D modelling
  references for Meshy (image-to-3D and retexture): one clear, solid, fully three-dimensional object, faithful to the
  concept, **not a new design**.

## Inputs (attached in this order)

1. `concept.png`: the approved sheet. Large right view = the main front three-quarter view, the subject lit. Left
   column, top to bottom: side profile, back view, the **off state** (ignore the off state: always draw the subject
   lit, as the main view).
2. `concept_main.png`: crop of the main view (detail authority).
3. `concept_side.png`: crop of the side profile (proportions authority).
4. `concept_back.png`: crop of the back view.
5. Run 2 only: the selected `00_three_quarter.png` (the identity, pose and proportions authority for 01–04).

## Deliverables (in the subject's folder)

Unresized returns, true transparent background (RGBA), no floor, no shadow, no text, no glow halo.

| File | View |
|---|---|
| `00_three_quarter.png` | front three-quarter as the concept's main view, camera slightly above the object's mid-height |
| `01_front.png` | straight front |
| `02_back.png` | straight back |
| `03_left.png` | strict 90° profile of the object's LEFT side |
| `04_right.png` | strict 90° profile of the object's RIGHT side |

**Left and right:** the object's front is its muzzle (turret) or the side facing the viewer in the concept's main
view (cell, conduit). In `03_left` the object's front points to image LEFT; in `04_right` it points to image RIGHT.

Run 1: `00_three_quarter.png` only. Check it; at most one corrective regeneration; then stop.
Run 2 (separate invocation): `01`–`04` with the selected 00 as input 5. At most one corrective regeneration per view.

## Common prompt content

GAME ASSET, a faithful high-definition 3D modelling reference of an approved concept, for an MM6–8-style first-person
RPG. Near-orthographic camera, even soft neutral studio light (no dramatic or rim light, no strong cast shadows: light
is baked into the texture), painterly-realistic game materials like the concept, sharp fine detail, a credible solid
three-dimensional object. The whole object inside the frame with generous margins. Glowing parts are bright and
clearly separate from the surrounding material, **without** halos, bloom, rays, sparks or light spill.

## Subjects

### `starport_turret` — Old Starport Turret (10054), 1536 × 1024 landscape

About 1.6 m tall in all. Rest pose: the barrel exactly **horizontal**, head level. `00`: as the concept's main view,
the barrel points toward image LEFT and about 35° toward the camera, showing the muzzle, the head's LEFT side with the
lens and the pedestal's front with its red stripe.

- **Base and pedestal:** a low square base plate of ivory ceramic slabs with four big bronze hex bolts on square
  blocks at the corners; on it a squat tapered pedestal (wider at the foot) of ivory ceramic panels and faded
  deep-blue painted panels with one vertical red stripe at the front, bronze rivets; on top a heavy riveted gold
  turning ring and a dark turntable disc.
- **Yoke:** two thick angled ivory-and-blue ceramic arms (a fork) rising from the turntable to big round gold hub
  trunnions on each side of the head.
- **Head:** a boxy armoured gun housing of chamfered ceramic plates, longer than tall, with a hooded brow over the
  front; faded blue panels, a red band and a worn gold circle-and-line emblem on its flank; **one** round blue-white
  sensor lens in a gold ring on the head's LEFT side, below the brow.
- **Barrel:** **one** long energy barrel from the head's front: ceramic sleeves and gold collars, a glowing blue-white
  coil section visible between the sleeves, a ceramic-and-gold muzzle with a blue-white emitter.
- **Wear:** heavy age: chipped paint, rust-brown streaks under gold rivets and bolts, scorch marks, cracks, dust.
- **Do NOT:** add a pennant, cloth, banner, second barrel, extra lenses, resin, bone, chitin or any orange; raise the
  barrel; draw a shield, floor or text.
- **Checks:** square plate with four corner bolts; tapered pedestal with the red front stripe; gold ring; fork yoke
  with gold hubs; boxy hooded head; one level barrel with a visible coil and emitter; one lens on the LEFT side.
  `03_left`: barrel to image LEFT, lens visible. `04_right`: barrel to image RIGHT, no lens. `01_front`: the muzzle
  emitter centred. `02_back`: the closed rear of the head, no muzzle.

### `capacitor_column` — Capacitor Column cell (10142), 1024 × 1536 portrait

About 3 m tall and 2 m across, upright, rooted. Lit (on) state.

- A broad low **gold base** of chunky bevelled blocks with black-violet ribbed resin roots and cables spilling over
  it onto the floor.
- Above it **three stacked glowing drum cells**: thick translucent violet-white crystal drums with a darker vein
  pattern, lit from within, separated and capped by heavy gold clamp rings (four rings: bottom, two between, top).
- **Ivory ceramic armour plates** with gold edges on the front left and front right and at the back, curving up the
  sides of the drums like clamps; ribbed black-violet resin cables climbing between the plates and the drums.
- On top: a gold collar with three or four short thick resin-sheathed cable stubs capped in gold.
- **Do NOT:** turn it into a column (it is the cell only), add orange, add more or fewer than three drums, draw sparks,
  arcs or a floor.
- **Checks:** three drums, four gold rings, plates at front left / front right / back, resin roots on the gold base,
  cable stubs on top; the same object in all five views.

### `throne_conduit` — Throne Conduit (10143), 1024 × 1536 portrait

About 6 m tall, slender, about 1.6 m across at its flared base. Lit (on) state.

- A **flared root base**: tall pointed ivory ceramic plates with gold edges, splayed like a skirt, with thick ribbed
  black-violet resin cables between them; **four thick cables leave the base on its LEFT side** (image right
  in a front view, as the concept's main view), banded with gold rings, running along the floor about 2 m and ending cut short with gold caps.
- **The stack:** a tall **continuous vertical violet-white glowing core** (a crystal tube lit from within, a brighter
  white seam in it) held by slim gold-edged ceramic struts and a few gold bands; a gold diamond ornament at the core's
  foot.
- **The crown:** a ring of ivory-and-gold collar plates at the top of the core, then four backswept pale bone-and-gold
  horn fins around a glowing violet crystal node, a gold spike at the very top.
- **Do NOT:** segment the core, add orange, add more cables, draw a floor, arcs or sparks.
- **Checks:** flared plate base; four gold-banded cables on the object's LEFT (image right in 00 and 01); one continuous core; crown with four
  fins, the violet node and the gold spike; the same object in all five views. `02_back`: the cables to image LEFT.
  `03_left`: the cables come toward the camera (foreshortened). `04_right`: the cables point away from the camera,
  hidden or foreshortened behind the base.

## Records

`generation_runs.json` in the subject's folder: one entry per generation (id, view, prompt, input paths with sha256,
output path, selected flag, reason, superseded runs). After run 2: `selected_views_review.png`, a contact sheet of
the five selected views.
