# MM9 outdoor map to native ODM: playbook

Status: pilot (Isle of Ashes); tunnels and caves under terrain open (below). **The BLV route** (MM9's mesh as one
open-air sector, `outdoor_blv.py`, pilots `../mm9r_isleofashes_blv/` and `../mm9r_sturmford_blv/`) avoids all of
this and measured cheaper. **Decided (user, 2026-11-02): MM9's outdoor maps are built as BLVs; this ODM route is
superseded** and kept as a record.

The route of the [MM9 rework](../../../devdocs/mm9_rework/PLAN.md) from an MM9 DAT wilderness map to a native
OpenYAMM outdoor map: a 128 × 128 height grid of 512-unit cells (heights in steps of 32, at most 8 160) with MM6–MM8
tiles and our terrain materials, plus BModels for the structures. The pilot converter is
[`../mm9r_isleofashes/convert.py`](../mm9r_isleofashes/convert.py) (record:
[`../mm9r_isleofashes/README.md`](../mm9r_isleofashes/README.md)); the next map starts from a copy of it until a
shared package is worth extracting, as `dungeon/` was for the dungeons. Everything builds into the isolated review
root `output/mm9_rework/assets_dev` ([`review_root.py`](review_root.py)).

## What the grid can and cannot hold

MM9's terrain is a free triangle mesh; ours is one height per 512-unit node. Converting means resampling, and the
resample loses everything narrower than a cell:

| MM9 feature | On the grid | Route |
| --- | --- | --- |
| Hills, coasts, broad valleys | fine | resample (top surface at each node) |
| Openings in the terrain mesh under a structure (a castle standing in a hole, a tunnel mouth) | read as sea if nothing is done | **cut-out fill** (below) |
| Paths and switchbacks up a slope (128–300 wide) | lost: their cells slide | **route grading** (below) |
| Structures' feet | gaps where the grid misses MM9's ground | foundation fit, floor clamp |
| Tunnels, caves, arches with terrain above them | impossible: one height per node | **open**, see Tunnels |

The party slides on a terrain triangle whose corners differ by more than 512 (`terrainSlopeTooHigh`, per triangle;
the converter's gating checks the whole cell, which is stricter). MM9 walks on slopes under about 50° at its own
scale, so a narrow path at 30° across a 45° hillside is walkable in MM9 and a slide cell here.

## Steps

1. **Terrain.** Rasterize the visible terrain world models (terrain-folder textures; water volumes and the VisBSP and
   PhysicsBSP helpers excluded) at the nodes and at 64-unit fine samples. Transform `x = LT.x * 2.56 - offset_x`,
   `y = LT.z * 2.56 - offset_y`, `z = (LT.y - sea) * 2.56`, offsets on a cell boundary. Keep the seabed heights
   for the diving decision.
2. **Structures before heights.** Load the structure faces (PhysicsBSP, fort walls, world objects, the non-terrain
   faces of terrain models) and cluster them into BModels first: the cut-out fill, foundation fit and floor clamp
   need them.
3. **Cut-outs** (`fill_cutouts`). An uncovered region of the fine raster that does not reach the grid's edge is a
   hole MM9 cut into its terrain for a structure, never sea. Each sample takes the lowest upward structure face over
   it minus 8; samples no floor covers are filled from the rim. Without this, the Isle of Ashes castle (a
   2 000-unit opening) stood in water pits with gaps under its walls.
4. **Coast.** A node is dry when land lies within 128 of it; shore tiles follow the wet corners; diagonal wet pairs
   are dried.
5. **Foundations and floors.** Nodes under a structure's lowest vertices meet them (only where those met MM9's
   ground); nodes within a cell of a floor MM9 shows go 8 under it. These nodes are pinned for the next step.
6. **Route grading.** Two sources of route cells, solved together:
   - **Trails.** MM9's painted map (`worlds/mm9/ui/maps/<map>.pcx`, bounds and flips in `catalog.yml`, in the old
     map's frame) draws paths, beaches and plazas pale (any channel ≥ 180; rock is darker). A cell that is at least
     20 % painted trail on MM9-walkable ground, and slides on the grid, is a trail cell (`painted_trails`).
   - **Cuts.** For each MM9 walkable component (8-connected fine samples; a cell belongs to it when 20 % of the
     cell is that component, so 128-wide paths count), the grid's walkable parts inside it are joined to the largest
     by the shortest chain of the component's cells; the slide cells on that chain are cuts. A break can be several
     cells long (a path up a slope to a plateau): checking only single cells between two parts misses it.

   Each route cell gets corner targets from its path samples: the principal axis of the samples is the path's
   direction, the rise along it is fitted, and the corners take the path's height there, level across the path. A
   cell can hold two walkable levels (a hill path above a valley floor): take the samples of one component only.
   Then all route cells are solved at once (`grade_routes`): route nodes start at the mean of their cells' targets,
   and each cell is pulled into a 480 window around its mean until nothing moves; pinned nodes stay and the window
   moves to include them; cells next to the sea are skipped. Grading cells one at a time and re-checking oscillates
   (neighbours share corners and undo each other: 134 edits for 17 cells on the isle).
7. **Tiles and materials.** One tile per land cell from the MM9 texture covering most of its land; the world's
   material file and `tools/terrain_materials.py weights`.
8. **Shared tables.** Exits and arrivals are moved into the frame under the review tables lock
   (`dungeon/tables.py locked`). Rewrite only this map's side of a row and keep the rest as the review root has it:
   another conversion may own the other side (rebuilding the isle once put `verhoffinruins.odm` back over the
   dungeon's `verhoffinruins.blv`, and the game refused the whole table).

## Checks

- `work/gating.png` and `gating.json`: MM9-walkable against grid-walkable, remaining cuts. Grading opens some
  ground MM9 blocks (`opened`); look at the larger spots.
- `work/route_fixes.json`: every graded cell, trail or cut, corners before and after.
- Painted-map overlay: the art resampled into the map frame with slide cells crossed; trails should run clear.
- Walk the trails (`make_trail_walk.py`): a headless scenario walks the party along MM9's trails between named
  endpoints (the cheapest line on MM9-walkable ground, preferring painted trail), one ~400-unit segment at a time.
  A straight segment can clip a steep cell's corner the party would walk round: check a blocked segment's cells.
- The map's own scenarios (chests, story) after every terrain change.
- Screenshot tours at the user's reported positions (`debug.screenshot_tour_path`; positions are the party's feet,
  pitch in radians in the tour).

## Tunnels and caves under terrain (open)

The Isle of Ashes tunnel is a complete structure inside a hill: floor at 286–335, walls, roof at 808–859, winding
2 500 units east to west with a branch north; MM9's terrain mesh runs over it as the hill (up to 2 500). One height per
node cannot leave room for it. Options, to be chosen with the user:

- **Trench and hill patch (converter only).** Lower the nodes over the tunnel's footprint under its floor and lay
  MM9's hill mesh over those cells as a BModel (clipped to the cells, its border on the grid's edges, a skirt
  against cracks from the rendered terrain's smoothing). The terrain stays inside the hill, hidden; trench cells take
  a rock tile so no grass grows under the tunnel floor. The patch shows MM9 textures, not our terrain materials.
- **Terrain holes (engine).** A per-cell hole flag: no terrain drawn, collided, decorated or lit in those cells; the
  same MM9 hill patch fills them. Cleaner, reusable for every MM9 canyon, cave and arch, but a shared engine feature
  across rendering, collision, grass, bakes and the minimap.
- **Cave mouth into a BLV.** The plan's fallback; breaks continuity for a short tunnel.
