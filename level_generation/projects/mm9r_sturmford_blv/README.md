# MM9 rework: Sturmford as a BLV (`sturmford.blv`), large-region check

The large-region check of converting MM9's outdoor maps as BLVs open to the sky (pilot:
[`../mm9r_isleofashes_blv/`](../mm9r_isleofashes_blv/README.md); shared part:
[`../mm9r_common/outdoor_blv.py`](../mm9r_common/outdoor_blv.py)): a full wilderness region, and monster pathing at
MM6-MM8 density (user, 2026-11-02: "we will VERY LIKELY use more monsters ... so it needs to work").

```sh
python3 level_generation/projects/mm9r_sturmford_blv/convert.py     # 4 min; into output/mm9_rework/isleofashes_blv_root
./tools/run_game.sh --isolated sturm_blv --world mm9 --map sturmford.blv \
    --assets "$PWD/output/mm9_rework/isleofashes_blv_root" --position -17388 11761 260 --yaw-radians 0 \
    --pitch-degrees -10 --visible --seconds 0 --set debug.immortal=true
```

## The map

- Terrain0 (21 725 polygons, 20 000 x 20 000 LT = 51 200 native) centred: offset (-2 519, 35, 0), native x and y
  within +-25 600.
- **1 sector, 22 041 vertices (34 % of 16-bit), 26 937 faces**, 12 doors (rotating doors, hatches, the drawbridge,
  the portcullis, its chain and the Portcullislever, whose click drives both), 17 lights. 24 M air voxels at 32 LT.
- Sky: cloudy preset, daylight; footstep sounds by floor; `party_movement: {steep_slopes: block}`; 12 boat arrivals
  rewritten to the BLV. No props yet (no Sturmford props.json), no scripts.
- `generate_bsp: false` and `half_steps: false`: the BSP split choice and the city's half-step pass are quadratic in a
  sector's faces and did not finish in half an hour on this one sector (the game uses no BSP; terrain has no plinths).
  `dungeon/floors.py cut_floors_under_overlays` was made linear-ish for the same reason (same result).

## Deviations

- **Anskram Keep's drawbridge chains** (DestructableBrush0/1, destructibles 315 and 316; the user, 2026-11-08): MM9's
  RayHit boxes round them are 21 x 10 native across, a sliver under the gatehouse chamber's ceiling that a blow hit
  only within about 1.5 degrees of aim (an arrow from beyond blow reach did hit). `convert.py` (`CHAIN_HIT_BOX`) grows
  the invisible boxes to 96 x 96 across (their length and the visible chain stay MM9's), so a melee blow from the chamber
  floor breaks a chain as MM9 allowed, and missiles still do (`tests/scenarios/mm9/destructibles/anskram_chain_melee.yml`).

## The pathing check

`outdoor: {test_population: 200}`: MM9's 51 monsters with a floor (5 water spores float over the sea and are left
out), plus copies on the floor 400-1 200 units round them, 200 in all (85 dragonflies, 64 field thralls, 23 mites,
12 basilisks, 8 thralls, 8 fire dragonflies). A measurement aid, not a design.

Party immortal in the densest spot (20 monsters within 3 000), 75 s, visible window, `logging.performance_trace`;
MM8's Ravenshore (`out02.odm`, 143 placed monsters and 59 spawn points) the same way:

| | Sturmford BLV, first run | after the grid fixes | after the profiled fixes | Ravenshore ODM |
| --- | --: | --: | --: | --: |
| Monster update (avg per call) | 340-500 ms | 157 us | 70 us | - |
| AI step (collect + apply) | - | 1.57 ms | 0.74 ms | - |
| Frame CPU p50 | 374 ms | 0.46 ms | 0.54 ms | 0.73 ms |
| Frame CPU p95 (median / max) | 500 ms | 2.4 / 8.1 ms | 1.6 / 2.1 ms | 0.9 / 1.5 ms |
| Frame CPU average | - | 0.71 ms | 0.55 ms | - |
| Active monsters | 48 of 200 | 48 of 200 | 48 of 200 | - |
| Paths active (max) | - | 84 | 78 | - |

The first run spent the time in two full scans of the one sector per query: floor sampling and the collision sweep's
candidates (devdocs/mm9_rework/BLV_GEOMETRY_COSTS.md, "The grid for floor queries and collision sweeps"). With the
sector face grid used there too, the indoor AI keeps its cap of 48 active monsters within 10 240 units and the cost no
longer grows with the sector. The 40-second screenshot shows thralls and a basilisk round the party, attacking.

The p95 is the frames that carry one of the AI's fixed 1/128 s steps (one frame in eleven at 1 400 fps). A `perf`
profile found two leftover full-sector scans in the flying moves and a third in the renderer's model lighting; the
fixes and the profile are in BLV_GEOMETRY_COSTS.md ("The p95 spikes"). Remaining per step: the AI facts (0.30 ms,
mostly the active monsters' line of sight to the party and their target scans) and the active monsters' moves
(0.44 ms, mostly the dragonflies'); no full-sector scan is left in the profile. Open: pathing across steep MM9 slopes
with `steep_slopes: block` for monsters was not studied beyond this spot.
