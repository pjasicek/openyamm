# MM9 Thjorad Mine props as 3D decorations (2026-10-30)

The props, lanterns, oil lamps, mine carts, ore bins, barrels, crates, chests and quest machine parts of MM9's Thjorad
Mine, converted from their LithTech ABC models into OpenYAMM 3D decorations for the native BLV
([map project](../../projects/mm9r_thjoradmine/README.md)). The route is Dook's Castle's props project
([`../mm9_dookscastle_claude/`](../mm9_dookscastle_claude/README.md)): one material per MM9 skin, the isle's `blib`
build and `finish` checks, with flame cards and a glass split added in `build.py`. No paid services, no Meshy, no
Codex: every model is MM9's own mesh with its skin x4 (plain Lanczos, the isle's `textures.upscale`).

## Outputs

- **13 models built here**, installed with `tools/install_model.py --world mm9`
  (`assets_source/worlds/mm9/models/mm9_deco_*.glb`), all through `check_winding.py` in `finish.py` (0 inverted closed
  parts each): `minelantern02` (99 placements, `minelantern-bright` skin), `stonedebris05thjorad` (34, the ore debris
  with `thjorad.dtx`), `thjoradbin` (26, two skins: the bin and its ore), `minecart` (22, two skins: the cart and its
  ore), `oillamp` (5, flame cards, glass chimney), `stool01` (5), `woodbin` (2), `boiler`, `box02pantry` (the slag
  extractor's base, `SlagBase.scr`), `bucket02`, `tableroundplain` (`tableround.abc` with the plain skin),
  `machinepartbroken` (the broken slag extractor, `slag`), `machinepartwhole` (the repaired one; not placed in the DAT:
  `SlagExtractor.scr`'s `OnShow` swaps the model, `SetModelFilenames Machine-Part_Whole.ABC`).
- **16 reused** (same ABC, skin; their GLBs, rows and bindings stay with their owners): Anskram Keep's `barrel` (55),
  `barrel03` (12), `bedmedium` (21), `crate` (16), `trashpile` (11), `scroll` (8, the signs), `weaponscabinet01` (2),
  `chest1` (2); Drangheim Prison's `anvil` (2), `bench01`, `bucket01` (10), `coalbin` (2), `tablebench2` (7); the
  Temple of Honk's `chairdesk03` (3); Tasar Academy's `dwarfaxeonside` (17, the pickaxes' PropAnim.scr `onside` pose);
  Verhoffin Ruins' `bedmedium2onside` (2, Bed22/Bed24 `onside`).
- Rows **2338-2358** (21 rows) in `assets_dev/worlds/mm9/data_tables/decoration_data.txt`, sprites 26139-26159,
  bindings in `worlds/mm9/models/indoor_decorations.yml`, appended under `mm9r_common/locks/mm9_decorations.lock`
  (`tables.py --apply` takes it): the 13 models and the scale variants `mm9_anvil_x60`, `mm9_barrel_x125`,
  `mm9_bucket01_x90`, `mm9_dwarfaxeonside_x200`, `mm9_minecart_x150`, `mm9_thjoradbin_x200`, `mm9_trashpile_x200`,
  `mm9_weaponscabinet01_x90`. 14 rows reused from other projects (`mm9_barrel`, `mm9_crate`, `mm9_scroll`, ...).
  No row carries a light: MM9's `Light` objects beside the lamps and lanterns are the map's BLV or bake-only lights.
- `../../projects/mm9r_thjoradmine/props.json`: **370 placements** (240 props, 86 destructible props, 15 chests, 12
  barrels, 11 bone piles, 5 oil lamps, plus `slag_whole`). Each checked against the old map's baked BModel as Dook's
  Castle does: median of medians **0.49 units, worst 0.88** (MovingBin1). Not baked by the old import, so placed by the
  transcoder's rule with the floor drop of MoveToFloor objects: the 86 `DestructableProp`s (barrels, crates, stools,
  mine carts, the `DB_Barrel*` chain), `slag`, and the posed pickaxes and beds (below).
- `review/props_sheet.png`: contact sheet of the 13 built models (looked at); `review/<prop>/`: the review renders.

## Scripted props (the map project wires them by anchor)

| Anchor | Model | MM9 script | What it does in MM9 |
| --- | --- | --- | --- |
| `Bin2` | `thjoradbin` | `Mine.scr` | de-activated in TELP 1.3 (`:Onuse` exits at once) |
| `MineCarA` | `minecart` x1.5 | `TM_MineCarA.scr` | damaged: rolls to `MCarAMarker0`, breaks `MCarBlocker1`, then `ABMineBoards0` |
| `DB_Barrel6`, `DB_Barrel7` | `barrel` x1.5 | `BlowUpTheBoards.scr` (`ABMineBoards3`, `ABMineBoards2`) | `HitMe` destroys their boards |
| `DB_Barrel0-9` | `barrel` | (targets of `TM_TorchFlame.scr` / `TM_FirstFallingFlame.scr`) | the exploding barrel chain |
| `WorldObject0` | `box02pantry` | `SlagBase.scr` | use with item 399: `slag` Show |
| `slag` | `machinepartbroken` | `SlagExtractor.scr` | use: item 398, key 9512, hidden; Show: 5000 XP, key 37, takes 399, model -> whole |
| `slag_whole` | `machinepartwhole` | (the swap above) | extra placement at `slag`'s position: hidden until the quest is done |
| `Sign0-7` | `scroll` | `BookLetter.scr` (572, 571, 574, 573, 573, 426, 486, 487 `Letter`) | `DoLetter` |
| `Miningax0-16`, `Bed22`, `Bed24` | posed models | `PropAnim.scr onside` | the pose (baked in their models) |

Every placement in `props.json` carries `script` and `script_params`.

## Route (`scripts/`)

```sh
cd level_generation/props/mm9_thjoradmine_claude
python3 scripts/props_table.py && python3 scripts/convert_all.py && python3 scripts/textures.py
blender --background --factory-startup --python scripts/build.py
python3 scripts/finish.py --install
python3 scripts/tables.py --apply                 # takes the decorations lock itself
python3 scripts/placements.py
python3 ../../projects/mm9r_common/review_root.py
blender --background --factory-startup --python scripts/review.py -- && bash scripts/contact_sheet.sh
```

## Notes

- **Oil lamps** (`CandleProp`, no Flame socket, `Offset` 0): the skin's translucent texels (alpha 7-110) are the glass
  chimney; `build.py glass_faces` puts the 59 faces whose UV centre is translucent on their own blended double-sided
  material (`oillamp_glass_2s`, finish.py `BLEND`), the brass stays opaque. The flame cards (the shared CC0 Flame02
  flipbook, `card` billboards: the isle's `FIRE` in finish.py, the pipeline as fixed on 2026-10-30) are seated on the
  wick inside the chimney (`specs.json` seat (-0.024, 0, 0.19) m: the skin's own painted flame quad stands there,
  alpha 0), 0.10/0.08 m wide, 0.25/0.20 m tall. Looked at from the front, three-quarter, side and below in the renders:
  the flame stands on the wick behind the glass. Not yet looked at in game.
- **Posed props**: the old bake is the ABC's bind pose, so the pickaxes (MoveToFloor 0, 7 LT over the floor) and the two
  beds (MoveToFloor 1) lie with their posed base on the floor under the DAT position (`placements.py POSED`), as Tasar
  Academy's pickaxes and Verhoffin's beds; no fit number.
- **Collision**: MM9's `Solid` flag, except the hanging lanterns (MoveToFloor 0), oil lamps, signs, the slag base,
  the pickaxes and the ore debris (`tables.py NO_COLLISION`).
- `minelantern02`'s panes are MM9's `minelantern-bright` skin (opaque, alpha 255 throughout: no glow mask); the hook on
  top is part of the mesh.
- The boiler's back is open in MM9's mesh (it stands against a wall); its material is double-sided.
