"""P5 Clouds of the Ancients: the L1 design as data (A5 sub-agent, 2026-11-21). gen_l1.py writes the brief from it;
render_p5.py draws and measures it. Units are map units (512 to a cell), x east, y north, the shrine's middle at
(0, 0); floors are heights in map units over Darkstone's crown (the arrival, 0). Nothing here is read by the game or
the studio. After level_generation/projects/xeen/x9/design.py (X9's L1).

Source: the Clouds of the Ancients, MM5 maze 129 with x181-x183 (a 32 x 32 sky), its events and its text
dark/aazex129. A single cloud road leaves Darkstone Tower's roof in the south-east corner (the cupola at (28-30, 0-2),
"Descend into Darkstone Tower?", :14) and spirals inward, counter-clockwise, for 358 squares to the Pharaoh's shrine in
the middle (13,15). The Pharaoh's note (:15) stands two steps from the arrival (29,7); eight "Rest Stop" signs (:0)
stand along the road; nine game-name signs (:2-10) stand in the four corners of the sky, off the road; "Might and
Magic" (:1) is the last sign, beside the shrine (12,17). "The observatory is closed." (:11) has no event in the source.

P5 keeps that order on one ring of cloud road round the shrine's cloud (the long way round: the shrine is in sight
the whole walk, across 1,400 of sky), with the corners' signs as billboards on the road's outer shoulder.
"""

ROOM = (26, 26)                 # cells: 13,312 x 13,312 units
HALF = (ROOM[0] * 256, ROOM[1] * 256)
RING = 3584                     # the road's middle line: a square ring 7,168 on a side round the shrine
ROAD_WIDTH = 768

# ------------------------------------------------------------------------------------------------ spaces
# kind: cloud (walkable pad), shrine (the middle cloud)
SPACES = [
    dict(id='room:crown', name="Darkstone's crown", kind='cloud', at=(3968, -4352), extent=(2816, 2816), floor=0,
         seed=1, order=0, anchor=(RING, -RING),
         shape="a flat cloud round the stair house, a small black copy of Darkstone Tower's crown standing up through it",
         purpose="Arrival from FD-03's roof stair and the way back down (the stair house's door). The Pharaoh's note "
                 "by the door; the 'New World Computing' board on the west rim. Quiet."),
    dict(id='room:rest_east', name='The first Rest Stop', kind='cloud', at=(RING + 320, 0), extent=(2048, 1792), floor=64,
         seed=2, order=1, anchor=(RING, 0),
         purpose="A Rest Stop hut on the road's outer (east) side, a bench under it."),
    dict(id='room:ne_turn', name='The north-east turn', kind='cloud', at=(RING + 192, RING + 192), extent=(2048, 2048),
         floor=128, seed=3, order=2, anchor=(RING, RING),
         purpose="The road turns west. 'Empire Deluxe' and 'Spaceward Ho!' on the outer corner (the source's "
                 "north-east pair, (30-31, 31))."),
    dict(id='room:observatory', name='The observatory', kind='cloud', at=(0, 4096), extent=(2560, 2560), floor=192,
         seed=4, order=3, anchor=(0, RING),
         shape="the north road's widening, the observatory's round tower on its north side",
         purpose="A domed observatory beside the road, its door shut: 'The observatory is closed.' (m42.observatory)."),
    dict(id='room:nw_turn', name='The north-west turn', kind='cloud', at=(-RING - 192, RING + 192), extent=(2048, 2048),
         floor=256, seed=5, order=4, anchor=(-RING, RING),
         purpose="The road turns south. 'Planets Edge' and 'Vegas Games' (the source's north-west pair, (0-1, 31))."),
    dict(id='room:rest_west', name='The second Rest Stop', kind='cloud', at=(-RING - 320, 0), extent=(2048, 1792),
         floor=320, seed=6, order=5, anchor=(-RING, 0),
         purpose="A Rest Stop hut on the road's outer (west) side."),
    dict(id='room:sw_turn', name='The south-west turn', kind='cloud', at=(-RING - 192, -RING - 192), extent=(2048, 2048),
         floor=384, seed=7, order=6, anchor=(-RING, -RING),
         purpose="The road turns east. 'Tunnels and Trolls' and 'Nuclear War' (the source's south-west pair, (0, 0-1))."),
    dict(id='room:rest_south', name='The last Rest Stop', kind='cloud', at=(0, -3904), extent=(2304, 2048),
         floor=448, seed=8, order=7, anchor=(0, -RING),
         purpose="The last Rest Stop hut, on the outer (south) side; the causeway leaves north from it to the shrine."),
    dict(id='room:shrine', name="The Pharaoh's shrine", kind='shrine', at=(0, 0), extent=(3328, 3328), floor=512,
         seed=9, order=8, anchor=(0, 0),
         shape="a round high cloud paved in pale gold stone, the shrine's dais at its middle, the pavilion's place behind",
         purpose="The end of the road: the Dragon Pharaoh at his shrine (m42.shrine, the ending cinematic); 'Might and "
                 "Magic', the last sign; after the ceremony the wedding pavilion with Roland and Kalindra."),
]

# ------------------------------------------------------------------------------------------------ links
# style: road (the cloud road, a dashed line of cloud-stone flags down its middle), causeway (cloud-stone on a cloud
# tongue over the sky), door (the stair house's door, the way down)
LINKS = [
    dict(id='link:road_1', a='room:crown', b='room:rest_east', kind='road', style='road', width=ROAD_WIDTH),
    dict(id='link:road_2', a='room:rest_east', b='room:ne_turn', kind='road', style='road', width=ROAD_WIDTH),
    dict(id='link:road_3', a='room:ne_turn', b='room:observatory', kind='road', style='road', width=ROAD_WIDTH),
    dict(id='link:road_4', a='room:observatory', b='room:nw_turn', kind='road', style='road', width=ROAD_WIDTH),
    dict(id='link:road_5', a='room:nw_turn', b='room:rest_west', kind='road', style='road', width=ROAD_WIDTH),
    dict(id='link:road_6', a='room:rest_west', b='room:sw_turn', kind='road', style='road', width=ROAD_WIDTH),
    dict(id='link:road_7', a='room:sw_turn', b='room:rest_south', kind='road', style='road', width=ROAD_WIDTH),
    dict(id='link:causeway', a='room:rest_south', b='room:shrine', kind='path', style='causeway', width=ROAD_WIDTH,
         notes="the last stretch, straight north over the sky to the shrine's south rim"),
]

# the road's middle line as walked: from the arrival round the ring and up the causeway to the shrine's dais
STAIR_HOUSE = dict(at=(4608, -4864), radius=448, wall=512, band=256, cone=1562)
ARRIVAL = (4608, -3968)
WALK = [ARRIVAL, (RING, -3072), (RING, RING), (-RING, RING), (-RING, -RING), (0, -RING), (0, -384)]

# ------------------------------------------------------------------------------------------------ places
# kind: arrival, exit, note, board (a billboard with a game's name), rest (a Rest Stop hut and its sign), observatory,
# shrine, figure (a placed peaceful figure), pavilion, chest, landmark. `at` is absolute (map units); `face` the
# direction the thing's front looks (compass).
B = 640                         # a board stands on a bulge 640 out from the road's middle line, its legs off the road
PLACES = [
    dict(id='entrance:fd03_roof', kind='arrival', space='room:crown', at=ARRIVAL, face='n',
         text="Arrival from FD-03's roof stair: out of the stair house's door, facing north up the road."),
    dict(id='exit:stair_house', kind='exit', space='room:crown', at=(4608, -4416), face='n',
         text="The stair house's door, the way down into Darkstone Tower: an exit preset, its meaning 'Descend into "
              "Darkstone Tower?' (aazex129:14), to FD-03's entrance:p5_stair."),
    dict(id='poi:pharaoh_note', kind='note', space='room:crown', at=(4096, -4224), face='n',
         text="m42.pharaoh_note: 'A message reads: It's a long road ahead so rest where you can. But don't forget to "
              "recast your spells. Signed, The Dragon Pharaoh' (aazex129:15), on a post by the door (the source's (29,7))."),
    dict(id='poi:board_nwc', kind='board', space='room:crown', at=(2944, -3712), face='e', text='New World Computing'),
    dict(id='poi:board_kings_bounty', kind='board', space='room:crown', at=(RING + B, -2176), face='w',
         text="King's Bounty"),
    dict(id='poi:rest_1', kind='rest', space='room:rest_east', at=(RING + 768, 0), face='w', text='Rest Stop'),
    dict(id='poi:board_inherit', kind='board', space='room:rest_east', at=(RING + B, 1792), face='w',
         text='Inherit the Earth'),
    dict(id='poi:board_empire', kind='board', space='room:ne_turn', at=(RING + 704, RING + 704), face='sw',
         text='Empire Deluxe'),
    dict(id='poi:board_spaceward', kind='board', space='room:ne_turn', at=(RING - 1280, RING + B), face='s',
         text='Spaceward Ho!'),
    dict(id='poi:observatory', kind='observatory', space='room:observatory', at=(0, 4096), face='s',
         text="m42.observatory: the observatory's door, 'The observatory is closed.' (aazex129:11)."),
    dict(id='landmark:observatory', kind='landmark', space='room:observatory', at=(0, 4672), face='s',
         text="The observatory: a round tower of pale stone with a copper dome and a shut slit, 576 in radius."),
    dict(id='poi:board_planets', kind='board', space='room:nw_turn', at=(-RING + 1280, RING + B), face='s',
         text='Planets Edge'),
    dict(id='poi:board_vegas', kind='board', space='room:nw_turn', at=(-RING - 704, RING + 704), face='se',
         text='Vegas Games'),
    dict(id='poi:rest_2', kind='rest', space='room:rest_west', at=(-RING - 768, 0), face='e', text='Rest Stop'),
    dict(id='poi:board_tunnels', kind='board', space='room:sw_turn', at=(-RING - 704, -RING - 704), face='ne',
         text='Tunnels and Trolls'),
    dict(id='poi:board_nuclear', kind='board', space='room:sw_turn', at=(-RING + 1280, -RING - B), face='n',
         text='Nuclear War'),
    dict(id='poi:rest_3', kind='rest', space='room:rest_south', at=(0, -RING - 768), face='n',
         text="Rest Stop: the last one"),
    dict(id='poi:board_mm', kind='board', space='room:shrine', at=(-640, -1408), face='e', text='Might and Magic'),
    dict(id='poi:shrine', kind='shrine', space='room:shrine', at=(0, -384), face='s',
         text="m42.shrine: the Pharaoh's shrine, a dais with two great stone hands held up open; true sets the Cube "
              "in one and the Scepter in the other and starts the ending cinematic."),
    dict(id='npc:pharaoh', kind='figure', space='room:shrine', at=(0, 192), face='s',
         text="The Dragon Pharaoh (npc 5453): a peaceful, placed-only, uncounted, NoArena figure behind the dais, "
              "shared with DD-15, made unkillable by the map's load event (D-56 Q5)."),
    dict(id='decor:cube', kind='landmark', space='room:shrine', at=(-384, -320), face='s',
         text="The Cube of Power in the west hand: the ground-item model item_xeen_12365.glb bound again as a scaled "
              "world decoration, hidden until state:wedding (D-56 change 4)."),
    dict(id='decor:scepter', kind='landmark', space='room:shrine', at=(384, -320), face='s',
         text="Xeen's Scepter in the east hand: item_xeen_12366.glb as a scaled world decoration, hidden until "
              "state:wedding (D-56 change 4)."),
    dict(id='thing:pavilion', kind='pavilion', space='room:shrine', at=(0, 960), face='s',
         text="The wedding pavilion: white canvas and gold on four posts, 1,536 x 1,024, open to the south. Hidden "
              "until m42.done (state:wedding)."),
    dict(id='npc:roland', kind='figure', space='room:shrine', at=(-224, 960), face='s',
         text="Prince Roland under the pavilion, after m42.done (question 6)."),
    dict(id='npc:kalindra', kind='figure', space='room:shrine', at=(224, 960), face='s',
         text="Queen Kalindra in her wedding look under the pavilion, after m42.done: a new row (not 11918, DD-14's "
              "cursed body) keeping npc 5001 (D-56 change 3)."),
    dict(id='landmark:cake', kind='landmark', space='room:shrine', at=(576, 832), face='s',
         text="A cake on a small table inside the pavilion (m42's else_text: 'somebody has left cake')."),
    dict(id='poi:gift_chest', kind='chest', space='room:shrine', at=(-576, 1088), face='s',
         text="The wedding gift (T6), against the pavilion's back, clear of the couple and the walking line, after "
              "m42.done (question 7)."),
    dict(id='poi:disc', kind='disc', space='room:shrine', at=(1216, 320), face='n',
         text="A cloud-stone disc beside the pavilion's open south side (east of it, off the walking line), shown with "
              "state:wedding: it moves the party to entrance:fd03_roof with A3's line (D-56 change 7, Q10)."),
]

# the three game boards per corner and the Rest Stops, in walking order, for the census and the board
BOARDS_IN_ORDER = [p['text'] for p in PLACES if p['kind'] == 'board']

# ------------------------------------------------------------------------------------------------ cameras
# yaw: degrees, 0 east, 90 north (X9's convention)
CAMERAS = {
    'walk': dict(id='view:long_road', at=(3328, -3328), floor=0, eye=176, yaw_deg=105.0, pitch_deg=-2.0, fov=74.0,
                 what="The long road: from the crown's north edge where the road starts, up the east road to the "
                      "first Rest Stop and the north-east turn, the boards on its right shoulder, the shrine's "
                      "hands on their cloud across the sky on the left, the observatory's dome far off."),
    'shrine': dict(id='view:shrine', at=(0, -1920), floor=496, eye=176, yaw_deg=90.0, pitch_deg=-2.0, fov=72.0,
                   what="The end of the road: from the causeway, north to the dais and its two raised hands (the "
                        "Cube and the Scepter set in them), the Dragon Pharaoh behind it, the pavilion with Roland "
                        "and Kalindra after the ceremony; the observatory's dome far beyond across the sky."),
}

# X5's Darkstone Tower (A6's sketch thing:darkstone at [53.75, 59.75], 2.5 cells, its door on the north face; the
# rock's top 1,500): the proposed fall landing, before the door (X5: x = cell * 512 - 32768, y = 32768 - row * 512)
DARKSTONE_X5 = dict(cell=(55.0, 61.0), at=(-4608, 1536), rock_top=1500, tower_radius=544)
FALL_LANDING_X5 = dict(at=(-4608, 2304), ground=1500, facing=1536,
                       text="On Darkstone's rock on X5, 224 before the tower's north door, facing it (south)")
