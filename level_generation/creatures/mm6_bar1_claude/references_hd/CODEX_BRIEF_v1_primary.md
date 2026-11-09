# Codex brief (run 1): HD three-quarter primary for the MM6 Barbarian (bar1)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm6_bar1_claude/references_hd/`.
Do not edit any other file, do not run builds, do not call Meshy.

This run produces ONLY the primary `00_three_quarter.png`; the four orthographic views are a later run.

Use your built-in image generation, with the prompt style and record format of
`level_generation/creatures/mm6_ske_claude/references_hd/generation_runs.json`. Attached inputs, in order (paths
relative to `level_generation/creatures/`):

1. `mm6_bar1/references/standing.png` — ORIGINAL native five-view standing sheet (top row: front, front
   three-quarter, profile; bottom row: rear three-quarter, back). Magenta is background. Design and proportion
   authority. NOTE: this sheet is drawn in the BLUE palette; the colour authority is input 2.
2. `mm6_bar1/native_variants/bar1sta0_663.png` — ORIGINAL native front frame in the tier A palette (gold/bronze
   armour): COLOUR authority.
3. `mm6_bar1/native_variants/bar1sta1_663.png` — ORIGINAL native front three-quarter frame, tier A palette.
4. `mm6_bar1/native_variants/bar1sta2_663.png` — ORIGINAL native profile frame, tier A palette.
5. `mm6_bar1/aligned_2x/bar1sta0.png` — restored 2x front view, for SURFACE MATERIAL ONLY (scale mail, metal,
   leather). It never sets the design, pose, proportions or colours.

The sprites show a longsword in her right hand and a long red scabbard at her left hip. The 3D model gets the sword
as a separate prop, and the scabbard is left out: the reference must show her EMPTY-HANDED and WITHOUT the scabbard.

## Deliverable

| File | View |
|---|---|
| `00_three_quarter.png` | front-right three-quarter (camera 40–45 degrees toward HER OWN RIGHT side), camera at chest height, slightly above; 1024 x 1536 portrait, true transparent background, unresized return |

Keep raw returns under `raw/` (`bar1_three_quarter_v1.png`, ...). Write `generation_runs.json` (id, family `bar1`,
role `primary`, prompt, inputs with sha256, output path, selected flag, reason, superseded runs). If the first return
fails a check, do ONE targeted corrective regeneration, select the better one and note any residual fault. Do not
chase minor differences.

## Prompt content

TASK CONTEXT — MM6 FANTASY-GAME ASSET RESTORATION: faithful high-definition reconstruction of the EXISTING Might and
Magic VI Barbarian (a female warrior) from the supplied original sprites, as a 3D modelling reference. Not a new
design. Output: exactly ONE 1024 x 1536 portrait PNG with a genuine transparent background. ONE complete figure, top
of the hair to the boot soles, centred, generous margins, near-orthographic camera, no floor, no shadow, no scenery,
no text. Even soft neutral studio light (no dramatic lighting, no rim light) that still shows form. Credible, fully
three-dimensional sculpt, semi-realistic game materials, sharp fine detail.

Identity (from the native sprites, tier A colours): an athletic, muscular adult woman of normal height (head about
one-seventh of body height), tanned bronze skin, strong shoulders and toned arms and legs, a determined face with
dark eyes and full lips, long thick wavy AUBURN / dark red hair parted in the middle, falling past the shoulders at
the back and framing the face.
- ARMOUR TOP: a metal bikini top of two rounded cups in polished PALE GOLD / light bronze metal, with gold trim.
- PAULDRONS: a gold collar and two flared gold shoulder guards with short upward points at their outer edge, sitting
  on top of the shoulders.
- ARMLETS: a gold band around each upper arm.
- GLOVES: long dark brown leather gauntlets from the hands up to just below the elbows, with small gold studs; the
  fingers and thumb are separate and fully formed.
- BELT: a brown leather belt with a gold buckle and gold fittings at the hips.
- LOINCLOTH: a front panel of overlapping bronze-gold metal scales (scale mail) hanging from the belt to mid-thigh,
  narrow at the bottom; the hips and thighs at the sides are bare skin.
- BOOTS: dark brown leather boots to just below the knee with gold straps and studs, and a thick pale fur cuff
  around the top of each boot at the knee.
- No other clothing: midriff, upper arms (above the gauntlets) and thighs are bare skin.

Pose: a neutral A-pose for rigging. Standing upright, weight even, legs straight and slightly apart with a clear gap
of air between the legs and between the boots, feet flat with toes forward. Arms hang down and out to the sides at
about 35 degrees from vertical, elbows very slightly bent, palms facing the thighs, with a clear gap of air between
each arm and the body and between each hand and the thigh. BOTH HANDS RELAXED AND OPEN, fingers slightly curled and
slightly apart, thumbs relaxed. Head level, looking forward.

Do NOT: draw the sword, the scabbard or any weapon or shield; add a cape, cloak, skirt, helmet, belt pouches or extra
jewellery; cover the midriff or thighs; change the colours (pale gold armour, bronze-gold scales, brown leather, pale
fur, auburn hair, tanned skin); make her cartoonish or exaggerate her figure; crop the hair or the boots; add a floor,
shadow or text.

## Checks before selecting

- front-right three-quarter (her own right side toward the camera), chest-height near-orthographic camera, whole
  figure inside the frame with margins, 1024 x 1536, true transparent background (not a drawn checkerboard);
- empty open hands with five separate fingers each, no weapon, no scabbard;
- gold bikini top, pointed gold pauldrons, gold armlets, brown gauntlets to below the elbows, belt, bronze scale
  loincloth, brown boots with pale fur knee cuffs, long auburn hair;
- A-pose with the stated gaps (arms clear of the body, legs apart).
