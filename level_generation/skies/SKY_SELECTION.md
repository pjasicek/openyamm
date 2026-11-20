# Native continent sky selection

Updated 2026-09-09 after the original-MM6 comparison (`test_img/1289.png`).
The authoritative data is `assets_dev/engine/data_tables/continent_settings.txt`, column 21 (zero-based).
No renderer/alias-precedence or scene YAML changes were needed.

| Continent | Ordered seven-slot sky list |
| --- | --- |
| Jadam / MM8 | `plansky3, plansky1, sky06, sky02, sky03, stormclds, stormclds` |
| Antagarich / MM7 | `7plansky3, 7sky01, sky12, 7sky02, sky12, 7sky04, sky19` |
| Enroth / MM6 | `6plansky1, 6plansky1, 6sky06, 6sky12, 6sky03, 6sky04, 6sky19` |

Each name exists in the corresponding world's native `textures/` directory. The existing loader tries the explicit
name first, so the merged mount no longer chooses another world's image for these continent-list entries.

## Mapping rationale

- MM6: `plansky3` and `plansky1` become `6plansky1`. There is no native `6plansky3`; the existing loader already
  names `6plansky1` as its MM6 fallback. `sky06/03/04` use their `6` variants; `cloudsabove` uses `6sky12`.
- MM7: `6sky12` becomes `sky12`, `6sky02` becomes `7sky02`, `cloudsabove` becomes `sky12`, `sky04` becomes
  `7sky04`, and `6sky19` becomes `sky19`. MM7's sky12 and sky19 are unprefixed native filenames.
- MM8: `6sky02` becomes `sky02`; `6sky19` becomes `stormclds`, matching the existing native alias policy.

Keep repeated names: removing duplicate entries changes the number of weather states and their weighting.
These are explicit native counterparts for the existing seven-slot merged weather system, not a reconstruction
of each original game's complete weather algorithm or a guarantee of the exact state in the user's screenshot.

`bolster_maps.txt` map assignments, fixed custom skies, precipitation settings and the cross-world Between Time
list remain unchanged. Scripted sky overrides also remain unchanged: Frozen Highlands' winter event still explicitly
requests `sky04`. That event-specific presentation question is tracked separately in the restoration plan.

## New Sorpigal and x2

New Sorpigal continues to inherit Enroth's list. Its first two clear-weather slots now select native MM6
`6plansky1` (512 × 512), rather than MM8 `plansky1` (256 × 256). Other weather states can still select other skies.
Restart/reload the map to rebuild its weather profile; development assets require no game rebuild for this table change.

The old installed `textures_x2/plansky1.png` is preserved as reviewed MM8-palette artwork. It does not restore
`6plansky1`; native MM6 needs a separate 1024 × 1024 result. Main `sky=x1` is unchanged. Do not enable main x2 until
all intended native names have reviewed outputs. Current fallback lookup can otherwise substitute another-world
name or omit missing states.

`level_generation/creatures/mm6_peasants/prepare_playtest.py` now exports the six unique native MM6 skies as
nearest-neighbour x2 placeholders for its seven weather slots. It does not relabel the earlier pale AI result as
native MM6. This change updates the installer only; existing private playtest files were not regenerated here.

## Validation and remaining review

The user confirmed the corrected selection works in-game on 2026-09-09: “OK this works.”
This confirms the selection fix; restored x2 artwork still requires its own native/restored visual comparison.

The table regression verifies seven slots per world, native-world file availability and merged virtual sky lookup.
The map-loading regression checks New Sorpigal's two native fair-weather slots and the Bracada/Ironsand custom skies.
The refreshed audit parses all 42 outdoor / 161 indoor maps and records current lists and source hashes.

Use the corrected native selection as the x1 baseline for matched-camera restoration comparisons.
User confirmation is not a recorded exhaustive projection, time-of-day or weather-distribution test. The current 19-image outdoor weather/custom union consists of 6 unique entries per world plus sunsetclouds.
The restoration queue is now A0=1, A=18, B=3, C=9, D=33, still 64 distinct native sky images total.
