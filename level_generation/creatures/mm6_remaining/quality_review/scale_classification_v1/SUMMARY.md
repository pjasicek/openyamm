# MM6 deterministic scale classification

Every current frame is included. Screens are review priorities, not accepted art diagnoses.
Translation remains in the user’s viewer workflow. This run changes no artwork or viewer state.

```json
{
  "families": 60,
  "frames": 3481,
  "screens": {
    "empty_endpoint": 2,
    "no_scale_signal": 1555,
    "proportion_or_pose_review": 1370,
    "size_signal_needs_body_measurements": 76,
    "uniform_scale_candidate": 478
  },
  "decisions": {
    "keep_empty_endpoint": 2,
    "review_measurements": 3479
  },
  "frames_with_body_measurements": 0,
  "source_flags": {
    "current_sampling_below_requirement": 4,
    "missing_raw_source": 1,
    "nonuniform_source_geometry": 72
  }
}
```

Full frame/action/view mapping: [frames.csv](frames.csv). Evidence and source hashes: [classification.json](classification.json).

| Family | Frames | Scale candidate | Size signal | Proportion/pose review | No scale signal | Other |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| BArcher A | 58 | 6 | 0 | 0 | 52 | 0 |
| Barbarian A | 57 | 6 | 0 | 8 | 43 | 0 |
| BBat A | 78 | 30 | 0 | 18 | 30 | 0 |
| BBeholder A | 48 | 11 | 0 | 29 | 8 | 0 |
| Bloodsucker A | 78 | 41 | 0 | 28 | 9 | 0 |
| Cleric A | 59 | 7 | 4 | 24 | 24 | 0 |
| Cobra A | 59 | 9 | 12 | 24 | 14 | 0 |
| Cockatrice A | 59 | 2 | 0 | 46 | 11 | 0 |
| DemonFly A | 54 | 3 | 0 | 41 | 10 | 0 |
| Demon A | 67 | 3 | 0 | 15 | 49 | 0 |
| DragonCave A | 59 | 7 | 0 | 37 | 15 | 0 |
| BDragonFly A | 78 | 11 | 1 | 60 | 6 | 0 |
| DragonLand A | 59 | 10 | 1 | 32 | 16 | 0 |
| DragonCover A | 55 | 7 | 0 | 39 | 9 | 0 |
| Druidess A | 59 | 6 | 3 | 27 | 23 | 0 |
| BDwarf A | 59 | 6 | 5 | 14 | 34 | 0 |
| ElemAir A | 24 | 9 | 0 | 11 | 4 | 0 |
| ElemEarth A | 59 | 2 | 1 | 26 | 30 | 0 |
| ElemFire A | 47 | 1 | 2 | 39 | 5 | 0 |
| ElemWater A | 71 | 15 | 3 | 34 | 19 | 0 |
| FighterChain A | 59 | 5 | 4 | 18 | 32 | 0 |
| FighterLeath A | 59 | 8 | 6 | 29 | 16 | 0 |
| BGargoyle A | 48 | 7 | 0 | 33 | 8 | 0 |
| BGenie A | 60 | 11 | 1 | 21 | 27 | 0 |
| BGhost A | 48 | 8 | 0 | 30 | 10 | 0 |
| BGoblin A | 59 | 8 | 0 | 12 | 39 | 0 |
| Guard A | 59 | 13 | 0 | 21 | 25 | 0 |
| BHarpy A | 48 | 1 | 0 | 39 | 8 | 0 |
| BHydra A | 59 | 7 | 0 | 38 | 14 | 0 |
| Jackalman A | 59 | 6 | 0 | 11 | 42 | 0 |
| KnightPlate A | 59 | 3 | 0 | 20 | 36 | 0 |
| BLich A | 59 | 15 | 1 | 15 | 28 | 0 |
| LizardArch A | 65 | 8 | 1 | 28 | 28 | 0 |
| BMedusa A | 59 | 9 | 0 | 28 | 22 | 0 |
| BMinotaur A | 51 | 4 | 0 | 24 | 23 | 0 |
| Nobleman A | 71 | 6 | 0 | 25 | 40 | 0 |
| BOoze A | 54 | 6 | 1 | 18 | 29 | 0 |
| Ogre A | 60 | 5 | 0 | 24 | 31 | 0 |
| PeasantF1 A | 59 | 2 | 4 | 26 | 27 | 0 |
| PeasantF2 A | 59 | 9 | 2 | 21 | 27 | 0 |
| PeasantF3 A | 59 | 8 | 0 | 11 | 40 | 0 |
| PeasantF4 A | 59 | 6 | 4 | 19 | 30 | 0 |
| PeasantM1 A | 59 | 4 | 4 | 22 | 29 | 0 |
| PeasantM2 A | 59 | 7 | 0 | 24 | 28 | 0 |
| PeasantM3 A | 59 | 8 | 1 | 31 | 19 | 0 |
| PeasantM4 A | 59 | 3 | 0 | 37 | 19 | 0 |
| BRobot A | 54 | 4 | 1 | 6 | 43 | 0 |
| SeaSerpent A | 59 | 5 | 1 | 41 | 12 | 0 |
| Skeleton A | 59 | 7 | 2 | 25 | 25 | 0 |
| Sorcerer A | 59 | 6 | 3 | 23 | 27 | 0 |
| BThief A | 59 | 5 | 4 | 16 | 34 | 0 |
| BTitan A | 57 | 0 | 0 | 23 | 34 | 0 |
| Werewolf A | 63 | 5 | 0 | 15 | 43 | 0 |
| zDemonQueen | 24 | 8 | 0 | 10 | 6 | 0 |
| zReactor | 31 | 0 | 0 | 9 | 22 | 0 |
| Cactus A | 89 | 36 | 4 | 11 | 36 | 2 |
| Merchant A | 58 | 0 | 0 | 0 | 58 | 0 |
| BMonk A | 57 | 1 | 0 | 3 | 53 | 0 |
| BRat A | 59 | 12 | 0 | 2 | 45 | 0 |
| BSpider A | 58 | 20 | 0 | 9 | 29 | 0 |

## Interpretation

- A scale candidate may come from silhouette bounds; it still needs verified body dimensions.
- Proportion/pose review can also indicate bad landmarks, weapons, or effects. It is not a regeneration order.
- No scale signal is not a clean bill of health. Missing/small/occluded features can hide defects.
- New downsample factors require artifact-bound X/Y fit dimensions and a withheld check dimension.
- Row summaries deduplicate source cells; they never assign a common resize to a row.
- Sampling estimates do not prove visual detail. Trial export must recheck integer resize rounding, clipping, masks, sampling, proportions and motion.
- Viewer offsets are ignored; notes/flags are included only for the exact current viewer artifact digest.
