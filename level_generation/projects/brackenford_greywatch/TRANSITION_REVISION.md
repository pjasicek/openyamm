# Regional road continuation

Follows the driver's Ravenshore transition images1243–1248. [Reference calibration](../../REGIONAL_TRANSITION_CALIBRATION.md)
compares three Ravenshore and three Alvar exits using native roads/heights, navigation bounds and textured views.

The driver accepted these passes and clarified that bends and enclosing hills are optional for future maps.
Straight open continuations are equally valid; this project's occlusion check applies specifically to its two passes.

The old west and north roads ended 1,024 units beyond the travel trigger. Both now continue 8,192 units to the final
rendered terrain cell, with graded bent cuts in the outer hills. Neither road has a terminal cap. These are native
terrain tiles and height samples, with no added terrain BModels or event scripts.

The travel square remains ±24,576. All height samples inside it, all 87 BModels, all native decoration entities,
accepted houses/arrivals and 102 fixed actors remain identical to the landscape revision. Both destinations and travel
rules are preserved: west → Ravenshore; north → Alvar. No required content is placed beyond the trigger.

## Review

- [Reference and before/after plans](../../evidence/transition_calibration/exit_plans.png),
  [measurements](../../evidence/transition_calibration/measurements.json).
- Native [west pass](review/brackenford_native_transition_west.png),
  [north pass](review/brackenford_native_transition_north.png),
  [full map](review/brackenford_native_transition_region.png).
- Normal-game [west approach](review/gameplay/transition_west_approach.png),
  [Ravenshore prompt](review/gameplay/transition_west.png),
  [north approach](review/gameplay/transition_north_approach.png),
  [Alvar prompt](review/gameplay/transition_north.png).

The prompt captures show the road visibly turning onward with the far terrain ending screened by the hillside.
They were produced by a brief ordinary-game forward step across each actual boundary. They verify prompt presentation
and destination labels, not another complete destination/return playthrough. Original travel wiring was not changed.
Flying/high overview cameras can still expose the finite native terrain, as in the originals.

[Quick transition check](review/transition_revision/transition_check.json) passes: connected native road cells through
the outer region, correct outward NS/EW tile at the last cell, unchanged inner terrain/entities/BModels, and a sampled
walking-eye ray to each far road cell blocked by terrain. Maximum centerline grades are 0.09375 west and 0.0625 north.
[Tile/frontage](review/transition_revision/frontage_check.json) and [IDs/clearance](review/transition_revision/quick_check.json)
pass with zero corner mismatches. No engine rebuild or broad outdoor scenario matrix was needed. Editable Blender
source reopens with packed images, no linked libraries and 1,367 objects.

## Reproduce and play

Author with the connected Blender MCP using `author_brackenford_blender.py`. Plan entries in `regional_exit_scenery`
define native cell bends, floor heights, destination and trigger. Run source checks before native export:

```sh
python3 level_generation/projects/brackenford_greywatch/check_transitions.py --source
python3 level_generation/projects/brackenford_greywatch/check_frontage.py --source --review-directory transition_revision
python3 level_generation/projects/brackenford_greywatch/build_brackenford.py
python3 level_generation/projects/brackenford_greywatch/check_transitions.py
python3 level_generation/projects/brackenford_greywatch/check_frontage.py --review-directory transition_revision
python3 level_generation/projects/brackenford_greywatch/check_facade_revision.py --review-directory transition_revision
python3 level_generation/scripts/measure_transitions.py
```

Run `review_transitions_blender.py` through MCP for the native automap and three views. Normalize/reopen the Blender
source and stage/package according to [REBUILD.md](REBUILD.md). The previous source/native snapshot is preserved
under `review/transition_revision/before/`; previous playtest directories remain frozen.

```sh
/tmp/openyamm-brackenford-playtest-transitions/play.sh outdoor
```

Choose **Load Game → Scenario** for the God character. Use `indoor` for Greywatch.

Outdoor SHA256: `4a76ed6d49ca0e49ea929246f289d860572ace10ed01439af0bb5b3758b1607b`.
Indoor unchanged: `b227608891142f1982f2cd6039124eaab2310775b6760760a8570baff8679fec`.
Package SHA256: `992ff79f32b3911c89e9701d4a307c79c1c3dbd37b8e7d01880ab32f6d82d7c7`.

[Final artifact verification](review/transition_revision/artifacts.json) records the archive and both reloaded God starts.
All reference/generated views and prompt captures were opened and inspected. Blender MCP remains connected with the
unrelated default scene restored.
