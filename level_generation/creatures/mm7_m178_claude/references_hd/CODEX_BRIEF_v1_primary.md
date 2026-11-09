# Codex brief (run 1): HD three-quarter primary for the MM7 Devil (m178)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm7_m178_claude/references_hd/`.
Do not edit any other file, do not run builds, do not call Meshy.

This run produces ONLY the primary `00_three_quarter.png`. The four orthographic views are a later, separate run.

Use your built-in image generation. Record format: `level_generation/creatures/mm7_m418_claude/references_hd/
generation_runs.json` (id, family `m178`, role `primary`, prompt, inputs with sha256, output path, selected flag,
reason, superseded runs). Attached inputs, in order (paths relative to `level_generation/creatures/`):

1. `mm7_m178/native/m178sa0.png` — ORIGINAL native front frame (transparent background). Design, proportions and
   palette authority.
2. `mm7_m178/native/m178sa1.png` — ORIGINAL native front three-quarter frame.
3. `mm7_m178/native/m178sa2.png` — ORIGINAL native right profile (the creature faces IMAGE RIGHT; its right side is
   toward the camera): tail, spikes, hands, feet.
4. `mm7_m178/native/m178sa3.png` — ORIGINAL native rear three-quarter.
5. `mm7_m178/native/m178sa4.png` — ORIGINAL native back.
6. `mm7_m178/aligned_2x/m178sa0.png` — restored 2x front view, for SURFACE MATERIAL ONLY (pebbled hide, plates,
   spikes). It never sets the design, pose or proportions.

## Deliverable

| File | View |
|---|---|
| `00_three_quarter.png` | front-right three-quarter (camera 40–45° toward the creature's own RIGHT side), camera at chest height, slightly above; 1024 x 1536 PORTRAIT, true transparent background, unresized return |

Keep raw returns under `raw/` (`m178_three_quarter_v1.png`, ...). Write `generation_runs.json`. If the first return
fails a check below, do ONE targeted corrective regeneration, then select the better of the two and note any
residual fault in its reason. Do not chase minor differences.

## Prompt content

TASK CONTEXT — MM7 FANTASY-GAME ASSET RESTORATION: faithful high-definition reconstruction of the EXISTING Might and
Magic VII Devil monster (a wingless, long-armed demon creature) from the supplied original sprites, as a 3D modelling
reference. Not a new design. Output: exactly ONE PNG with a genuine transparent background. ONE complete creature,
from the head spike tips to the toe claws and the tail tip, centred, generous margins, near-orthographic camera, no
floor, no shadow, no scenery, no text. Even soft neutral studio light (no dramatic lighting, no rim light) that still
shows form. Credible, fully three-dimensional sculpt, semi-realistic game materials, sharp fine detail.

Identity (from the native sprites): a lean, upright, wiry biped about as tall as a man.
- HEAD: a small broad reptilian head on a short neck; a wide horizontal mouth with a grin of many pale fine pointed
  teeth (upper and lower rows); bright glowing-yellow eyes with tiny pale centres under a heavy brow; small pointed
  ears at the sides; short horns. THREE long ivory-grey curved SPIKES rise from the top and back of the skull.
- SHOULDERS AND BACK: two or three long ivory-grey spikes rise from each shoulder top and the upper back, curving
  outward and up; a low ridge runs down the spine.
- BODY: lean muscular torso with a narrow waist; a broad dark slate-violet (blue-grey) PLATED chest and abdomen with
  defined pectoral and abdominal plates down to the groin; the rest of the body is ochre-brown pebbled reptilian hide.
- ARMS: very LONG thin arms; a row of six to eight short ivory spikes along the outer edge of each forearm.
- HANDS: ENORMOUS hands, reaching down to the knees, each with four very long separated bony fingers (three long
  fingers and a long thumb) ending in long ivory-grey hooked talons.
- LEGS: lean, slightly bent legs; big clawed feet: dark slate-violet tops of the feet, three or four pale hooked toe
  claws in front and a pale backward hooked spur at the heel.
- TAIL: a long thin ochre tail from the base of the spine, curving out behind and then UP, with a row of small ivory
  spikes along its upper curve and a small pointed spear-head (cone) tip.
- COLOUR AND MATERIAL: ochre-brown to tan pebbled hide with darker brown shading in the creases; dark slate-violet
  plates on chest, abdomen and feet; ivory-grey spikes, claws and teeth; glowing yellow eyes.

Pose: a neutral A-pose for rigging, close to the native stance: standing upright on the two legs with the feet
apart (a clear gap between the legs), the knees only slightly bent, the arms hanging down and OUT about 35 degrees
from vertical with a clear gap of air between each arm, hand and the body and legs, the long fingers open and
slightly spread so each finger is separate. The tail sweeps back and curls up behind the body, clear of the legs.
Head facing forward, mouth closed in its toothy grin.

Do NOT: add wings, armour, clothing, weapons, a loincloth, jewellery, fire, glow effects or extra horns; change the
colours; make the hands small; give the hands more or fewer than four fingers; crop the spikes, claws or tail tip;
add a floor, shadow or text.

INPUT ROLES: Inputs 1–5 are the native standing views (front, front three-quarter, right profile, rear
three-quarter, back): design, proportions and palette authority; transparent pixels are background. Input 6 is the
restored front: SURFACE MATERIAL ONLY, never design, pose or proportions.
CAMERA for this primary: FRONT-RIGHT THREE-QUARTER, camera 40–45 degrees toward the creature's anatomical RIGHT from
straight front, chest height slightly above, near-orthographic. The face looks diagonally toward IMAGE LEFT.
FRAMING / ALPHA: the whole creature including the head spikes, hands and tail tip with generous transparent margins,
genuine RGBA alpha outside the silhouette and in the air gaps. No painted checkerboard. Return unresized.

## Checks before selecting

- front-right three-quarter camera, near-orthographic, whole creature including the tail tip and spike tips inside
  the frame with margins, true transparent background (not a checkerboard drawn into the pixels), 1024 x 1536;
- small reptilian head with toothy grin, yellow eyes, pointed ears, three head spikes, shoulder spikes;
- dark slate-violet chest/abdomen plates, ochre pebbled hide elsewhere;
- enormous hands with four separated long clawed fingers each, forearm spike rows;
- big clawed feet with slate tops and heel spurs; long thin tail with spikes and a cone tip;
- arms, hands and tail clear of the body and legs.
