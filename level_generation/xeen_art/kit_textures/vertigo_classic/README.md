# The classic Clouds town kit

Clouds of Xeen's own town walls on the Cloudside maps' half-timbered houses, in place of MM7's Harmondale kits
(the user's decision U-14, 2026-11-24, after a Discord request for "the original building textures ... upscaled
modernized"). The original (XEEN.CC `ftown1.fwl`, `ftown2.fwl`; every Clouds town uses the same set) has cream
plaster panels in a timber frame and a plank door; windows, corner posts, beams and roofs never appear in its towns
and are painted in its style (shingle after the town well `012.obj`, thatch after the straw hut `052.obj`).

## The kit

Installed in `assets_dev/worlds/xeen/textures_x4` (BC7) and `textures_x2`, masters in
`assets_source/worlds/xeen/textures_x4`, registered in `source/textures.yml` (kit `cloudside_town`), classes in
`worlds/xeen/models/texture_classes.yml` (`tools/xeen/texture_classes.py --only ...`; the bays are storey modules in
`tools/xeen/texture_classes_overrides.yml`).

| Role | Texture | Size |
| --- | --- | --- |
| wall, gable | `xvwall` | 128 x 256 |
| window | `xvwin` | 128 x 256 |
| door | `xvdoor` | 128 x 256 |
| double door (one wing, the second leaf mirrored) | `xvdoorw` (the original's double door, `ftown2` frame 8) | 128 x 256 |
| post_left / post_right | `xvcornl` / `xvcornr` | 128 x 256 |
| trim / ridge | `xvbeam` / `xvridge` | 64 x 32 / 32 x 64 |
| roof | `xvshgl` (shingle), `xvthat` (thatch, the houses that had MM7's poor thatch) | 128 x 128 |

The map generators of X1-X7 call `level_generation/projects/xeen/common/classic_kit.py` (`apply(sketch)`) after the
wild-land pass: it puts the kit on every part of an MM7 half-timber kit (plaster, timber, grey, rich, poor), keeps a
wall, door or window a part names itself (the town hall's carved double door), and gives those buildings the stone
footing `cwb1`. A part that names a wall of its own (a wreck's planks, a pagoda, a machine) stays as its generator
made it, and MM7's carved double-door wings on a kit house (the Vertigo Town Hall's `7hhr1d1`) become `xvdoorw`.

Roof edges (the user, 2026-11-24: "the roof outlines deserve some more work"): a box part's gable runs 40 past each
gable end with a barge board 24 high under its edge (Map Studio's `verge` and `barge`, made for this; the board in
the `trim` texture, here `xvbeam`), and gable and hip roofs reach 24 out over the walls (`eaves`), where the part
names neither itself and the overhang meets no other part of its building that stands as high as its roof.

## The stone kit

The towns' stone buildings (temples, guilds, banks, stone farmhouses: district plots built of MM7's `stone` kit) wear
Clouds of Xeen's castle walls (`XEEN.CC fcstl1/fcstl2`), registered under the kit `royal_castle`: `xvswall` (a marbled
sandstone slab between courses of dressed blocks, also the gable), `xvswin` (an arched leaded window, painted in the
style), `xvsdoor` (the original's arched iron-banded door), `xvscornl`/`xvscornr` (a column of quoins at the corner),
with the houses' shingle roofs, oak trim and roof edges. Made from the `xvas*` pieces (`prep_stone.py`, `xtex.py`) by
`compose_stone.py`: the plain bay is every bay's ground, the door and window cut from their paintings by their
outlines and set in, the quoins stretched to the original's proportion. `stone_pilot.py` is the Vertigo pilot (scratch
root, comparison shots). The out-of-town stone structures (the Witch Tower, the pyramid, shrines, ruins) are left as
they are; the original's dark tower set (`ftowr`) would suit the evil towers.

## The tower kit

The dark places (the evil towers, Castle Blackfang, Necropolis) wear Clouds of Xeen's tower walls (`XEEN.CC
ftowr1/ftowr2`), registered under the kit `towers`: `xvtwall` (big dark blocks, three courses to a storey, a seamless
tile: also the corners and gables), `xvtdoor` (the original's plank door with its iron ring between pilasters under a
lintel), `xvtwin` (a barred round-headed slit, painted in the style), dark slate roofs (`xtslate`). Made from the
`xvat*` pieces (`prep_tower.py`, `xtex.py`; brightness at the original's own, luma 43) by `compose_tower.py`.

## Which building takes which kit

`level_generation/projects/xeen/common/classic_kit.yml` (decision U-15): the rules (the half-timber kits' parts:
house; the towns' stone-kit plots: stone; Darkside's plots with MM8 stand-in walls: civic buildings stone, the rest
house, Necropolis tower; special materials kept) and the buildings by name (castles and keeps stone, the evil towers
and Castle Blackfang tower, stand-in shrines and huts). Town walls, gates and watchtowers are not listed and stay.

## Stables and double doors

Stables, caravan yards and the travel pit (`stables_words`, on the maps in `stables_maps`) are rebuilt by
`classic_kit.stables()` as MM8's are: a small closed office with the door and the sign (in the town's kit), an open
pen on posts with a low plank fence and a shingle roof, and the old lean-to shed as a fenced paddock open to the sky
(planks, posts and rails in `xvbeam`). Approved by the user after the X4 pilot, 2026-11-24.

A two-leaf door (`door: {leaves: 2}`) hangs one wing per leaf, the second mirrored: `xvdoorw` (house kit, the
original's town double door), `xvsdoorw` (stone kit, the castle set's arched iron-banded pair, fcstl2 frame 8) and
`xvtdoorw` (tower kit, the tower set's X-braced pair, ftowr2 frame 8). A kit's single door bay on two leaves showed its
frame twice with a gap between (the user, on Necropolis).

## How it was made

1. `prep_refs.py`: `pics/` from the original frames (enlarged) and layout guides of one bay made from them.
2. `xtex.py --project <this folder> gen|finish` (`level_generation/textures_xeen/xtex.py`, with this project's own
   `style` prompt and `squeeze: true` for the bays): the generated pieces of variant A (`xva*`) and of variant B
   (`xvb*`, weathered, set aside). 23 Codex calls in all (`state.json`, `prompts/`, `raw/`).
3. `compose.py`: the kit from the A pieces, so every bay joins every other. Posts (24 texels) and beams (28) are cut
   from the seamless beam tile, half of each at every bay edge; one plaster (the plain bay's, its marks evened) in
   every bay; the door (lintel, jambs, leaf: `DOOR_SOURCE`, measured on its painting) and the window (by its outline)
   set into it. `sheets/compose_facade.png` shows the joins.
4. `derive.py`: the B variant's derived pieces (pilot only).
5. `pilot.py`: the scratch comparison (hard-link roots under `output/xeen_classic_pilot/`, X1 built with each variant,
   the same camera tour, the comparison page from `page_template.html`).

## Not done

- Darkside's town set (log walls, `DARK.CC ftown1/ftown2`) for D1-D6.
- The town walls, gates and wall towers (MM7 `cnb` and others), by the user's choice.
- Darkside's own log-cabin town set (`DARK.CC ftown`): Darkside's towns wear the Clouds kits (U-15).
