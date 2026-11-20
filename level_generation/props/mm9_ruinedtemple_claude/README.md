# MM9 Ruined Temple props as 3D decorations (2026-10-30)

The props, torches, chandeliers, barrels, bone piles and chests of MM9's Ruined Temple, converted from their LithTech ABC
models into OpenYAMM 3D decorations for the native BLV ([map project](../../projects/mm9r_ruinedtemple/README.md)). The
route is the Beethoven props project's ([`../mm9_beethoven_claude/`](../mm9_beethoven_claude/README.md), itself the
Anskram Keep's): its scripts, pointed at this project. No paid services, no Meshy, no Codex: every model is MM9's own
mesh with its skin x4 (Lanczos, the isle's `textures.upscale`); the flames are the shared CC0 flipbook recoloured blue
(Chasm of the Dead's `flame02_basecolor.png`).

## Outputs

- **8 models** installed with `tools/install_model.py --world mm9` (`mm9_deco_*.glb`), all through `check_winding.py`:

| Prop | ABC / skin | Triangles (LODs) | Notes |
| --- | --- | --- | --- |
| `torchmetal` | TORCH2 / torch_metal | 178 | wall torch, **blue flame** cards on the head (`card` billboard, the isle's finish), hung |
| `chandelier3` | CHANDELIER3 | 322 / 157 / 89 | hung; **four blue candle flames**, one on each candle above MM9's `Flame..Flame4` sockets (the sockets sit in the cups; each flame stands on the highest vertex within 5 units of its socket) |
| `tapestry_bannergeo3` | TAPESTRY-OLD01 / BannerGeo3 (level texture) | 48 | MM9 `Transparent 1`: the skin's ragged edge is a cut-out; placed at 2.0 and 2.5 |
| `stonedebris04`, `stonedebris05` | STONEDEBRIS04 / c_dirt, STONEDEBRIS05 / ruinfloor | 112, 96 | the shaft bottom's rubble |
| `skeletonlaying` | SKELETONLAYING / Skeleton2 | 519 / 258 / 129 | the skeleton in the crypt |
| `genielamp` | GENIELAMP / GenieLamp_Old | 332 / 154 / 82 | the lamp that calls the genie (GenieCrystal.scr) |
| `treeoflife` | TREEOFLIFE (quest pickup) | 34 | the Tree of Life (TreeofLife.scr) |

- **Reused** (same ABC and skin): `chest` (Anskram), `barrel`, `barrel03`, `crate` (Anskram), `scroll` (Anskram),
  `bonepile`, `urngargoyle` (Beethoven), `pew3ns`, `podium01` (Lich Lab).
- Rows **2225-2233** in `assets_dev/worlds/mm9/data_tables/decoration_data.txt` (sprites 26026-26034), bindings in
  `worlds/mm9/models/indoor_decorations.yml`, appended under `mm9r_common/locks/mm9_decorations.lock`.
- `../../projects/mm9r_ruinedtemple/props.json`: 68 placements, each checked against the old map's baked BModel: median of
  medians 0.54 units; the 22 torches 5.7-5.9 (the torch2 model's known offset, as Beethoven's and the Chasm's: their
  flame head is cut from the fit); the Tree of Life (no bake: a quest pickup) stands on the floor under its DAT position.
- `review/props_sheet.png`: the review renders (LOD0 front, three-quarter, side, behind-above, below, LODs).

## Route (`scripts/`)

```sh
cd level_generation/props/mm9_ruinedtemple_claude
python3 scripts/props_table.py && python3 scripts/convert_all.py && python3 scripts/textures.py
blender --background --factory-startup --python scripts/build.py
python3 scripts/finish.py --install
flock -x ../../projects/mm9r_common/locks/mm9_decorations.lock python3 scripts/tables.py --apply
python3 scripts/placements.py          # needs the map's work/lights.json (one convert.py first)
python3 ../../projects/mm9r_common/review_root.py
blender --background --factory-startup --python scripts/review.py && bash scripts/contact_sheet.sh
```

## Notes

- Every `CandleProp` here carries `Blue 1` and its light is 0 / 128 / 255: blue flames on the torches and chandeliers.
- The pews' `PropAnim.scr onside` names an animation `pew3NS.abc` does not have: they stand upright, as in MM9.
- No normal or roughness maps; these are not Meshy-textured. The Codex x4 pass replaces the Lanczos skins.
