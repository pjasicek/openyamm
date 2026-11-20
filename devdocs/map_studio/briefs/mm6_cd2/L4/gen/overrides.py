"""Per-sector decisions of the Castle Darkmoor rebuild that the measurement in gen.py cannot make."""

THEMES = '''themes:
  - id: theme:darkmoor
    wall: {texture: d2wctra, size: [128, 256]}
    floor: {texture: crdrf2, size: [128, 128]}
    ceiling: {texture: d2ceil3, size: [128, 128]}
    notes: "The castle's stone, by area 98 % of the original: d2wctra walls, crdrf2 floors, d2ceil3 ceilings."
defaults: {theme: theme:darkmoor, ambient: 20}
'''
NAMES = {}
NOTES = {}
MODE = {}
FLOOR = {}
CEIL = {}
SKIP = {194}
NOT_FRAME = set()
FORCE_FRAME = set()
MANUAL = {}
NO_JOIN = set()
THEME_OF = {}
STEP_DEPTH = {}
MIN_PIECE = 5000
NO_NOOKS = set()

WINGS = {}


def wing_of(si):
    return WINGS.get(si, 9)

DROP_Z = {163: [773, 738]}
SPLIT_Z = {73: [600]}
RAMP_SEGMENTS = {}
# the caves: one level floor each (their relief cannot be said)
MODE.update({s: 'single' for s in (1, 66, 71, 72, 73, 74, 142, 143)})
CEILING_INSET = 16
NO_CEILING_LEVELS = set()

# (room, room, x, y of the doorway's centre, width, bottom z, top z, why)
EXTRA_OPENINGS = [
    ('room:s073_a', 'room:s073', -7304, 10016, 254, 600, 856, 'the sliding panel of door record 9: from the gate bridge out over the cave, a drop of 780'),
]
# door record -> (opening, title, note)
DOOR_OPENINGS = {
    1: ('open:s155_s156', 'Door', 'Door record 1: a skull-faced wall that slides 254 west.'),
    4: ('open:s157_s162', 'Door', 'Door record 4: a leaf that slides 254 north.'),
    5: ('open:s058_s159_b', 'Door', 'Door record 5: a leaf that slides 250 north.'),
    6: ('open:s187_s185', 'Door', 'Door record 6: a wall panel that slides 125 north.'),
    7: ('open:s101_s188', 'Door', 'Door record 7: a wall panel that slides 125 north.'),
    8: ('open:s104_s103', 'Door', 'Door record 8: a wall panel that slides 255 west.'),
    9: ('open:s073_a_s073', 'Door', 'Door record 9: a wall panel that slides 254 east.'),
}

# floor taken out of a sector's rooms: (x0, y0, x1, y1). 159: the pocket the door leaf of record 5 stands in.
CUT = {159: [(12624, 9880, 12722, 10150)]}

# sloped floor read as level at this height: the rock that climbs the great hall's north-west corner (uneven relief)
FLATTEN = {56: -180}

# ---- the room list: what each sector of the original is (wing, name) ------------------------------------------
_R = '''
1|51|Entry hall (the way out to the Darkmoor region)
1|50|Entry gallery
1|49|Crypt passage
1|48|West crypt chamber
1|38|Sunken chamber with the broad steps
1|37|Crypt corridor
1|32|Stepped crypt landing
1|31|South crypt hall
1|35|South-east crypt hall
1|36|Ramp from the crypt to the ground floor
1|39|South-west vault
1|40|Cell passage
1|41|Cell doorway
1|42|Trap-floor cell
1|43|Cell
1|44|Stepped cell
1|45|Cell
1|46|Cell corridor
1|47|East vault
1|20|Long ramp from the stair hall down to the crypt
1|2|Cross hall, south arm
1|3|Cross hall, portal slot
1|5|Cross hall
1|6|Arrow slit
1|7|Arrow slit
1|13|Arrow slit
1|30|Arrow slit
1|8|East tall hall
1|9|Middle tall hall
1|10|West tall hall
1|63|Great arch between the west and middle halls
1|64|Great arch between the middle and east halls
1|65|Great arch to the great hall
1|11|Guard room doorway
1|12|Guard room
1|21|East room
1|22|East anteroom
1|23|Doorway to the east hall
1|24|Cell block
1|25|Cell block passage
1|26|Cell
1|27|Cell doorway
1|28|Cell
1|29|Cell doorway
1|33|East side chamber
1|34|Doorway to the side chamber
2|14|Stair hall
2|15|Steps from the guard room to the stair hall
2|16|Lever closet
2|17|North passage of the stair hall
2|18|Stair hall doorway
2|19|Octagon at the stair head
2|52|Spiral ramp, first quarter
2|53|Spiral ramp, second quarter
2|54|Spiral ramp, third quarter
2|55|Spiral ramp, last quarter
2|151|Tower room at the top of the spiral
2|152|Upper passage from the tower
2|4|Battlement gallery over the south cavern
2|173|Doorway from the battlement
2|174|Upper west passage
2|175|Upper doorway
2|176|Upper hall
2|177|Upper doorway
2|178|Upper east passage
2|179|Upper south room
2|180|Upper doorway
2|181|Ramp from the upper floor down to the balcony
2|182|Balcony doorway
2|183|Window from the upper hall into the east tall hall
2|1|South cavern
2|142|South cavern, west arm
2|143|South cavern, far west arm
3|56|Great hall
3|57|East balcony of the great hall
3|58|North passage under the gallery
3|59|North gallery
3|60|North-east corner room
3|61|Balcony arch
3|62|Balcony arch
3|67|Portcullis
3|68|Arch to the north passage
3|69|Arch to the north passage
3|70|Gallery window
3|153|North-west room over the hall
3|154|Ramp passage down to the skull room
3|155|Skull room
3|156|Ramp behind the skull door
3|157|Door passage
3|158|Long low tunnel
3|159|Stair down to the low tunnels
3|160|Low tunnel, east-west
3|161|Low tunnel, north-south
3|162|Low tunnel end
3|166|North-east stair
3|167|North-east ramp
3|168|North-east ramp, upper leg
3|169|North-east cellar
3|172|Tunnel end
3|66|North cavern
4|75|Gatehouse
4|76|Gatehouse step
4|77|Gatehouse stair
4|79|Gatehouse stair doorway
4|95|Gatehouse step
4|96|Gatehouse stair
4|97|Gatehouse stair doorway
4|78|Inner court
4|80|Throne hall
4|81|North gallery of the throne hall
4|82|South gallery of the throne hall
4|83|North-west gallery stair
4|84|South-west gallery stair
4|85|North-west tower room
4|86|South-west tower room
4|87|Gallery passage
4|88|South-east upper hall
4|89|Upper east room
4|90|Closet
4|91|Closet doorway
4|92|Window over the cavern
4|93|Ramp from the south range up to the upper hall
4|103|North-east upper hall
4|104|Secret room behind the sliding wall
4|105|Upper stair
4|106|North-east tower room
4|107|Tower window
4|108|Tower window
4|109|Ramp from the north range up to the upper hall
4|110|North-east lower room
4|111|Closet
4|112|North-east passage
4|113|Alcove
4|114|North-east corridor
4|115|North room
4|116|North stair room
4|117|North range room
4|118|North range corridor
4|119|North range room
4|120|North range end room
4|121|Barred room
4|122|South-east room
4|123|Doorway
4|124|South-east corridor
4|125|East lower room
4|126|South range hall
4|127|South range room
4|128|Doorway
4|129|South range room
4|130|South range room
4|131|South corridor under the gallery
4|132|Doorway
4|133|South range closet
4|134|South-east lower room
4|135|South range cross passage
4|136|Doorway
4|137|South range stepped passage
4|138|Doorway
4|139|Doorway
4|140|Doorway
4|141|Doorway
4|171|Doorway
5|144|West ward with the sunken ring
5|145|South-west hall
5|146|Passage to the south range
5|147|Doorway
5|148|North-west end room
5|149|North-west hall
5|150|North-west great room
5|163|Tall corridor with the long ramp
5|164|Lever gallery at the head of the ramp
5|165|Cellar under the lever gallery
5|94|West court
5|170|Crystal chamber
5|98|Wall walk, south
5|99|Wall walk, south-west corner
5|100|Wall walk, west
5|101|Wall walk, north-west room
5|102|Wall walk doorway
5|184|Gate tower, west
5|185|Gate tower, east
5|186|Hidden room behind the gate tower
5|187|Hidden passage
5|188|Secret passage
5|189|Secret passage
5|190|Secret passage
5|191|Secret treasure room
5|71|North-west cavern
5|72|West cavern
5|73|South cavern before the gate
5|74|East cavern
6|192|Teleport chamber (reached only by teleport)
6|193|The lich's study (reached only by teleport)
'''
for _l in _R.strip().split('\n'):
    _w, _s, _n = _l.split('|')
    WINGS[int(_s)] = int(_w)
    NAMES[int(_s)] = _n

CAVES = {1, 66, 71, 72, 73, 74, 142, 143}
NO_BANKS = set()

# Things read off the original by hand. The three teleporter cubes (glowing water blocks, 256 square and 231 high,
# hanging above the floor): the block is drawn, its touch-to-teleport faces are placeholders in objects (no event
# can be bound to a block).
_CUBE = {'texture': 'orwtrtyl', 'size': [128, 128]}
FEATURES = {
    'room:s056': {'platforms': [{'at': [13632, 6720], 'size': [256, 256], 'base': 308, 'rise': 231, 'surface': _CUBE}]},
    'room:s080': {'platforms': [{'at': [448, 14144], 'size': [256, 256], 'base': 274, 'rise': 231, 'surface': _CUBE}]},
    'room:s170': {'platforms': [{'at': [-12816, 15936], 'size': [256, 256], 'base': 258, 'rise': 231, 'surface': _CUBE}]},
}

# floor textures a look through a wall may land on (the edge of a slab, a step): never a wall's surface
NOT_WALL_TEXTURES = {'d2flor4', 'd2flor5', 'crdrf2', 'crdflr4', 'ctflor1', 'ctflor5'}
