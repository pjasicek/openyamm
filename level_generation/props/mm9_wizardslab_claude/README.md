# MM9 Wizard's Lab props as 3D decorations (2026-11-05)

The props, candles, sconces, cauldrons, bone piles, chests and the Saint's Relic of MM9's Wizard's Lab
(`WIZARDSLAB.dat`) as OpenYAMM 3D decorations for the native BLV ([map project](../../projects/mm9r_wizardslab/)).
Route: Drangheim City's ([`../mm9_drangheimcity_claude/`](../mm9_drangheimcity_claude/README.md), scripts copied and
adapted): MM9's own meshes, one material per skin, the isle's `blib` build and `finish` checks, skins redrawn by
[`../mm9_skins_x4/skins.py`](../mm9_skins_x4/skins.py).

## Outputs

- **243 placements** in `../../projects/mm9r_wizardslab/props.json`: 156 Props, 75 lit CandleProps, 4 BonePiles,
  3 TreasureChests (kind chest), 2 Barrels (stat barrels: dungeon/content.py), the Cauldron and 2 WellMMIX.
  Every one but the relic fits the old import's bake of the same object at 0.33-0.91 units (median of medians about
  0.5); the torch2 sconces fit MM9's own `static_object` pose at 0.64 (their old bakes are another pose, 5.87, as
  Ruined Temple's).
- **5 models built** and installed (`tools/install_model.py --world mm9`, `check_winding.py` 0 inverted in finish.py),
  with their skins redrawn: `relic` (the Saint's Relic, a 10-unit gilded bone; new skin `relic`), `skeletonlaying1`
  (skeleton1.dtx, the isle's `skull` skin by content), `ropecoilcauldron` (MM9 gives the three cauldrons RopeCoil.ABC
  with the cauldron01 skin at Scale 2 and 3: an iron ring in each DirtyWater basin, as the old import baked),
  `torchmetalunlit` (the four torch2 sconces that are Props: MM9 burns no fire on a Prop) and `shelfitem02ha`
  (HidePiece Amulets1). Contact sheet: `review/props_sheet.png`.
- **35 models reused** (props_table._OWNERS), among them Ruined Temple's blue `torchmetal` (53 CandleProps with Blue
  1) and Hall of the Gods' `torchmetalorange` (21 with Blue 0), Thjorgard City's `clawlampupblue` (the CandleProp claw
  lamp) and Sturmford City's `clawlampup` (the Prop claw lamps; Prop43's HidePiece Amulets1 names no piece of
  ClawLamp.ABC and is ignored, as MM9 does).
- **30 rows** (2741-2770) in `assets_dev/worlds/mm9/data_tables/decoration_data.txt` with sprites and indoor bindings
  (`work/tables_apply.log`): the 5 new models and 25 new-scale variants of reused ones. Hints are neutral (the
  cauldron ring `iron cauldron`, not `cauldron`: the engine reads that as MMerge's interactive cauldron).
- Not placed: the seven invisible candles (candle.abc with invisible.dtx; their lights are DAT Lights).

## Notes

- The relic's DAT name is `barrel`, also a decoration's name: placements.py writes it as `barrel_877` (dat_name
  `barrel`) and the map's citylua.py finds it by its script (Relic.scr), not by name.
- The letter Prop8 (`499 Letter 1`, BookLetter.scr bDown 1) lies flat in MM9 but stands here, as every map's: the
  final reconversion's props pass fixes all of them (devdocs/mm9_rework/HANDOFF_MAPS_FINAL.md).

## Route (`scripts/`)

```sh
cd level_generation/props/mm9_wizardslab_claude
python3 work/registry.py && python3 scripts/props_table.py && python3 scripts/convert_all.py && python3 scripts/textures.py
blender --background --factory-startup --python scripts/build.py
python3 scripts/finish.py --install
blender --background --factory-startup --python scripts/review.py && bash scripts/contact_sheet.sh
cd ../../.. && flock -x level_generation/projects/mm9r_common/locks/mm9_decorations.lock \
    python3 level_generation/props/mm9_wizardslab_claude/scripts/tables.py --apply && cd -
python3 scripts/placements.py --verbose
python3 ../../projects/mm9r_common/review_root.py      # the new rows into the review root before convert.py
```

New skins: `python3 ../mm9_skins_x4/skins.py inventory`, then `gen`/`finish` the new names and `install` them into
the models built here.
