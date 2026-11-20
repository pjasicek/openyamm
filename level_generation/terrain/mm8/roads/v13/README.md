# Shared cobble material and continuous diagonal coverage — v13

Screenshot1304 rejects v12: its separately generated stone faces are visibly flatter, and shaping reused NE2 tiles around a single straight junction introduced repeated dirt bites along diagonal roads. The earlier declaration of a complete fix was wrong.

V13 replaces all eight dirt/grey-dirt diagonal variants with a continuous coordinate mapping of the **actual accepted v7 `drsrew.png` pixels**, including their grain, colour, bevels and grout. No new imagegen calls or independently calibrated diagonal stone interiors. The two halves share phase at both joins. Width is increased from the initial strip trial toward the native diagonal footprint. Fresh substrate contact shadow samples the same continuous field. All 28 other cobble roads remain byte-identical, as do 231 other terrain files and all unrelated enhanced content.

[Final supplied-pose comparison](exact_pose_comparison.png), [final capture](captures/mm8_1304_width.png), [continuity checks](continuity.json), [review](visual_review.json).

Final pose: `(7766.500,3508.695,545)`, yaw `1.782` radians, pitch `-26.385` degrees. Reviewed material beside the unchanged straight road and repeated diagonal coverage upstream. Earlier alternate-heading captures are narrower trial evidence, not final-width assets.

**Known limitation:** stone layout and outlines remain discontinuous at bends into straight/other directional road tiles. The user explicitly prioritizes matching material and no repeated holes over a perfect straight-junction pattern. The raw road gradient screen has 122 failed bend combinations out of 724; these are retained honestly, not marked seamless. All continuous repeated-diagonal checks pass, and all 36 road masks have one component and no holes. Full-pack checking recomputed all 1,668 affected contacts: the same 122 bend discontinuities remain, with zero unexpected failures. The 22,760 unchanged checks are hash-proven reuse. Do not interpret this as an all-seams-pass delivery.

Rebuild: `python3 level_generation/terrain/mm8/roads/v13/build.py`, then the existing road checker with `--version v13`. `validate_update.py` retains raw failures and separately classifies known road-bend discontinuities. `install_revision.py` is an explicit hash-guarded migration from v12; final captured stage and all 239 installed/exported hashes agree. Broad gallery and ZIP were not rebuilt.

Lessons: review the repeated path, not only one appealing corner. A tile reused at both diagonal and straight joins cannot be narrowed for one straight neighbour without breaking another use. Do not paint separate material variations when the accepted pixels can be reused directly. Do not manipulate masks or broad colour strips merely to force gradient metrics to pass. Actual foreground coverage and boundary repetition need checks, not just a cleaned auxiliary mask.
