# MM6 packed-animation restoration — batch and follow-up

The original 15-family request was completed with 850 native bitmap names and 219 complete animation/view jobs.
The user's subsequent Fire Elemental acceptance, MM6-context retries and reuse of earlier Druidess/Earth Elemental
art bring the follow-up to the [initial four](../mm6_packed_outline_20260930/README.md) to **19 additional accepted
families, 1,075 native bitmap names and 275 complete animation/view jobs**, with all three original palette variants per family. Original held
frames, mirror bindings, durations, unused art and native placement remain authoritative. These are visually reviewed
staged assets; they have not been installed into gameplay.

Use the [packed animation and outline workflow](../PACKED_ANIMATION_OUTLINE_WORKFLOW.md), invocable as
[$creature-restore](../../../.agents/skills/creature-restore/SKILL.md). One complete original animation at one stored
rotation goes into imagegen as one native sheet plus its matching outline-only sheet and detailed appearance art;
one complete sheet comes back. Fine texture and natural shading stay independent of the outline guide.

Every new prompt now begins with explicit **MM6 existing fantasy-game asset upscale/restoration context**, before
the original animation instructions. The default is saved in the skill, workflow template and shared prompt builder.
The six requested context retries kept their previous prompt bodies unchanged and retained all reference hashes.
Genie's attack and fidget sheets and Druidess's death sheet returned successfully; the other three retries were
blocked by imagegen output moderation. Exact submissions and errors remain in each run ledger.

The user's 2026-10-01 decision makes this complete-sheet scope the priority. Optimize the grid toward 2× or more
generated detail, but accept lower sampling after visual and technical review when the full animation exceeds the
returned pixel budget. Report actual sampling separately from the 2× physical export. Do not split cycles or repeat
calls solely to reach the resolution target. Wrong poses, extra steps, clipped features and incorrect materials
still require correction.

The links below open each accepted family's reviewer. Sampling is the minimum actual generated pixels per native
pixel after uniform registration, before export enlargement. All physical exports are 2× native.

| Family / reviewer | Native names | Whole-animation jobs | Minimum sampling | Names below 2× |
| --- | ---: | ---: | ---: | ---: |
| [Barbarian](mm6_bar1/redo_2x/review.html) | 57 | 15 | 2.111× | 0 |
| [Dwarf](mm6_dwa1/redo_2x/review.html) | 59 | 16 | 2.422× | 0 |
| [Chain Fighter](mm6_figc/redo_2x/review.html) | 59 | 15 | 2.456× | 0 |
| [Plate Knight](mm6_kni/redo_2x/review.html) | 59 | 15 | 2.112× | 0 |
| [Lich](mm6_lch/redo_2x/review.html) | 59 | 15 | 2.134× | 0 |
| [Monk](mm6_mnk1/redo_2x/review.html) | 57 | 16 | 2.672× | 0 |
| [Rat](mm6_rat/redo_2x/review.html) | 59 | 16 | 2.543× | 0 |
| [Skeleton](mm6_ske/redo_2x/review.html) | 59 | 16 | 2.128× | 0 |
| [Sorcerer](mm6_sor1/redo_2x/review.html) | 59 | 15 | 2.210× | 0 |
| [Spider](mm6_spi1/redo_2x/review.html) | 58 | 15 | 2.983× | 0 |
| [Thief](mm6_thf/redo_2x/review.html) | 59 | 15 | 2.344× | 0 |
| [Cobra](mm6_cob/redo_2x/review.html) | 59 | 15 | 1.544× | 21 |
| [Beholder](mm6_bh/redo_2x/review.html) | 48 | 9 | 1.293× | 42 |
| [Gargoyle](mm6_gar/redo_2x/review.html) | 48 | 9 | 1.141× | 47 |
| [Minotaur](mm6_min1/redo_2x/review.html) | 51 | 17 | 1.925× | 5 |
| [Fire Elemental](mm6_fie1/redo_2x/review.html) | 47 | 9 | 1.970× | 6 |
| [Genie](mm6_djn/redo_2x/review.html) | 60 | 15 | 2.273× | 0 |
| [Druidess](mm6_dru1/redo_2x/review.html) | 59 | 16 | 2.303× | 0 |
| [Earth Elemental](mm6_ert/redo_2x/review.html) | 59 | 16 | 2.079× | 0 |

These 275 prepared jobs preserve complete native animation/view scope. The exported packages use **262 selected
source generation sheets**, including five earlier sheets used for the 12 retained poses described below. Identical
native bitmap aliases reuse the reviewed canonical pose rather than installing inconsistent redraws. Native holds,
repeated frames and alias bindings remain unchanged. Historical retained sheets keep their original generation
layout; they are not relabelled as new complete-sheet imagegen returns.

Every selected native bitmap was inspected in paired original/restored placement contacts. Review also covered
representative generated detail at 100%, alpha edges against light and dark backgrounds, every material mask and
every pose in every native palette variant. Acceptance used static contacts; watched playback is not claimed.
Each family's `redo_2x/review/acceptance.json` binds its frozen package hashes and visual evidence. Existing technical
checks passed for source and generation provenance, unclipped cells, crop/atlas reconstruction, unchanged variant
alpha, base-palette bypass, native anchors and per-palette timing/mirror bindings.

Corrections retained complete-sheet scope. Beholder's side-view jaw required repacking both native colour and
outline references with ten native pixels of padding after a padding-only prompt still clipped the tip. Gargoyle's
rear wing tip required a whole-sheet replacement. Scale stays uniform within each animation; placement corrections
translate the entire pose and preserve independent limb, eye, jaw and equipment proportions.

Four initially selected families were unfinished when Cobra, Beholder, Gargoyle and Minotaur filled their slots to
complete the original 15-family request. The user then explicitly accepted Fire Elemental's latest complete death
sheet, including its known late-stage flame/haze approximation; that approval is bound to the selected raw sheet in
its [acceptance record](mm6_fie1/redo_2x/review/acceptance.json). Genie's two missing sheets subsequently succeeded
with the MM6 header, and all 60 poses, material masks and three palette variants were reviewed and frozen.

The user's next request authorized reusing previously generated x2 art to fill Druidess's and Earth Elemental's
remaining coverage. The new packed artwork remains selected for their other 106 native poses. Both combined
families now have all 59 native sprites, were freshly reviewed in native sequence order, and are frozen staged
packages. The earlier source families' pending placement acceptance was not inherited.

| Combined family / run ledger | Coverage | Earlier art retained | Retained sampling |
| --- | ---: | --- | ---: |
| [Druidess](mm6_dru1/redo_2x/run.json) | 59 / 59 | One unused fidget bitmap (`dru1fib0`) from `mm6_dru1/redo_2x`; the new death sheet remains selected. | 7.963× minimum |
| [Earth Elemental](mm6_ert/redo_2x/run.json) | 59 / 59 | Six walk-view-2 and five death poses from `mm6_ert/redo_2x`, preserving the earlier four-sheet composite selection. | 2.621–3.123× |

Retained raw/prompt/reference, cleaned/aligned/mask pixels and native registration are hash-bound to the earlier
sources. No new imagegen calls were made for reuse. The 12 poses retain their actual generated sampling and 2×
physical export. Earth Elemental's earlier death poses have a slightly darker stone finish; this and historical
split-sheet registration are recorded limitations. Druidess's unused pose has slight historical surface-detail
differences. New and retained poses, all masks, all three palettes and 100% detail/alpha were inspected together.

All 19 started families are now complete. The original three blocked sheet submissions and their exact prompts,
reference hashes and output-moderation errors remain recorded; reuse resolved their missing coverage. Preserve
selected raw sheets, rejected versions and per-job crop/padding revisions. The [queue](queue.json) records the
current selection and reuse authorization. Frozen provenance and package hashes passed for all 23 accepted
families, including the initial four. Gameplay installation remains separate.
