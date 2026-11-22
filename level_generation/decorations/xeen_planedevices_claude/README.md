# Xeen plane devices: the Ember Font, the burnt camp, the wrecked basket (P1, P2), 2026-11-21

Lane S sub-agent (11th session). Three small static indoor (BLV) decorations for the elemental planes, built from
scratch: procedural meshes and procedural textures, **no Meshy, no Codex, no shipped mesh recast**. Installed with
`tools/install_model.py --world xeen`; rows, sprites and bindings appended to the world's tables (below).

| Row | Decoration | Hint | Model (`worlds/xeen/models/`) | Binding height | Row radius | Triangles | Size (units) |
|---|---|---|---|---|---|---|---|
| 4056 | `xeen_emberfont` | Ember Font | `xeen_deco_emberfont.glb` | 107.0 | 90 | 466 | 178 x 178, lip 103, shimmer to 107 |
| 4057 | `xeen_firecamp` | burnt camp | `xeen_deco_firecamp.glb` | 35.53 | 0 | 1,354 | 222 x 105, 36 tall (the kettle) |
| 4058 | `xeen_balloonbasket` | wrecked basket | `xeen_deco_balloonbasket.glb` | 162.07 | 64 | 1,364 | 209 x 205 with rocks, 162 at the raised corner |

- All under 1,500 triangles: no LODs (guidelines §1). Winding: 0 inverted closed parts on all three.
- Model space: 1 model metre = 100 units, front toward glTF +Z, origin at the bottom centre of the bounds (y 0 =
  the floor). Bindings `yaw: facing`, `yaw_offset: -1.570796327` (the map's facing is where glTF +Z looks).
- Sprites 27056-27058 in `rendering/sprite_frame_data_world_decorations.yml`, texture `"pending"` like 27055.
- Rows: radius 90 on the font (solid and clickable: it is drunk from), 64 on the basket (solid; clickable for the
  logbook if A3 hangs the event on the decoration), 0 on the camp (walk over it; the find is a floor item). No
  decoration light on any (LightRadius 0): a warm light over the font, if wanted, is the map lane's own light.

## Placement for the map lanes (checked in game, `build-xeen`, debug `model spawn` at these numbers)

| Plane | Piece | Spot (x, y) | z (what it stands on) | Facing | Notes |
|---|---|---|---|---|---|
| P1 | Ember Font | (-1152, -448) poi:font | 96, the islet floor | any (0 used) | 12-sided and round: facing only turns the facets |
| P1 | burnt camp | (-3968, -4736) poi:camp | 0, the vent field floor | 90 used | front (+z) = the kettle and dead-fire side; bedroll head roll at model -x |
| P2 | wrecked basket | (-3712, 4224) poi:basket | 320, Kite Isle floor | 0 used | raised side and its rocks at model +x, the dropped sandbag at model -x/+z |

- **Font**: the fire's surface is 95 above the origin (8 under the lip top), radius 72. Clear 90 round it for the
  party; it reads from the islet's far edge (shot `emberfont_far`, about 900 away).
- **Camp**: the find (floor items) at the same spot lands on the bedroll or beside it; in the captures the current
  potions sit just beside it, which reads well. The ember-cache chest at (-4736, -4352) is 870 away (visible from
  the camp).
- **Basket**: radius 64 is solid; put the find and anything clickable outside about 110 from the spot (the current
  potions stand about 100-150 from it, fine). The cache chest at (-5056, 3840) is the map lane's ("wedged in the
  basket" in the plan; it stands 1,400 away in the current map, so the text may want "by the rocks" instead).

## Models

- **Ember Font**: one lathe, 12 flat facets: a chamfered foot (r 80), a stem (r 50), a bowl flaring to
  r 92, a chamfered lip (top at 103) and the inner wall down below the fire. Basalt (dark grey, grain, vesicles,
  fine cracks; v runs along the profile, so the lip and inner wall get a rust scorch and faintly glowing cracks).
  The fire: a 12-gon matching the inner wall (rings, strip-split centre), crusted lava (plates, glowing channels
  and veins; emissive, strength 1.1), `openyamm_uv_scroll` [0.018, 0.011], `openyamm_pulse` [0.12, 3.4]; over it a
  low additive shimmer shell (12 high, faded in its texture, u drift, `openyamm_flicker`).
- **Burnt camp**: a wool bedroll sheet lying flat (its edges on the floor, cloth lumps), its foot burnt away along a
  ragged line; soot rising toward the burn, char, nine scorch holes, faint ember specks at the burnt edge (pulse);
  a rolled head end; a dented iron kettle (lathe with a dent, spout, bail; 1.35x real size to read in game, tipped
  9 degrees); a dead fire of ash (blended disc, its rim fading), two crossed charred logs (faint ember cracks) and
  seven scorched stones.
- **Wrecked basket**: a rounded-square wicker gondola (bottom 118, top 130, 104 tall, 4.5 thick: outer and inner
  walls, floor, base), a rope binding round the rim, tilted 17 degrees (roll) and 5 (pitch) onto pale wind-carved
  rocks (one under the raised side, one under its highest corner, two small at the side), two snapped ropes above
  the rim, two hanging to the ground, a sandbag hanging over the raised side's wall, one dropped on the ground.
  Wicker tile: stakes under round weavers going over and under (colour and normal), weathered grey patches.
- Textures are tiling materials (repeat wrap; one unique map each for the bedroll and the ash), deliberately not a
  0-1 atlas (guidelines §4 deviation: procedural tiles stay sharp at these sizes). Base colours within sRGB 31-236.
- Pipeline: `scripts/build.py font|camp|basket|all` (helpers `scripts/lib.py`: periodic noise, height-to-normal,
  lathe/grid/tube/ellipsoid/disc, GLB writer) -> `work/<id>/xeen_deco_<name>.glb`, `textures/*.png`,
  `report.json` -> `check_winding.py` -> `tools/install_model.py --world xeen --name xeen_deco_<name>.glb`.
  `scripts/glbinfo.py` prints a GLB's parts and bounds.

## Checks

- In game (`build-xeen`, `xeen_p1.blv` and `xeen_p2.blv`, monsters cleared with `actor kill 100000`, the pieces
  spawned with the bindings' yaw at the spots above): tours from `scripts/ingame_tour.py <tag>`, runs
  `scripts/run_tours.sh <tag>` (P1 and P2 at once, exact-PID waits), sheets `scripts/sheet.py`.
  Final sheets: `review/ingame/c_p1_sheet.jpg` (font: front, three-quarter, top, far; camp: front, three-quarter,
  side, top) and `review/ingame/d_p2_sheet.jpg` (basket: front, three-quarter, side, top). Every piece stands on the
  floor at the plan's z (font islet 96, camp 0, basket 320), at the expected scale; no model warnings in the logs.
- Fixed on the way: the bedroll sheet was inverted (culled) in the first run; the font's stone was too rusty and
  the fire too yellow (more crust, deeper orange); the basket's raised side floated (rocks now sized from the tilted
  base, a third under the highest corner); the wicker's over-under made visible.

## Known limits

- The fire's bright channels bloom toward yellow at close range: it reads as liquid fire, not a lava rock.
- The kettle and the dead fire are small beside the bedroll; from more than about 500 away the camp reads as a
  bedroll alone.
- The basket's wicker is a tile: no broken strands or holes; the rim rope is a smooth binding.
- Not placed in the maps (the map lanes' L4/rooms): the decorations exist only as rows, bindings and models.

## Session 13 (2026-11-21): torn envelope on the basket (installed in session 14)

Stopped at a checkpoint (usage limits). The installed basket is still session 11's. Done in `scripts/build.py`
(`build.py basket` only): `wreck_wicker` (darker, grime, dust, three broken weavers, scuffs; own seed),
`envelope` (a polar height-field sheet of 36 x 13 vertices behind and left of the basket, model -z/-x, clipped at the
basket's hull, draped over the rocks; two torn flaps; a load ring; four rigging ropes from the rim; two load lines;
three splintered stakes) and `envelope_tex` (1024 planar map: red/cream/ochre gores, seams, tapes, patches, tears,
soot, dust, fold creases). The back-left corner's old hanging rope now runs to the envelope. Added after the shift,
so the origin and the basket stay where P2 placed them; the snapped rope stays the highest point, so the binding
height 162.07 should hold (check `work/basket/report.json` height_units; the bounds' footprint grows to the back).
The last build succeeded (work/basket/report.json): height 162.1 (unchanged), envelope 900 triangles; the envelope reaches 312 back (model -z 3.12 m), so check the space west of the spot in P2 and maybe shorten it.
Before shots: `review/s13/before_p2/` (`scripts/ingame_tour.py <tag> --placed`: no spawn, the map places it).
Left: run `build.py basket`, confirm triangles (target under about 3,000) and height 162.07, `check_winding.py`,
look in game (`ingame_tour.py after --placed`, map `xeen_p2.blv`), iterate, then `tools/install_model.py
work/basket/xeen_deco_balloonbasket.glb --world xeen --name xeen_deco_balloonbasket.glb`, validate, sheets.

### Session 14 (2026-11-21): installed

The session-13 export (2,848 triangles, height 162.1 = binding 162.07, footprint 312 x 414) passed `check_winding.py`
(0 inverted) and was installed unchanged (`--world xeen --name xeen_deco_balloonbasket.glb`). Placed tour on
`xeen_p2.blv` (`ingame_tour.py after --placed`): `review/s13/after_p2/`, sheet `review/s13/before_after.jpg`. The
envelope lies on the isle's open top well inside its edge (the `far` shot), clear of the chest and the potions; no
shortening needed. Validate: 335 descriptors on 84 models, 0 refused. Row, binding and placement unchanged. The
previously installed source (session 11) is kept as `work/basket/installed_s11_balloonbasket.glb` for rollback.
