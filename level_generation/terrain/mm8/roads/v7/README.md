# Connected join repair after1297

[Before/after joins, repeated native path and camera checks](index.html).
[Remaining border line, before/after colour correction](border_colour_comparison.png).

V6 failed because separately generated interiors did not agree with retained
border artwork. Two built-in imagegen calls repair assembled east and south join
neighborhoods. Their raw outputs and exact prompts are in `raw/` and `prompts/`.
`compose.py` registers those outputs to neighboring stones, reconstructs both sides
of each connection and splits the joined result back into the diagonal pair.
Grey companions share the repaired stones and retain grey-earth contact shading.

The rejected trial that retained an8px authoring strip still showed an internal
line. Removing all connection anchors broke other compatible road joins. The
final reconstruction uses a4px connection anchor with a smooth12px handoff; the
old16px graft line is fully inside the repaired area. These are connected repairs
around an existing road connection, not independently painted tile interiors.

A low-camera UV diagnostic then identified a second line at the shared border.
Even the original tiles show that boundary at this pose. The old directional
endpoint colours disagreed despite passing the relative-gradient screen.
`match_ports.py` applies a road-only colour correction within8 runtime pixels of
open borders, matching common endpoint profiles. It does not change road shapes
or mask geometry. Both reported cameras and walking samples must be reviewed
after this step; the earlier `final_pose` captures predate it and are not final.

Final scope: four reconstructed diagonal images and32 border-only road corrections.
The central240×240 pixels of those32 other roads remain byte-identical to v6.
The other203 terrain files, original terrain and other enhanced content remain
unchanged. This revision retains v6's road width; it does not claim exact native
width or perfectly smooth outlines.

Rebuild in order:

```sh
python3 level_generation/terrain/mm8/roads/v7/compose.py
python3 level_generation/terrain/mm8/roads/v7/match_ports.py
python3 level_generation/terrain/mm8/roads/v2/check.py --version v7
python3 level_generation/terrain/mm8/roads/v7/build_review.py
```

Run `match_ports.py` once after a fresh compose. Final source hashes are in
`build.json`, the capture stage in `review_stage.json`, and inspected evidence
in `visual_review.json`. Installation uses the explicit hash-guarded migration
in `install_revision.py`. Historical delivery records are in `previous_delivery/`.

Reproduce the closer reported pose:

```sh
./level_generation/terrain/mm8/play.sh enhanced out01.odm --position 6304.584 5271.343 545 --yaw-radians 5.410 --pitch-degrees -21.487
```

Acceptance requires clean enlarged **interior join neighborhoods**, native entry
and exit, repeated path, and low-angle movement. Seam-gradient scores and matching
boundary hashes alone cannot establish visual continuity. Xvfb captures do not
establish hardware GPU performance.
