# Eight inventory items in one imagegen call

## Live-queue adoption

`6hat2`, `6hat3`, `6helm1`, and `6helm2` are accepted and staged after measured landmark and full
comparison review. `adoption.json` records retained attempt `bd9971c8f928499daf5ab883ce4c8694`.
No imagegen call was made during historical adoption. Three crowns and the green cap were deferred
for internal detail/tone or feather placement; their newer repair candidates are in
`../../production/headwear_01/`. The benchmark observations below describe the original trial.

Completed 2026-09-10 as a throughput experiment requested by the user. These eight distinct inventory
targets had no existing restoration attempts when selected: `6crown1`, `6crown2`, `6crown3`, `6hat1`,
`6hat2`, `6hat3`, `6helm1`, `6helm2`. Source-identical extra crown variants were excluded.

One built-in imagegen call restored the 4-column, 2-row `reference.png`, using `prompt.txt`.
Generation took 42.626 seconds. The actual output was 1774×887, despite requesting 2560×1280;
extraction uses actual output dimensions. All eight objects remained inside their assigned cells.

`process.py` uses the existing HUD matte and uniform scale/translation fitting, producing transparent
PNGs at exactly each source's doubled dimensions. Extraction, fitting, registration and proof creation
took 3.70 seconds. This is processing time, not total authoring/review time. Run again with:

```sh
python3 level_generation/ui/hud_inventory/experiments/eight_items_v1/process.py
```

See `comparison.png` for original nearest-neighbor x2 versus restored x2, plus light/dark previews.
All eight pass existing footprint checks. The raw sheet and both comparison sheets were visually
reviewed. The hats and helmets are promising; crowns are brighter and some small details are interpreted
more freely. `review.json` records per-item observations and limits. Smooth painted detail is visible;
the outputs are not simply enlarged pixel blocks.

These are experimental candidates, not installed or accepted production assets. The manifest retains
source hashes and the two original frozen job memberships. It does not rewrite those jobs or count
these as accepted queue targets. Raw imagegen output, prompt, reference, clean masters, exact x2 PNGs,
registration reports and processing provenance are retained here.

This demonstrates eight candidates per call with inexpensive batch postprocessing. It does not yet
establish a sustained speedup or retry rate. Prefer further sheets of similarly sized items and review
one combined proof, retrying only cells with visible problems.
