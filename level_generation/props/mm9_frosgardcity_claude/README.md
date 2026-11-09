# MM9 Frosgard City props as 3D decorations (2026-10-31)

The props, candles, chandeliers, braziers, the sitting dogs, the maypole, the viking ship, the clover patches and the
well of MM9's Frosgard City (`FROSGARDCITY.dat`), converted from their LithTech ABC models into OpenYAMM 3D decorations
for the native BLV ([map project](../../projects/mm9r_frosgardcity/)). The route is Thjorgard City's
([`../mm9_thjorgardcity_claude/`](../mm9_thjorgardcity_claude/README.md), itself Sturmford City's): one material per MM9
skin, `specs.json` turns, `POSES`, HidePiece variants, the isle's `blib` build and `finish` checks. No paid services,
no Meshy, no Codex, no Real-ESRGAN: every model is MM9's own mesh with its skin x4 by plain Lanczos.

## Outputs

- **8 models built** and installed with `tools/install_model.py --world mm9` (`assets_source/worlds/mm9/models/mm9_deco_*.glb`,
  cooked copies in `assets_dev/engine/models/`), all through `check_winding.py` (0 inverted closed parts each,
  `work/check_winding_installed.log`).
- **63 models reused** (same ABC and skin, same pose, tilt and hidden pieces; `props_table.REUSED`): the isle
  (`cot`, `vikingship`, `well`, `logsburning`), Sturmford City, Thjorgard City (`bedmediumew`, `herbrack2`), Thronheim
  City (`coatrack2`, `herbrack1`, `shelfitem02mp`, `shield3flat`, `shield4flat`, `suitofarmor01plain`), Drangheim City
  (`clover`), and the dungeons' props projects (Anskram Keep, Lich Lab, Drangheim Prison, Temple of Honk, Klusos House,
  Tasar Academy, Training Hall, Dook's Castle, Ruined Temple, Dark Passageway, Thjorad Mine, Bathhouse, Beethoven).
- Rows **2623-2636** (14 rows: the 8 new models and 6 new-scale variants of reused ones: `mm9_hangingbowl_x100`,
  `mm9_herbrack1_x200`, `mm9_logsburning_x250`, `mm9_mug1_x100`, `mm9_spikepit_x150`, `mm9_winebottle_x100`) in
  `assets_dev/worlds/mm9/data_tables/decoration_data.txt`, sprites **26424-26437**, 17 bindings in
  `worlds/mm9/models/indoor_decorations.yml`, appended in one run under `mm9r_common/locks/mm9_decorations.lock`
  (`work/tables_apply.log`). A rerun of `tables.py` reports 0 rows to add. No row carries a light.
- `../../projects/mm9r_frosgardcity/props.json`: **177 placements** (156 `prop` with the swapped maypole, 21 `torch`): every Prop (149), CandleProp (15), Brazier (6), DestructableProp (2), Clover (2), WellMMIX (1) and
  PropDamager (1) of the DAT, and `Prop0Maypole`. **170** are checked against the old map's baked BModel of the same
  object: median of medians 0.50 units, worst 0.80 (`work/placements.log`). Not checked against a bake: the four
  `ew` beds and the two sitting dogs (on MM9's own pose instead: `fit_pose_units` 0.0) and the swapped maypole (at
  Prop0's place).
- `review/props_sheet.png`: contact sheet of the 8 built models (LOD0 views, LODs), looked at.

| Model | Triangles | Placements | Notes |
|---|---|---|---|
| `dogsitting` | 320 / 140 / 74 | 2 | Dog1, Dog2 (`models\dog.abc`, PropAnim.scr `sitting`) posed at the animation's first key (`POSES`) |
| `maypoleold` | 323 / 161 / 80 | 1 | Prop0, the old maypole in the square |
| `maypole` | 194 | 1 | ChangeModel.scr's new maypole (key 268): a second decoration at Prop0's place, shown by the map's cog |
| `plateset2p1` | 298 | 2 | Plate-Set2 with the plate-set1 skin (Thronheim's `plateset2` has plate2); no LODs |
| `tapestry_banner1` | 48 | 1 | Tapestry-Old01 with banner1; cut-out frayed edge (3.6 % of the texels transparent); hung |
| `weaponracknsusedg2`, `weaponracknsusedg3` | 936 / 1 001 | 1 each | WeaponRackNS with the used skin without Group2 / Group3 (HidePiece), `turn: 90` |
| `weaponscabinet03s3` | 26 | 3 | WeaponsCabinet03 with its own skin (Thjorgard's has weaponscabinet06) |

## Route (`scripts/`)

```sh
cd level_generation/props/mm9_frosgardcity_claude
python3 scripts/props_table.py && python3 scripts/convert_all.py && python3 scripts/textures.py
blender --background --factory-startup --python scripts/build.py
python3 scripts/finish.py --install
blender --background --factory-startup --python scripts/review.py && bash scripts/contact_sheet.sh
cd ../../.. && flock -x level_generation/projects/mm9r_common/locks/mm9_decorations.lock \
    python3 level_generation/props/mm9_frosgardcity_claude/scripts/tables.py --apply && cd -
python3 scripts/placements.py --verbose
python3 ../../projects/mm9r_common/review_root.py
```

`work/registry.py` maps every (ABC, skin) of the other MM9 props projects to its prop and owner (the reuse check).

## Notes

- **Kinds**: Brazier and CandleProp are `torch` (each names its nearest DAT Light, 0-102 units away); the rest `prop`.
  The townsfolk (PeasantMale, Tryggva, Tamur Leng) are actors of the map, not decorations; Dog0 is an AmbientSound.
- **Scripted decorations** (the map's `citylua.py`): Prop0 / Prop0Maypole (ChangeModel.scr, key 268), Prop1 the
  runestone (HideModel.scr "278 UnHide"), DestructableProp0 the powder barrel on the ice (NPC215.scr, key 1022; its
  click starts the ice breaking), Prop6-9 the letters (BookLetter.scr 462-465), Book1, TownPortal0, WellMMIX0.
- **Logs0-2** lie under MM9's Fire0-2 in Tryggva's hall (Scale 2.5): the isle's burning `logsburning` (flame cards).
- Not shipped by MM9: `models\TamurLeng.abc` (Forad Darre's and Tamur Leng's DAT Filename; the actors use their rows).
