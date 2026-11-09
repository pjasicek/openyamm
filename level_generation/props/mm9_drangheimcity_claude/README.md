# MM9 Drangheim City props as 3D decorations (2026-10-31)

The props, candles, chandeliers, burning logs, barrels, clover and the well of MM9's Drangheim City
(`DRANGHEIMCITY.dat`), as OpenYAMM 3D decorations for the native BLV ([map project](../../projects/mm9r_drangheimcity/)).
The route is Sturmford City's ([`../mm9_sturmfordcity_claude/`](../mm9_sturmfordcity_claude/README.md): scripts copied
and adapted), itself Drangheim Prison's and Hall of the Gods': MM9's own meshes, one material per skin x4 by plain
Lanczos (the isle's `textures.upscale`), the isle's `blib` build and `finish` checks. No paid services, no Meshy, no
Codex.

## Outputs

- **20 models built** and installed with `tools/install_model.py --world mm9` (`assets_source/worlds/mm9/models/mm9_deco_*.glb`,
  cooked copies in `assets_dev/engine/models/`), each through `check_winding.py` (0 inverted closed parts) in
  `finish.py`: `barstool2`, `box01`, `box02`, `cart01`, `cart02`, `cart02nohay` (HidePiece `Hay`), `clover`,
  `hitchingpost`, `jug1`, `platestack1set1`, `platestack2set1` (the plate-set1 skin; Klusos House's are plate2),
  `shelfitem03hc` (HidePiece Hourglass1, Crystals1), `shelfitem09` (plain; Sturmford built only its HidePiece variants),
  `shelfitem09g` (HidePiece Gloves), `tapestry_banner2`, `weaponrackg1`, `weaponrackg2` (the weaponrack_used skin
  without Group1 / Group2), `winebottle02`, `winebottle03`, `winebottle05`. Contact sheet: `review/props_sheet.png`
  (looked at).
- **56 models reused** (same ABC and skin; `props_table._OWNERS`), among them Thronheim City's `coatrack2`,
  `steinfancy01`, `shield3flat` and `shield4flat`, installed by that session minutes before (the flat shields were built
  here too, byte-identical, and not installed), the isle's `well`, `coatrack`, `dresser` and `logsburning`, and
  Sturmford City's `candelabra`, `chandelier2`, `kegbeer`, `portalwhole`, `trainingarchery1`, `strawdummy2c/l/r`,
  `winebottle04` and the HidePiece shelves `shelfitem03f`, `shelfitem09sg`, `shelfitem09d`.
- Rows **2552-2578** (27 rows: the 20 new models and 7 new-scale variants of reused ones: `benchstone02_x120`,
  `bookcase02ns_x100`, `logsburning_x70`, `logsburning_x200`, `pillarstand_x150`, `suitofarmor01_x120`, `winebottle`)
  in `assets_dev/worlds/mm9/data_tables/decoration_data.txt`, sprites 26353-26379, 27 bindings in
  `worlds/mm9/models/indoor_decorations.yml`, appended under `mm9r_common/locks/mm9_decorations.lock`
  (`work/tables_apply.log`). No row carries a light (every candle, chandelier and fire has its DAT Light, a BLV light).
- `../../projects/mm9r_drangheimcity/props.json`: **201 placements** (174 `prop`, 27 `torch`), every Prop, CandleProp,
  Barrel, Clover and WellMMIX of the DAT. All 201 are checked against the old map's baked BModel of the same object:
  **median of medians 0.53 units, worst 1.02** (the crates).

## Choices

- **Burning logs**: all six `logsburning` objects stand under an MM9 `Fire` (within 48 LT on the plan): the isle's
  `logsburning` (flame cards), unlit rows of their own (`OWN_ROW`). MM9 sinks the log piles 15-31 units into the hearth
  floor; the map's `convert.py` lifts them onto the floor (they did not draw sunk).
- **Shields** (pitch 90): Shield.ABC stands and MM9's pitch lays it flat; the old bake is flat. Klusos House's hanging
  `shield3` and Dook's Castle's `shield4` fitted at 36.5 / 39.7 units; Thronheim's flat variants fit.
- **HidePiece**: ShelfItem05.ABC has no Wands1 or Crystals1 piece (five jars), so the shelf hiding them is the plain
  Lich Lab model.
- **Barrels** (class `Barrel`, MM9's drinkable barrels): placed as the barrel decoration; drinking from them is not
  carried (no native MM9 barrel event yet: STATUS "open with the user", `evt.UseMm9Barrel`).
- **Clover** (class `Clover`) and the well (`WellMMIX`) are placed (Sturmford left its clover out).
- 0 repeated DAT names; no DAT name is a decoration's name.

## Route (`scripts/`)

```sh
cd level_generation/props/mm9_drangheimcity_claude
python3 work/registry.py && python3 scripts/props_table.py && python3 scripts/convert_all.py && python3 scripts/textures.py
blender --background --factory-startup --python scripts/build.py
python3 scripts/finish.py --install
blender --background --factory-startup --python scripts/review.py && bash scripts/contact_sheet.sh
cd ../../.. && flock -x level_generation/projects/mm9r_common/locks/mm9_decorations.lock \
    python3 level_generation/props/mm9_drangheimcity_claude/scripts/tables.py --apply && cd -
python3 scripts/placements.py --verbose
python3 ../../projects/mm9r_common/review_root.py
```

Before installing, check that no other city session installed a model of the same name meanwhile
(`assets_source/worlds/mm9/models/mm9_deco_<prop>.glb`): Thronheim and Thjorgard City build several of the same ABCs the
same evening; reuse theirs (`_OWNERS`) instead of installing over them.
