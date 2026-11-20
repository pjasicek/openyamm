# Codex brief (run 1): HD three-quarter primary for the MM7 Wight (m430)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm7_m430_claude/references_hd/`.
Do not edit any other file, do not run builds, do not call Meshy.

This run produces ONLY the primary `00_three_quarter.png`. The four orthographic views are a later, separate run.

Use your built-in image generation. Record format: `level_generation/creatures/mm6_ske_claude/references_hd/
generation_runs.json` (id, family `m430`, role `primary`, prompt, inputs with sha256, output path, selected flag,
reason, superseded runs). Attached inputs, in order (paths relative to `level_generation/creatures/`):

1. `mm7_m430/native/m430sa0.png` — ORIGINAL native front frame (transparent background). Design, proportions and
   palette authority.
2. `mm7_m430/native/m430sa1.png` — ORIGINAL native front three-quarter frame.
3. `mm7_m430/native/m430sa2.png` — ORIGINAL native right profile (head carried forward, hair, robe fall).
4. `mm7_m430/native/m430sa3.png` — ORIGINAL native rear three-quarter.
5. `mm7_m430/native/m430sa4.png` — ORIGINAL native back (hair, cord, hem).
6. `mm7_m430/aligned_2x/m430sa0.png` — restored 2x front view, for SURFACE MATERIAL ONLY (cloth, skin finish). It never
   sets the design, pose or proportions.

The sprites show a short dagger in the right hand. The 3D model gets the dagger as a separate prop later, so this
reference must show the wight EMPTY-HANDED.

## Deliverable

| File | View |
|---|---|
| `00_three_quarter.png` | front-right three-quarter (camera 40–45° toward the figure's own RIGHT side), camera at chest height, slightly above; 1024 x 1536 portrait, true transparent background, unresized return |

Keep raw returns under `raw/` (`m430_three_quarter_v1.png`, ...). Write `generation_runs.json`. If the first return
fails a check below, do ONE targeted corrective regeneration, then select the better of the two and note any
residual fault in its reason. Do not chase minor differences.

## Prompt content

TASK CONTEXT — MM7 FANTASY-GAME ASSET RESTORATION: faithful high-definition reconstruction of the EXISTING Might and
Magic VII Wight monster from the supplied original sprites, as a 3D modelling reference. Not a new design. Output:
exactly ONE 1024 x 1536 portrait PNG with a genuine transparent background. ONE complete figure, from the top of the
head to the bottom of the robe hem, centred, generous margins, near-orthographic camera, no floor, no shadow, no
scenery, no text. Even soft neutral studio light (no dramatic lighting, no rim light) that still shows form. Credible,
fully three-dimensional sculpt, semi-realistic game materials, sharp fine detail.

Identity (from the native sprites): a tall, thin undead humanoid in a long ragged robe.
- HEAD: small, gaunt, skull-like face with pale desaturated grey-green skin stretched over the bone: bald high
  forehead, deep BLACK empty eye sockets, narrow nose, sunken cheeks, a thin closed lipless mouth showing a hint of
  teeth. Long straight thin silver-grey hair hangs from the sides and back of the otherwise bald head to the
  shoulders. No hood.
- ROBE: one worn dark earth-brown full-length coarse cloth robe: broad crossed V neckline exposing the thin neck and
  upper chest, loose long flared sleeves ending in long pointed torn strips below the wrists, a narrow dark brown
  waist cord tied in front with hanging ends, and a widely spread ragged lower hem with holes and sharply torn points
  that reaches the ground and hides the feet completely.
- HANDS: long bony pale grey-green hands with very thin long fingers (thumb plus four fingers), no gloves, emerging
  from the sleeves.
- COLOUR AND MATERIAL: dark umber-brown cloth with deeply shaded folds and muted brown-grey highlights, coarse worn
  fabric; pale grey-green skin; silver-grey hair.

Pose: a neutral pose for rigging. Standing upright, the robe falling straight to the ground. Arms held down and out to
the sides at about 35 degrees from vertical, elbows very slightly bent, with a clear gap of air between each arm (with
its sleeve and torn strips) and the body. Both hands open and relaxed, the long fingers slightly apart, palms facing
the body. Head level, looking forward (keep only a slight forward carry of the head as in the native profile).

Do NOT: draw the dagger or any weapon, a hood, a crown, armour, boots or feet, a scythe, a cape over the robe, extra
limbs; add blood, glow, smoke or magic effects; change the robe colour (stays dark earth-brown); make it cartoonish
or muscular; crop the head or the hem; add a floor, shadow or text.

INPUT ROLES: Inputs 1–5 are the native standing views (front, front three-quarter, right profile, rear
three-quarter, back): design, proportions and palette authority; transparent pixels are background. Input 6 is the
restored front: SURFACE MATERIAL ONLY, never design, pose or proportions.
CAMERA for this primary: FRONT-RIGHT THREE-QUARTER, camera 40–45 degrees toward the figure's anatomical RIGHT from
straight front, chest height slightly above, near-orthographic. Show FRONT and RIGHT flank: the face points diagonally
toward SCREEN-LEFT. FRAMING / ALPHA: the whole figure occupies about 80 % of the height with generous transparent
margins, genuine RGBA alpha outside the silhouette and in the air gaps between the arms and the body. No painted
checkerboard. Return exactly 1024 x 1536 unresized.

## Checks before selecting

- front-right three-quarter camera at chest height, near-orthographic, whole figure inside the frame with margins,
  1024 x 1536, true transparent background (not a checkerboard drawn into the pixels);
- empty hands, no dagger;
- gaunt grey-green skull-like face with black sockets, long silver hair at the sides and back, no hood;
- dark brown floor-length robe with V neckline, flared torn sleeves, waist cord, ragged hem hiding the feet;
- long bony five-digit hands; arms out with clear gaps.
