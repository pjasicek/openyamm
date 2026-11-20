# Road v5: finished artwork across joins

Fixes the repeating projecting stone fragments reported in `test_img/1288.png`.
The v4 compositor faded generated border detail back to the base masked cobbles near
shared tile edges. Those two outlines differed: the fade exposed pieces of base stones.
Solid masks and passing RGB gradient checks did not catch the visible fragments.

`collars.py`, called by `../roads_v4/compose.py`, now continues a strip of finished
border artwork through each open edge. Opposite edges receive adjacent halves of the
same two-dimensional straight-road donor strip. The contact zone blends back into the
tile over 64 authoring pixels; destination master dirt phase is retained. This does not
flatten RGB into a constant edge band. Broad stone irregularity and contact shade remain.
The 19 saved imagegen edits are reused; no masters or other terrain are regenerated.

`before/` retains the installed v4 roads and manifest. `straight_join_comparison.png`
shows the old and new repeated east–west join. `check.py` measures an outward spike in
the finished RGB stone border at that join: v4 is 5.80 runtime pixels, v5 is 1.34, below
its 3px gate. This is a regression for this observed defect, not a universal art test.
Review the full road sheet, repeated strips and BOTH east–west and north–south native
close-ups. A north–south capture alone previously missed this east–west failure.

Rebuild from the MM7 project directory:

```sh
python3 roads_v4/compose.py
python3 build_land.py
python3 roads_v4/review.py
python3 roads_v5/check.py
python3 check_roads.py
python3 check.py
```

Then stage the current PNGs, refresh native captures, run `package.py` and `install.py`,
and refresh `RESTORATION_STATE.json`. See the project handoff for capture provenance.
The package gate binds this regression report to the exported road hashes. All 19 road
PNGs change; the other 97 runtime PNGs, accepted masters and MM6 checkpoint stay unchanged.
