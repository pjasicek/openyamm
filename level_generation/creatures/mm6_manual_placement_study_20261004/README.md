# MM6 manual placement study — 2026-10-04

The frozen MM6 source bank contains **60 families and 3,486 reviewed frame records**. This study reads the selected
reviewed art and approved manual recipe without changing them. Its purpose is to turn the user's alignment
choices into a repeatable agent procedure, not to reaccept or reinstall the restored collection.

Use the resulting [anatomical placement workflow](../ANATOMICAL_PLACEMENT_WORKFLOW.md) and its shared JSON
proposal compiler. An agent still needs to identify corresponding anatomy visually; the old recipe records
the result, but not all the landmark choices that produced it.

## Numerical coverage

The [numerical audit](numerical_audit.json) checks every approved record against the viewer's fresh
**Match family height & bottom** operation. All selected manifest hashes and retained reviewed base-page
hashes matched the recipe/source selection. All 60 complete selected packages also passed the shared loader's
master/frame/palette/binding checks and matched their full reviewed-artifact digests. The audit pins 383 read-only
input files; the approved checkpoint, original geometry snapshot and collection were checked separately.

| Finding | Frames |
| --- | ---: |
| Approved frame records | 3,486 |
| Non-unit approved scale | 2,862 |
| Nonzero approved offset | 3,090 |
| Nonzero approved X offset | 2,173 |
| Scale differs from fresh silhouette-height fit | 332 |
| Y differs from fresh silhouette-bottom fit | 47 |
| Entire transform equals a fresh fit with zero X | 1,216 |
| Completely transparent frames, excluded from anatomical fitting | 2 |

All 3,486 records serialize `scale_anchor: bottom`. **That is a geometric representation, not proof that feet
were the semantic anchor.** A planted foot or a head can be aligned using bottom serialization plus offset.
The recipe contains no saved anatomical point sets and no nonempty per-frame notes. It therefore cannot reveal
the exact chosen foot/eye or reconstruct the editing history. The fresh baseline uses zero X; the actual UI
button preserves any X already present. Differences measure the saved final state, not a count of manual clicks.

The 3,484 visible frames have valid automatic fit ranges. The empty records are unused `mm6_mcac/mcacdq0` and
`mcacdr0`; both retain identity transforms. Empty unused native art should remain empty and outside playback.

## Visual examples inspected

Six poses per clip were inspected, for **48 poses across eight families**, on fixed-coordinate contacts with
native, fresh fit and saved manual placement in adjacent columns. Both halves of each clip were viewed.
The contacts retain two physical pixels per native pixel. They display canonical geometry before native frame
scale/mirroring and do not independently normalize frames. Brightness/palette grading is outside this geometry study.

| Family / inspected clip | Saved adjustments beyond the fresh fit, across the whole family | Lesson from the inspected art |
| --- | --- | --- |
| Goblin / attack view 0 | 47 X offsets; 5 scale differences | X changes track the native stance rather than the sword-dependent silhouette centre. Raised-sword poses b/c use the same manually chosen 1.049 size despite different silhouette-fit sizes. |
| Male peasant 2 / walk view 0 | 33 X offsets; 3 scale differences | Most of this walking clip retains the initializer. Match each native stance and head bob; do not flatten the walk onto one constant head/foot pair. |
| Sorcerer / attack view 0 | 36 X offsets; 19 scale differences | The staff flame/raised hand can extend above the head. Saved size corrections and X shifts bring the body/head closer while retaining the bottom line. |
| Harpy / walk (flying) view 0 | 22 X offsets; 22 scale differences | Head and torso provide more useful size evidence than changing wing extent. Native vertical bob remains part of the sequence. |
| Flying Demon / walk (flying) view 0 | 27 X offsets; 3 scale differences | This front flying loop largely retains the initializer; changing wing spread does not automatically require another size change. |
| Gargoyle / walk (flying) view 0 | 36 X offsets; 19 scale differences | Several saved size changes visibly adjust the body/head relation even though the wing silhouette also changes. |
| Rat / walk profile view 2 | 50 X offsets; 4 scale differences | A long tail distorts silhouette centring. Check the body core and native leg contacts as the legs alternate. |
| Spider / fidget view 0 | 56 X offsets; 18 scale differences | Body/head placement provides a useful X reference while multiple legs move. Several fidget poses use 0.99 size rather than following each leg-dependent silhouette fit. |

The complete contacts are indexed in [contacts.json](contacts.json). Representative files:

- [Goblin raised-sword attack](mm6_goblin_attack_view0_00.png) and [follow-through](mm6_goblin_attack_view0_01.png).
- [Sorcerer staff/head comparison](mm6_sor1_attack_view0_00.png).
- [Gargoyle head/body comparison](mm6_gar_walk_view0_00.png).
- [Rat profile walk](mm6_rat_walk_view2_00.png).
- [Spider fidget](mm6_spi1_fidget_view0_01.png).

These are visual interpretations, not recovered saved landmark annotations. The saved Harpy, Flying Demon and
Gargoyle transforms all retain the initializer's exact silhouette bottom, including their nonzero Y offsets.
Those offsets correct the original staging position; they do not demonstrate a separate manual head-Y shift.
The user's intended flying rule—calibrate body size, align head, permit feet/wings to differ—is consequently
documented as the requested policy for future proposals, not falsely described as proven by every old flying edit.

## Scope and reproducibility

The audit uses the pinned reviewed base tile's alpha ≥128 bounds, matching the shared viewer. Native bounds
come from the selected package's prepared native-palette PNGs, with exact centre-anchor Y correction.
Scales, offsets, timing, aliases, mirrors, palette controls and approved source pixels were not changed.

The source recipe SHA-256 is `042d1a268684e8d315f20dfbae4e3b448cc623aa5ce72dd34176e3c9498365f8`.
The audit records individual manifest/page pins and all baseline comparisons. The shared proposal compiler has
focused tests for custom-foot compensation, two-point scale calibration, independent anatomical checks,
occlusion, JavaScript rounding, immutable seed checkpoints and stale-art rejection.

All **28 focused tests** passed (12 new proposal tests plus the existing checkpoint/landmark tests).
One hundred synthetic compensated-anchor proposals also matched the current viewer's actual JavaScript geometry
function with **zero physical-pixel difference**. Those cases validate coordinate arithmetic, not visual anatomy.
All 383 input pins and the three protected state files remained unchanged after the study.

This is an all-family **numerical** audit plus the listed visual sample. It is not a fresh all-pose/palette/mask,
100% material-detail, timed-playback or in-game acceptance of 3,486 frames. Existing frozen approvals are retained.
The current deployment receipt says **published; binary/package/in-game verification pending**; the source-bank
README's older “curation/export pending” text is stale. This study performs no deployment work.
