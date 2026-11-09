# Connected diagonal road correction

Current regression: screenshot1297 exposes broken stone continuity at the retained border strips. V6 remains installed but its visual acceptance is superseded by [the connected-path audit](regression1297/README.md).

V6 supersedes the local v5 edits rejected in screenshot1296. The problem was the
whole repeated road band: its broad interior narrowed sharply at fixed openings.
Trimming individual stones made the inward bite deeper.

The built-in imagegen tool painted two complete diagonal bands. Three calls are
retained in `raw/`, with prompts in `prompts/`. `prepare_guides.py` constructs band
guides from the existing openings. `compose.py` registers whole painted stones
and their shading to those guides in diagonal coordinates, then blends against
the retained border. It does not clip a new mask through old cobbles. Grey-earth
counterparts share the same coverage and stones, with scalar contact shading.

Only `drsrne1`, `drsrne2`, `gdrdne1`, and `gdrdne2` change. The outer four runtime
pixels, other32 roads, and other235 terrain files remain byte-identical to v5.

[Both reported views, before/after](exact_comparison.png). The deep repeating
inward bays are removed; small polygonal stone-edge irregularities remain. The
band is narrower through former bulges to match the fixed openings. This is not
a claim of matching every native road width. On the measured connected patch,
the5th–95th percentile width spread falls from36.8 to14.1 runtime pixels.

Review covers both supplied poses and13 native walking samples, plus the connected
top-down patch and all four changed tiles. Xvfb captures establish visual behavior,
not hardware performance. `visual_review.json` binds the exact stage and evidence.

Reproduce screenshot1296's camera from the repository root:

```sh
./level_generation/terrain/mm8/play.sh enhanced out01.odm --position 6304.584 5271.343 545.000 --yaw-radians 5.410 --pitch-degrees -21.487
```

Rebuild with `prepare_guides.py`, `compose.py`, then
`../v2/check.py --version v6`. Full export, validation, explicit hash-guarded
installation and packaging use the normal MM8 workflow. Do not rerun historical
v5 acceptance to undo this revision. Retained old delivery records are under
`previous_delivery/`.

Lesson: seamless edges and solid masks are necessary but do not prove a good
connected silhouette. Inspect the exact reported diagonal and later viewpoints;
do not substitute a nearby straight-road capture or trim isolated teeth blindly.
