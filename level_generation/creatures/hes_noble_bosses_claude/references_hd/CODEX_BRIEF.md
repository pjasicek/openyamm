# Codex brief: HD modelling masters for the Noble bosses (Hesper 10105/10106, 10108, 10109, 10120/10145/10146)

Scope: image generation only. Write ONLY into `level_generation/creatures/hes_noble_bosses_claude/references_hd/<boss>/`
(the boss named in your task). Do not edit any other file, do not run builds, do not call Meshy. Use your built-in
image generation tool; PIL only to check sizes and alpha, and to turn a plain flat background into true transparency.

These are new bosses of the Hesper world (an OpenYAMM world in the Might and Magic VI-VIII style). Their body already
exists as a finished, rigged 3D model: **the winged Kreegan body** (the MM6 flying demon). The guide renders attached
below ARE that model, rendered from the exact cameras we will use. The masters must show **the same body with the
boss's armour painted onto it**, so that a 3D modeller can fit the armour onto the existing model. The armour design
comes from the boss's APPROVED concept sheet.

## Inputs (attached in this order)

1. `guides/00_three_quarter.png`: the existing 3D body, front three-quarter: it faces toward image left and the
   camera; we see its front and its LEFT side (its left arm is the one on image right). Perspective camera at
   mid-body height.
2. `guides/01_front.png`: the body straight from the front (its left arm on image right).
3. `guides/02_back.png`: the body straight from behind (its left arm on image left).
4. `guides/03_left.png`: strict profile of the body's LEFT side (it faces image LEFT).
5. `guides/04_right.png`: strict profile of the body's RIGHT side (it faces image RIGHT).
6. The boss's APPROVED concept sheet (design authority for armour, colours and add-ons; see your boss section).
7. (where listed) further crops or item art named in your boss section.

The guides have their wings removed ON PURPOSE (the wings are a separate, finished part). **Do not add wings.**

## Deliverables (in `references_hd/<boss>/`)

Five masters, **1024 × 1536 portrait**, true transparent background, no floor, no shadow, no text:

| File | Paint over guide |
|---|---|
| `00_three_quarter.png` | `guides/00_three_quarter.png` |
| `01_front.png` | `guides/01_front.png` |
| `02_back.png` | `guides/02_back.png` |
| `03_left.png` | `guides/03_left.png` |
| `04_right.png` | `guides/04_right.png` |

Generate `00_three_quarter.png` first; check it; at most one corrective regeneration. Then 01-04, each with its own
guide AND your selected 00 attached, so all five show the same armour. At most one corrective regeneration per view.
Save every raw return too (`raw_<view>_<n>.png`).

## The one hard rule: same body, same framing

Each master is its guide with armour on it. Keep **exactly** the guide's canvas, figure position, figure size, pose,
camera and proportions: head, horns, ears, open fanged mouth, eyes, the long arms hanging down with open claws, the
six-clawed hands, the legs and the taloned feet stay where they are and the same size. Armour sits ON the body
surface (fitted, a few centimetres thick; pauldrons and spurs may stand further out). Do not move, lengthen, bend or
re-pose any limb; do not change the camera; do not crop.

## Prompt content (adapt per view)

TASK CONTEXT, GAME ASSET: a high-definition 3D modelling reference: the attached 3D body render, repainted as the same
figure wearing the boss's armour from the approved concept. Near-orthographic (as the guide), even soft neutral
studio light (no dramatic light, no rim light, no cast shadows; light is baked into the texture), painterly-realistic
game materials like the concept, sharp fine detail, a credible solid three-dimensional figure.

Common Noble carapace (from the concept): gilded grown-chitin plates with ivory bone-ceramic inserts, fine gold edges,
black-violet resin joints between plates, restrained orange glowing conduit seams; fitted rib/leaf-shaped plates that
leave the lean body legible: a fitted cuirass over chest and abdomen (the charcoal ribbed belly may show between
plates), spurred pauldrons, upper-arm and forearm guards with ivory spurs, a belt with pointed leaf-plate tassets
hanging over the hips front, sides and back (no lower than mid-thigh), thigh plates, knee caps, plated shins. Hands,
feet, head and horns stay bare (claws ivory). The skin keeps the body's violet; change only its hue as the boss
section says. Upper back: two small bare dark resin sockets on the shoulder blades where the wings attach; the back
armour stays clear of them.

Do NOT: add wings, a tail, a cape, a robe, extra limbs, a weapon or anything held in the hands, a shield, a floor or
shadow, energy effects in the air, text; change the pose, the camera or the head.

## Per-image checks (re-run before selecting)

1. Overlay the master on its guide (PIL, 50 %): the bare head, hands and feet line up within a few pixels; the
   figure's outline grows only where armour stands out.
2. 1024 × 1536, true alpha, nothing cropped, no wings.
3. The armour matches the concept (plates, colours, add-ons) and is the same in all five views; left/right correct.

## Records

`generation_runs.json` in your folder: per run id, prompt, input sha256, output path, selected flag, reason,
superseded runs; and a `selected_views_review.png` contact sheet of the five selections.

---

## vhorrax: Lord Vhorrax (10105/10106)

Concept: `design/kreegan_world/concepts/monsters/boss_vhorrax.png` (input 6), the duellist. Skin deep plum. His
**distinctive gilded carapace** as drawn: rich pale-gold leaf plates with ivory inserts and many sharp ivory/gold
spurs, high spurred pauldrons rising beside the head, a layered pointed-leaf tasset skirt to mid-thigh, sculpted knee
and shin plates, forearm guards with backswept spurs, orange seams. Aristocratic and precise, not bulky. His saber is
a separate model: **empty hands.**

## coil_keeper: The Coil Keeper (10108)

Concept: `design/kreegan_world/concepts/monsters/boss_coil_keeper.png` (input 6). Skin plum-violet. The Noble
carapace in pale rich gold with ivory inserts and orange seams, as drawn, plus **the coil harness**: a gilded back
frame (shoulder yoke and waist band) carrying **two upright coil cylinders** on the upper back between the shoulder
blades, glass-and-ceramic capsules wound with gold wire, glowing **deep electric violet with white-hot cores**, capped
in ivory and gold, short resin cables from their bases into the spine plates. The cylinders stand up behind the head
(visible over the shoulders from the front). His halberd is a separate model: **empty hands.**

## conductor: The Conductor (10109)

Concept: `design/kreegan_world/concepts/monsters/boss_conductor.png` (input 6). Skin dark red-violet. The Noble
carapace in pale rich gold with ivory inserts and orange seams, as drawn, plus: **a raised gorget** of ivory fins and
gold around the neck and upper chest framing the head, with **one glowing violet-white node at the throat**; on the
back of his LEFT forearm and upper arm, gold sockets with **three short ribbed resin cables** ending in open gold plugs
that hang free a short way (no lower than his knee; they do not reach the floor), glowing violet-white at the plugs.
His staff is a separate model: **empty hands.**

## hierarch: The Hierarch (10120/10145/10146)

Concept: `design/kreegan_world/concepts/monsters/boss_hierarch.png` (input 6), the standing views (upper left, lower
left), not the throne. Skin dark red-violet. **Imposing gilded carapace**: heavier, taller spurred pauldrons and
cuirass than the other Nobles, a long layered leaf-plate tasset skirt to the knee, plated limbs, orange seams. **A
crown of fused irregular ivory bone** grows around the head and between the horns (the horns stay, the crown adds
tall bone points around them). **Spinal cables:** four to six thick ribbed black-violet cables leave his spine between
the shoulder blades, each with a gold coupling ring, and hang down his back to about the back of the knees (not to
the floor), their gold end-plugs glowing orange. No weapon, staff or orb: **empty hands.**
