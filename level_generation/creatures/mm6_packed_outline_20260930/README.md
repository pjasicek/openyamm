# MM6 accepted packed-animation restorations — 2026-09-30

Fresh DemonFly, Cleric, DragonLand and BArcher candidates, kept together in this new folder.
All 230 original bitmap names have candidates. There are 52 complete animation/view submissions and eight
replacement returns, with all original palette variants exported. All four families have completed static
anatomy/placement, detail, edge, mask and palette review and have frozen artifact-bound acceptance records.
The user's 2026-10-01 decision accepts below-2× generated sampling when preserving one complete animation/view
on one submitted and returned sheet. DemonFly and DragonLand retain that explicitly reported resolution tradeoff.

| Creature | Sources | Complete sheets | Generation calls | Lowest actual sampling | Below 2× target | Reviewer |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| DemonFly | 54 | 9 | 11 | 1.362× | 49 frames | [Review](mm6_wdm/redo_2x/review.html) |
| Cleric | 59 | 15 | 17 | 2.063× | 0 | [Review](mm6_cle/redo_2x/review.html) |
| DragonLand | 59 | 12 | 14 | 1.510× | 13 frames | [Review](mm6_drr1/redo_2x/review.html) |
| BArcher | 58 | 16 | 18 | 2.290× | 0 | [Review](mm6_arc1/redo_2x/review.html) |

Sampling is measured from the selected generated sheet and its uniform native registration, including rounding.
Every atlas exports at two physical pixels per native logical pixel; this export size does not add generated detail.
Large DemonFly wings and DragonLand profile/death poses exceeded the pixel budget of the delivered whole sheets.
Complete cycles were preserved. They are accepted under the recorded complete-animation resolution policy;
their measured generated detail remains below the 2× target.

The method is [Packed Animation and Outline Workflow](../PACKED_ANIMATION_OUTLINE_WORKFLOW.md), invoked through
[$creature-restore](../../../.agents/skills/creature-restore/SKILL.md). Each submission contains a whole native
animation for one stored view, a separate alpha-boundary outline guide and prior detailed appearance art.
The outline controls anatomy and animation steps; skin, cloth, metal and scale texture remain richly shaded.
Initial sheets use two native pixels of padding; the eight replacements use six. Padding and union crop are
recorded for each job. Native visible reference colours remain unchanged; hidden RGB in replacement transparency
is zeroed so a decoder that ignores alpha cannot expose the old key colour.

Native filenames, pivots, fractional offsets, action/view bindings, frame durations, mirrored directions and held
frames are preserved. Identical native bitmap names reuse one exported tile. Unreferenced source files are retained
without inventing playback bindings. Registration applies one scale per sheet and restores each cell to its native
union coordinates. Cleric and BArcher use the subsequent anatomical registration in `review/anatomy_points.json`:
one uniform crown-to-boot scale per complete sheet, native crown X/boot-plane Y placement, and manual corpse
landmarks. This corrected the Cleric corpse's roughly 13-native-pixel vertical error. There is no independent pose
stretching or silhouette warping.

Each creature's `redo_2x/` contains:

- `review.html`: shared atlas/animation/palette reviewer.
- `manifest.json`, `atlas/`, `aligned_2x/`, `masks_2x/`: exported artwork and native placement/playback metadata.
- `references/`, `prompts/`, `raw/`, `run.json`, `generation.json`: original submissions, all attempts and selected provenance.
- `registration.json`, `calibration.json`, `validation.json`: mapping, measured sampling and checks.
- `review/*_registered.png`: ordered native-versus-restored contacts for each complete animation/view.
- `review/all_base_dark.png`, `all_masks_light.png`, `standing_variants.png`, `edge_current.png`: visual diagnostics.

Source/palette and generation hashes, atlas extraction, alpha/mask invariants, native anchors and native animation
bindings pass for all four packages. Cleric and BArcher were reviewed pose by pose in `review/placement_*.png`,
with actual drawn body-point candidates, independent crown-Y checks, visual limb/gesture/stance comparisons,
100% generated detail, masks, palettes and flagged colour contacts. Their hash-bound review is stored in
`review/decision.json` and `review/acceptance.json`. Lowest-boot X can switch feet or include dark cloak pixels;
its diagnostic residual is not asserted as anatomical correspondence. No timed playback was watched.
DemonFly and DragonLand were also reviewed pose by pose, including all unused DragonLand source art, representative
generated detail at 100%, and the regenerated edge/mask/palette contacts. Their artifact-bound
`review/decision.json` records the completed visual review and user-authorized resolution tradeoff;
`review/acceptance.json` binds the accepted package hashes. The colour detector flags legitimate purple DemonFly skin
and wings, so its count alone is not evidence
of matte contamination. Two isolated DragonLand cleaned-cell flags occur on pale horns; the final exported and
atlas-extracted frames have zero above-threshold candidates.

Additional DemonFly body calibrations are saved in `processing.json` → `anatomical_sheet_calibration` for front,
side and rear-oblique flight and death. Manually identified skull/eye and ankle points set one uniform scale and
common cell-coordinate correction for each complete sheet. The front correction repairs the nominal mapping's
roughly 17-native-pixel downward head error and overlarge body. Independent pelvis/abdomen and wrist points are
drawn on the actual art in `review/placement_*.png`. The ash mound receives translation only at its unchanged scale;
all corpse view aliases reuse its corrected bitmap. Its contact-plane Y is meaningful; contact X can move across
the mound and is diagnostic.

DragonLand's hit and death sheets also use one body-based scale per whole animation, with independent neck/fore-wrist
or tail-base checks. Five later death phases additionally need vertical placement corrections to their visible
tail/body/residue ground-contact planes, saved in `frame_translation_calibration`. Those corrections preserve the
shared body scale, horizontal sheet motion and limb proportions; detached embers do not determine the ground plane.
Other sheets retain their original shared mapping after the independent manual `anatomical_sheet_review`. No local
warping, per-pose resizing or equal-silhouette-bound fitting was used. The corrected body-based sampling figures
above supersede the initial nominal-grid figures of 1.182× and 1.360×.

Eight replacements corrected three wrong pose counts and five clipped-feature returns. The selected DemonFly
rear-quarter sheet has one reviewed complete wingtip touching its top border: two fading pixels, maximum alpha 99,
with a closed point and no opaque flat cut. Its exception is bound to that raw sheet's SHA-256 in `processing.json`.

Resume from `run.json` and the selected raw hashes. Reuse existing successful generations and exports, repair only
demonstrated defects, and do not resubmit whole families or replace installed/accepted packages without a request.
The shared scripts are in [mm6_remaining/redo_2x](../mm6_remaining/redo_2x): `prepare_packed_outline.py`,
`stage_result.py`, `extract_run.py`, `register_packed_outline.py`, `register_landmarks.py`, `export_run.py` and
`freeze_review.py`. For the anatomically calibrated Cleric/BArcher packages, use their saved annotations with
`register_landmarks.py`; rerunning initial grid registration would discard the reviewed correction.

The user requested 15 further MM6 families after these four. Their separate
[resumable queue](../mm6_packed_outline_20261001_batch15/queue.json) contains Barbarian, Druidess, Dwarf,
Earth/Fire Elemental, FighterChain, Genie, KnightPlate, Lich, Monk, Rat, Skeleton, Sorcerer, Spider and Thief:
869 native bitmap names in 225 complete animation/view submissions. The initial four are complete; the next batch
uses the same complete-animation resolution policy and separate staging folders.
