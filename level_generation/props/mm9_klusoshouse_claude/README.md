# MM9 Klusos House props as 3D decorations (2026-10-30)

The props, wall candles, chandeliers, fireplace logs, the chest and the Blackheart of MM9's Klusos House, converted
from their LithTech ABC models into OpenYAMM 3D decorations for the native BLV
([map project](../../projects/mm9r_klusoshouse/README.md)). The route is the Ruined Temple / Beethoven props projects'
(the Anskram Keep scripts run on this project's table through `scripts/anskram.py`; `build.py` runs the Anskram build
with this project's flame specs). No paid services, no Meshy, no Codex: every model is MM9's own mesh with its skin
x4 (plain Lanczos, the user's rule since 2026-10-30; the Codex x4 pass replaces them later).

## Outputs

- **21 models** built and installed with `tools/install_model.py --world mm9` (`assets_source/worlds/mm9/models/mm9_deco_*.glb`),
  all through `check_winding.py` in `finish.py`: `wallcandle` (flame cards), `basketfruit`, `basketveggies`, `bed02`,
  `cabinet01`, `cabinet02`, `cabinet02ns`, `cabinet03`, `cabinet03ns`, `cabinet05`, `dresserfancy`, `dresserfancyns`,
  `pew2ns`, `pitcher01`, `platestack1`, `platestack2`, `shield3`, `stovens`, `tableround5`, `tabletrestle2`, `dirk`
  (the Blackheart).
- **19 reused** (same ABC and skin; their GLBs and rows stay with their owners): Anskram's `barrel`, `bed`,
  `bookcase02ew`, `chair02`, `scroll`, `weaponscabinet04`, `tableround`; the Temple of Honk's `cabinet01ns`,
  `cabinet04`, `table02`; the Lich Lab's `chair03`, `table01ns`, `blackchest`; Drangheim Prison's `cabinet04ns`,
  `shelfitem06/07/08`; the isle's `logsburning` (its three flame cards: MM9's `Fire` objects burn on the logs); the
  Ruined Temple's `chandelier3` (candle flames on its four sockets).
- Rows **2239-2262** (24 rows: the 21 models plus `mm9_logsburning_x150`, `mm9_shelfitem06_x200`,
  `mm9_table01ns_x120`, scale variants of reused models) in `assets_dev/worlds/mm9/data_tables/decoration_data.txt`,
  sprites 26040-26063, bindings in `worlds/mm9/models/indoor_decorations.yml`, appended under
  `mm9r_common/locks/mm9_decorations.lock`. No row carries a light: every candle, chandelier and fireplace has its MM9
  `Light` beside it, kept as a BLV light (or bake-only where a floor point was already under four).
- `../../projects/mm9r_klusoshouse/props.json`: **112 placements** (89 props, 22 candle props, 1 chest), each checked
  against the old map's baked BModel: median of medians 0.54 units; worst `Prop27` (below) and the Blackheart 1.77.

## Route (`scripts/`)

```sh
cd level_generation/props/mm9_klusoshouse_claude
python3 scripts/props_table.py && python3 scripts/convert_all.py && python3 scripts/textures.py
blender --background --factory-startup --python scripts/build.py
python3 scripts/finish.py --install
flock -x ../../projects/mm9r_common/locks/mm9_decorations.lock python3 scripts/tables.py --apply
python3 scripts/placements.py            # needs the map's work/lights.json: build the map once first
python3 ../../projects/mm9r_common/review_root.py
```

## Notes

- **`wallcandle`**: the Ruined Temple chandelier's small candle cards on the top 12 % of the model, which is the candle
  top: MM9's `Flame` socket (0.13, 12.0, 5.0 LT) sits 0.34 LT above it. Looked at from the side in game
  (`review/flames01` of the map project): the flame stands on the wick.
- **`*ns` furniture** (`cabinet02ns`, `cabinet03ns`, `dresserfancyns`, `pew2ns`, `stovens`) carries MM9's quarter
  turn (`turn: 90`, as Drangheim's `cabinet04ns`). `placements.py` centres a model without flame cards on its old bake
  where that fits better (the Chasm's rule, kept only where it lowers the median): the pews went from 7.5 to under 0.6.
- **`shield3` (`Prop27`)**: MM9 hangs the red-and-white shield on the wall over the dining-room fireplace (pitch 1.58);
  the old transcoder baked it flat, 10 LT thick, so its fit (36.5) measures the old bake, not ours. The pitch is baked
  into the model (`BOOK_TILT`); in game it hangs flat against the wall facing the room (review v04, l09).
- **The Blackheart (`dirk`)**: MoveToFloor 1 at 10 LT over the mantel; the old bake dropped it to 34 LT, inside the
  fireplace opening. `placements.py` (`DROP_TO_FLOOR`) stands it on the mantel top (143.4 native).
- **The `*ns` quarter turn is MM9's pose** (2026-11-06): the `*ns` ABCs are their plain twins' files whose first
  animation turns the Scene Root a quarter; MM9 draws a prop in that pose. The map converter applies it to every such
  prop (`mm9r_common/dungeon/prop_pose.py`, yaw -ry - 90 for the bind-mesh GLBs), so `YAW_FIX` is empty: its +90 for
  `cabinet04ns` (from the real screenshots 1 and 3, where the old placement showed the narrow end) put the carved front
  to the wall.
- `CandleProp`s and `Fire` objects make no light of their own: the map's `Light` objects light the house.
