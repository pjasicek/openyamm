# The elemental planes' ways up (D-58 C5/C7), 2026-11-21

Lane S session 8. The effect over each plane's way back up to the Skyroads (A6's `exit:way_up`): P3's dust shaft, P2's
updraft, P1's heat column (P4's waterspout is A6's geometry). No Meshy, no Codex, no Blender.

`scripts/build_column.py <preset>` writes each GLB from `scripts/column_presets.py`: open shells round a vertical
axis, every one additive (`openyamm_additive`), its noise texture scrolling up (`openyamm_uv_scroll`), faded at the foot
and the top by the shell's own shape (the static model shader reads COLOR_0 as placement lighting, so the vertex
fades in the GLB only matter in other viewers). It imports the water fall's `GlbWriter` and noise textures
(`../xeen_waterfall_claude/scripts/build_fall.py`).

| Decoration | Row / sprite | Model | Size | Triangles |
|---|---|---|---|---|
| `xeen_wayup_earth` "dust shaft" (P3) | 4041 / 27041 | `worlds/xeen/models/xeen_deco_wayup_earth.glb` | radius 175, 2,400 high: pale gold light core, dust streaks and motes rising | 2,432 |
| `xeen_wayup_air` "updraft" (P2) | 4040 / 27040 | `worlds/xeen/models/xeen_deco_wayup_air.glb` | radius 170, 2,000 high: white wisps streaming up | 1,664 |
| `xeen_wayup_fire` "heat column" (P1) | 4039 / 27039 | `worlds/xeen/models/xeen_deco_wayup_fire.glb` | half an ellipse 350 wide, 120 deep, 1,400 high: orange heat and embers | 1,344 |

Bindings in `assets_dev/worlds/xeen/models/indoor_decorations.yml` (from `integration/indoor_decorations.yml`), `yaw:
facing`, no `yaw_offset`; rows radius 0 (no collision: the party walks into the exit).

## Placement (for A6)

- **P3**: at the dust shaft's disc centre (`exit:way_up`, the L1 (-4864, 4864)), z = the disc's top (floor 0 + 4),
  any facing. The bowl's sky is about 2,400 over it; the column fades out over its top half.
- **P2**: at the updraft's disc centre (A6's `WAY_UP`), z = the disc's top, any facing.
- **P1**: at the foot of the molten sheet's middle (`exit:way_up` (5152, -5152), the sheet 268 wide), on the lava/
  shelf floor in front of the wall, `facing` = the wall's outward normal (the half-ellipse opens away from the wall:
  its flat side is the model's back, x across the sheet).

## Checks

- First looks with the debug `model spawn` in P3 (`review/p3/`, `p3b/`) drew the column opaque white: a spawned
  debug model does not use the material's blend state, so effects must be checked as placed decorations.
- Placed in an X6 overlay (`scripts/ingame_overlay.py <mount>`, tour `work/tour_x6.yml`, three runs): `review/x6a/`
  (too bright, solid), `x6b/` (toned down; the outer haze shells showed hard tube edges), `x6c/` (haze shells dropped:
  accepted). Seen only outdoors in X6's daylight; P3's bowl is dimmer, so the columns will read brighter there.
- P3 loads with the bindings (`work/p3load.log`: no manifest errors).
- Not yet seen at their spots in P1-P3: A6 places them.

## Session 9 tuning (A6's placed look, 2026-11-21)

A6's captures at the placed spots (`output/studio_cal/a6/s20/pics/sheet_p1.jpg`, `sheet_p3.jpg`) showed two problems:
- P3's dust shaft was a bright, nearly solid pale-gold column in the dim bowl.
- P1's heat column was lost against the molten sheet: orange added to orange.

`scripts/column_presets.py` now has these changes; the session-8 presets are kept in `work/column_presets_s8.py`.
- **Earth (P3).**
  - The glow and dust shells are dimmer: the glow is about 40 % and the dust 50 % of before, and their emission is
    about a quarter of before.
  - The dust texture's base is 0.22 → 0.08 and the glow's 0.6 → 0.35, so the shaft shows gaps.
  - The motes are 75 % as bright.
- **Fire (P1).**
  - The heat is a pale yellow-white streaked shimmer (texture base 0.15 → 0.02, more streak contrast), not orange.
  - It is wider than the 268 sheet (radius 250–300 and 190–250), so it also shows over the dark rock beside it.
  - The embers are paler, larger, denser and brighter (strength 3).

Rebuilt with `scripts/build_column.py earth|fire`, 0 inverted, and reinstalled under the same names: the bindings and
A6's placements are unchanged. Seen at A6's poses in P1 and P3 (`review/s9_sheet.jpg`, tours `work/s9/tour_p*.yml`):
- P3 is now a translucent column with the rock showing through.
- P1's streaks and embers stand apart from the sheet. The shimmer's edge over the dark rock reads as a faint grey band
  in the near shot.

## Session 10: P1's grey edge (A6's `output/studio_cal/a6/s21/pics/p1_near_edge_crop.jpg`)

The heat shells' ends showed as a pale grey-olive band over the dark rock. There were two causes:
- COLOR_0's side fade never reaches the game;
- a pale yellow added at low strength reads grey over brown rock.

The heat texture now carries the side fade itself (`u_fade` 0.25 in `build_column.py`; the heat shells use u_tiles 1
and no drift). It is amber (1.0, 0.78, 0.46), and the shells are twice as strong, so the streak over the sheet still
reads. The session-9 presets are kept in `work/column_presets_s9.py`.

Reinstalled under the same name and seen at A6's poses (`review/s10b/`): no grey band, the streak and embers over the
molten sheet, and warm streaks in the side views.
