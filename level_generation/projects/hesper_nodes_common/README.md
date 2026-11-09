# Shared Lattice node rooms

`node_rooms.py` builds NODE_SKELETON's common rooms for D6, D7 and D16 with the existing
`hesper_stage/blv_kit.py`. D6 is the first complete caller; this module does not install a map or own quest logic.
The authoritative geometry inputs remain `design/kreegan_world/zone4/dungeons/plans_zone4.py`.

The nine common rooms occupy sixteen sectors: vestibule, guard hall (2), ramp, galleries (3), T1, T3,
core (4), vault and tunnel (2). `shell()` builds the entire supplied plan, including its middle-room shells,
64-unit reveals, split portals, six common movers and the two external exit faces. Internal portal splits have
no physical jamb across the opening. Sector 0 remains the compiler's empty sector.

## Import and extend

Run in background Blender. Add `hesper_stage` and this directory to `sys.path`, load the zone4 plan with
`importlib.util`, add the required kit master folders to `blv_kit.FOLDERS`, then:

```python
from node_rooms import NodeRooms, ROLES

b = kit.Builder('hes_d06.blv', ROLES, PROJECT / 'source')
node = NodeRooms(b, zone4.d6,
    splits={'pumps': ('x', [9264]), 'loop': ('y', [8056])},
    doors={'loop to T2': ('t2', 7, 58)},
    floor_cuts={}, accent='cool',
    middle_walls={'pumps': 'cool', 'loop': 'cool'},
    middle_floors={'pumps': 'grate', 'loop': 'grate'}, ambient={'loop': 23})
node.shell()
node.common_contents(zone4, coupling_radius=800)
node.terminal('t2', 81)
# Add this node's machines, hazards, movers, lights, actors and semantic data, then export.
```

The complete D6 author script also cuts floors for its vents and core-entry plates. Common floor holes for the
vestibule trigger, dais, arc strips and heart annulus are automatic. Extra `floor_cuts` are additive rectangles
`(x0, x1, y0, y1)` keyed by parent room. `plate()` clips a pressure surface to each owning sector;
`at(x, y, base)` returns an owning sector for geometry or decorations.

D7 supplies `splits={'assembly': ('x', [9664])}`; D16 supplies `{'graft': ('y', [7500])}`. Supply each middle's
own door-label substrings and `(name, id, event)` tuples. The common door matching is fixed to the skeleton's
plan labels. Both plans retain the same room ids, common coordinates and events. `coupling_radius` is explicit:
D6 requires 800; the skeleton normally uses 1000. Node-specific coupling art/behaviour can replace the shared
coupling surfaces after construction; no boss or hazard behaviour is assumed by this module.
D16 passes `common_contents(..., coupling_geometry=False)` to omit only the three standard coupling stems and
clickable collars, retaining their cables, and supplies hollow capacitor columns instead. The default remains
`True`, preserving D6 geometry.

`common_contents()` adds guard cover and stairs, pylon/niche, readable plates, arc posts/strips/scorch,
cable trunks, T1/T3 consoles, the quartered heart and grated annulus, three couplings and cables, vault racks,
tunnel ribs/channel, three lockers and two cache shelves. Middle dressing, loot payloads and actors stay with
the caller. All machines and furniture are BLV geometry. Add plan lights in the caller with `b.plan_light()`;
ramp fixtures must follow its falling floor. Sort `b.rooms` before assigning actor sector ids and exporting,
as D6 does, because GLB room-node order controls compiled sector ids.

## Contracts

| Content | Event / cog | Door |
|---|---|---|
| Exit / vestibule approach | 50 / 51 | 1 |
| West core / east core / T3 doors | 52 / 53 / 54 | 2 / 3 / 4 |
| Vault / service / tunnel exit | 55 / 56 / 57 | 5 / 6 / none |
| Pylon and niche | 70 / 70 | — |
| Arc strips | 71–73 / 71–73 | — |
| Terminals | 80–82 / 80–82 | — |
| Couplings | 85–87 / 85–87 | — |
| Heart | 90 / 90 | — |
| Readables / lockers | 10–12 / 30, 31, 33 | — |

The resin foot of the heart also clicks as event 90 but has no texture cog, so changing the capacitors leaves
the roots black. Fixture cogs come from the plan's `FIXTURE_COG + group`. The caller owns Lua timers, state,
quest bits, chest indices, arrivals, extra events and the vault mover's texture cog.

The design's 900-high consoles do not fit 448/512-high rooms: the shared console retains its 600 × 300 footprint
and stops 64 below the ceiling. Some simple sectors are below the guide's 100-face target; none needs decorative
subdivision merely to increase its count. D6's native walk scenario checks the dais and the ramp opening centre.

## Greybox fixtures

`author_standins_blender.py` writes our own flat-colour, low-poly GLBs into `standins/`, metres and glTF Y-up.
D6 calls `build()` before creating its map Builder. Seven outputs passed the repository winding checker with
zero inverted closed parts. They are small temporary meshes without LODs, not final art.

Installed here: `hes_lattice_coil`, `hes_lattice_coil_off`, `hes_alarm_pylon_off`. Coil light values exactly
match the plan: radius 640, RGB 205/175/255; the dark pylon retains collision radius 90.
Existing stage `hes_tunnel_lamp` aliases use the colonial amber wall light and remain authoritative.
The generated alternative tunnel fixtures are unbound. Two frost sizes are prepared but unbound/unplaced:
the design gives no dressing positions, and the integrator must supply or approve them.

No runtime or shared stage files are changed by importing this module. Build/stage and game-run locks are
the caller's responsibility; see the [D6 commands](../hesper_d06/README.md).

## D7 wall accents (2026-10-23)

`NodeRooms(..., wall_roles={('t2', 'west'): 'wall', ('t2', 'east'): 'motor'})` overrides the
lower wall band on named room sides. It is opt-in and defaults to an empty mapping. D7 also passes
`accent='motor'` and `middle_walls={'assembly': 'motor', 'core': 'motor'}`. The D6 construction data
(rooms, bounds, portals, triggers, movers, decorations and lights) was compared before/after this addition
in Blender and is identical; see `output/hesper_stage/logs/d07_common_unchanged.log`.

Use `hesper_stage/rebuild_all.sh --scenarios-only` for regression during concurrent builds. Only the
integrator runs the full rebuild; D7 does not rebuild the Crown.

## Walkable room shapes (2026-10-24)

The three node authors now share chamfered vestibule, Guard Hall, terminals and octagonal Power Core shells,
with hipped ceilings 128 above their original wall tops. The core's smaller north-west cut preserves the
service door. Its heart column meets the raised crown; the ramp and its sloping roof retain their original
floor cut. Guard dais flights have eight 16-unit risers on 32-unit treads, with solid parapets closing their
side edges. `validate_shapes()` checks room geometry, event surfaces, mechanisms and decoration centres
against the trimmed footprints; door mouths are asserted during shell authoring. Terminal corner cuts leave
the existing supply shelves intact. The only callers are D6, D7 and D16; the general BLV kit is unchanged.
