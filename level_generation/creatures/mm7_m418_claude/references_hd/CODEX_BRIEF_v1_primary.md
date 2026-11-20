# Codex brief (run 1): HD three-quarter primary for the MM7 Troglodyte (m418)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm7_m418_claude/references_hd/`.
Do not edit any other file, do not run builds, do not call Meshy.

This run produces ONLY the primary `00_three_quarter.png`. The four orthographic views are a later, separate run.

Use your built-in image generation. Record format: `level_generation/creatures/mm6_ske_claude/references_hd/
generation_runs.json` (id, family `m418`, role `primary`, prompt, inputs with sha256, output path, selected flag,
reason, superseded runs). Attached inputs, in order (paths relative to `level_generation/creatures/`):

1. `mm7_m418/native/m418sa0.png` — ORIGINAL native front frame (transparent background). Design, proportions and
   palette authority.
2. `mm7_m418/native/m418sa1.png` — ORIGINAL native front three-quarter frame.
3. `mm7_m418/native/m418sa2.png` — ORIGINAL native right profile (the hunched body, head-hood, spines, tail, legs).
4. `mm7_m418/native/m418sa3.png` — ORIGINAL native rear three-quarter.
5. `mm7_m418/native/m418sa4.png` — ORIGINAL native back.
6. `mm7_m418/aligned_2x/m418sa0.png` — restored 2x front view, for SURFACE MATERIAL ONLY (scales, plates, patches).
   It never sets the design, pose or proportions.

## Deliverable

| File | View |
|---|---|
| `00_three_quarter.png` | front-right three-quarter (camera 40–45° toward the creature's own RIGHT side), camera at chest height, slightly above; 1024 x 1536 portrait OR 1536 x 1024 landscape if the long tail does not fit (prefer landscape), true transparent background, unresized return |

Keep raw returns under `raw/` (`m418_three_quarter_v1.png`, ...). Write `generation_runs.json`. If the first return
fails a check below, do ONE targeted corrective regeneration, then select the better of the two and note any
residual fault in its reason. Do not chase minor differences.

## Prompt content

TASK CONTEXT — MM7 FANTASY-GAME ASSET RESTORATION: faithful high-definition reconstruction of the EXISTING Might and
Magic VII Troglodyte monster from the supplied original sprites, as a 3D modelling reference. Not a new design.
Output: exactly ONE PNG with a genuine transparent background. ONE complete creature, from the dorsal spine tips to the
toe claws and the tail tip, centred, generous margins, near-orthographic camera, no floor, no shadow, no scenery, no
text. Even soft neutral studio light (no dramatic lighting, no rim light) that still shows form. Credible, fully
three-dimensional sculpt, semi-realistic game materials, sharp fine detail.

Identity (from the native sprites): a squat, hunched reptilian biped.
- HEAD AND BACK: a very large rounded armoured HOOD-like head that merges into a high arched upper back (no neck): the
  head is the front of one big rounded mass. Under the forward rim of the hood a WIDE dark MAW full of short ivory
  pointed teeth (upper and lower rows), a narrow vivid cyan-blue rim around the lower edge of the head. No visible eyes,
  no horns. A row of small pointed olive-brown dorsal SPINES runs from the top of the hood down the arched back to the
  tail base.
- BODY: a narrow waist, a dark olive segmented throat and belly with plate-like rings.
- ARMS: two long thin olive arms hanging forward from the shoulders, each hand with three long pale curved CLAWS.
- LEGS: strong, bent, scaly olive legs (knees bent, the creature crouches), feet with pale curved toe claws.
- TAIL: a long, thin, tapering olive tail curving out behind the body.
- COLOUR AND MATERIAL: olive-green fine scales and plates with darker shading; vivid cyan-blue irregular broad vertical
  stripes on the head-hood and broad patches on the flanks, with small muted purple-magenta mottling; ivory teeth and
  claws; dark olive belly.

Pose: a neutral pose for rigging, close to the native stance: standing on its two bent legs with the feet apart (a
clear gap between the legs), the body leaning forward in its natural hunch, the arms hanging down and slightly forward
and OUT from the body with a clear gap of air between each arm and the body and legs, the three claws slightly
spread, the tail extended straight back and slightly raised so it does not touch the legs. Head-hood facing forward.

Do NOT: make it upright like a human, add a neck, eyes, horns, wings, armour, weapons or clothes; add glow, slime
puddles or effects; change the colours or the blue pattern; give the hands more than three claws; crop the tail or
the claws; add a floor, shadow or text.

INPUT ROLES: Inputs 1–5 are the native standing views (front, front three-quarter, right profile, rear
three-quarter, back): design, proportions and palette authority; transparent pixels are background. Input 6 is the
restored front: SURFACE MATERIAL ONLY, never design, pose or proportions.
CAMERA for this primary: FRONT-RIGHT THREE-QUARTER, camera 40–45 degrees toward the creature's anatomical RIGHT from
straight front, chest height slightly above, near-orthographic. FRAMING / ALPHA: the whole creature including the
tail with generous transparent margins, genuine RGBA alpha outside the silhouette and in the air gaps. No painted
checkerboard. Return unresized.

## Checks before selecting

- front-right three-quarter camera, near-orthographic, whole creature including the tail tip inside the frame with
  margins, true transparent background (not a checkerboard drawn into the pixels);
- huge hood-head merged into the arched back, wide toothy maw, cyan-blue rim and stripes, dorsal spines;
- two thin arms with three claws each, bent legs with toe claws, long thin tail;
- arms and tail clear of the body and legs.
