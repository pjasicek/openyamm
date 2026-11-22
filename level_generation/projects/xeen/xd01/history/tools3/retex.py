"""Texture pass 3 of XD-01: one-off edit of rooms.yml and objects.yml (exact string swaps, each counted)."""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[6])  # the repository root
import sys
L = _REPO_ROOT + '/devdocs/xeen/briefs/xd01/L4/'

def swap(text, old, new, count):
    n = text.count(old)
    if n != count:
        sys.exit(f'expected {count} of {old!r}, found {n}')
    return text.replace(old, new)

r = open(L + 'rooms.yml').read()
# ---- themes ----
r = swap(r, '''  - id: theme:aisle
    wall: {texture: bwoodb1, size: [256, 256]}
    bands:
      - {height: 160, surface: {texture: cbmxbrck, size: [128, 128]}}
    ends: {length: 32, surface: {texture: d6ebeam, size: [32, 256]}}
    floor: {texture: tfb07, size: [128, 128]}
    ceiling: {texture: d2ceil2, size: [256, 256]}
    reveal: {texture: d6ebeam, size: [32, 256]}
    door: {texture: bwooda2, size: [256, 256], fit: true}
    notes: "The north-east aisle, a lean-to shed against the warehouse: the outer weatherboard (bwoodb1) over a brick footing (cbmxbrck), dark log posts in the corners (MM6 d6ebeam), stone flags underfoot (tfb07) running on to the cellar stair, boards overhead."''',
'''  - id: theme:aisle
    wall: {texture: t66floor, size: [128, 128]}
    bands:
      - {height: 256, surface: {texture: t66b01, size: [128, 256]}}
    ends: {length: 32, surface: {texture: t66abc10a, size: [32, 128]}}
    floor: {texture: t66flr2, size: [128, 128]}
    ceiling: {texture: t66roof, size: [128, 128]}
    reveal: {texture: t66abc10a, size: [32, 128]}
    door: {texture: gkp103a, size: [128, 256], fit: true}
    notes: "The north-east aisle, a lean-to shed against the warehouse, in the Pirate Outpost's storeroom wood (MM8 d06): the panelled wainscot (t66b01) to 256 with upright planks above (t66floor, which d06 lays on walls too), posts in the corners (t66abc10a), flagstones underfoot (t66flr2) running on to the cellar stair, the beamed roof (t66roof)."''', 1)
r = swap(r, '''    floor: {texture: tfb07, size: [128, 128]}
    ceiling: {texture: cbrdbrck, size: [64, 64]}
    reveal: {texture: d1medbw, size: [128, 128]}
    door: {texture: bwooda2, size: [256, 256], fit: true}
    notes: "Old cellar brick: weathered mixed brick (MM6 cbmxbrck) on a damp stone footing (d1smbw), dark stone slab floor (MM7 tfb07), red brick vaults (cbrdbrck), old stone in the doorways (d1medbw), grilled plank doors (MM8 bwooda2). Cellar stair and shipping room."''',
'''    floor: {texture: d1medbw, size: [128, 128]}
    ceiling: {texture: cbrdbrck, size: [64, 64]}
    reveal: {texture: d1medbw, size: [128, 128]}
    door: {texture: beemdorc, size: [128, 256], fit: true}
    notes: "Old cellar brick: weathered mixed brick (MM6 cbmxbrck) on a damp stone footing (d1smbw), the Free Haven Sewer's block stone underfoot and in the doorways (d1medbw), red brick vaults (cbrdbrck), MM6 plank doors (beemdorc). Cellar stair and shipping room."''', 1)
r = swap(r, '''    wall: {texture: d1medbw, size: [128, 128]}
    floor: {texture: 7wtrtyl, size: [128, 128]}
    ceiling: {texture: d1smbw, size: [128, 128]}
    reveal: {texture: d1medbw, size: [128, 128]}
    door: {texture: gcstdoor, size: [128, 256], fit: true}
    notes: "River culvert: mossy river stone (MM6 d1medbw, d1smbw), moving water underfoot (MM7 7wtrtyl, the liquid shader, on floors marked water), an iron door (gcstdoor)."''',
'''    wall: {texture: d1wldle2, size: [256, 256]}
    floor: {texture: swprrf3, size: [128, 128]}
    ceiling: {texture: d1wle, size: [256, 256]}
    reveal: {texture: d1medbw, size: [128, 128]}
    door: {texture: d8dorf, size: [128, 256], fit: true}
    notes: "River culvert, in the Free Haven Sewer's set (MM6 sewer.blv): its mossy block walls (d1wldle2, d1wldle3) and roof stone (d1wle), the walkway stone (d1medbw), its sewage underfoot (swprrf3, the liquid shader, on floors marked water), an MM6 iron door (d8dorf)."''', 1)
r = swap(r, '''    wall: {texture: lilbrick, size: [128, 128]}
    floor: {texture: thjophayqa, size: [128, 128]}
    ceiling: {texture: d2ceil2, size: [256, 256]}
    reveal: {texture: cbeam5, size: [32, 256]}
    door: {texture: tdoora, size: [256, 256], fit: true}
    notes: "Joe's covered loading dock on the lane: the neighbours' old brick (lilbrick) on three sides, the warehouse's weatherboard front (bwoodb1, a wall entry) with a pair of shuttered windows (bwoodb4) on the fourth, the lane's cobbles underfoot (thjophayqa), the canopy's boards overhead."''',
'''    wall: {texture: t66c01a, size: [128, 256]}
    floor: {texture: t66flr2, size: [128, 128]}
    ceiling: {texture: t66floor, size: [128, 128]}
    reveal: {texture: t66abc10a, size: [32, 128]}
    door: {texture: t66b03l, size: [128, 256], fit: true}
    notes: "Joe's covered loading dock on the lane, in the Pirate Outpost's set (MM8 d06): the neighbours' brick (t66c01a, d06's hall brick) on three sides, the warehouse's plank front (t66floor, a wall entry) with its boarded shutters (gt003b) on the fourth, the lane's flagstones underfoot (t66flr2), the canopy's planks overhead."''', 1)
r = swap(r, '''    floor: {texture: straw, size: [256, 256]}
    ceiling: {texture: d2ceil2, size: [256, 256]}
    reveal: {texture: d1medbw, size: [128, 128]}
    door: {texture: cbmxbrck, size: [128, 128]}
    notes: "Cellar brick under a plank ceiling (d2ceil2), spilt chaff on the floor (MM6 straw). Its door surface is the brick, so the stash's sliding door shows nothing until it is opened."''',
'''    floor: {texture: straw, size: [256, 256]}
    ceiling: {texture: d1ceil1, size: [256, 256]}
    reveal: {texture: d1medbw, size: [128, 128]}
    door: {texture: cbmxbrck, size: [128, 128]}
    notes: "Cellar brick under the Free Haven Sewer's plank ceiling (d1ceil1), spilt chaff on the floor (MM6 straw). Its door surface is the brick, so the stash's sliding door shows nothing until it is opened."''', 1)
r = swap(r, '''    wall: {texture: bmplnk, size: [256, 256]}
    ends: {length: 32, surface: {texture: d6ebeam, size: [32, 256]}}
    floor: {texture: tfb07, size: [128, 128]}
    ceiling: {texture: d2ceil2, size: [256, 256]}
    reveal: {texture: d6ebeam, size: [32, 256]}
    door: {texture: tdoora, size: [256, 256], fit: true}
    notes: "Warehouse, bay variant: dark tarred upright boards (MM6 bmplnk) over a brick footing (the bay's own band), stone flags where the carts come in (tfb07), joists and boards overhead (MM6 d2ceil2), a dark log post in every corner (MM6 d6ebeam), barn doors of barred planks (tdoora). Also the loading ramp (no band: a band needs a level floor)."''',
'''    wall: {texture: t66floor, size: [128, 128]}
    ends: {length: 32, surface: {texture: t66abc10a, size: [32, 128]}}
    floor: {texture: t66flr2, size: [128, 128]}
    ceiling: {texture: t66roof, size: [128, 128]}
    reveal: {texture: t66abc10a, size: [32, 128]}
    door: {texture: t66b03l, size: [128, 256], fit: true}
    notes: "Warehouse, bay variant, as the Pirate Outpost's storerooms (MM8 d06) are built: upright planks (t66floor) over the panelled wainscot (t66b01, the bay's own band, 256: one picture high), flagstones where the carts come in (t66flr2), the beamed roof (t66roof), a post in every corner (t66abc10a), d06's braced plank doors (t66b03l). Also the loading ramp (no band: a band needs a level floor)."''', 1)
r = swap(r, '''    wall: {texture: grtop, size: [128, 256]}
    floor: {texture: bembllg, size: [256, 256]}
    ceiling: {texture: d2ceil2, size: [256, 256]}
    reveal: {texture: cbeam5, size: [32, 256]}
    door: {texture: vh3door, size: [128, 256], fit: true}
    notes: "Joe's office: whitewashed plaster under a moulded cornice (MM6 grtop) over a wainscot of plank panels (MM6 bemhwal: the office's own band), warm board floor (MM6 bembllg), boards overhead, a studded plank door (vh3door). The only white room of the map: Joe keeps up appearances where the customers come."''',
'''    wall: {texture: t66d01, size: [128, 256], scale: 1.5}
    floor: {texture: t66floor, size: [128, 128]}
    ceiling: {texture: t66roof, size: [128, 128]}
    reveal: {texture: t66abc10a, size: [32, 128]}
    door: {texture: t66b03r, size: [128, 256], fit: true}
    notes: "Joe's office, as the Pirate Outpost's better rooms (MM8 d06): cream plaster under a cornice over a carved panel wainscot (t66d01, one picture from floor to ceiling, 384 at scale 1.5), plank floor (t66floor), the beamed roof (t66roof), a braced plank door (t66b03r). The only plastered room of the map: Joe keeps up appearances where the customers come."''', 1)
r = swap(r, '''    floor: {texture: straw, size: [256, 256]}
    ceiling: {texture: cbmxbrck, size: [128, 128]}
    reveal: {texture: d1medbw, size: [128, 128]}
    door: {texture: bwooda2, size: [256, 256], fit: true}
    notes: "A slime pen''', '''    floor: {texture: straw, size: [256, 256]}
    ceiling: {texture: cbmxbrck, size: [128, 128]}
    reveal: {texture: d1medbw, size: [128, 128]}
    door: {texture: beemdorc, size: [128, 256], fit: true}
    notes: "A slime pen''', 1)
r = swap(r, '''    floor: {texture: tfb07, size: [128, 128]}
    ceiling: {texture: cbmxbrck, size: [128, 128]}
    reveal: {texture: d1medbw, size: [128, 128]}
    door: {texture: bwooda2, size: [256, 256], fit: true}
    notes: "Cistern brick: red brick (MM6 cbrdbrck) over a mossy stone course where the water has stood (d1smbw), stone slab floor, a mixed-brick dome (cbmxbrck), old stone reveals; the pen gates are grilled plank doors (no barred-gate texture exists)."''',
'''    floor: {texture: d1medbw, size: [128, 128]}
    ceiling: {texture: cbmxbrck, size: [128, 128]}
    reveal: {texture: d1medbw, size: [128, 128]}
    door: {texture: beemdorc, size: [128, 256], fit: true}
    notes: "Cistern brick: red brick (MM6 cbrdbrck) over a mossy stone course where the water has stood (d1smbw), the Free Haven Sewer's block stone underfoot and in the reveals (d1medbw), a mixed-brick dome (cbmxbrck); the pen gates are iron bars (movers)."''', 1)
r = swap(r, '''    wall: {texture: beams1v9u9, size: [128, 128], scale: 2}
    floor: {texture: bmplnk, size: [256, 256]}
    ceiling: {texture: d2ceil1, size: [256, 256]}
    reveal: {texture: d6ebeam, size: [32, 256]}
    door: {texture: tdoora, size: [256, 256], fit: true}
    notes: "The grain hall: the old river-side store's half-timbered walls, dark oak frames with rubble stone between them (MM6 beams1v9u9, one bay every 256), dark plank floor (bmplnk), open rafters overhead (MM6 d2ceil1). No band: the hall's floor sags toward its gutter, and a band needs a level floor."''',
'''    wall: {texture: t66c01a, size: [128, 256]}
    floor: {texture: t66floor, size: [128, 128]}
    ceiling: {texture: t66roof, size: [128, 128]}
    reveal: {texture: t66abc10a, size: [32, 128]}
    door: {texture: t66b03l, size: [128, 256], fit: true}
    notes: "The grain hall, as the Pirate Outpost's big hall (MM8 d06): its brick walls (t66c01a), plank floor (t66floor), the beamed roof (t66roof), posts and beams (t66abc10a). No band: the hall's floor sags toward its gutter, and a band needs a level floor; the loft's front is d06's panelled wainscot (t66b01)."''', 1)

# ---- rooms ----
r = swap(r, "top_surface: {texture: bmplnk, size: [256, 256]}, base: 112", "top_surface: {texture: crcn96, size: [64, 64]}, base: 112", 3)
r = swap(r, "slope: {to: -192, toward: north, steps: 6, riser: {texture: d1smbw, size: [128, 128]}, tread: {texture: tfb07, size: [128, 128]}}",
            "slope: {to: -192, toward: north, steps: 6, riser: {texture: d1smbw, size: [128, 128]}, tread: {texture: d1medbw, size: [128, 128]}}", 1)
r = swap(r, "slope: {to: -384, toward: north, steps: 6, riser: {texture: d1smbw, size: [128, 128]}, tread: {texture: tfb07, size: [128, 128]}}",
            "slope: {to: -384, toward: north, steps: 6, riser: {texture: d1smbw, size: [128, 128]}, tread: {texture: d1medbw, size: [128, 128]}}", 1)
r = swap(r, "floor: {texture: 7wtrtyl, size: [128, 128]}, lower: {texture: d1smbw, size: [128, 128]}, wall: {texture: d1medbw, size: [128, 128]}, upper: {texture: d1smbw, size: [128, 128]}, ceiling: {texture: d1smbw, size: [128, 128]}",
            "floor: {texture: swprrf3, size: [128, 128]}, lower: {texture: d1wldle3, size: [256, 256]}, wall: {texture: d1wldle2, size: [256, 256]}, upper: {texture: d1wle, size: [256, 256]}, ceiling: {texture: d1wle, size: [256, 256]}", 2)
r = swap(r, '''        surface: {texture: 7slimywtr, size: [128, 128]}
        notes: "The drain pool, sunk 64, slime-green water."''', '''        surface: {texture: swprrf3, size: [128, 128]}
        notes: "The drain pool, sunk 64, slime-green water."''', 1)
r = swap(r, '''        surface: {texture: tfb07, size: [128, 128]}
        notes: "A dry ledge''', '''        surface: {texture: d1medbw, size: [128, 128]}
        notes: "A dry ledge''', 1)
r = swap(r, '''        edge: {texture: d1smbw, size: [128, 128]}
        surface: {texture: d1lggrt, size: [256, 256], fit: true}''', '''        edge: {texture: d1wldle2, size: [256, 256]}
        surface: {texture: d1lggrt, size: [256, 256], fit: true}''', 1)
# feed store joists: d6ebeam -> cbeam5 (the sewer's beam)
r = swap(r, '''        bottom: -8
        surface: {texture: d6ebeam, size: [32, 256]}''', '''        bottom: -8
        surface: {texture: cbeam5, size: [32, 256]}''', 2)
r = swap(r, "surface: {texture: slim423fqx, size: [32, 32], scale: 4}, notes: \"The gutter", "surface: {texture: swprrf3, size: [128, 128]}, notes: \"The gutter", 1)
r = swap(r, "rise: 320, surface: {texture: bmplnk, size: [256, 256]}, top_surface: {texture: straw", "rise: 320, surface: {texture: t66floor, size: [128, 128]}, top_surface: {texture: straw", 2)
r = swap(r, "rise: 592, surface: {texture: d6ebeam, size: [32, 256]}, top_surface: {texture: d6ebeam, size: [32, 256]}", "rise: 592, surface: {texture: t66abc10a, size: [32, 128]}, top_surface: {texture: t66abc10a, size: [32, 128]}", 6)
r = swap(r, "surface: {texture: t66cratev, size: [128, 128]}, top_surface: {texture: t66crateh, size: [128, 128]}", "surface: {texture: ch002a, size: [64, 64], fit: true}, top_surface: {texture: ch002a, size: [64, 64], fit: true}", 4)
r = swap(r, "surface: {texture: crate_w64, size: [64, 64], scale: 2}, top_surface: {texture: crate_w64, size: [64, 64], scale: 2}, base: 192}", "surface: {texture: gt001a, size: [64, 64], fit: true}, top_surface: {texture: gt001a, size: [64, 64], fit: true}, base: 192}", 3)
r = swap(r, "rise: 128, surface: {texture: crate_w64, size: [64, 64], scale: 2}, top_surface: {texture: crate_w64, size: [64, 64], scale: 2}, notes: A crate left", "rise: 128, surface: {texture: gt001a, size: [64, 64], fit: true}, top_surface: {texture: gt001a, size: [64, 64], fit: true}, notes: A crate left", 1)
r = swap(r, "rise: 72, notes: Rail post on the loft's edge.}", "rise: 72, surface: {texture: t66abc10a, size: [32, 128]}, top_surface: {texture: t66abc10a, size: [32, 128]}, notes: Rail post on the loft's edge.}", 1)
for x in (640, 1080, 1320, 1600, 1840):
    r = swap(r, "{at: [%d, 2256], size: [16, 16], rise: 72}" % x, "{at: [%d, 2256], size: [16, 16], rise: 72, surface: {texture: t66abc10a, size: [32, 128]}, top_surface: {texture: t66abc10a, size: [32, 128]}}" % x, 1)
r = swap(r, "rise: 96, surface: {texture: bmplnk, size: [256, 256]}, top_surface: {texture: straw", "rise: 96, surface: {texture: t66floor, size: [128, 128]}, top_surface: {texture: straw", 1)
r = swap(r, "edge: {texture: bwooda2, size: [256, 256]}\n        surface: {texture: straw", "edge: {texture: t66b01, size: [128, 256]}\n        surface: {texture: straw", 1)
r = swap(r, "edge: {texture: bwoodb1, size: [256, 256]}\n        surface: {texture: d2ceil1, size: [256, 256]}", "edge: {texture: t66floor, size: [128, 128]}\n        surface: {texture: t66roof, size: [128, 128]}", 1)
r = swap(r, "sides: {height: 40, thickness: 12, surface: {texture: d6ebeam, size: [32, 256]}, top_surface: {texture: d6ebeam, size: [32, 256]}}, riser: {texture: bmplnk, size: [256, 256]}, tread: {texture: bembllg, size: [256, 256]}",
            "sides: {height: 40, thickness: 12, surface: {texture: t66abc10a, size: [32, 128]}, top_surface: {texture: t66abc10a, size: [32, 128]}}, riser: {texture: t66abc11a, size: [128, 32]}, tread: {texture: t66floor, size: [128, 128]}", 1)
r = swap(r, "surface: {texture: d6ebeam, size: [32, 256]}", "surface: {texture: t66abc10a, size: [32, 128]}", 10)
r = swap(r, "rise: 128, surface: {texture: crate_w64, size: [64, 64], scale: 2}, top_surface: {texture: crate_w64, size: [64, 64], scale: 2}}", "rise: 128, surface: {texture: gt001a, size: [64, 64], fit: true}, top_surface: {texture: gt001a, size: [64, 64], fit: true}}", 2)
r = swap(r, "rise: 72, surface: {texture: bmplnk, size: [256, 256]}, top_surface: {texture: bembllg, size: [256, 256]}", "rise: 72, surface: {texture: t1books1, size: [128, 128]}, top_surface: {texture: t1books1, size: [128, 128]}", 2)
r = swap(r, "surface: {texture: bookcas1, size: [128, 128], fit: true}", "surface: {texture: t66d01j, size: [128, 256], fit: true}", 1)
r = swap(r, '''    bands:
      - {height: 128, surface: {texture: bemhwal, size: [256, 128]}}
''', '', 1)
r = swap(r, "surface: {texture: 7t1cab, size: [128, 256], fit: true}, end_surface: {texture: bemhwal, size: [256, 128]}, top_surface: {texture: bembllg, size: [256, 256]}",
            "surface: {texture: t1cab, size: [128, 256], fit: true}, end_surface: {texture: t1books1, size: [128, 128]}, top_surface: {texture: t1books1, size: [128, 128]}", 1)
r = swap(r, "surface: {texture: ironn7dmbs, size: [128, 128]}, top_surface: {texture: ironn7dmbs, size: [128, 128]}", "surface: {texture: gt002c, size: [64, 64], fit: true}, top_surface: {texture: gt002g, size: [64, 64], fit: true}", 1)
r = swap(r, "rise: 40, surface: {texture: bmplnk, size: [256, 256]}, top_surface: {texture: bembllg, size: [256, 256]}", "rise: 40, surface: {texture: t1books1, size: [128, 128]}, top_surface: {texture: t1books1, size: [128, 128]}", 1)
r = swap(r, '''    bands:
      - {height: 192, surface: {texture: cbmxbrck, size: [128, 128]}}''', '''    bands:
      - {height: 256, surface: {texture: t66b01, size: [128, 256]}}''', 1)
r = swap(r, "rise: 16, surface: {texture: crate_w64, size: [64, 64], scale: 2}, top_surface: {texture: bembllg, size: [256, 256]}", "rise: 16, surface: {texture: gt003a, size: [64, 64], scale: 2}, top_surface: {texture: t66floor, size: [128, 128]}", 1)
r = swap(r, "rise: 192, surface: {texture: crate_w64, size: [64, 64], scale: 2}, top_surface: {texture: crate_w64, size: [64, 64], scale: 2}}", "rise: 192, surface: {texture: gt001a, size: [64, 64], fit: true}, top_surface: {texture: gt001a, size: [64, 64], fit: true}}", 2)
r = swap(r, "        surface: {texture: bwoodb1, size: [256, 256]}\n        panels:", "        surface: {texture: t66floor, size: [128, 128]}\n        panels:", 1)
r = swap(r, "surface: {texture: bigsign, size: [128, 64], fit: true}", "surface: {texture: sign01-1, size: [256, 128], fit: true}", 1)
r = swap(r, "surface: {texture: bwoodb4, size: [256, 256], fit: true}", "surface: {texture: gt003b, size: [64, 64], fit: true}", 1)
r = swap(r, "rise: 128, surface: {texture: crate_w64, size: [64, 64], scale: 2}, top_surface: {texture: crate_w64, size: [64, 64], scale: 2}}", "rise: 128, surface: {texture: gt001a, size: [64, 64], fit: true}, top_surface: {texture: gt001a, size: [64, 64], fit: true}}", 0)
r = swap(r, "{at: [336, -1000], size: [192, 128], rise: 128, surface: {texture: crate_w64, size: [64, 64], scale: 2}, top_surface: {texture: crate_w64, size: [64, 64], scale: 2}}", "{at: [336, -1000], size: [192, 128], rise: 128, surface: {texture: gt001a, size: [64, 64], fit: true}, top_surface: {texture: gt001a, size: [64, 64], fit: true}}", 0)
r = swap(r, "surface: {texture: crate_w64, size: [64, 64], scale: 1.5}, top_surface: {texture: crate_w64, size: [64, 64], scale: 1.5}", "surface: {texture: gt001a, size: [64, 64], fit: true}, top_surface: {texture: gt001a, size: [64, 64], fit: true}", 2)
r = swap(r, "surface: {texture: beamplnv, size: [32, 256]}, top_surface: {texture: beamplnv, size: [32, 256]}", "surface: {texture: t66abc10a, size: [32, 128]}, top_surface: {texture: t66abc10a, size: [32, 128]}", 1)
r = swap(r, "rise: 24, surface: {texture: bmplnk, size: [256, 256]}, top_surface: {texture: straw", "rise: 24, surface: {texture: crcn96, size: [64, 64]}, top_surface: {texture: straw", 1)
r = swap(r, "top_surface: {texture: slim423fqx, size: [32, 32], scale: 4}, notes: \"The pair's feeding trough", "top_surface: {texture: swprrf3, size: [128, 128]}, notes: \"The pair's feeding trough", 1)
r = swap(r, "slope: {to: 64, toward: west, steps: 2, riser: {texture: cbeam5, size: [32, 256]}, tread: {texture: bembllg, size: [256, 256]}}", "slope: {to: 64, toward: west, steps: 2, riser: {texture: t66abc11a, size: [128, 32]}, tread: {texture: t66floor, size: [128, 128]}}", 1)
r = swap(r, "rise: 32, surface: {texture: cbeam5, size: [32, 256]}, top_surface: {texture: bwooda1, size: [256, 256]}, bottom_surface: {texture: bwooda1, size: [256, 256]}", "rise: 32, surface: {texture: cbeam5, size: [32, 256]}, top_surface: {texture: crcn96, size: [64, 64], scale: 2}, bottom_surface: {texture: crcn96, size: [64, 64], scale: 2}", 1)
r = swap(r, "rise: 256, surface: {texture: crate_w64, size: [64, 64], scale: 2}, top_surface: {texture: crate_w64, size: [64, 64], scale: 2}, notes: Crates addressed", "rise: 256, surface: {texture: crcn96, size: [64, 64], scale: 2}, top_surface: {texture: crcn96, size: [64, 64], scale: 2}, notes: Crates addressed", 1)
r = swap(r, "rise: 128, surface: {texture: crate_w64, size: [64, 64], scale: 2}, top_surface: {texture: crate_w64, size: [64, 64], scale: 2}, base: 256}", "rise: 128, surface: {texture: crcn96, size: [64, 64], scale: 2}, top_surface: {texture: crcn96, size: [64, 64], scale: 2}, base: 256}", 1)
r = swap(r, "rise: 72, surface: {texture: bwooda1, size: [256, 256]}, top_surface: {texture: bembllg, size: [256, 256]}", "rise: 72, surface: {texture: crcn96, size: [64, 64], scale: 2}, top_surface: {texture: crcn96, size: [64, 64], scale: 2}", 1)
r = swap(r, "        edge: {texture: bwooda1, size: [256, 256]}\n        surface: {texture: d2ceil2, size: [256, 256]}", "        edge: {texture: crcn96, size: [64, 64], scale: 2}\n        surface: {texture: d1ceil1, size: [256, 256]}", 1)
r = swap(r, "threshold: {texture: cbeam5, size: [32, 256]}", "threshold: {texture: t66abc11a, size: [128, 32]}", 2)
open(L + 'rooms.yml', 'w').write(r)

o = open(L + 'objects.yml').read()
o = swap(o, "surface: {texture: tdoora, size: [256, 256], fit: true}", "surface: {texture: t66b03l, size: [128, 256], fit: true}", 2)
o = swap(o, "surface: {texture: gcstdoor, size: [128, 256], fit: true}", "surface: {texture: d8dorf, size: [128, 256], fit: true}", 1)
o = swap(o, "    back_surface: {texture: bwooda2, size: [256, 256], fit: true}\n", "", 1)
o = swap(o, "surface: {texture: bwooda2, size: [256, 256], fit: true}", "surface: {texture: gkp103a, size: [128, 256], fit: true}", 1)
o = swap(o, "surface: {texture: swr4, size: [64, 64]}", "surface: {texture: d1lggrt, size: [256, 256], fit: true}", 1)
o = swap(o, "surface: {texture: dkwdr, size: [128, 256], fit: true}", "surface: {texture: beemdorc, size: [128, 256], fit: true}", 1)
o = swap(o, "surface: {texture: cbeam5, size: [32, 256]}, notes: \"The loft ladder", "surface: {texture: t66abc10a, size: [32, 128]}, notes: \"The loft ladder", 1)
o = swap(o, '''    surface: {texture: 7t1cab, size: [128, 256], fit: true}
    end_surface: {texture: bemhwal, size: [256, 128]}
    top_surface: {texture: bembllg, size: [256, 256]}''', '''    surface: {texture: t1cab, size: [128, 256], fit: true}
    end_surface: {texture: t1books1, size: [128, 128]}
    top_surface: {texture: t1books1, size: [128, 128]}''', 1)
o = swap(o, "drawer fronts on its long sides (MM7 7t1cab), panelled ends, a board top", "drawer fronts on its long sides (MM8 t1cab, as in the pirate maps), plain wooden ends and top (t1books1)", 1)
o = swap(o, "    surface: {texture: crate_w64, size: [64, 64], fit: true}\n    treasure_level: 1", "    surface: {texture: crcn96, size: [64, 64], fit: true}\n    treasure_level: 1", 1)
o = swap(o, '''    at: [240, 2544]
    facing: e
    treasure_level: 1''', '''    at: [240, 2544]
    facing: e
    surface: {texture: gt002b, size: [64, 64], fit: true}
    top_surface: {texture: gt002g, size: [64, 64], fit: true}
    treasure_level: 1''', 1)
o = swap(o, "surface: {texture: csdoor, size: [256, 256], fit: true}", "surface: {texture: gkp103b, size: [128, 256], fit: true}", 1)
o = swap(o, "\"The gate painted red with a big flower for a heart (the nearest painted gate there is), MR & MRS WOBBLES - DO NOT SEPARATE over it.\"",
            "\"The gate painted red with a big flower for a heart (MM8 gcrydoor, the nearest painted gate there is: a stand-in, see NOTES.md textures to generate), MR & MRS WOBBLES - DO NOT SEPARATE over it.\"", 1)
open(L + 'objects.yml', 'w').write(o)
print('ok')
