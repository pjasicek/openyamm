# Codex brief (run 1): HD three-quarter primary for the MM7 Ghoul (m470)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm7_m470_claude/references_hd/`.
Do not edit any other file, do not run builds, do not call Meshy.

This run produces ONLY the primary `00_three_quarter.png`. The four orthographic views are a later, separate run.

Use your built-in image generation. Record format: `level_generation/creatures/mm6_ske_claude/references_hd/
generation_runs.json` (id, family `m470`, role `primary`, prompt, inputs with sha256, output path, selected flag,
reason, superseded runs). Attached inputs, in order (paths relative to `level_generation/creatures/`):

1. `mm7_m470/native/m470sa0.png` — ORIGINAL native front frame (transparent background). Design, proportions and
   palette authority.
2. `mm7_m470/native/m470sa1.png` — ORIGINAL native front three-quarter frame.
3. `mm7_m470/native/m470sa2.png` — ORIGINAL native right profile (mane, ears, overalls, eyelets down the leg).
4. `mm7_m470/native/m470sa3.png` — ORIGINAL native rear three-quarter.
5. `mm7_m470/native/m470sa4.png` — ORIGINAL native back (mane down the back, lacing at the centre back).
6. `mm7_m470/aligned_2x/m470sa0.png` — restored 2x front view, for SURFACE MATERIAL ONLY (skin, leather, eyelets).
   It never sets the design, pose or proportions.

## Deliverable

| File | View |
|---|---|
| `00_three_quarter.png` | front-right three-quarter (camera 40–45° toward the figure's own RIGHT side), camera at chest height, slightly above; 1024 x 1536 portrait, true transparent background, unresized return |

Keep raw returns under `raw/` (`m470_three_quarter_v1.png`, ...). Write `generation_runs.json`. If the first return
fails a check below, do ONE targeted corrective regeneration, then select the better of the two and note any
residual fault in its reason. Do not chase minor differences.

## Prompt content

TASK CONTEXT — MM7 FANTASY-GAME ASSET RESTORATION: faithful high-definition reconstruction of the EXISTING Might and
Magic VII Ghoul monster from the supplied original sprites, as a 3D modelling reference. Not a new design. Output:
exactly ONE 1024 x 1536 portrait PNG with a genuine transparent background. ONE complete figure, from the top of the
hair and ear tips to the soles, centred, generous margins, near-orthographic camera, no floor, no shadow, no scenery,
no text. Even soft neutral studio light (no dramatic lighting, no rim light) that still shows form. Credible, fully
three-dimensional sculpt, semi-realistic game materials, sharp fine detail.

Identity (from the native sprites): a tall, narrow, lean undead humanoid.
- HEAD: pale ivory-grey skin, an angular gaunt face with a pointed chin, hollow cheeks, a stern brow, small bright
  yellow-green glowing eyes, wide pointed ears sticking out to the sides, a thin grim mouth. Coarse ash-blond hair
  swept upward at the front and falling as a narrow long mane down the back of the neck to the upper back.
- BODY: bare pale shoulders, upper arms and upper back between the straps; lean but defined.
- CLOTHES: dark mottled brown LEATHER bib overalls: a chest bib with crisscross pale lacing through silver eyelets,
  two narrow shoulder straps, a laced panel at the centre back, close-fitting long trousers with a vertical row of round
  silver eyelets along the outside of each leg down to the ankle. Matching brown leather forearm BRACERS from the elbow
  to the wrist with eyelets and lacing.
- HANDS AND FEET: bare pale elongated bony hands with five long fingers ending in long thin curved BLACK claws; bare
  pale elongated feet with black toenails.
- COLOUR AND MATERIAL: pale ivory-grey skin with soft grey shading, dark mottled brown leather with warm highlights,
  bright silver eyelets, pale lacing, ash-blond hair, black claws.

Pose: a neutral A-pose for rigging. Standing upright, weight even, legs straight and apart with a clear gap of air
between the legs and between the feet, feet flat with toes forward. Arms hang down and out to the sides at about 35
degrees from vertical, elbows very slightly bent, with a clear gap of air between each arm and the body and between
each hand and the thigh. Both hands open and relaxed, the long clawed fingers slightly apart and slightly curled,
palms facing the thighs. Head level, looking forward.

Do NOT: add weapons, armour, a shirt, shoes, a cape, jewellery or any accessory not listed; add blood, wounds, glow
halos, smoke or magic effects; change the colours; make it bulky, muscular or cartoonish; crop the ears, hair or
feet; add a floor, shadow or text.

INPUT ROLES: Inputs 1–5 are the native standing views (front, front three-quarter, right profile, rear
three-quarter, back): design, proportions and palette authority; transparent pixels are background. Input 6 is the
restored front: SURFACE MATERIAL ONLY, never design, pose or proportions.
CAMERA for this primary: FRONT-RIGHT THREE-QUARTER, camera 40–45 degrees toward the figure's anatomical RIGHT from
straight front, chest height slightly above, near-orthographic. Show FRONT and RIGHT flank: the face points
diagonally toward SCREEN-LEFT. FRAMING / ALPHA: the whole figure occupies about 80 % of the height with generous
transparent margins, genuine RGBA alpha outside the silhouette and in the air gaps. No painted checkerboard. Return
exactly 1024 x 1536 unresized.

## Checks before selecting

- front-right three-quarter camera at chest height, near-orthographic, whole figure inside the frame with margins,
  1024 x 1536, true transparent background (not a checkerboard drawn into the pixels);
- gaunt pale face with pointed ears, yellow-green eyes, blond swept hair and mane;
- brown leather bib overalls with lacing and eyelet rows, bracers, bare shoulders;
- five-fingered clawed hands, bare feet; A-pose with the stated gaps.
