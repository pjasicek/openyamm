# Xeen elemental planes: statues, test pedestals, return daises, the Drowned Bell (D-58 C7), 2026-11-21

Lane S sub-agent. Thirteen static indoor (BLV) decoration models for P1-P4: the four statues from the installed
elemental models, posed, frozen and recoloured as the element's stone; the four test pedestals and the four return
daises (P5's 12-sided disc in each element's stone); P4's Drowned Bell. **No Meshy, no Codex.** Installed with
`tools/install_model.py --world xeen`; bindings and rows are fragments for the lane to merge (`integration/`).

| Row | Decoration | Model (`worlds/xeen/models/`) | Height | Row radius | LOD triangles |
|---|---|---|---|---|---|
| 4027 | `xeen_statue_fire` | `xeen_deco_statue_fire.glb` | 673.4 | 224 (its plinth) | 8,396 / 4,198 / 1,930 / 754 |
| 4028 | `xeen_statue_air` | `xeen_deco_statue_air.glb` | 540 | 0 (A6's plinth) | 8,708 / 4,354 / 2,002 / 782 |
| 4029 | `xeen_statue_earth` | `xeen_deco_statue_earth.glb` | 479.9 | 0 (A6's plinth) | 5,200 / 2,600 / 1,196 / 468 |
| 4030 | `xeen_statue_water` | `xeen_deco_statue_water.glb` | 542 | 0 (A6's plinth) | 7,370 / 3,685 / 1,694 / 663 |
| 4031-4034 | `xeen_pedestal_fire/air/earth/water` | `xeen_deco_pedestal_<el>.glb` | 110 | 48 | 432 / 216 |
| 4035-4038 | `xeen_dais_fire/air/earth/water` | `xeen_deco_dais_<el>.glb` | 10 | 0 | 108 (no LODs) |
| 4042 | `xeen_drownedbell` | `xeen_deco_drownedbell.glb` | 177 | 90 | 2,048 / 1,024 / 512 |

- Bindings: `integration/indoor_decorations.yml` (for `assets_dev/worlds/xeen/models/indoor_decorations.yml`), every
  one `yaw: facing`, **`yaw_offset: -1.570796327`**: the map's facing is the direction the model's front looks
  (glTF +Z), as the P5 hands. Heights are the LOD0 bounds.
- Rows: `integration/rows.txt` (only Radius and Height differ from the reserved lines; names and sprites match).
- Model space: 1 model metre = 100 units; front toward glTF +Z.

## Origins and placement for A6 (checked in game, `build-xeen`, debug `model spawn` at these numbers)

| Plane | Piece | Spot (x, y) | z (what it stands on) | Facing |
|---|---|---|---|---|
| P1 | statue of Fire | (512, -2432) poi:statue | 64, the shelf floor (origin = its own plinth's bottom) | 315 (se) |
| P1 | pedestal | (464, 2048): 208 east of the plate's centre | 256, the arena floor | 180 (faces the plate) |
| P1 | dais | (-4864, 3904) exit:dais | 384, the chamber floor (**P1 has no dais geometry**) | 0 |
| P2 | statue of Air | (-384, -1792) on `platform:plinth` | 224 = plinth top (floor 128 + 96) | 225 (sw) |
| P2 | pedestal | (2528, -2864): 208 north of the plate (2528, -3072) | 256 | 270 (faces the plate) |
| P2 | dais | (3456, 2944) over `platform:dais` | 768 = the disc's base (its top 776) | 0 |
| P3 | statue of Earth | (-512, 1920) on `platform:plinth` | -16 = plinth top (floor -128 + 112) | 135 (nw) |
| P3 | pedestal | (-2496, -1584): 208 north of the plate (-2496, -1792) | -384 | 270 |
| P3 | dais | (-2816, -4736) over `platform:dais` | -768 = the disc's base | 0 |
| P4 | statue of Water | (256, 768) on `platform:plinth` | 128 = plinth top (floor 32 + 96) | 45 (ne) |
| P4 | Drowned Bell | (996, -57): BELL (973, 51) + 110 to the beam's south side | 32, the forecourt floor | 282 |
| P4 | pedestal | (-2880, 1872): 208 north of the plate (-2880, 1664) | 128 | 270 |
| P4 | dais | (-4864, -3712) over `platform:dais` | 192 = the disc's base | 0 |

- **Statues** on A6's plinths: origin at the plinth top's centre (z 0 = plinth top). The fire statue includes its own
  black plinth (448 square, 96 high, a raised plaque 200 x 40 on its front face): origin at the plinth's bottom
  centre; A3's `m38.plaque_fire` belongs on it (row radius 224 makes it solid and clickable).
- **Water**: the jar is in her right hand (front-left from the viewer, x about -132); the carved stream lands about
  356 in front of the plinth centre and ends 84 under the plinth top, i.e. 12 under the basin's water (top 56), inside
  its curb (inner edge about 452). Her tail coils on the plinth top (within about 340 x 360).
- **Air**: wingspan 680 (the wings overhang the 448 plinth by about 116 a side, 300+ above it).
- **Pedestals**: origin bottom centre, radius 48. Front = the sign's reading side; put each beside its plate (208 from
  the plate's centre leaves 32 between the plate's edge and the column) facing the plate, off the walking line.
- **Daises**: origin bottom centre at the disc's base; 10 high over A6's 8, so they cover the geometry disc exactly
  (vertex radius 226 over 224, twelve sides with a vertex on +x like `ring(..., 224, 12)`; any facing that is a
  multiple of 30 keeps the sides aligned). The geometry is hidden until the sleeper wakes: **the decoration needs the
  same condition** (A3/A6: hide it on load until m38_<element>). P1 has no `platform:dais`: either add it as on P2-P4
  or place the model alone on the floor (it is walkable: radius 0, 10 high).
- **Bell**: lying on its side, its axis along the beam (the mouth toward the post, east-north-east at facing 282), its
  back 8 units clear of the beam's south face (the beam's centreline passes 25 north of BELL, half width 36), the
  post 64 clear. Click radius 90 at the origin (A3's `planes.bell`; its event now sits on `platform:bell_frame`).
  It stands on the dry forecourt (floor 32); "half under the water" would need A6's pool there or a `z_offset`.

## Models

- **Fire**: `assets_source/worlds/mm6/models/mm6_fie1.glb` (its MPFB figure; the alpha flame cage, fins and effect
  quads dropped), clip `Standing` frame 0 with both arms aimed up in a V, head raised; 41 built flame tongues (swept
  tapered tubes: a column of 18 round the legs, flanks, back, hair, forearms and palms) fused by a voxel remesh
  (1.4 cm) and smoothed. Dark red stone (`vlcwl3a` grain on a red ramp), ember orange in the crevices with a subtle
  emission map (`map_emit`), black basalt plinth (`6voltyl`).
- **Air**: `mm6_aie1.glb` is only a wind funnel (no figure), so the statue uses the installed MM8 air elemental
  `assets_source/worlds/mm8/models/mm8_m508.glb` (its torso; the wind shells dropped): right arm raised, left arm
  out, head up. Built: a robe lofted from the waist to the plinth (11 twisting folds, streaming 0.26 m back) and two
  feathered wings (three rows of flattened ellipsoid feathers on a leading edge, voxel-fused). White marble
  (`7tws1f` grain, desaturated ramp, grey crevices).
- **Earth**: `assets_source/worlds/mm8/models/mm8_m504.glb` (the rubble mesh dropped), `Standing` frame 0 posed
  seated (thighs forward, shins down, torso leaning 12 degrees, fists on the knees), widened 12 % / deepened 6 %, on a
  rough-hewn block seat. Grey-brown granite (`6voltyl` speckle, warm weathering, dust on top faces). LOD0 is 5,200
  (the source mesh has 4,500 triangles; nothing to keep beyond it).
- **Water**: `assets_source/worlds/mm7/models/mm7_m210.glb`, `Standing` frame 0, the tail coiled round her left side
  (`Tail_04` -70 degrees, `Tail_06`-`Tail_17` -12.5 each) with the fluke raised, the right arm reaching forward;
  a built amphora (lathe and two handles) in her hand and a carved stream (a flattened tube on a parabola, widening,
  with a splash ring and droplets). Green-veined stone (`gn_mtl01` grain, `marb94orui` veins).
- **Pedestals**: a fluted column (24 flutes in the normal map), base and capital, the element's alchemical sign (fire
  and air up, water and earth down, air and earth with a bar) in a ring carved on the top (normal map from a carved
  high patch, plus a tint). **Daises**: the 12-sided disc, chamfered edge, two carved rings, 24 ticks, an inner ring
  and the sign. Stones: fire black glass (`xpfglass`, the Crucible's own glass, with its red veins faintly emissive,
  roughness 0.5 so it stays black in game), air white marble, earth grey granite, water green-veined marble.
- **Bell**: lathe (outer and inner profile, lip ring), crown loop and boss, four raised bands (normal map); lying on
  its side, lip and shoulder on the floor. Bronze (metallic) with verdigris patches, crevices and top faces green.
- Pipeline (`build.sh <id>`): `scripts/build_high.py` (statues) or `scripts/build_props.py` (props) -> high and LOD0
  pieces -> `scripts/lowbake.py` (join, UVs `claude_shared/uv_atlas.py` PartUV + sparrow, normal baked from the high
  pieces, colour / metallic-roughness / emission evaluated on LOD0 from `scripts/stones.json`) ->
  `scripts/finish_maps.py` (miss clean-up, gutter fill last) -> `scripts/export_model.py` (LODs 0.5 / 0.23 / 0.09) ->
  `tools/link_static_model_lods.py` -> winding. `reexport.sh <id>` re-bakes colour only. Configs:
  `scripts/statues.json`, `scripts/props.json`, `scripts/stones.json`; emblems `scripts/emblems.py`; poses previewed
  with `scripts/pose_preview.py` (`posing.py` adds world-axis rotations, `aim` and `lift`, and a bone-chain coil).
- Maps: statues and bell 2048 base colour and normal, 1024 metallic-roughness (and 1024 emission, fire); pedestals
  and daises 1024 / 512. Base colour sRGB luminance within 31-227 everywhere (Khronos 30-243). Atlas use 53-76 %.
  Winding: 0 inverted closed parts on all thirteen.

## Checks

- Review renders (Cycles, eye height 170): `review/statues/statue_<el>_sheet.png` (front, three-quarter, side, close,
  far 2,000), `review/props/` (`earth_props.png`, `water_props.png`, `air_props.png`, `bell.png`, `top_check.png`:
  the four daises from above, the signs reading from the front).
- In game (`build-xeen`, each plane's installed BLV, the pieces spawned with the bindings' yaw at the numbers above,
  tours `work/ingame/p*.yml`, `work/ingame/run_queue.sh`): sheets `review/ingame/p1_sheet.jpg` ... `p4_sheet.jpg`,
  `p4b_p1b_sheet.jpg` (fire pedestal and dais after the roughness fix), `p4c_sheet.jpg` (the bell against the frame).
  Every statue sits on its plinth with its front at the map's facing; the water stream falls into the basin water; no
  model errors in the run logs.

## Known limits

- The fire figure is MM6's smooth MPFB body: up close it reads as a smooth figure among carved flames.
- The water elemental keeps MM7's fish-like face and fins (it is the installed model); the coiled tail's fin sheets
  show collapse facets close up. The jar and stream are one stone with her, a fountain sculpture, not liquid.
- The air robe and wings are built shapes; the feathers read as scales at a distance below about 600.
- The P2/P3/P4 plinths are A6's (their own textures), so plinth and statue stone differ slightly in tone.
- The bell does not lie in water at (996, -57) (dry floor).
