# Xeen sphinxes (X6 Desert of the Sphinx: XD-15, FD-02), 2026-11-21

Lane S (session 7, sub-agent `xeen-s7-sphinx`). Two world decorations that replace the visible parts of A5's
sculpted building masses (`output/studio_cal/x6/tools/places.py` `northern_sphinx`, `southern_sphinx`): the
**Northern Sphinx**, a recumbent lion with a human face under a striped nemes, a framed doorway in its breast between
the paws, and the **Southern Sphinx**, buried to its shoulders with the same head (scaled 0.78) and a framed doorway
under its chin. No Meshy, no Codex: **0 credits**.

| Decoration | Row / sprite | Model | Binding height | Collision radius |
|---|---|---|---|---|
| `xeen_sphinx_north` ("sphinx") | 4010 / 27010 | `worlds/xeen/models/xeen_deco_sphinx_north.glb` | 2453.46 | 0 |
| `xeen_sphinx_south` ("sphinx") | 4011 / 27011 | `worlds/xeen/models/xeen_deco_sphinx_south.glb` | 1414.39 | 0 |

Rows in `assets_dev/worlds/xeen/models/decoration_data.txt`, sprites (the engine's `pending` texture) in
`assets_dev/worlds/xeen/rendering/sprite_frame_data_world_decorations.yml`, bindings at the end of
`assets_dev/worlds/xeen/models/decorations.yml` (`yaw: facing`, `lod_pixels: [900, 400, 160]`, no jitter). Sources
`assets_source/worlds/xeen/models/xeen_deco_sphinx_{north,south}.glb` (installed with `tools/install_model.py
--world xeen`); the binding height is the LOD0 bounds' height, so the models stand at 1:1 (1 model metre = 100 units).

## Model space and facing

- Origin = the middle of the door's threshold on the breast face, at the ground. Front (the face) toward glTF +Z.
- glTF +X is the sphinx's own **left** (a viewer's right when facing its face); the engine maps glTF +X to world -X
  at facing 0 (`engine/models/ModelAsset.cpp` `gltfModelPlacement`). Facing 0 faces +Y (north), 90 west, **180
  south, 270 east** (`game/maps/DecorationModelSet.cpp`: the scene's facing is in degrees for decorations).
- Northern: facing **180**; its tail lies along its left flank, which is the east flank at facing 180 (A5's tail).
  Southern: facing **270**. Both verified in game (below).
- Bounds (model units): north x ±922, forward -6,310 (haunch back) to +518 (paw tips), z -53 (skirt) to 2,400;
  south x ±673, forward -2,810 to +64, z -128 (skirt) to 1,286. The skirt sinks below z 0 (48 / 128) so slopes leave
  no gap; the bottom is open.

## Route

Procedural, no source creature for the body (`scripts/sphinx_sdf.py`): a signed distance field in numpy, polygonised
by my own surface-nets code at 6 units (high: 2.73 M / 0.66 M triangles) and at 14 units without stripe relief (the
low mesh's source).
- **Body** (north): smooth union of a rump ellipsoid, folded hind thighs and hind paws along the flanks, a loaf-shaped
  torso, shoulders, two forelegs (upper arm to elbow, forearm lying flat, paw with four toes), a flat-fronted breast
  between the paws curving back to the throat, a neck, and a tail lying along the left flank with the tip curled up.
  South: a shorter body sunk 560 into the sand (haunch dome, hump of back, shoulders, upper breast, neck).
- **Door**: an Egyptian frame (jambs, lintel, cornice) raised 32 off the breast, and the opening cut through it; the
  opening's back faces are removed (`build_mesh.py`), so the doorway is **open at the back** as specified.
- **Head** (shared, `HEAD`): the nemes as front-, side- and top-view profiles intersected (flat top, wings flaring to
  1,380 wide, cloth wrapping the skull behind them), raised gold stripes (period 64, 7 high) by the same band function
  the colour uses, a plain forehead band, a uraeus, two striped lappets falling in front of the shoulders, and a window
  for the face.
- **Face**: the MM6 peasant's head (`assets_source/worlds/mm6/models/mm6_pman.glb`, bind pose), cut below the chin
  and behind what the nemes hides, scaled to 850 chin-to-crown (x0.78 for the south) and set in the window; it keeps
  its own normal map in the bake (carved brows, eyes, lips). The MM9 lion statue and cat were surveyed and not used
  (too faceted).
- **LOD0**: the flat SDF mesh collapse-decimated to 12,465 / 7,000 triangles plus the face (1,716). UVs
  `claude_shared/uv_atlas.py` (PartUV charts on region groups, seam pass, sparrow packing, 4-texel margin); density
  classes: face and breast/door x1.6, paws x1.35, head x1.3, shoulders x1.1, the rest x1.
- **Bakes** (`lowbake.py`, Cycles): tangent normal from the high meshes (the striped SDF surface with the egywalh grain
  as bump, the face with its own normal map), AO over 4 m and 0.6 m with a ground plane.
- **Colour** (`finish_maps.py`, numpy): every atlas texel gets its model position and normal by rasterising LOD0; the
  SDF tells body, nemes and frame apart there. Pale sandstone from `egywalh` (MM6 x4) grain, triplanar at 256 and 960
  units per tile, on a ramp around X6's egy stone, horizontal strata, broad weathering patches, AO darkening, wind-blown
  sand in up-facing crevices, on top faces and in a band at the foot; nemes and lappets gold (218, 172, 86) and dark
  umber (104, 72, 40) stripes (egycol64's colours), weathered toward the stone. Chroma x1.45, gain 0.92 in linear
  space, because the first in-game look (`review/ingame/`) read grey under the cool sky ambient; after it
  (`review/ingame2/`, `ingame3/`) the stone matches A5's egybiga/egywalh. Roughness 0.86-0.97 (gold 0.72), metal 0.
  Nearest-texel gutter fill last on every map.
- **LODs** (`export_sphinx.py`): collapse decimation of LOD0 at 0.5 / 0.24 / 0.08, LOD1-3 hard edges above 60
  degrees, `tools/link_static_model_lods.py`; `check_winding.py`: **0 inverted closed parts** (both).

## Results

| | LOD0 | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|
| North triangles | 14,170 | 7,085 | 3,400 | 1,132 |
| South triangles | 8,714 | 4,356 | 2,091 | 697 |

One material each: base colour 2048 (sRGB), normal 2048 (cooks to 1024), metallic-roughness 1024.
`texture_quality.py` (`work/texture_quality.json`): north atlas 65.0 %, stretch p90 1.13, fragments 0.1 %, density
spread 1.61 (the deliberate front/head classes); south atlas 73.3 %, stretch p90 1.24, fragments 0.1 %, spread 1.54.
Texel density (p50 / p90): north ~25 / 35 texels per metre (4 / 2.9 units per texel: body / breast, door and face),
south ~53 / 74 (1.9 / 1.4 units per texel). sRGB luminance p1 / p50 / p99: 92 / 155 / 181 (north), 92 / 152 / 177
(south). Normal bake misses flattened: 0.3 % / 0.4 % of island texels. Projected-size LOD switches with
`lod_pixels [900, 400, 160]`: LOD1 beyond about 14,300 units (north) and 7,100 (south), LOD3 beyond about 63,000 /
31,000.

## Placement (for A5)

Machine-readable contract: [`integration/sphinx_collision.yml`](integration/sphinx_collision.yml) (written by
`scripts/collision.py` from the installed LOD0 meshes; every outline in model units, world units and X6 cells).

**Northern Sphinx** (`decoration_list_id` 4009, row 4010): origin world **(9216, 10240)**, z = the forecourt
(1,408, FORE_H), cell **(82.0, 44.0)**, **facing 180**. The door plane is the plane through the origin across the
breast (world y 10240, cell y 44.0; A5's door point is at 43.98: put the leaves on y 44.0 or move the origin to
10250). The haunch's back reaches cell y 31.8, the paw tips y 45.0, x 80.2-83.8 (the shoulders bulge to ±922, 26
beyond A5's ±896, between y 38.3 and 41.5).

**Southern Sphinx** (`decoration_list_id` 4010, row 4011): origin world **(-12544, -10240)**, z = the dune (1,536,
SPHINX2_H), cell **(39.5, 84.0)** (the breast's east wall), **facing 270**. It spans x 34.0-39.6, y 82.7-85.3.

**Door rectangles** (model units, in the door plane y = 0 through the origin; x across, z up from the threshold):
- north: opening **x -192..192, z 0..512** (A7's 384 x 512); reveal from y -16 (open behind) to y +52 (the frame's
  front); frame x -264..264, z 0..612, cornice to x ±290, its front at y +78.
- south: opening **x -160..160, z 0..448** (A7's 320 x 448); reveal y -16..+44; frame x -220..220, z 0..532,
  cornice to ±242, front at y +66.
The doorway has no back face: A5's two leaves (BModel faces) must stand in the door plane and close the whole
opening. While the studio's paired-leaf doors stay 256 high, the carrier block's wall must close z 256..512 (north) /
256..448 (south) in the same plane, or the inside of the model shows through (`review/ingame3/18-cn_door.jpg` shows
the open doorway without a carrier).

**Which masses go**: every visible part of `thing:northern_sphinx` (haunch, body, forelegs, chest, nemes, face,
lappets, brow, tail) and of `thing:southern_sphinx` (back, haunch, shoulders, nemes, face) except a minimal block that
carries the door leaves: its front face in the door plane, the leaves in the opening, its other faces inside the
model's breast: north x -380..380, y 0 to -200 (model), z 0..640; south x -300..300, y 0 to -200, z 0..520 (both
hidden behind the breast and frame, which stand 20-52 in front of the plane). The hoard mound (7dec11) at (82.62,
44.7) stands in the open gap between the paws, outside the body ring (the east paw's inner edge is at x 82.84 at
ground level, the paw tips at y 45.0): it stays reachable.

**Collision** (barriers, the studio's `barrier` with `closed: true`):
- `body` ring per sphinx: the footprint at 40 over the ground, pushed out 8 units, simplified to 20 units (75 points
  north, 38 south). It follows the paws' inner edges and the frame's front, so the gap between the paws stays open to
  the door (clear between the paws: 864 at 40 high, 768 at 200 high). Suggested `bottom: -64`, `height` = the model's
  top (2,450 north, 1,300 south) so a flying party cannot enter the ring from the side.
- `head` ring (optional): the nemes's section (north at 1,660, south at 709), for a barrier from about 1,200 / 550 up
  to the head's top, where the wings overhang the shoulders' footprint.
- Tops (`tops` in the yml, mesh maxima): north forearms and paws 427-440 (x ±453..907, y -465..518), breast and frame
  1,389, shoulders 1,700, back 1,107, rump 1,126, head 2,400; south breast 558, shoulders 558, back 454, haunch 528,
  head 1,286. With barriers up to these heights the party could stand on the paws (430) only if A5 adds an invisible
  `platform` there; nothing else of the model is walkable (the decoration has no collision).
- **Facing word**: the studio writes every decoration's facing as 0 today (L4 NOTES, "Words the studio lacked"); the
  sphinxes need 180 and 270, so they wait on A1's decoration facing word (or a scene post-step).
- **Lighting**: `tools/lighting/stale_bakes.py` lists 0 stale bakes now (the decorations are not in X6's scene yet);
  once A5 places them the X6 outdoor bake must be redone (the models cast into it). A5 bakes.

## Checks

- Review renders (Cycles, eye 170, desert sun; textures before the chroma lift): `review/final/` (`north_sheet.jpg`:
  head-on 3,000, three-quarter, side, at the door, face, back three-quarter; `south_sheet.jpg`; `lods_sheet.jpg`
  LOD0-3 of both at 3,000 / 2,000; single views `north_front8000.jpg`, `south_crest.jpg`).
- In game (`build-xeen`, X6 from assets_dev with an overlay of X6's scene through `--extra-mount
  work/ingame/mount`, made by `scripts/ingame_scene.py`; A5's masses still there; tour `scripts/ingame_tour.py`):
  `review/ingame/` (first colour, grey), `review/ingame2/` and `review/ingame3/` (final colour): the head-on views
  from 3,000 and 8,000 and the X4 road, three-quarter, side (tail on the east flank: facing 180 is right), the door
  between the paws (the model's frame stands around A5's door), back; the southern one from the D-35 crest (38, 96)
  toward (31, 81) and toward it, head-on from the east (frame around A5's east door: facing 270 is right), at the door,
  side. Because A5's masses hide most of the models, `ingame3` also places clean copies on open ground (north at cell
  (72, 82), south at (66, 92); `ingame3/clean_sheet.jpg`, `16-cn_q.jpg`): both read as sphinxes in the X6 light. Run
  log: no model or table warnings.

## Rebuild

```sh
cd level_generation/decorations/xeen_sphinx_claude
./build.sh [north] [south] [--review]   # SDF -> meshes + face -> LOD0, UVs, bakes -> maps -> LODs, export, link,
                                         # winding (about 25 min for the north, 15 for the south; Blender through the
                                         # lane lock)
python3 scripts/collision.py             # integration/sphinx_collision.yml + review/collision_*.png
# from the repository root:
python3 tools/install_model.py level_generation/decorations/xeen_sphinx_claude/export/xeen_deco_sphinx_north.glb \
    --world xeen --name xeen_deco_sphinx_north.glb    # and the south
```

Config `scripts/sphinx.json` (bounds, skirt, head placement and scale, door sizes, LOD0 budgets, regions and density
classes); shapes in `scripts/sphinx_sdf.py` (`HEAD`, `north_body`, `south_body`, `door_cut`); `--preview` writes quick
orthographic depth previews (`work/<id>/sdf_*.png`, `scripts/sdf_sheet.py`). The sparrow packing is stochastic, so a
rebuild changes the UV layout (the bakes follow). After a rebuild set the binding heights to the new LOD0 bounds and
delete the old cooked `.oytex` by name. Survey tools: `preview.py` (Workbench views), `head_survey.py` (candidate faces).
`work/` keeps the bakes, maps and `low.blend`; the high meshes are regenerated by the build.

## Known limits

- Texel density is modest on a 68 m model with one 2K atlas (cook cap for world models): at the door the north's
  stone reads soft (2.9 units per texel; the x4 egy BModel textures are 1). A 4K colour map would need a cook sidecar
  (`max_size`), which install_model.py does not write; not done.
- The body is a smooth stylised lion (no muscle or rib detail beyond the stone grain); the face is the MM6 peasant's,
  calm but small inside the nemes window, with dark gaps beside the cheeks.
- The north shoulders reach ±922 (26 beyond A5's ±896) for about 1,600 units of length.
- LOD2/3 of the southern head show decimation blotches at the uraeus and face (only at their switch sizes).
- The review renders in `review/final/` predate the chroma lift (Blender shows the earlier, less saturated stone).
