# MM9 PC03 portrait pilot — 2026-11-05

Can an MM9 player portrait set become an MM6–MM8-compatible family (56 frames, 118×158 RGBA, oval cut-out head,
our frame order and states)? Pilot on MM9 `PC03` (young human male, 55 native frames, 60×80 busts on navy).
Nothing is installed; `frames/` is review material only.

## Why not a straight x2 restore

MM9 portraits are busts (shoulders, chain-mail collar, navy background) with a smaller head and dark blue rim
lighting, and their frame numbers mean different things (stone is 53–55, not 12; no poisoned/cursed/insane tints,
few head-turn frames). So each of our 56 slots gets a meaning, the closest MM9 frame and a state source:
see `prepare.py` / `mapping.json`.

## Recipe

1. `prepare.py` builds, per sheet (A = slots 01–28, B = 29–56, 7×4 in the 1092×728 layout of the accepted
   2026-09-27 run): `template_<X>.png` (accepted transparent `pc07` x2 frames: framing, head angle, crop, lighting,
   state treatment), `source_<X>.png` (the chosen MM9 frame per slot, 2× nearest: identity and expression) and
   `identity.png` (MM9 frame 1 at 4×).
2. Codex built-in image generation (`codex exec`, effort medium) per `CODEX_BRIEF.md`. Sheet B is generated
   after A with `raw_A.png` as the identity master (`CODEX_BRIEF_B2.md`): independently generated B
   (`attempt1_B/`) drew fuller, curlier hair and darker skin, which would jump between frames in play.
3. `extract.py` splits at transparent gutters and registers each cell to the template frame's bottom and centre,
   with one uniform scale for all 56 frames (`HEAD_FIT` 0.96 × median height fit), so the head never pulses.
   Generated alpha is untouched. Writes `frames/`, `comparison_<X>.png` (MM9 source | pc07 | new on grey | new
   on dark), `report.json`; `lineup.png` and `all_frames.png` show the result next to existing families.

## Result

- Real RGBA from Codex in both sheets (Codex's own self-check misread transparency as a brown backdrop on its
  first sheet A run; check the alpha channel, not its preview).
- About 3 generated pixels per native pixel (gate: more than 2).
- Identity reads as MM9 PC03; style, framing and states sit with MM6–MM8 families (`lineup.png`).
- The face plus hair is wider than pc07's at equal height. Even at 96 % head size, the tilted frames clip
  hair at the canvas sides: 04 (~10 px total), 11 (~11 px), 06 (~4 px), smaller elsewhere. For a batch,
  ask for hair kept within the template's head width, or fit these frames individually.
- Weak slots: 24 (O mouth) reads nearly neutral; 38 (moderate hit) reads as a downward glance.
  Injury slots were asked for bruising without blood, as in the accepted run's reduced-injury sheets.

Selected masters: `raw_A.png`, `raw_B.png` (records with hashes in `generation_<X>.json`), plus
`repair_18_48/raw.png` for slots 18 and 48 (see Verification).

## Verification against MM6–MM8 (2026-11-05)

`measure.py` runs MediaPipe's face landmarker (not a project dependency: a scratch venv with `mediapipe` and the
`face_landmarker.task` model) over every frame of every 56-frame family in `engine/icons_x2` and the pilot:
eye closure and gaze, jaw, smile, frown, pucker, brows, head yaw/pitch/roll, visible head height and skin tint.
`verify.py` compares each slot as a change from the family's own frame 01, so identity cancels out, against the
consensus of the 42 human families (monster heads are not detected and drop out). It also lists what the engine
shows each slot for, from `portrait_frame_data.txt`, `face_animations.txt` and the idle picker.
`verification.json` holds the numbers; `verification_1..4.png` show each slot beside six families, pc07 and the
pilot, with its usage and status.

Findings and fixes:

- Slot 48 was mapped wrong ("stern"): every family smiles there (Portrait45: kills, skill increases, threats,
  shop sales). Regenerated as a smug smile in `repair_18_48/`; `prepare.py` and `mapping.json` corrected.
- Slot 18 (idle look-right, and the wake-up animation 5→19→18): the eyes followed the head instead of glancing to
  the character's own left. Regenerated in the same repair.
- Dodge slots 35/36: the extractor sat a whole small head on the bottom edge; MM6–MM8 heads duck out of the
  frame (22 % and 42 % lower). Now registered to the template's crown and clipped by the frame bottom.
- Head shake (25–29) and nod (30–33) directions differ between MM6–MM8 families (23 vs 18, 22 vs 20); the pilot
  follows pc07 exactly. Not a defect.
- Hits 37/38: most families snap the head back; pc07 and the pilot drop it. Reported as `template`.
  A batch with one template per character should choose the template per slot from the consensus.
- Slot 05 (fear): the pilot lacks the raised inner brows; minor.

Final tally: 34 pass, 18 match with extra motion or expression (`check`), 2 follow pc07 (`template`),
1 minor mismatch (05), 1 not measurable (36, nearly out of frame, as intended).

The batch for the other MM9 characters follows the [MM9 PC portrait playbook](../mm9_pc_portraits/PLAYBOOK.md),
whose `portraits.py` generalises these scripts (it reproduces this pilot's frames exactly).
