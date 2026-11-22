# D-66 thrones and DD-17's teal statue, 2026-11-21

Lane S, session 9. No Meshy, no Codex. These pieces finish D-66 items 8 (DD-17) and 7 (DD-08), the case of
D-63 item 14: the thrones and the statues must not be stand-ins at done.

MM6–MM8 ship no throne decoration: their thrones are map geometry, and `engine/data_tables/decoration_data.txt` has
no throne, chair or seat. So the throne is MM9's carved throne (`mm9_deco_throne.glb`, 220 triangles), copied into
Xeen under the D-44 rule, the same route as P5's bench. The statue is a shipped MM6–MM8 statue, as D-61 asks: MM8's
sword-raising "Elf Statue" (`mm8_deco_elfstatue.glb`, row `dec01`), cast in teal metal.

| Row / sprite | Decoration | Model (`worlds/xeen/models/`) | Size | For |
|---|---|---|---|---|
| 4043 / 27043 | `xeen_throne` | `xeen_deco_throne.glb` (MM9's throne, unchanged) | 250 tall, 150 x 133, radius 70, seat about 78 up | DD-08: four Emotion Thrones, the Throne of the Dunce |
| 4044 / 27044 | `xeen_throne_steel` | `xeen_deco_throne_steel.glb` (Ancient steel frame, dark teal cushion, metallic) | as above | DD-17: Sheltem's throne in the apse |
| 4045 / 27045 | `xeen_throne_gold` | `xeen_deco_throne_gold.glb` (gilded frame, ivory cushion) | as above | DD-08: the Euphoria Throne |
| 4046 / 27046 | `xeen_statue_teal` | `xeen_deco_statue_teal.glb` (5,893 / 2,651 / 1,060 triangles) | 300 tall (the figure about 250), plinth 124 x 100 x 49, radius 60 | DD-17: the three propaganda statues and the true-name statue (replaces `sta1a`) |

The bindings are in `assets_dev/worlds/xeen/models/indoor_decorations.yml`, each with `yaw: facing` and
`yaw_offset` -90 deg, so an entity's facing is the direction the seat or statue looks. The sprites use the engine's
`pending` texture. The rows were appended by `../xeen_p5props_claude/scripts/append_rows.py rows.json --apply`.

## Placement (A8)

- **Thrones:** the origin is the centre of the foot, on the floor. Replace each `xdthrone` / `swgirder` seat block and
  its back with one throne at the seat block's centre.
  - DD-08: Emotion Thrones at x 1088 face 0, at x 1984 face 180; the Euphoria Throne faces 270 on the dais
    (z 1392); the Dunce faces 90.
  - DD-17: the apse throne at (-3840, -4000) faces 0, at z 1312 on the dais.
  - The throne is 150 wide: inside the old 128 seat block plus its 32 back.
- **Statue:** the origin is the bottom centre of its own plinth. Either drop the `platform:statue*` plinths
  (256 x 128, rise 32) and stand it on the floor, or stand it on top of them (z + 32). It faces the way the old
  statue faced (the first one 270, away from the north wall).

## Build

```
python3 scripts/recolour.py work                      # work/tex/: steel, gold, teal base colour + metallic-roughness
blender -b --python scripts/build.py -- $PWD          # export/xeen_deco_throne_{steel,gold}.glb, work/..._statue_teal_raw.glb
python3 tools/link_static_model_lods.py work/xeen_deco_statue_teal_raw.glb export/xeen_deco_statue_teal.glb
```

- The source textures are pulled out of the GLBs into `work/` (`throne_img0.png`, `elf_img*.png`).
- The throne's atlas is wood and carving left of x 718 and the red cloth right of it; each part is recoloured
  separately.
- The statue's granite speckle is softened toward the mean, so the figure reads as cast metal (metallic 0.75,
  roughness 0.42).
- The plinth has a flat dark-steel material.
- LOD1 and LOD2 are collapse decimations.
- `xeen_deco_throne.glb` is MM9's file unchanged.
- Winding: 0 inverted closed parts on all four.

## Checks

In game (`build-xeen`), with the installed models as debug spawns at their spots (`scripts/tours.py`,
`work/ingame/run.sh`):
- DD-08's Hall of Thrones: two red thrones and the gold one on the dais, still overlapping A8's seat blocks
  (`review/ingame/sheet.jpg`).
- DD-17's apse: the steel throne inside the girder block. The teal statue stands beside MM6's `sta1a` in the Hall of
  Order (`review/ingame/sheet_dd17.jpg`).
- DD-17 refuses a party without the Soul Box, so its tour gives item 12364 and re-enters with
  `evt.MoveToMap(..., [[xeen_dd17.blv]])`.

Renders: `review/sheet_models.png`. Not used: MM9's sorcerer, guardian, Fre and Krohn statues, MM7's dwarf and
winged statues (`work/cand/sheet.png`).

## Also used by A7 (D-63 item 14, D-57 Q27)

- **FD-02's "Throne of Legends"**: `xeen_throne` (4043). A7 replaces the two-block chair with it: the origin is the
  centre of the foot, on the floor, and the facing is the way the seat looks.
- **FD-04's nest eggs**: `xeen_dragonegg` (4048 / 27048, `rows_egg.json`). It is the Dragon Egg item's own ground model
  (`engine/world_items/models/item_7item291.glb`, MM7's 7item291) at 2.34x: 58 long and 40 high, lying on its side,
  origin at its foot. No collision; any facing. It is the same egg the party takes.
- FD-04's lizard (Alister changed) is not made yet. Its likely route is a static, small-scaled pose of a shipped MM
  lizard creature (MM8's Thunder Lizard).
