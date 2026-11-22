# FD-04's lizard (D-57 Q27), 2026-11-21

Lane S, session 10. No Meshy, no Codex. This is the small lizard that Alister becomes after he drinks the egg potion.
FD-04's `deco:lizard` sits in Alister's alcove, hidden until 118147 is set.

The model is MM8's Thunder Lizard (`assets_source/worlds/mm8/models/mm8_m516.glb`), held still at `Standing` frame 0.
- Each of its four LOD meshes is baked into a static mesh, so the chain keeps the creature's own reductions.
- It is scaled to 50 units tall: about 87 long, snout to tail tip, and 27 wide.
- Skin A (green, orange crest) is baked into plain base colours with `claude_shared/tier_textures.py`, because a
  decoration has no tiers. The normal and metallic-roughness maps are kept, with metallic 0.

| Row / sprite | Decoration | Model | Binding (`worlds/xeen/models/indoor_decorations.yml`) |
|---|---|---|---|
| 4049 / 27049 | `xeen_lizard` "lizard" | `worlds/xeen/models/xeen_deco_lizard.glb` (LOD 7,584 / 3,791 / 1,895 / 943) | height 50, radius 24, `yaw: facing`, `yaw_offset` -90 deg |

## Placement (A7)

- In `output/studio_cal/fd04/tools/gen.py`, set `S_LIZARD = 'xeen_lizard'`. The existing code then places it at
  Alister's spot, (-1040, -768) on the alcove floor, hidden.
- Give it `facing: 0` (east, out of the alcove), the way Alister faces. With the binding's `yaw_offset`, facing is the
  way the lizard looks.
- The origin is between its feet on the floor. The snout reaches 28 ahead and the tail 59 behind, so it fits the alcove
  (320 deep) with room to spare.

## Build

```
python3 scripts/textures.py                                                    # work/tex/: skins A-C baked per set
python3 scripts/expose_lods.py <repo>/assets_source/worlds/mm8/models/mm8_m516.glb work/m516_lods.glb
blender -b --python scripts/build.py -- Standing 0 50 [--preview <tag>]     # work/xeen_deco_lizard_raw.glb
python3 <repo>/tools/link_static_model_lods.py work/xeen_deco_lizard_raw.glb export/xeen_deco_lizard.glb
python3 <repo>/tools/install_model.py export/xeen_deco_lizard.glb --world xeen --name xeen_deco_lizard.glb
python3 ../xeen_p5props_claude/scripts/append_rows.py rows.json --apply           # row, sprite, binding
```

Use the lane's `xeen_tiers_claude/bin/blender` wrapper. Skins B (wine and violet) and C (slate and green) are baked
too (`work/tex/skins.png`) if another tint is wanted.

## Checks

- Winding: 0 inverted closed parts.
- `build-xeen` validate: 334 descriptors, 0 refused.
- Renders: `work/sheet_stand0.png` (preview at 60 tall).
- In game, FD-04, the installed model as a debug spawn beside Alister's spot: `review/ingame/alcove.png`, `near.png`.
  It stands on the floor and reads as a small green lizard from the gate hall. Tour: `work/ingame/fd04.yml`.
