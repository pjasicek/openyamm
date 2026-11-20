# Grey-stone family with shared finished edge artwork

This candidate replaces all13 non-base grey-stone names. Generated sources and exact
prompts/ordered references are retained in `../grey_fringe_ai/`; that directory now
has13 generation receipts. The former four-pilot local composites are historical.

`../../build_grey_family.py` aligns broad native forms, restores native low-frequency
tone and composites restored stone neighbourhoods over accepted masters. It then
quilts finished edge strips from the central portions of `gse`, `gsw`, `gsn`, `gss`.
Pure borders and corners use the corresponding periodic master in destination phase.
The minimum-error overlap cut avoids stretching stones. No old scalar-mask border
band is retained. Outputs remain separate from the partial runtime union.

`comparison_*.png`, `island.png`, `hole.png` were visually reviewed. Rounded fringe
forms and contact shadows are clearer, with no obvious straight tile boundary lines
in the assembled layouts. This is not a claim that every native placement is valid.
`validation.json` substitutes this family into the90-image opaque land screen:
1042 compatible joins, zero failures. The review stage has182 textures:13 shared-art
overrides and the restored `gdtyl` base, in addition to the older partial union.
`effective_inventory.json` includes Shadowspire's scene overlay, which changes its
direct terrain to grey dirt; the raw ODM-only inventory missed this use.

Reproduce from the repository root:

```sh
python3 level_generation/terrain/mm8/build_grey_family.py
python3 level_generation/terrain/mm8/check_grey_family.py
python3 level_generation/terrain/mm8/stage_candidates.py --grey-family
```

`stage_candidates.py` without `--grey-family` stages the older partial union. Use
the explicit flag until the final union builder incorporates this screened family.
Do not overwrite the original transition build/land-validation baselines: they are
inputs to the substitution check and allow the older experiments to be reproduced.

The native review uses an out06 `gsn` placement. Initial `grey_fringe` and debug-only
`grey_fringe_overhead` captures mostly showed bare ground and are insufficient
transition evidence. A stable elevated view requires the saved party flying state
and an actual Fly buff; `debug.start_flying` does not suffice after this save load.
The project-local `prepare_capture_save.cpp` and `build_pose_helper.py` create a
review-only flying save, following the established MM7 helper. `capture_native.py`
must omit `--pose` when loading that save: the subsequent teleport reinitializes
movement and defeats its fixed altitude. No engine changes.

`native_comparison.png` and `native_review.json` record the final representative
`grey_fringe_detail` x1/x2 comparison. Its matching saved pose shows sharper rounded
stones and contact shadows in a similar broad grey palette. With `gdtyl` included,
the old/new square boundary is gone. This is one elevated native neighbourhood,
not ground-level motion or every family tile in-game. Both screenshots and their
metadata,182-file stage manifest, effective inventory and build are hash-bound.

Remaining full-goal checks still include controlled native flat fixtures and motion,
the stepping-stone paths, three liquid families, all overlays/phases, final complete
coverage, production installation and final deliverables.
