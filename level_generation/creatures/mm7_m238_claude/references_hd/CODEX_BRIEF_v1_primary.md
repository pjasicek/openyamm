# Codex brief (run 1): HD three-quarter primary and the lamp prop sheet for the MM7 Genie (m238)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm7_m238_claude/references_hd/`.
Do not edit any other file, do not run builds, do not call Meshy.

This run produces the primary `00_three_quarter.png` and one prop sheet `lamp.png`. The four orthographic views are a
later, separate run.

Use your built-in image generation. Record format: `level_generation/creatures/mm7_m398_claude/references_hd/
generation_runs.json` (id, family `m238`, role `primary` / `prop`, prompt, inputs with sha256, output path, selected
flag, reason, superseded runs). Keep raw returns under `raw/` (`m238_three_quarter_v1.png`, `m238_lamp_v1.png`, ...).

## Attached inputs, in order (paths relative to `level_generation/creatures/`)

1. `mm7_m238/native/m238wa0.png` — ORIGINAL native front frame (transparent background). Design, proportions and
   palette authority.
2. `mm7_m238/native/m238wa1.png` — ORIGINAL native front three-quarter frame.
3. `mm7_m238/native/m238wa2.png` — ORIGINAL native side profile.
4. `mm7_m238/native/m238wa4.png` — ORIGINAL native back.
5. `mm7_m238/native/m238xa0.png` — ORIGINAL native corpse frame: the oil lamp she leaves behind.
6. `mm7_m238/aligned_2x/m238wa1.png` — restored 2x three-quarter view, for SURFACE MATERIAL ONLY (skin, gold, cloth,
   mist finish). It never sets the design, pose or proportions.

The sprites show her with the arms folded across the chest. The 3D model needs a rigging pose, so the reference must
show the arms OPEN in an A-pose (described below), not folded.

## Deliverable 1: `00_three_quarter.png` (primary)

Portrait 1024 x 1536, true transparent background, unresized return. Front-right three-quarter (camera 40–45° toward
the figure's own RIGHT side), camera at chest height, slightly above, near-orthographic.

### Prompt content

TASK CONTEXT — MM7 FANTASY-GAME ASSET RESTORATION: faithful high-definition reconstruction of the EXISTING Might and
Magic VII Genie monster from the supplied original sprites, as a 3D modelling reference. Not a new design.
Output: exactly ONE 1024 x 1536 portrait PNG with a genuine transparent background. ONE complete figure from the top
of the ponytail to the tip of the vortex tail, centred, generous margins, near-orthographic camera, no floor, no
shadow, no scenery, no text. Even soft neutral studio light (no dramatic lighting, no rim light, no glow) that still
shows form. Credible, fully three-dimensional sculpt, semi-realistic game materials, sharp fine detail.

Identity (from the native sprites): a slender, athletic female genie with cobalt-blue skin and NO LEGS.
- HEAD: a stern beautiful face, blue skin, almond eyes, pointed elf-like ears; dark navy-blue hair pulled back into a
  tall high ponytail that rises from the crown and curves back and down, wrapped by four or five polished gold rings
  along its length and ending in a gold cone tip; a thin gold circlet / diadem across the forehead with a small red
  jewel in the middle; long green drop earrings.
- NECK AND TORSO: a green high collar / choker with gold edges; a green halter top (bikini-like) with gold trim over the
  bust; bare blue midriff, slim waist, a visible navel.
- ARMS: bare blue arms; green wrist cuffs with gold trim on both wrists; five-fingered blue hands.
- LOWER BODY: at the hips the body turns into a SWIRLING VORTEX TAIL of pale blue and white water-mist: twisting
  spiral ribbons of translucent-looking light blue mist that narrow downward into a pointed tip below where the knees
  would be, about as long as the torso and head together; the vortex wraps the hips like a skirt and tapers to the
  tip. Paint it as a solid sculpted spiral of mist ribbons (not particles), light blue to white.
- COLOUR AND MATERIAL: cobalt-blue skin, navy hair, polished gold, emerald-green cloth, pale blue-white mist.

Pose: a neutral A-pose for rigging. Upright, floating, the vortex tail hanging straight down under the hips. Arms hang
down and out to the sides at about 35 degrees from vertical, elbows very slightly bent, a clear gap of air between each
arm and the torso and between each hand and the vortex; both hands open and relaxed, five fingers slightly apart,
palms facing the body. Head level, looking forward. The ponytail clear of the shoulders.

Do NOT: fold the arms; add legs, feet, a skirt of cloth, trousers, a lamp in her hands, sparkles, magic effects, glow,
smoke clouds or a halo; add extra hair, horns or jewellery; change the colours (skin stays cobalt blue, cloth green,
trim gold, the tail pale blue-white); crop the ponytail or the tail tip; add a floor, shadow or text.

INPUT ROLES: Inputs 1–4 are the native standing views (front, front three-quarter, side, back): design, proportions and
palette authority; magenta/black/transparent pixels are background, not part of her. Input 5 is the corpse lamp
(for the prop sheet only). Input 6 is the restored three-quarter: SURFACE MATERIAL ONLY.
CAMERA: FRONT-RIGHT THREE-QUARTER, camera 40–45 degrees toward the figure's anatomical RIGHT from straight front, chest
height slightly above. Her face points diagonally toward SCREEN-LEFT. FRAMING / ALPHA: the whole figure inside the
frame with generous transparent margins, genuine RGBA alpha outside the silhouette and in the air gaps between the arms
and the body. No painted checkerboard. Return exactly 1024 x 1536 unresized.

### Checks before selecting

- front-right three-quarter camera at chest height, near-orthographic, whole figure inside the frame with margins,
  1024 x 1536, true transparent background;
- arms OPEN in an A-pose with the stated gaps, five fingers per hand, empty hands;
- blue skin, navy ponytail with gold rings and gold tip, gold circlet with a red jewel, pointed ears, green earrings;
- green collar, halter top and wrist cuffs with gold trim;
- no legs: a pale blue-white spiral vortex tail from the hips to a pointed tip.

If the first return fails a check, do ONE targeted corrective regeneration, then select the better of the two and
note any residual fault in its reason. Do not chase minor differences.

## Deliverable 2: `lamp.png` (prop sheet)

Landscape 1536 x 1024, transparent background, flat diffuse studio light, no ground, shadow or text, no person or hand.
TWO large views of the SAME prop side by side, uncropped, with physical thickness: LEFT a pure side view (spout to the
right, handle to the left), RIGHT a three-quarter view from slightly above. The genie's oil lamp from input 5: a
classic brass "Aladdin" oil lamp, polished gold, a long tapering spout, a looped handle, a low round body on a short
foot, a domed lid with a small knob, decorated with a few royal-blue enamel bands as in the native frame. About 30 cm
long. No flame, no smoke, no added ornament.
Checks: prop alone, complete, both views of the same object, transparent background.
