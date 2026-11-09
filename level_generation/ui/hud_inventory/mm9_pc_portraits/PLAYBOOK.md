# MM9 PC portraits as MM6–MM8 portrait families — playbook

Turns each MM9 player portrait set (`mm9/extracted/ART/ART/PCPORTRAITS/PCnn`, 51–56 frames of 60×80 busts on a
coloured background) into a 56-frame MM6–MM8 family: 118×158 RGBA oval cut-out heads in our slot order, with our
states, framing and lighting. Worked example and evidence: [PC03 pilot](../mm9_pc03_pilot_20261105/README.md).
Tool: `portraits.py` in this folder. Character table: `characters.json`. Default slot mapping: `mappings/human.json`.

Nothing here installs runtime assets. Installation is a separate, user-approved step (step 9).

## What MM9 gives and what it lacks

- Every human, elf, dwarf and half-orc set shares one layout: groups of three (clean, bruised, variant) up to
  about frame 18, smiles and talking around 19–27, collapse 28–29, drunk/sleepy/sick 30–35, yawns 39–40, talking
  mouth shapes 41–52, stone 53–55. The acting at a given number differs per character (frame 3 is a glance for
  PC03 but a smile for PC02/PC05), so each character's mapping is reviewed (step 3).
- PC06 and PC12 have 52 frames: no stone frames. The four liches (PC19, 20, 23, 24) have 51 frames in a different
  layout and no stone; they wait for a lich pilot that writes `mappings/lich.json` (step 10).
- MM9 has no poisoned/cursed/insane tints and few head-turn frames. Those states come from the template family.
- Our 56 slots and what the engine shows them for are listed by `portraits.py verify` (from
  `portrait_frame_data.txt`, `face_animations.txt` and the idle picker); see the pilot's `verification_*.png`.

## Method in one paragraph

Per character, two Codex image-generation sheets of 28 slots (A = 01–28, B = 29–56), 7×4, in the layout of the
accepted 2026-09-27 PC restoration. Input 1 is a **template**: the accepted x2 frames of one MM6–MM8 family of the
same sex and similar head (framing, head angle, crop, lighting, state treatment). Input 2 is the **source**: the
mapped MM9 frame per slot (identity and expression). Input 3 is MM9 frame 01 enlarged. Sheet B also gets the
accepted `raw_A.png` as identity master; independently generated sheets drift in hair and skin. Codex returns real
RGBA; the extractor registers each cell to the template frame with one head size for all 56 frames. A face-landmark
check compares every slot with the MM6–MM8 consensus; wrong slots get a targeted regeneration.

## Prerequisites

- `codex` CLI with the built-in image generation tool (no API key).
- For verification only: a scratch venv with MediaPipe and its face model (not a project dependency):
  ```sh
  python3 -m venv <scratch>/venv && <scratch>/venv/bin/pip install mediapipe pillow numpy scipy
  curl -sSL -o <scratch>/face_landmarker.task \
    https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task
  ```
  `measurements_families.json` (all MM6–MM8 families) is already measured and cached here; delete it only when
  the installed families change.

Run commands from this folder. Each character works in its own subfolder (`pc05/`, …).

## Steps

### 1. Survey and confirm the template

`python3 portraits.py survey PC05` writes `survey_native.png` (all native frames, numbered),
`survey_templates.png` (MM9 frame 01 beside every 56-frame family, the proposed template first) and
`survey_mapping.png` (step 3), and copies `mappings/<name>.json` to `pc05/mapping.json`.

Confirm or change `template` in `characters.json`. Rules: same sex; similar head shape, hair length and width
(wide hair or horns against a compact template clip at the canvas sides); same ear type for elves; bearded
dwarves for dwarves. Half-orcs are brown-skinned and horned in MM9: use dark-skinned human templates, never the
green MM7 orcs, or the skin drifts green. The proposals in `characters.json` were made from frame 01 only.

Optional per-slot overrides (`template_overrides`, slot → family): `python3 portraits.py verify <family>` lists
the slots where a template family departs from the 42-family consensus (records in `template_checks/`). Every
original family departs on 5–12 slots, because families act differently, so overrides are not required. Use one
only when that slot looks wrong for the new character (pc07's hits drop the head where most families throw it
back, for example). Choose an override family of the same sex and similar head size, or the head size jumps.

### 2. Identity description

Write `description` in `characters.json` from `survey_native.png`: age, hair (length, colour, style, parting),
face shape, nose, cheekbones, lips, eye colour, beard, horns, ears, tattoos, jewellery that sits on the head.
It goes into both briefs. `prepare` refuses to run without it.

### 3. Review the slot mapping

Open `survey_mapping.png`: each slot's meaning, the chosen MM9 frame and the template frame. Edit
`pcnn/mapping.json`, never `mappings/human.json`, unless the change holds for every character.

- `state_from: mm9` slots (blink, wink, talk shapes, smiles, frowns, stone): the MM9 frame must show that
  expression for this character. Pick the right frame number from `survey_native.png` when it does not.
- `state_from: template` slots: the template sets angle and state; the MM9 frame only adds mood. Prefer a frame
  with a fitting mood; frame 1 is always safe. Never feed MM9's drunk/sick block (30–36): its poses differ wildly
  per character (PC13's are big head drops, PC05's tongue-out faces) and mislead the generator.
- When no MM9 frame shows a `mm9` slot's expression (blink and wink often have no clean frame; a dwarf's beard
  hides most mouth shapes), switch that slot to `state_from: template`. The race pilot mappings for PC05, PC09
  and PC13 changed 17–22 slots each beyond the shared default; expect that much per character.
- Missing native frames (52-frame sets: 53–55) stop `prepare` with the slot number. Point those slots at frame 1.
- Slot 48 is a smug smile (kills, skill increases, threats) and 18 is a glance to the character's own left.
  These two were wrong in the first pilot mapping and are fixed in `mappings/human.json`.

Re-run `survey` after edits to check the sheet.

### 4. Prepare and generate

`python3 portraits.py prepare PC05` writes `template_A/B.png`, `source_A/B.png`, `identity.png`,
`brief_A.md`, `brief_B.md`, and two runner scripts, `run_A.sh` and `run_B.sh`. Each runs one Codex job and
retries with a growing pause while Codex reports "Selected model is at capacity", which three parallel jobs hit
regularly on 2026-11-05. Run them from the repository root in the background. Run sheet A, then:

- Check `raw_A.png` yourself over a solid colour (`Image.alpha_composite` on green). Codex's self-check has
  reported "brown backdrop" for genuinely transparent sheets: trust the alpha channel, not its report.
- Check identity against `identity.png`, the 7×4 grid, separate portraits, and that the states read, above all
  poisoned (8), diseased (9), stone (12) and the asymmetric features (tattoos, scars, a single earring) in the
  turned and tilted frames (4, 11, 18, 19, 25–29).
- When sheet A fails, move its files to `attempt1_A/` with a note, fix the cause (template override, description,
  mapping), re-run `prepare` and `run_A.sh`. Then run sheet B (it attaches `raw_A.png`) and check that hair
  volume, skin and features match sheet A.

Each sheet takes a few minutes. Different characters' A sheets can run in parallel; each B waits for its A.
The brief allows one corrective regeneration and keeps the rejected first result.

### 5. Extract

`python3 portraits.py extract PC05` splits at transparent gutters and writes `frames/<prefix>01..56.png`,
`comparison_A/B.png` (MM9 source | template | new on grey | new on dark) and `report.json`. It prints grid
issues (must be none), the lowest sampling (must be above 2 generated pixels per native pixel; the pilot had 3.0)
and the frames clipped at the canvas sides.

Registration: one uniform scale for all 56 frames (`head_fit`, default 0.96, times the median template-height fit),
so the head never pulses between frames; bottom contact and centre from the template frame; heads shifted inward
to stay on the canvas; ducking dodge slots 35/36 aligned to the template's crown so they sink out of the frame,
but at least `MIN_DODGE_DROP` (27 and 55 px) below frame 01's crown. Those are the lower quartile of the 59 native
56-frame families (medians 35 and 64 px); templates that only tip the head forward (pc03, pc04, pc05, pc07, pc32,
pc34, 7pc14) otherwise give a dodge that reads as a flinch. Slot 36 is then too far out of frame for the landmark
check (`no-face`), as in the native families. Generated alpha is never edited.

### 6. Width clipping

Tilted frames (4, 6, 11, 25, 26) of wide-haired characters clip a few pixels at the sides; the pilot clipped
10–11 px total on 4 and 11 and accepted it. If frontal frames clip, lower `head_fit` for that character in
`characters.json` (e.g. 0.92) and re-extract. If that makes the head visibly smaller than the party's other
faces, regenerate the sheet with the hair held closer to the head instead.

### 7. Verify

```sh
<scratch>/venv/bin/python portraits.py measure --model <scratch>/face_landmarker.task PC05
python3 portraits.py verify PC05
```

Every slot is measured as a change from the family's own frame 01 (eyes, gaze, mouth, smile, brows, head
yaw/pitch/roll, visible height, tint) and compared with what at least 70 % of 42 MM6–MM8 human families do in
that slot. Statuses: `pass`; `check` (defining features present, plus extra movement or expression);
`template` (misses a feature the template family also lacks: it follows a real family); `mismatch`;
`no-face` (slot 36, nearly out of frame, is expected). `verification_1..4.png` show each slot beside six
families, the template and the new frame, with what the engine uses it for.

Gate: look at every `mismatch` and the `check`s on the sheets and decide whether the slot is really wrong. The
measure is noisy (closed lids, beards, stone); for scale, original families score 5–12 mismatches each and the
PC03 pilot ended with 1. Shake (25–29) and nod (30–33) directions differ between original families; follow the
template.

### 8. Repair wrong slots

Regenerate only the wrong slots:

```sh
python3 portraits.py repair PC05 6 44 47 --families pc02,7pc05,pc05 --frontal 44
```

It makes `pc05/repair_06_44_47/` with the template frames of those slots, one consensus strip per slot from the
given families (pick three or four that show the wanted look on the verification sheets), a brief that attaches
`raw_A.png` and `raw_B.png` as identity master, `slots.json` (`frontal` is a frontal-head slot whose height sets
the repair's scale to match frame 01) and `run.sh`. Run `run.sh` from the repository root; `extract` picks repairs
up automatically. Re-run `measure` and `verify`. The pilot's hand-written `repair_18_48/` is the same thing.

### 9. Review and install

`python3 portraits.py sheet PC05` writes `9pc05_spritesheet.png` (7×8 cells of 118×158, transparent),
a preview on grey and `lineup.png` beside existing party faces. Show these to the user.

Installed 2026-11-06 for all 20 (rows 9001–9024, bodies grafted onto existing dolls): see
[MM9 PC paperdolls](../mm9_pc_dolls/README.md), whose `install.py` copies frames, bodies and NPC pictures and writes
the rows. For a new character, add it to `../mm9_pc_dolls/dolls.json` and follow that README.

Installation needs the user's approval and is separate work:
- frames go to `assets_dev/engine/icons_x2/<prefix>NN.png` (portraits are engine content; lowercase,
  0644), through the hud_inventory accepted-icon index and `deploy_icons.py` like the 2026-09-27 PC families;
- a `character_data.txt` row with `Face pics prefix` `9pcNN-`, race and sex, and a doll body (the MM9 rework
  roadmap plans grafting MM9 heads onto existing dolls) and voice (MM9's voice tables in
  `mm9/extracted/DATA/DATA/PCVOICES` follow our speech events closely);
- an in-game HUD check with `tools/run_game.sh --isolated`.

Record each character's status in `characters.json`.

### 10. Liches

`mappings/lich.json` (from PC19 and PC24, 2026-11-05) covers the 51-frame lich layout: 1–3 neutral, 4–6 dimmed
eyes, 7–12 head turns, 13–15 head up, 16–19 bowed, 20–24 jaw opening, 28–29 collapse, 45–51 talking jaw. Liches
act through eye glow, jaw and head angle, so every state comes from the template lich; only neutral and the talking
jaw slots take MM9 expressions. Templates: pc27 (PC19, PC20), pc29 (PC23), pc28 (PC24). pc28's
magenta eyes leaked into PC20's first sheet, so name the eye colour and "never pink or magenta" in the
description. Large horns need `head_fit` about 0.87 (PC19). The face model does not detect skulls, so step 7
is by eye on the sheets only.

### 11. Hirelings (NPCnn)

MM9's 15 hireling sets (`mm9/extracted/ART/ART/NPCPORTRAITS/NPCnn`, `NPC-nn-ff.pcx`) go through the same steps under
the ids `NPC01`–`NPC15` (workspace `npcNN/`, prefix `9npcNN-`). Every set has the same 18 frames (01 04 07 10 13 16
20 21 25 26 28 30 31 32 45 47 49 51; NPC05 also 29), so the shared mapping is `mappings/hireling.json`: neutral 01,
eyes closed 04, head turns 07/10, look up 13, look down 16, smiles 20/21, stern 25, sad 26, drowsy drop 28, drunk 30,
pained or thrown back 31, slumped 32, mouth shapes 45/47/49/51. More slots take their state from the template than
for the PCs. Check sex and race from the hireling's map object class (`characters.json` `mm9_object_class`, from
the "Where met" column of `devdocs/mm9/MM9_HIRELINGS.md` 1.1 and `assets_editor_dev/worlds/mm9/maps/<map>.raw_objects.yml`),
not from the face: Randver is a dwarf, Alvar a human, Cleirach a male elf, Edina an elf with hidden ears.

They are MM9 world portraits for the hireling rail, not player portraits: installation (with the user's approval)
goes to `assets_dev/worlds/mm9/icons_x2/9npcNN-NN.png` with no `character_data.txt` row, so they never appear in
party creation. The hireling HUD carries `portraitTextureName = "9npcNN-01"`. All 15 were installed on 2026-11-06
(840 files, user approval via the MM9 rework session), also copied into the review roots
`output/mm9_rework/assets_dev` and `output/mm9_rework/isleofashes_blv_root`, with
`MM9_HIRELING_PORTRAITS_PROVENANCE.md` beside them.

Pilot NPC07 Edina (2026-11-06): template pc06, one A and one B attempt, repair of slots 2, 5, 40, 47 (cursed came out
as a wink, fear without raised brows, smile neutral, calm eyes squinting); 40 pass, 13 check, 2 template, 1 mismatch.
Slot 14 ("wink") shows open eyes in every MM6–MM8 family, so open eyes there are correct. Helmets and hoods (NPC01,
05, 06, 14) belong to the head, as horns do; lower `head_fit` if they clip.

Batch (2026-11-06, all 15 done, `overview_hirelings.png`): verify 27–42 pass and 0–8 mismatches per character (NPC09's 8
mostly beard noise). Template changes: NPC09 7pc01 (pc01's bulging eyes leaked), NPC12 pc34 with 43/47 from pc33 (pc33
alone fails 11 consensus slots). Mapping per character: frames 45/51 swap roles for about half the hirelings, frame 4
is not always closed eyes, and the head-turn frames 07/10 must match the template's head-shake direction (notes in
`mappings/hireling.json`). Template faults leak and need a line in the repair brief: pc34's insane fangs, green skin on
43, a circlet missing in pc31-style state frames (NPC03). A repair can recolour a hood or fur (NPC04's first repair
went grey-tan): name the colour in the description. `head_fit` 0.92–0.93 for big hair, beards and hoods (NPC06, 09,
10, 11).

## Race pilot results (2026-11-05)

PC05 (elf, pc34), PC09 (half-orc, pc03 with 8/9 from pc35) and PC13 (dwarf, 7pc13) confirmed the templates:
see `race_pilot_lineup.png` and each folder's spritesheet, `lineup.png` and verification sheets. Lessons:

- A template's weak state frames carry over. pc03's poisoned and diseased frames barely change its dark skin, so
  PC09's first sheet A had neither; overriding 8 and 9 to pc35 fixed it. Before generating, look at the template's
  8, 9, 12 and 54 in `survey_mapping.png`, and run `verify <template>` for the rest.
- Asymmetric features mirror in turned frames unless the description names the side in the character's own terms
  and says it never mirrors (PC09's tattoo). Expect 1–3 px of drift even then.
- Mappings change a lot per character: 30–35 of 56 slots differ from the PC03 pilot mapping for these three
  (13 of them are the shared template-slot inputs now in `mappings/human.json`; step 3).
- Beards confuse the face model: frame 01 reads as puckered, so most frames report "lips relax", and smiles hide
  in the beard. Judge bearded characters on the sheets. The MM7 dwarves' smiles are toothy grimaces, and PC13
  inherits that.
- Wide elf ears and horns clip 1–3 px on a few frames, and up to 12 px on the brief dodge frames 35/36; accepted.
- Codex renders darker skin a little lighter than the MM9 native under the template's warm lighting (PC09).
- Verification after fixes: PC05 2 mismatches (both follow pc34), PC09 1, PC13 4 (beard). Original families
  score 5–12.

## Batch results (2026-11-05)

All 20 MM9 characters are done (four parallel agents plus the liches in the main session); each `characters.json`
status records template, attempts, repairs, verify counts and what the user should judge. Lessons beyond the race
pilot:

- Proposed templates were often wrong: 6 of the 12 batch characters changed (PC01 pc05, PC07 pc34, PC11
  pc03 with pc35 for 8/9, PC12 7pc08, PC14 7pc16, PC16 7pc15), plus PC20 pc27. Per-slot overrides helped
  where a template's own state frame is weak (PC07 43/47 from pc33, PC08 8/9/11/43 from pc31).
- Sheet B can come out at a different head size than A (PC16 +12 %, PC23 −6 %). `extract` now reports
  `sheet_head_ratio_b_to_a` and warns beyond 5 %; regenerate B then. `brief_B.md` asks for A's head size.
- Codex sometimes copies sheet A's state layout into sheet B (stone in B's 12th window, slot 40: PC23; also
  PC07, PC10). Look for grey or tinted faces outside slots 8, 9, 12 and 54 on every sheet B.
- Codex's image tool takes at most five reference images; `repair` combines all consensus rows into one
  `consensus.png` (four inputs in total) and carries the character description, so eye and hair colour hold.
- Repairs used to shrink long elf ears and horns; the brief now says to keep their size.
- The run scripts retry capacity, rate-limit (429) and connection errors, at most six times. A job that fails for
  another reason but whose log also shows "Reconnecting" is retried pointlessly; stop it and fix the cause.
- Codex renders darker and greyer native skin lighter and warmer under the template lighting (PC09, PC10); hair
  often comes out curlier and more orange than the native (PC01, PC06, PC08).
- Beards and heavy brows skew the face measure (PC11 30 checks, PC13, PC15); judge those on the sheets.

Next: user review of the 20 spritesheets (`overview.png`), then installation (step 9) as separate work.
