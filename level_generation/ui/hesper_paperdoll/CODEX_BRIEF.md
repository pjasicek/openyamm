# Codex brief: Hesper paperdoll masters

## Scope

- Image generation with your built-in image generation tool. Python (PIL) only to save and inspect your own outputs.
- Write only inside the job folder the prompt names (`level_generation/ui/hesper_paperdoll/work/<piece>/t<N>/raw/`).
  No other files, no builds, no code changes.

## The job

The job folder holds:

- `prompt.txt`: the exact image prompt. Use it verbatim.
- Its input images `in_1_*.png`, `in_2_*.png`, ..., attached in that order; `prompt.txt` says what each one is.
  An equipment job (armour, helm, boots, belt or cloak) has four: `in_1_reference.png` (the edit base: the fitted
  Might and Magic piece this layer replaces, repainted with the new design in the same outline), `in_2_mask.png`
  (grey = paint here, magenta = background), `in_3_doll.png` (the body) and `in_4_icon.png` (the item's design). A glove job has two: the Might and Magic glove
  (pose and framing) and the item's design.

Make **one** image generation with `prompt.txt` and its images, at the size the prompt names.

## Output

- Save the returned image unchanged (no crop, resize, colour or alpha edit) as `raw/gen_<n>.png`, `n` the next free
  number from 1.
- Check it against the inputs. Retry **once**, with the same prompt plus one sentence naming the fault, only if it
  clearly fails: a person, skin, arms or legs painted; the background not uniform magenta (checkerboard, white,
  scenery); the piece far outside the grey mask or leaving large parts of it empty; a different item than the design
  image; for a glove job, two gloves or a glove that is not upright. Never more than two generations per job.
- Append one record per generation to `raw/runs.json` (a JSON list): `file`, `prompt` (the full text you sent),
  `retry_reason` (empty for the first), `looks_ok` (true or false) and `notes` (one line).
