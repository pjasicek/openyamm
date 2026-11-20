# MM9 Chasm of the Dead props as 3D decorations (2026-10-30)

The props, fires, chests and quest objects of MM9's Chasm of the Dead, converted from their LithTech ABC models into
OpenYAMM 3D decorations for the native BLV ([map project](../../projects/mm9r_chasmofthedead/README.md)). The route is the
Temple of Honk props project's ([`../mm9_templeofhonk_claude/`](../mm9_templeofhonk_claude/README.md)): `scripts/anskram.py`
runs the Anskram Keep scripts on this project's table, `build.py` runs the Anskram build, `finish.py` the isle's. No paid
services and no Codex images: every model is MM9's own mesh and skin. The skins were enlarged x4 with Real-ESRGAN
before the user's decision to stop using it on props (2026-10-30); the shared `textures.py` now uses Lanczos, and the
Codex x4 pass replaces them all later.

## Outputs

- **29 models** installed with `tools/install_model.py --world mm9` (`assets_source/worlds/mm9/models/mm9_deco_*.glb`, cooked
  copies in `assets_dev/engine/models/`); all pass `check_winding.py`.
- Reused, not rebuilt: Beethoven's `jar01`, `jar04` (x1.5 variant rows here), the Lich Lab's `blackchest` (x0.8 row),
  Anskram's `spikepit` (`Spikes2`, placed by the map project).
- The MM9 world's decoration contribution: 37 rows appended under `locks/mm9_decorations.lock`
  (`assets_dev/worlds/mm9/data_tables/decoration_data.txt`, sprites, `worlds/mm9/models/indoor_decorations.yml`).
- `../../projects/mm9r_chasmofthedead/props.json`: **313 placements** (213 props, 82 fires, 16 chests, 2 quest objects),
  each checked against the old map's baked BModel: median distance 0.3-0.8 units; the wall torches 5.9 (a 2 LT bracket
  offset of the ABC's origin, not visible in the views).
- `review/props_sheet.png`: contact sheet of the first 27 models.

| Model | Source ABC (skin) | Placements | Triangles | Notes |
|---|---|---|---|---|
| `bluebrazier`, `bluebowl`, `bluesconce`, `bluetorch` | BRAZIER, HANGINGBRAZIERBOWL, SCONCE2 (x2), TORCH2 | 12 / 19 / 30 / 21 | 175-380 | **blue flames**: MM9's `CandleProp` carries `Blue 1` and every fire here has a 0/128/255 light: the shared CC0 flipbook recoloured (`textures/flame02_basecolor.png`); the Temple's orange brazier is not reused |
| `sarcophagusvert`, `sarcophagus`, `sarcophagusns`, `sarcophagusns3`, `mummyew` | SARCOPHAGUS2VERT, SARCOPHAGUS2, SARCOPHAGUS2NS, MUMMYEW | 39 / 4 / 5 / 1 / 8 | 126-242 | the mummies stand in the upright ones; `sarcophagus` and `mummyew` take the quarter turn the `*ns` furniture took elsewhere |
| `statueguardian`, `statueguardianew` | STATUE_GUARDIAN1, 1EW | 4 / 8 | 638 / 318 / 158 | x0.4-1; `ew` quarter turn |
| `altar1`, `pillarstand`, `urn1`, `urn2`, `cup1`, `goblet`, `tumbler1`, `boxornamental`, `chair1` | | 1-33 each | 60-188 | offerings |
| `altar1flip`, `pillarfallen`, `urn2tip1`, `urn2tip2` | | 1 each | 60-188 | toppled in MM9 (pitch 3.14, 1.57, 2.09, 0.87): the pitch baked in, as Beethoven's side jars |
| `treasurechute`, `treasurepile` | | 3 / 3 | 344 / 758 | |
| `chest5` | CHEST5 | 15 | 122 | |
| `cronakiga`, `lichinstructions` | PICKUPITEMS/QUEST | 1 / 1 | 252 / 80 | scripted pickups |

Decoration names are `mm9_<prop>` (a further scale `mm9_<prop>_x<scale %>`). No row carries a light: every fire has its
MM9 `Light` beside it, kept as a BLV light (`props.json` names it).

## Route (`scripts/`)

```sh
python3 scripts/props_table.py && python3 scripts/convert_all.py && python3 scripts/textures.py
blender --background --python scripts/build.py && python3 scripts/finish.py --install
blender --background --python scripts/review.py -- && bash scripts/contact_sheet.sh
flock -x ../../projects/mm9r_common/locks/mm9_decorations.lock python3 scripts/tables.py --apply
python3 scripts/placements.py && python3 ../../projects/mm9r_common/review_root.py
```

The blue sconce is a demon's head on the wall, not a cup: "the top 12 % of the model" finds its horns and rear rim, so
its flame has an explicit seat on the crown's apex (`build.py`, 0.001 / 0.074 / 0.518 in the asset frame), a seat the
old billboard mode hid by standing every flame on the model's axis. MM9's own `FireNode` is inside the head at the chin
(about 0, 0.09, -0.04), where a flame would show only through the eyes and mouth; the crown keeps the flame this
prop always showed. The tall card still ends at 1.0: the binding's height is the model's height, flame included, and
sets the scale. See the [Anskram README](../mm9_anskramkeep_claude/README.md#flames) for the card billboard.

`tables.py` accepts both sprite blocks (24801-24999, 26001-26999). `placements.py` centres each model without flame cards on
its old bake's box (a turned model's raw import is not the placed mesh).

## Notes

- `SpikePit` on the crushers and closing walls are not placed: decorations do not move (map README, deviations).
- `Transparent`/`Chromakey`: 0 placements here. `Shadow`, `TintColor`: none used.
