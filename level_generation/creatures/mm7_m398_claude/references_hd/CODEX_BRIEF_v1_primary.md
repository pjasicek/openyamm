# Codex brief (run 1): HD three-quarter primary for the MM7 Skeleton Warrior (m398)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm7_m398_claude/references_hd/`.
Do not edit any other file, do not run builds, do not call Meshy.

This run produces ONLY the primary `00_three_quarter.png`. The four orthographic views are a later, separate run.

Use your built-in image generation. Record format: `level_generation/creatures/mm6_ske_claude/references_hd/
generation_runs.json` (id, family `m398`, role `primary`, prompt, inputs with sha256, output path, selected flag,
reason, superseded runs). Attached inputs, in order (paths relative to `level_generation/creatures/`):

1. `mm7_m398/native/m398sa0.png` — ORIGINAL native front frame (transparent background). Design, proportions and
   palette authority.
2. `mm7_m398/native/m398sa1.png` — ORIGINAL native front three-quarter frame (the figure's RIGHT side toward camera).
3. `mm7_m398/native/m398sa2.png` — ORIGINAL native right profile (shows the open armour side with ribs, the neck,
   the helmet spike and the boot shape).
4. `mm7_m398/native/m398sa3.png` — ORIGINAL native rear three-quarter.
5. `mm7_m398/native/m398sa4.png` — ORIGINAL native back.
6. `mm7_m398/aligned_2x/m398sa0.png` — restored 2x front view, for SURFACE MATERIAL ONLY (metal, bone, cloth
   finish). It never sets the design, pose or proportions.

The sprites show a short straight sword in the right hand and two arrows stuck in the torso. The 3D model gets the
sword and the arrows as separate props later, so this reference must show the warrior EMPTY-HANDED and WITHOUT
ARROWS.

## Deliverable

| File | View |
|---|---|
| `00_three_quarter.png` | front-right three-quarter (camera 40–45° toward the figure's own RIGHT side), camera at chest height, slightly above; 1024 x 1536 portrait, true transparent background, unresized return |

Keep raw returns under `raw/` (`m398_three_quarter_v1.png`, ...). Write `generation_runs.json`. If the first return
fails a check below, do ONE targeted corrective regeneration, then select the better of the two and note any
residual fault in its reason. Do not chase minor differences.

## Prompt content

TASK CONTEXT — MM7 FANTASY-GAME ASSET RESTORATION: faithful high-definition reconstruction of the EXISTING Might and
Magic VII Skeleton Warrior monster from the supplied original sprites, as a 3D modelling reference. Not a new design.
Output: exactly ONE 1024 x 1536 portrait PNG with a genuine transparent background. ONE complete figure, full body
from the helmet spike to the soles, centred, generous margins, near-orthographic camera, no floor, no shadow, no
scenery, no text. Even soft neutral studio light (no dramatic lighting, no rim light) that still shows form.
Credible, fully three-dimensional sculpt, semi-realistic game materials, sharp fine detail.

Identity (from the native sprites): an undead human skeleton in battered armour, tall and lanky, narrow body, long
thin limbs.
- HEAD: a bare aged ochre-ivory human SKULL (no skin, no eyes): large dark hollow round eye sockets, dark nasal
  opening, a full row of exposed teeth, lower jaw closed. On top a small rounded dark steel skull-cap HELMET with a
  narrow brass band around its rim and one short thin spike on top. The face is fully open.
- NECK: thin bony cervical vertebrae under the skull, inside a raised brass-rimmed collar of the breastplate.
- TORSO: a dark battered steel breastplate (cuirass) with a thick polished brass-gold border around the neck, the
  arm holes and the lower edge; the plate is dented and streaked with rusty red. The SIDES of the cuirass are open
  frames rimmed in brass, through which thin curved ribs show (see input 3). A matching dark steel back plate.
- ARMS: the SHOULDERS and UPPER ARMS are bare bone (humerus, knobbly shoulder joint), ochre-ivory with rusty red
  stains. From the elbow down, dark steel GAUNTLETS (forearm tube plus articulated plated gloves with a thumb and
  four separate fingers).
- WAIST AND LEGS: a ragged faded BLUE-VIOLET cloth short trousers (breeches) from the waist to just below the knees,
  torn and frayed at the hem, stained rusty red; a thin brass belt band at the waist edge of the cuirass. Bare bone
  knees and the upper shins below the hem (ochre-ivory, stained). Tall dark steel GREAVES / boots from mid-shin to
  the feet, each with a brass ring at the top, armoured foot (sabaton).
- COLOUR AND MATERIAL: dark gunmetal steel with soft highlights, polished brass-gold trim, aged ochre-ivory bone,
  faded blue-violet cloth, rusty dark red streaks and smears on bone, armour and cloth (as in the native sprites).

Pose: a neutral A-pose for rigging. Standing upright, weight even, legs straight and apart with a clear gap of air
between the legs and between the feet (feet about shoulder width apart, flat on the ground, toes forward). Arms hang
down and out to the sides at about 35 degrees from vertical, elbows very slightly bent, with a clear gap of air
between each arm and the torso and between each hand and the thigh. Both gauntleted hands open and relaxed, the four
fingers slightly apart, thumbs relaxed, palms facing the thighs. Head level, looking forward.

Do NOT: draw the sword or any weapon, the arrows, a shield, a cape, a cloak, a skirt; add skin, flesh, eyes, muscles
or hair; cover the skull face with a visor; add extra spikes, horns, pauldrons, ornaments or jewellery; make it
cartoonish, chunky or muscular; change the colours (trousers stay faded blue-violet, metal stays dark steel with
brass trim); add glowing eyes, aura, smoke or magic effects; crop the helmet spike or the feet; add a floor, shadow
or text.

INPUT ROLES: Inputs 1–5 are the native standing views (front, front three-quarter, right profile, rear
three-quarter, back): design, proportions and palette authority; transparent pixels are background. Input 6 is the
restored front: SURFACE MATERIAL ONLY, never design, pose or proportions.
CAMERA for this primary: FRONT-RIGHT THREE-QUARTER, camera 40–45 degrees toward the figure's anatomical RIGHT from
straight front, chest height slightly above, near-orthographic. Show FRONT and RIGHT flank: the skull and toes point
diagonally toward SCREEN-LEFT. FRAMING / ALPHA: the whole figure occupies about 80 % of the height with generous
transparent margins, genuine RGBA alpha outside the silhouette and in the air gaps between legs and between arms and
body. No painted checkerboard. Return exactly 1024 x 1536 unresized.

## Checks before selecting

- front-right three-quarter camera at chest height, near-orthographic, whole figure inside the frame with margins,
  1024 x 1536, true transparent background (not a checkerboard drawn into the pixels);
- empty hands, no sword, no arrows, no other equipment beyond the listed armour;
- bare skull face with hollow sockets and teeth under a small spiked brass-banded cap helmet;
- bare-bone shoulders and upper arms, gauntlets from the elbow, five digits per gauntlet;
- blue-violet ragged trousers to below the knee, bare bone knees, greaves with brass rings;
- A-pose with the stated gaps.
