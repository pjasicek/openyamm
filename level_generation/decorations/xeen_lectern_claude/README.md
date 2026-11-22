# FD-02's lecterns (D-63 polish), 2026-11-21

Lane S, session 10. No Meshy, no Codex. MM6–MM8 ship no lectern, desk or chair decoration. D-63 moved the "Throne of
Legends" chair to `xeen_throne` (4043, session 9), which A7 already places. This is the polish item: the four
"lectern with a book" blocks in the Home of the Aged.

The stand is hand-built, 244 triangles:
- a foot and a plinth step;
- a pilaster post with the fluted, volute-capped panel;
- a carved skirt under the desk;
- a desk sloped at 24 degrees, with a lip at its low edge.

It is textured from the Throne of Legends' own wood atlas (`../xeen_throne_claude/work/throne_img0.png`), so it
matches Picard's chair. The book on the desk is MM9's open book `mm9_deco_bookflat`, copied into this model under
D-44. The cover shows from the front.

| Row / sprite | Decoration | Model | Binding (`worlds/xeen/models/indoor_decorations.yml`) |
|---|---|---|---|
| 4050 / 27050 | `xeen_lectern` "lectern" | `worlds/xeen/models/xeen_deco_lectern.glb` | height 120.5, radius 28, `yaw: facing`, `yaw_offset` -90 deg |

## Placement (A7)

- In `output/studio_cal/fd02/tools/gen.py`, replace the four `platform:book_<n>` blocks (64 x 48, rise 112) with
  `xeen_lectern` decorations at the same spots on the Home's floor (z 768).
- Face each one away from its wall, toward the room: the two by the north wall face 270, the two by the south wall
  face 90. Facing is the reader's side; the desk slopes down toward the reader.
- The origin is the foot's bottom centre. The desk is 54 x 41 and the foot 44 x 36. Stand it with its back about 24
  off the wall.
- If the books are clicked (their events), attach the events to the decorations as for the throne.

## Build

```
blender -b --python scripts/build.py -- [--preview]      # export/xeen_deco_lectern.glb (BOOK_YAW=<deg> turns the book)
python3 <repo>/tools/install_model.py export/xeen_deco_lectern.glb --world xeen --name xeen_deco_lectern.glb
python3 ../xeen_p5props_claude/scripts/append_rows.py rows.json --apply
```

Use the lane's `xeen_tiers_claude/bin/blender` wrapper. Previews are in `work/preview_sheet.png`; the book turns tried
are in `work/preview_yaw.png`.

## Checks

- Winding: 0 inverted closed parts.
- In game, FD-02's Home of the Aged, as a debug spawn by the south wall: `review/ingame/` (tour
  `work/ingame/fd02.yml`).
