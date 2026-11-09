# Codex brief (run 1): HD three-quarter primary and prop sheets for the MM7 Angel (m150)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm7_m150_claude/references_hd/`.
Do not edit any other file, do not run builds, do not call Meshy.

This run produces the primary `00_three_quarter.png` and two prop sheets (`sword.png`, `shield.png`). The four
orthographic views are a later, separate run.

Use your built-in image generation. Record format: `level_generation/creatures/mm7_m398_claude/references_hd/
generation_runs.json` (id, family `m150`, role `primary` / `prop`, prompt, inputs with sha256, output path, selected
flag, reason, superseded runs). Keep raw returns under `raw/` (`m150_three_quarter_v1.png`, `m150_sword_v1.png`, ...).

## Attached inputs, in order (paths relative to `level_generation/creatures/`)

1. `mm7_m150/native/m150sa0.png` — ORIGINAL native front frame (transparent background). Design, proportions and
   palette authority.
2. `mm7_m150/native/m150sa1.png` — ORIGINAL native front three-quarter frame.
3. `mm7_m150/native/m150sa2.png` — ORIGINAL native side profile.
4. `mm7_m150/native/m150sa3.png` — ORIGINAL native rear three-quarter.
5. `mm7_m150/native/m150sa4.png` — ORIGINAL native back (wings from behind, back of the helmet, skirt seat).
6. `mm7_m150/aligned_2x/m150sa1.png` — restored 2x three-quarter view, for SURFACE MATERIAL ONLY (feathers, metal,
   skin, cloth finish). It never sets the design, pose or proportions.

The sprites show a wavy-bladed sword in the angel's RIGHT hand and a round bronze shield on its LEFT forearm. The 3D
model gets the sword and the shield as separate props, so the body reference must show the angel EMPTY-HANDED and
WITHOUT THE SHIELD.

## Deliverable 1: `00_three_quarter.png` (primary)

Landscape 1536 x 1024, true transparent background, unresized return. Front-right three-quarter (camera 40–45°
toward the figure's own RIGHT side), camera at chest height, slightly above, near-orthographic.

### Prompt content

TASK CONTEXT — MM7 FANTASY-GAME ASSET RESTORATION: faithful high-definition reconstruction of the EXISTING Might and
Magic VII Angel monster from the supplied original sprites, as a 3D modelling reference. Not a new design.
Output: exactly ONE 1536 x 1024 landscape PNG with a genuine transparent background. ONE complete figure, full body
from the helmet crest to the soles AND both complete wings to their tips, centred, generous margins, near-orthographic
camera, no floor, no shadow, no scenery, no text. Even soft neutral studio light (no dramatic lighting, no rim light,
no glow) that still shows form. Credible, fully three-dimensional sculpt, semi-realistic game materials, sharp fine
detail.

Identity (from the native sprites): a tall, athletic, muscular winged male warrior in Greek / Roman style armour.
- HEAD: stern clean-shaven face with tan skin, strong jaw, straight nose, dark eyes. A polished BRASS-GOLD crested
  helmet: rounded bowl, a tall curling brass crest running front to back over the top (scroll-like), small swept-back
  brass wing ornaments at the temples, open face with cheek guards, a small green-teal jewel at each side. Dark hair
  only where the native shows it at the nape.
- TORSO: a dark gunmetal-steel muscled breastplate (cuirass) with polished brass-gold edges, brass shoulder rims and
  brass straps, a matching back plate; a brass belt at the waist.
- ARMS: bare muscular tan upper arms and shoulders; a dark steel / brass bracer on each forearm; bare tan hands with
  five fingers.
- WAIST AND LEGS: a GREEN cloth skirt (kilt) to just above the knee, with a row of dark brown leather strap tabs
  (pteruges) hanging over it from the belt; bare tan knees; dark steel greaves with brass rims and straps on the shins;
  brown leather sandals with brass buckles.
- WINGS: two large FEATHERED angel wings attached at the shoulder blades, behind the shoulders: white to pale
  lavender upper feathers with soft blue-violet shading, deep blue-violet undersides and flight-feather roots, long
  primary flight feathers at the tips, layered coverts, as in the native sprites.
- COLOUR AND MATERIAL: tan skin, polished brass-gold, dark gunmetal steel, green cloth, dark brown leather,
  white-lavender feathers with blue-violet undersides.

Pose: a neutral A-pose for rigging. Standing upright, weight even, legs straight and apart with a clear gap of air
between the legs and between the feet (feet about shoulder width apart, flat, toes forward). Arms hang down and out to
the sides at about 35 degrees from vertical, elbows very slightly bent, a clear gap of air between each arm and the
torso and between each hand and the thigh. Both hands EMPTY, open and relaxed, five fingers slightly apart, palms
facing the thighs. Head level, looking forward. WINGS spread wide and RAISED in a high open V like the native front
standing frame (do not fold them): wing roots behind the shoulder blades, the leading edges rising outward above the
shoulders, wing tips at about the height of the helmet crest, membranes / feathers fully open; the lower (trailing)
edge of each wing stays ABOVE the elbows and does not touch the arms, the head or the other wing.

Do NOT: draw the sword or any weapon, the shield, a cape, a cloak, a halo, a spear; add a beard, extra arms, extra
wings or extra feathers growing from the arms; add glow, aura, light rays or magic effects; change the colours (skirt
stays green, armour stays dark steel with brass, wings stay white-lavender with blue-violet undersides); make it
cartoonish or chibi; crop the wing tips, the crest or the feet; add a floor, shadow or text.

INPUT ROLES: Inputs 1–5 are the native standing views (front, front three-quarter, side, rear three-quarter, back):
design, proportions and palette authority; magenta/black/transparent pixels are background, not part of the angel.
Input 6 is the restored three-quarter: SURFACE MATERIAL ONLY, never design, pose or proportions.
CAMERA: FRONT-RIGHT THREE-QUARTER, camera 40–45 degrees toward the figure's anatomical RIGHT from straight front, chest
height slightly above. The face and toes point diagonally toward SCREEN-LEFT. FRAMING / ALPHA: the whole figure and
both wings inside the frame with generous transparent margins, genuine RGBA alpha outside the silhouette and in the air
gaps between legs, between arms and body. No painted checkerboard. Return exactly 1536 x 1024 unresized.

### Checks before selecting

- front-right three-quarter camera at chest height, near-orthographic, whole figure and both wing tips inside the
  frame with margins, 1536 x 1024, true transparent background (not a checkerboard drawn into the pixels);
- empty hands, no sword, no shield, no other equipment beyond the listed armour;
- brass crested helmet with open face, clean-shaven tan face;
- dark steel breastplate with brass trim, green skirt with brown leather tabs, greaves, sandals;
- two feathered wings attached behind the shoulder blades, raised in a V, not touching the arms or head;
- A-pose with the stated gaps, five fingers per hand.

If the first return fails a check, do ONE targeted corrective regeneration, then select the better of the two and
note any residual fault in its reason. Do not chase minor differences.

## Deliverables 2 and 3: prop sheets

Landscape 1536 x 1024, transparent background, flat diffuse studio light, no ground, shadow or text, no person or
hand in the image. Two large views of the SAME prop side by side, uncropped, with physical thickness. No decorative
additions absent from the sprites.

- `sword.png` — the angel's RIGHT-hand sword only: a long FLAMBERGE (wavy, serpentine double-edged blade with about
  six gentle waves along its length, tapering to a point), bright polished silver steel blade with a central fuller;
  a brass-gold crossguard with curled ends, a dark wrapped grip and a round brass pommel. Native proportions: blade
  about 1.0 m, grip one hand long. One broad flat view (the wave visible) and one edge-on / three-quarter view
  showing the blade thickness.
- `shield.png` — the angel's LEFT-forearm shield only: a round convex dark bronze shield about 70 cm across, with a
  raised brass-gold rim, a ring of short brass studs or small spikes around the rim as in the native front frame, a
  central brass boss; plain otherwise (no emblem). One exterior three-quarter view and one inner/back three-quarter
  view showing the curved shell thickness, the leather arm strap and the hand grip.

Checks: prop alone, complete, both views of the same object, transparent background, correct size proportions.
