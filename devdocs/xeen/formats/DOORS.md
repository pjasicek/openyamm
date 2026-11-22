# Doors: one leaf, two leaves and their pictures

The user (2026-11-20): "double-winged doors displaying just as single winged or tiling the single wings across a big
would-be double-winged door, e.g. castle or dungeon entrance". `oymap audit` runs the check on every Xeen map, indoor
and outdoor (others with `--doors`; `--doors-measure` prints each leaf's numbers). Code:
`openyamm-studio/core/TextureAudit.cpp`; data: `assets_dev/engine/models/texture_classes.yml` and
`assets_dev/worlds/xeen/models/texture_classes.yml`, written by `tools/xeen/texture_classes.py` from the pictures,
their names, the shipped maps and the hand-written `tools/xeen/texture_classes_overrides.yml` (A6 reviews it; the
classes themselves are in [TEXTURE_FIT.md](TEXTURE_FIT.md)).

## Building a double door

- **Indoors, hinged pair:** `{kind: hinged, leaves: 2, surface: <one wing>}`: two leaves, each half the doorway wide,
  the left (seen from the opening's `from` room) on the left jamb, the right on the right jamb, swinging apart away
  from whoever opens them. `surface` is one wing: the left leaf shows it, the right leaf mirrored. Two different wings:
  `pictures: [[{texture: <left wing>, ...}, {texture: <right wing>, ...}]]`. `hinge`, `tile`, `fold`, `travel`, `split`
  are refused on a pair.
- **Indoors, sliding pair:** `{kind: slide_left, leaves: 2}` (or `slide_up`), each leaf one wing through `pictures`
  (`mirror: true` on the second when one texture serves both).
- **Outdoors, building door:** `door: {leaves: 2}` (also with `arch`, and now on a door higher than its walls,
  `door_height` over `wall_height`: X6's gates). Each leaf shows the door picture once, the second mirrored, at the
  picture's own width when the texture classes know it (a 256-wide `egydrlgl` or `swdoora` whole on each leaf; D-91
  §3), else 128 texels across. A door whose picture is a wing and that says no `leaves` is a pair by itself (F2,
  merge point 41), its first leaf the left twin; on a wall whose bays are not listed a pair gets a bay 256 wide where
  the door is.
- **Outdoors, doorway** (`kind: doorway`, a gate in a cliff or a castle front): `leaves: 2` lays the door picture once
  on each half, the right half mirrored (X4's castle gate, `chb1dl` 384 wide).
- Pick the picture for the opening: a wing texture (below) on each leaf of a pair; a single-leaf door picture on a
  leaf up to about 192 wide; never one wing on a leaf over the whole opening, and never a door picture laid at its own
  size across a wider leaf (`tile: true`).

## Which textures are wings

The shipped maps never mirror a leaf: each wing of a double door is a texture of its own, a left and a right twin
(MM8's `gtrldrl`/`gtrldrr`, `gkp103a`/`gkp103b`, `gnecdr1l`/`gnecdr1r`; MM7's `hdr1dl`/`hdr1dr`, `hhm1d`/`hhm1d2`).
Measured over the 203 shipped MM6–MM8 maps: 1,788 door leaves, 475 of them in pairs (two leaves side by side in one
plane); 22 textures stand on the two leaves of a pair with a different texture beside them. Those are wings, unless the
shipped maps also lay them repeated across faces (MM7's `a1b`, `a2b`, `a2c`, `a2d`: a panel family tiled over whole walls
of 7d23, up to 15 copies), which makes them a surface. A further 36 twins named `…l`/`…r` (or `…a`/`…b`), each the
other's mirror image, whose door runs to the meeting edge with the frame or arch on the hinge side only, were looked at
one by one and are wings by the overrides (`chb1dl`/`chb1dr`, `ceb1dl`/`ceb1dr`, `cddl`/`cddr`, `t66b03l`/`t66b03r`,
...; `output/xeen_a1/doors/sheets/`). A texture whose name says door (`door`, `dor`, `gate`, MM6's `t1d3`, MM7's house
doors `hkm2d`) is a single leaf's picture, or a door surface that repeats (`door: tile`: planks, the Hive's ribs) when
its edges meet and it tiles or the shipped maps repeat it.

## Checks (numbers measured on the shipped MM6–MM8 maps)

A leaf indoors is a door record's front: its faces that move (a folding leaf's front stretches), stand upright, move in
their own plane, at least 32 by 32, posed shut, bearing the texture with the most area. Outdoors a leaf is a model face
with a door picture. Copies across = the leaf's width × its texels per unit across ÷ the texture's width.

| Code | Severity | Rule | Shipped |
| --- | --- | --- | --- |
| `doors.tiled` | error | a door picture (single or wing, not `door: tile`) shown more than 1.3 times across its leaf | 2 |
| `doors.half_wing` | error | a wing on a leaf of its own (no leaf beside it in its plane within 16) 192 or more wide | 0 |
| `doors.wing_unmirrored` | error | the two leaves of a pair showing one wing texture the same way round (mirror likeness under 0.85) | 1 |
| `doors.lone_wing` | error (Xeen), warning | outdoors: a wing on a leaf 96 or more wide with no leaf beside it | 5 |
| `doors.part_picture` | error (Xeen), warning | outdoors: a door picture (single or wing) shown under 0.75 times across its leaf (a single picture split over a pair too: D-91 §3) | 2 |
| `doors.narrow_pair` | error (Xeen), warning | outdoors: two leaves under 192 wide together | 3 |
| `doors.off_steps` | error (Xeen), warning | outdoors: a door more than 32 along its wall from the middle of the `..._steps`/`..._stairs` model before it | 0 |

The three shipped findings (`output/xeen_a1/doors_mm678.txt`): MM6's Rich magic shop in outd3 lays `t1d3` twice across
its two 256-wide door faces, and the pyramid in outb3 shows `egydrlgl` unmirrored on both faces of its door; the
shipped maps stay as they are (as D-7.2). The shipped leaves that repeat a picture by accident show it 1.5 times or
more; a leaf stretched at a slightly other scale stays under 1.3.
