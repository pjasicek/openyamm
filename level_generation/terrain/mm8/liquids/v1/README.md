# MM8 water, lava and tar candidates

This folder supplies all45 required liquid files:14 frames each for `hdwtr`, `hdlav`
and `hwoil`, plus `wtrtyl`, `lavtyl` and `tartyl`. These remain candidates, not a final
installed pack. Hardware animation sources are already256px; the runtime stays256px,
matching the x2 land texture array. Native128px static fallbacks become256px and use
the corresponding restored frame0, following the accepted MM6/MM7 workflow.

Three built-in imagegen atlas edits are retained in `raw/`, with exact prompts and
input/hash receipts in `generation_receipts.json`. Input atlases contain the14 native
frames followed by the static fallback twice. Each cell is a separate tile, not a
single large texture. The source artwork preserves blue diagonal water ripples,
orange/red lava streaks, and dark swirling tar ridges. `build.py` registers the AI
paint to each native frame, retains only bounded fine detail, and transports neighbour
frame detail through the native motion. Periodic residual correction removes the
smooth edge discontinuity without averaging a blurry seam strip. Native broad colour,
feature scale and animation progression remain authoritative.

All42 frame repeats pass the existing local16-pixel edge metric, including each
frame individually; no additional imagegen seam-repair atlas was required. Minimum
broad native correlation is above0.995 for every family. Water's last/first step is
1.325 times its average step versus1.380 in the original; lava and tar are near1.0.
These numbers screen fidelity and temporal consistency; they do not replace visual
review. Preview WebPs use117ms/frame; the unchanged runtime registry uses15ticks at
128ticks/second (1.640625s per14-frame cycle).

`check.py` composites all57 existing RGBA bank candidates against every phase and
checks shared edges across bank families, their3 matching land masters, and all3
liquids. All8134 checks pass (581 ordered compatible pairs times14phases). Opaque
bank pixels are exactly stationary. **Visual bank acceptance is still open:** some
dirt-bank outlines retain blocky native key contours, and some tar-bank pixels retain
purple contamination from the native colour-keyed bitmap. Do not call the overlays
finished because their RGB joins pass. Original bank examples and all5 family sheets
are retained for the next contour/key cleanup.

The staged pack now covers exactly239 effective names, with no extras/missing names:
see `coverage_pilot.json`. This proves isolated candidate coverage, not production
installation or whole-goal completion. Historical OUT still lacks these explicit
liquid, grey-family and stepping overrides.

Reproduce from the repository root:

```sh
python3 level_generation/terrain/mm8/liquids/v1/prepare_inputs.py
python3 level_generation/terrain/mm8/liquids/v1/build.py
python3 level_generation/terrain/mm8/liquids/v1/check.py
python3 level_generation/terrain/mm8/stage_candidates.py --grey-family --stepping-paths --liquids
```

Native animation captures use40 X11 screenshots at0.1s intervals, retaining timestamps
and source screenshot hashes. `review_motion.py` measures temporal steps and recurrence
near the expected cycle; sampled contact sheets must be viewed before accepting any
result. The initial `liquid_water`, `liquid_lava`, `liquid_tar` capture set is rejected:
liquid hazards killed the party, all final screenshots show the death movie, and the
lava burst itself includes death frames/projectile effects. Its retained numeric
measurements are diagnostic only (`rejected_capture_review.json`).

`prepare_flying.py` retains the scenario seed saves and creates fixed hovering saves
with the existing MM8 review helper and a real Fly buff. It avoids a second teleport
on loading, which would reset flying state. Fresh captures use distinct
`liquid_*_flying` names and preserve the failed set. Build the helper with
`python3 level_generation/terrain/mm8/build_pose_helper.py` if needed, then:

```sh
python3 level_generation/terrain/mm8/liquids/v1/prepare_flying.py
xvfb-run -a -s '-screen 0 1600x1200x24' python3 level_generation/terrain/mm8/capture_native.py liquid_water_flying liquid_lava_flying liquid_tar_flying --quality x1
xvfb-run -a -s '-screen 0 1600x1200x24' python3 level_generation/terrain/mm8/capture_native.py liquid_water_flying liquid_lava_flying liquid_tar_flying --quality x2
python3 level_generation/terrain/mm8/liquids/v1/review_motion.py --flying
```

Flying views are stationary native liquid reviews. They do not establish ordinary
camera movement, controlled flat bank fixtures, all shorelines in-game or GPU performance.

The initial flying tar pose landed on the lab's bmodel roof, so a zero-motion numeric
result there is a rejected view, not successful tar animation. The Plane of Fire lava
view remained obscured by enemy fire. `prepare_alvar_lava.py` chooses a native Alvar
pool over12000 units from the nearest authored spawn; `prepare_shadowspire_tar.py`
chooses a Shadowspire tar cell outside all expanded bmodel vertex bounds. These are
new saved poses, not map edits. The combined final candidate review uses:

```sh
python3 level_generation/terrain/mm8/liquids/v1/prepare_alvar_lava.py
python3 level_generation/terrain/mm8/liquids/v1/prepare_shadowspire_tar.py
xvfb-run -a -s '-screen 0 1600x1200x24' python3 level_generation/terrain/mm8/capture_native.py liquid_water_flying liquid_lava_alvar liquid_tar_pool --quality x1
xvfb-run -a -s '-screen 0 1600x1200x24' python3 level_generation/terrain/mm8/capture_native.py liquid_water_flying liquid_lava_alvar liquid_tar_pool --quality x2
python3 level_generation/terrain/mm8/liquids/v1/review_motion.py --flying --alvar-lava --open-tar-pool
```

The temporal screen requires actual image variation, a recurrence within0.12s of the
1.640625s native cycle, and recurrence error below40% of off-cycle error. This rejects
static roof captures and large unrelated effects. Visual review is still required.
