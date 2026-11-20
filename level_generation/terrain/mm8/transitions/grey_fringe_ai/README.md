# Grey-stone fringe restoration pilots

Four built-in imagegen restorations: `gsn`, `gse`, `gsne`, `gsnw`.
These are local-art pilots, **not accepted runtime replacements**. Production and the
181-file isolated stage are unchanged. Exact prompts are in `prompts/`, raw outputs
in `raw/`, and ordered reference hashes/cache paths in `generation_receipts.json`.

The original small fringe stones have complete rounded forms that differ from the
fractured master stone pattern. A two-material alpha plus scalar shadow cannot
reconstruct them faithfully. Native RGB deltas projected onto a different master
phase amplified cracks; native art plus bounded grain retained too much source blur.
Those earlier experiments remain under `grey_fringe_v2` and `grey_fringe_v3` as
rejected approaches, outside the runtime pack.

The AI outputs keep the original forms and contact shadows. Their earth grain is
too coarse, especially `gsn`. `../../grey_fringe_ai_pilot.py` registers broad shapes,
restores native low-frequency colour, and inserts complete stone neighbourhoods
over the accepted master-based composite. The first16 runtime pixels are preserved
for this experiment. Consequently chipped forms **remain in those old border strips**.
Do not mistake preserved join continuity for final visual acceptance.

From the repository root, rebuild each named pilot with:

```sh
python3 level_generation/terrain/mm8/grey_fringe_ai_pilot.py gsn
python3 level_generation/terrain/mm8/grey_fringe_ai_pilot.py gse
python3 level_generation/terrain/mm8/grey_fringe_ai_pilot.py gsne
python3 level_generation/terrain/mm8/grey_fringe_ai_pilot.py gsnw
python3 level_generation/terrain/mm8/check_grey_pilots.py
```

`*_comparison.png` shows native/current/raw AI/local composite/insertion coverage.
`review.json` records the visual findings. `validation.json` substitutes these four
pilots into the90-image land check and reports1042 compatible joins, zero failures.
It does not cover roads, overlays, animation, native layouts or movement.

Next restore the remaining nine grey-stone non-base names (`gss`, `gsse`, `gssw`,
`gstylx`, `gsw`, `gsxne`, `gsxnw`, `gsxse`, `gsxsw`). Build shared **finished** edge
artwork across the family rather than retaining the chipped scalar-mask borders.
Preserve master phase in pure regions, original fringe shapes and contact shade,
then repeat numerical, assembled-flat and native visual checks before incorporation.
The four generated raw files are useful source art; this compositor is not the
final family build. No generation or capture jobs remain running at this checkpoint.
