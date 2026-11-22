"""D7 The Skyroads: the L1 design as data (A6 sub-agent, phase 6, 2026-11-21).

d7_brief.py writes devdocs/xeen/briefs/d7/L1 from it; d7_render.py draws and measures it; board_d7.py shows it.
Nothing here is read by the game or the studio. Units are map units (512 to a cell), x east, y north, the room's
middle at (0, 0); floors are heights in map units.

Source: MM5's Skyroads (dark mazes 89-112, Sky A1-F4, a 6 x 4 grid of 16 x 16 squares over the Darkside; texts
dark/aaze0089-0099 and aazex100-112). Its layout is kept where it serves: a ring road round the whole sky with the four
element corners (A1 Fire, F1 Air, F4 Earth, A4 Water), the rope at A3, Olympus at C2, the Pyramid's door at D2, the
Sky Lake and its scarab sellers at E3, the merchants of the elements at A2, C1, D4, F2, a toll of sky bandits on every
side, "Eat at Joe's" and "Speeding??" boards, and the Megadragon on Alamar's roof at A1. Moved for the design: the
Megadragon's roost leaves the ring (a dead-end spur from A2), Olympus is joined to the roads (no sky ferry), and an
inner road crosses the sky from the rope to the Sky Lake through Olympus.

The sky's squares over the surface: A-B over D6 (rows 1-2) and D1 (rows 3-4), C-D over D5 and D2, E-F over D4 and D3.
"""
import math

ROOM = (128, 88)                       # cells: 65,536 x 45,056 units, one ODM side long, the source's 3:2
HALF = (ROOM[0] * 256, ROOM[1] * 256)  # (32768, 22528)
SQUARE = (HALF[0] * 2 / 6, HALF[1] * 2 / 4)   # one source square: 10,923 x 11,264


def square_centre(code):
    """'C2' -> the middle of that source square on D7."""
    col = 'ABCDEF'.index(code[0])
    row = int(code[1])
    return (-HALF[0] + (col + 0.5) * SQUARE[0], HALF[1] - (row - 0.5) * SQUARE[1])


RING = dict(x=28160, y=18432, width=768)   # the Skyroad's centre lines and width

# ------------------------------------------------------------------------------------------------ spaces
# kind: rest (a quiet rest stop with a hut), corner (an element corner, also a rest stop), road (a road island where
# monsters may stand), post (a quiet island of a merchant or a toll), hatch (a tower's roof hatch), lone (a lone cloud
# off the road), town (Olympus), roost (the Megadragon's), lake (the Sky Lake), cap (the Pyramid's door)
# square: the source square; region: north, east, south, west, inner
SPACES = [
    # ---- the north road (y 18,432)
    dict(id='room:fire_corner', name='The Fire Corner', kind='corner', square='A1', region='north',
         at=(-28672, 18944), extent=(4608, 4096), floor=1280, seed=1, element='fire',
         shape="a broad corner cloud where the north and west roads meet; its outer tip ends in nothing over a red glow",
         purpose="The Skyroads' north-west corner (Sky A1, 'Fire Zone'): the sky asks 'What do you seek?' at the tip; "
                 "'Fire' drops the party onto P1 (m38.corner_fire). A Rest Stop hut on the inner side; "
                 "entrance:p1_return by it. Quiet."),
    dict(id='room:griffin_watch', name='The Griffin Watch', kind='road', square='B1', region='north',
         at=(-16384, 18432), extent=(3584, 3072), floor=1280, seed=2,
         shape="a wide place in the north road, its south lip looking across the gap at the Megadragon's roost",
         purpose="Griffins over the road (the source's B1); the second 'DANGER! Mega Dragon' board on the south lip, "
                 "facing the roost 9,700 away; a genie's lamp in a crack of the cloud (the tired genie, one wish left)."),
    dict(id='room:north_crossing', name='The North Crossing', kind='rest', square='C1', region='north',
         at=(-1536, 18432), extent=(4096, 3584), floor=1280, seed=3,
         shape="a broad round cloud where the Olympus causeway leaves the north road",
         purpose="A Rest Stop (hut and sign) where the causeway to Olympus' north gate leaves the ring; the Merchant "
                 "of the Elements with the dusty barge (Dust, the source's C1). Quiet."),
    dict(id='room:north_toll', name='The North Toll', kind='post', square='D1', region='north',
         at=(5632, 18432), extent=(3072, 2816), floor=1280, seed=4,
         purpose="The sky bandits' north toll ('Pay us 10,000 gold or else!'); a 'Speeding??' board; a short spur "
                 "south to the Northern Tower's roof hatch. Quiet but for the bandits."),
    dict(id='room:north_tower_hatch', name="The Northern Tower's hatch", kind='hatch', square='D1', region='north',
         at=(5632, 14848), extent=(2048, 1792), floor=1152, seed=5,
         purpose="DD-08's roof hatch (the source's 'Descend to the North Tower?'): entrance:dd08_roof."),
    dict(id='room:east_rest', name='The East Rest Stop', kind='rest', square='E1', region='north',
         at=(16384, 18432), extent=(4096, 3328), floor=1280, seed=6,
         purpose="A Rest Stop (the source's E1 'Rest Stop') with a genie's lamp on its bench (the kind genie). Quiet."),
    # ---- the east road (x 28,160)
    dict(id='room:air_corner', name='The Air Corner', kind='corner', square='F1', region='east',
         at=(28672, 18944), extent=(4608, 4096), floor=1280, seed=7, element='air',
         shape="the north-east corner cloud, its tip torn into streamers by a wind from below",
         purpose="Sky F1, 'Air Zone': 'What do you seek?'; 'Air' drops the party onto P2 (m38.corner_air). Rest Stop "
                 "hut; entrance:p2_return. Quiet."),
    dict(id='room:blackfang_hatch', name="Blackfang's hatch", kind='hatch', square='F1', region='east',
         at=(23552, 13824), extent=(2304, 2048), floor=1152, seed=8,
         purpose="Castle Blackfang's roof trapdoor (the source's 'Descend to Castle Blackfang?'; DD-14's roost): "
                 "entrance:dd14_roof. A spur from the Air Corner."),
    dict(id='room:mud_wharf', name='The Mud Wharf', kind='post', square='F2', region='east',
         at=(28160, 5632), extent=(3584, 3328), floor=1152, seed=9,
         purpose="The east toll ('You have invaded our territory. Appease us with 10,000 gold or face our wrath!') "
                 "and the Merchant of the Elements with the muddy barge (Mud, the source's F2). Quiet but for the bandits."),
    dict(id='room:east_junction', name="The Eastern Tower's junction", kind='rest', square='F3', region='east',
         at=(28160, -5632), extent=(4096, 3584), floor=1024, seed=10,
         purpose="Where the Sky Lake road meets the east road: a Rest Stop, a 'Speeding???' board, and DD-07's roof "
                 "hatch (the source's 'Descend to the East Tower?'): entrance:dd07_roof. Quiet."),
    dict(id='room:earth_corner', name='The Earth Corner', kind='corner', square='F4', region='south',
         at=(28672, -18944), extent=(4608, 4096), floor=768, seed=11, element='earth',
         shape="the south-east corner cloud, grey and heavy, its tip crumbling like a cliff",
         purpose="Sky F4, 'Earth Zone': 'What do you seek?'; 'Earth' drops the party onto P3 (m38.corner_earth). Rest "
                 "Stop hut; entrance:p3_return. Quiet."),
    # ---- the south road (y -18,432)
    dict(id='room:south_rest', name='The South Rest Stop', kind='rest', square='E4', region='south',
         at=(16384, -18432), extent=(4096, 3328), floor=768, seed=12,
         purpose="A Rest Stop (the source's E4 'Rest Stop'); a bottle on the bench ('The test of the elements is "
                 "merely difficult, not impossible.'). Quiet."),
    dict(id='room:steam_post', name='The Steam Post', kind='post', square='D4', region='south',
         at=(5632, -18432), extent=(3328, 3072), floor=768, seed=13,
         purpose="The Merchant of the Elements with the steaming barge (Steam, the source's D4); a spur north to the "
                 "Southern Tower's hatch. Quiet."),
    dict(id='room:south_tower_hatch', name="The Southern Tower's hatch", kind='hatch', square='D4', region='south',
         at=(5632, -14592), extent=(2048, 1792), floor=704, seed=14,
         purpose="DD-06's roof hatch (the source's 'Descend into the South Tower?'): entrance:dd06_roof."),
    dict(id='room:south_toll', name="Joe's Corner", kind='post', square='C4', region='south',
         at=(-5632, -18432), extent=(3584, 3072), floor=768, seed=15,
         purpose="The south toll ('Many apologies, good folks, but this is a robbery.'), under an 'Eat at Joe's' "
                 "board with no Joe's anywhere. Quiet but for the bandits."),
    dict(id='room:skywaymen_camp', name="The Skywaymen's Camp", kind='road', square='B4', region='south',
         at=(-16384, -18432), extent=(3840, 3328), floor=768, seed=16,
         purpose="The bandits' camp: a tarpaulin, a cold fire and their strongbox (the tolls go somewhere), a second "
                 "'Eat at Joe's' board; cloud golems drifted in and stayed."),
    dict(id='room:water_corner', name='The Water Corner', kind='corner', square='A4', region='south',
         at=(-28672, -18944), extent=(4608, 4096), floor=768, seed=17, element='water',
         shape="the south-west corner cloud, wet and blue-shadowed, its tip dripping",
         purpose="Sky A4, 'Water Zone': 'What do you seek?'; 'Water' drops the party onto P4 (m38.corner_water). Rest "
                 "Stop hut; entrance:p4_return. On its inner side the roof hatches of Ellinger's Tower (DD-02) and "
                 "Castle Kalindra (DD-03), as in the source's A4. Quiet."),
    # ---- the west road (x -28,160)
    dict(id='room:west_toll', name='The West Toll', kind='post', square='A4', region='west',
         at=(-28160, -12288), extent=(3072, 2816), floor=832, seed=18,
         purpose="The west toll ('Hold! The toll for passing this part of the road is 10,000 gold!'). Quiet but for "
                 "the bandits."),
    dict(id='room:rope_head', name="The Rope's Head", kind='rest', square='A3', region='west',
         at=(-26624, -6144), extent=(5120, 3840), floor=1024, seed=19,
         shape="a broad cloud on the west road's inner side; the Dark Grove rope comes up through a hole in it",
         purpose="The Dark Grove rope's head (D1, after m30.done): entrance:d1_rope, 'Pull up the rope?' and the way "
                 "back down. The 'XEEN Skyroad' board, an 'Eat at Joe's' board, a Rest Stop hut, and the Western "
                 "Tower's hatch ('Enter West Tower?', DD-05). The inner road leaves east. Quiet. The arrival view."),
    dict(id='room:smoke_post', name='The Smoke Post', kind='post', square='A2', region='west',
         at=(-28160, 4096), extent=(3328, 3072), floor=1152, seed=20,
         purpose="The Merchant of the Elements with the smoking barge (Smoke, the source's A2) and the first "
                 "'DANGER! Mega Dragon' board at the foot of the dragon's road. Quiet."),
    dict(id='room:west_lookout', name='The West Lookout', kind='road', square='A2', region='west',
         at=(-28160, 12288), extent=(3072, 2816), floor=1216, seed=21,
         purpose="A wide place in the west road; griffins; a rope bridge east to the stranded traveller's island."),
    dict(id='room:stranded_west', name="The stranded traveller's island", kind='lone', square='A2', region='west',
         at=(-24320, 12800), extent=(1536, 1280), floor=1280, seed=22,
         purpose="'Help! I'm stranded on an air island in A2 at 12,14.' (a bottle at the Sky Lake): a skeleton and his "
                 "strongbox. Inside the Megadragon's breath (4,946 from its leash circle): a risk, not a route."),
    dict(id='room:roost', name="The Megadragon's Roost", kind='roost', square='B2', region='west',
         at=(-19456, 9216), extent=(5120, 4096), floor=1536, seed=23,
         shape="a high cloud round a black crag, gnawed bones, a hatch of Ancient metal under the dragon",
         purpose="Q-D26 (optional): the Megadragon (125) sleeps on Castle Alamar's roof hatch ('Descend to Castle "
                 "Alamar?' / 'The door is locked. Scratched on the surface are some words: The Megadragon has the "
                 "key!'). Its hoard. A dead-end road from the Smoke Post; its leash circle stands 5,900 or more from "
                 "every other walkable place."),
    # ---- the inner road
    dict(id='room:broken_launch', name='The Broken Launch', kind='road', square='B3', region='inner',
         at=(-15360, -3584), extent=(4096, 3584), floor=1152, seed=24,
         shape="a cloud with an old marble jetty and a launch with no boat (the source's 'Olympus Launch')",
         purpose="The gods' old launch, retired when Lucio's boats started sailing up from the jetties below; sky "
                 "golems stand guard; a bottle in the jetty's planks ('Evil Genies NEVER let their victims off the "
                 "hook--they will always kill someone.'); a lost traveller's pack. A rope bridge south to the genie's rock."),
    dict(id='room:genie_rock', name="The Genie's Rock", kind='lone', square='C3', region='inner',
         at=(-10240, -7168), extent=(2048, 2048), floor=1024, seed=25,
         purpose="A lone cloud with a lamp on a rock: the angry genie, two thousand years late (Q-D27). The bottle at "
                 "the Broken Launch warns about him."),
    dict(id='room:stranded_south', name="The second stranded island", kind='lone', square='C3', region='inner',
         at=(-5888, -10752), extent=(1536, 1280), floor=960, seed=26,
         purpose="'Help! I'm stranded on an air island in C3 at 7,0.' (the second bottle): a lean-to and a strongbox."),
    dict(id='zone:olympus', name='Olympus', kind='town', square='C2', region='inner',
         at=(-4608, 7168), extent=(9728, 7680), floor=1792, seed=27,
         shape="a raised cloud paved in white marble, a low balustrade round its rim, three gates, the gods' houses "
               "round a square",
         purpose="The city of the gods (WORLD_DESIGN 5.2; A4's d7.yml): six services, the mirror, Lucio's dock, the "
                 "six gods' houses, Soul Storage with Sheltem's plaque (M31), the four prophecy statues, the Olympus "
                 "Sewer's stair (DD-26). No monsters. The signature view."),
    dict(id='room:pyramid_cap', name="The Pyramid's Door", kind='cap', square='D2', region='inner',
         at=(8704, 3584), extent=(4608, 4096), floor=1408, seed=28,
         shape="a cloud round a golden capstone that floats a little above it, a door in its east face",
         purpose="The Great Pyramid's sky door (the source's D2 'Enter the Pyramid?'): DD-15's top, both ways after "
                 "m30.done (entrance:dd15_sky). Cloud dragons circle it (the source's D2)."),
    dict(id='room:sky_lake', name='The Sky Lake', kind='lake', square='E3', region='inner',
         at=(16896, -5120), extent=(7168, 6144), floor=896, seed=29,
         shape="a wide cloud bowl holding a shallow lake, an island of cloud in it, stalls on the west shore",
         purpose="The Sky Lake (the source's E3): four scarab sellers' stalls (Rahib, Wardoz the Blue, Clara the Cold, "
                 "Dorion the Energy Merchant), two bottles washed up on the shore (the stranded islands' notes), the "
                 "'Sky Lake' board. Quiet."),
]
SPACE = {s['id']: s for s in SPACES}

# ------------------------------------------------------------------------------------------------ links
# style: road (the Skyroad, cloud with a cloud-stone band), causeway (marble-flagged, to Olympus), spur (narrow cloud
# road), bridge (rope bridge, X8's), ramp. via: waypoints between the two islands' rims.
LINKS = [
    # the ring, clockwise from the Fire Corner
    dict(id='link:n1', a='room:fire_corner', b='room:griffin_watch', style='road', width=768),
    dict(id='link:n2', a='room:griffin_watch', b='room:north_crossing', style='road', width=768),
    dict(id='link:n3', a='room:north_crossing', b='room:north_toll', style='road', width=768),
    dict(id='link:n4', a='room:north_toll', b='room:east_rest', style='road', width=768),
    dict(id='link:n5', a='room:east_rest', b='room:air_corner', style='road', width=768),
    dict(id='link:e1', a='room:air_corner', b='room:mud_wharf', style='road', width=768),
    dict(id='link:e2', a='room:mud_wharf', b='room:east_junction', style='road', width=768),
    dict(id='link:e3', a='room:east_junction', b='room:earth_corner', style='road', width=768),
    dict(id='link:s1', a='room:earth_corner', b='room:south_rest', style='road', width=768),
    dict(id='link:s2', a='room:south_rest', b='room:steam_post', style='road', width=768),
    dict(id='link:s3', a='room:steam_post', b='room:south_toll', style='road', width=768),
    dict(id='link:s4', a='room:south_toll', b='room:skywaymen_camp', style='road', width=768),
    dict(id='link:s5', a='room:skywaymen_camp', b='room:water_corner', style='road', width=768),
    dict(id='link:w1', a='room:water_corner', b='room:west_toll', style='road', width=768),
    dict(id='link:w2', a='room:west_toll', b='room:rope_head', style='road', width=768),
    dict(id='link:w3', a='room:rope_head', b='room:smoke_post', style='road', width=768),
    dict(id='link:w4', a='room:smoke_post', b='room:west_lookout', style='road', width=768),
    dict(id='link:w5', a='room:west_lookout', b='room:fire_corner', style='road', width=768),
    # spurs
    dict(id='link:north_hatch', a='room:north_toll', b='room:north_tower_hatch', style='spur', width=512),
    dict(id='link:south_hatch', a='room:steam_post', b='room:south_tower_hatch', style='spur', width=512),
    dict(id='link:blackfang_spur', a='room:air_corner', b='room:blackfang_hatch', style='spur', width=512),
    dict(id='link:dragon_road', a='room:smoke_post', b='room:roost', style='spur', width=768,
         notes="the Megadragon's road: 'DANGER! Mega Dragon' at its foot; a dead end"),
    dict(id='link:stranded_bridge', a='room:west_lookout', b='room:stranded_west', style='bridge', width=256),
    # the inner road
    dict(id='link:launch_road', a='room:rope_head', b='room:broken_launch', style='road', width=768),
    dict(id='link:olympus_west', a='room:broken_launch', b='zone:olympus', style='causeway', width=768,
         gate=(-8704, 3584), notes="up to Olympus' south-west gate"),
    dict(id='link:genie_bridge', a='room:broken_launch', b='room:genie_rock', style='bridge', width=256),
    dict(id='link:stranded_south_bridge', a='room:genie_rock', b='room:stranded_south', style='bridge', width=256),
    dict(id='link:olympus_north', a='room:north_crossing', b='zone:olympus', style='causeway', width=1024,
         gate=(-1536, 11008), notes="the Olympus causeway, marble flags on a cloud, to the north gate"),
    dict(id='link:olympus_east', a='zone:olympus', b='room:pyramid_cap', style='causeway', width=768,
         gate=(256, 6656), notes="out of the east gate to the Pyramid's door"),
    dict(id='link:lake_road', a='room:pyramid_cap', b='room:sky_lake', style='road', width=768),
    dict(id='link:lake_east', a='room:sky_lake', b='room:east_junction', style='road', width=768),
]

# ------------------------------------------------------------------------------------------------ Olympus
# The town's lanes and buildings (A4's d7.yml houses 4801-4814). Doors: (x, y), facing (the side the door faces).
OLYMPUS_ZONES = [
    dict(id='zone:ol_square', name="The gods' square", at=(-4608, 7168), extent=(2560, 2560),
         purpose="The square: the Mirror of Olympus in its middle (entrance:olympus_square beside it), the four "
                 "prophecy statues at its corners (m31.statue_1-4)."),
    dict(id='zone:ol_temple_court', name='The temple court', at=(-4608, 9856), extent=(4608, 2048),
         purpose="The Temple of Olympus facing the square, the Light and Spirit guilds either side; Soul Storage "
                 "behind the temple's west wing."),
    dict(id='zone:ol_market', name='The east lane', at=(-1536, 6912), extent=(2304, 5632),
         purpose="The Forge of the Gods, the Nectar House and the Hall of Heroes, doors to the square."),
    dict(id='zone:ol_gods_row', name="The gods' row", at=(-7680, 6912), extent=(2816, 5632),
         purpose="Zeus', Hera's and Athena's houses facing the square; Ligono waits in Hera's (Q-C19); Hermes' and "
                 "Atlas' on the south lane; Adonis' on the west rim by the ants' lookout."),
    dict(id='zone:ol_dock', name="Lucio's dock", at=(-256, 3072), extent=(2560, 2048),
         purpose="Lucio's Dock (house 4808) and a marble jetty running out south-east over the void, a celestial boat "
                 "moored at its end: entrance:olympus_dock on the jetty."),
]
BUILDINGS = [  # (id, house, service, door at, facing, footprint cells, zone, note)
    ('building:ol_temple', 4803, 'Temple of Olympus', (-4608, 8960), 's', (4, 3), 'zone:ol_temple_court',
     'a marble temple with a gold dome and a portico of six columns'),
    ('building:ol_guild_light', 4805, 'Olympus Guild of Light', (-7680, 9216), 's', (2, 2), 'zone:ol_temple_court', ''),
    ('building:ol_guild_spirit', 4806, 'Olympus Guild of Spirit', (-2304, 9216), 's', (2, 2), 'zone:ol_temple_court', ''),
    ('building:ol_smith', 4801, 'The Forge of the Gods', (-2560, 8192), 'w', (2, 2), 'zone:ol_market', ''),
    ('building:ol_tavern', 4802, 'The Nectar House', (-2560, 6656), 'w', (2.5, 2), 'zone:ol_market', ''),
    ('building:ol_training', 4804, 'The Hall of Heroes', (-2560, 5120), 'w', (3, 2), 'zone:ol_market',
     'open to the sky inside: "No ceiling in this hall."'),
    ('building:ol_zeus', 4813, 'House of Zeus', (-6656, 8192), 'e', (2.5, 2), 'zone:ol_gods_row', ''),
    ('building:ol_hera', 4814, 'House of Hera', (-6656, 6656), 'e', (2, 2), 'zone:ol_gods_row', 'Ligono waits here'),
    ('building:ol_athena', 4810, 'House of Athena', (-6656, 5120), 'e', (2, 2), 'zone:ol_gods_row', ''),
    ('building:ol_hermes', 4811, 'House of Hermes', (-6144, 4608), 'n', (2, 1.5), 'zone:ol_gods_row', ''),
    ('building:ol_atlas', 4812, 'House of Atlas', (-4352, 4608), 'n', (2, 1.5), 'zone:ol_gods_row', ''),
    ('building:ol_adonis', 4809, 'House of Adonis', (-8704, 6912), 's', (2, 2), 'zone:ol_gods_row',
     "on the west rim, the ants' lookout terrace beside it"),
    ('building:ol_dock', 4808, "Lucio's Dock", (-768, 3712), 's', (2, 1.5), 'zone:ol_dock', 'Lucio lives here'),
]
OLYMPUS_GATES = [('north gate', (-1536, 11008), 'n'), ('south-west gate', (-8704, 3584), 'sw'),
                 ('east gate', (256, 6656), 'e')]
OLYMPUS_DOCK_START = (-768, 3456)        # the jetty leaves the dock's door
OLYMPUS_DOCK_END = (1536, 1792)          # the jetty's end over the void, the celestial boat
SOUL_STORAGE = dict(door=(-6400, 9472), facing='s', room_at=(-6400, 10112), room=(1024, 1280))
ANTS_LOOKOUT = (-9088, 6144)             # a balustraded terrace on the west rim

# ------------------------------------------------------------------------------------------------ points
# kind: corner (the step-off), sign, toll, merchant, lamp, bottle, hatch, scarab, chest, statue, mirror, door, vault,
# plaque, sewer, rope, lookout. hook: A3's hook if one exists (or a request). text: the source line it uses.
POINTS = [
    # the corners (corners.yml): the step-off at the tip and its zone board within 400
    dict(id='poi:corner_fire', kind='corner', space='room:fire_corner', at=(-30464, 20480), hook='m38.corner_fire',
         text="'Fire Zone' (aaze0089:0) on the tip's board; 'What do you seek?' (:6)"),
    dict(id='poi:corner_air', kind='corner', space='room:air_corner', at=(30464, 20480), hook='m38.corner_air',
         text="'Air Zone' (aazex109:0); 'What do you seek?' (:6)"),
    dict(id='poi:corner_earth', kind='corner', space='room:earth_corner', at=(30464, -20480), hook='m38.corner_earth',
         text="'Earth Zone' (aazex112:0); 'What do you seek?' (:5)"),
    dict(id='poi:corner_water', kind='corner', space='room:water_corner', at=(-30464, -20480),
         hook='m38.corner_water', text="'Water Zone' (aaze0092:0); 'What do you seek?' (:8)"),
    # rest stop signs (the huts are dressing)
    dict(id='board:rest_fire', kind='board', space='room:fire_corner', at=(-27392, 17664), text="'Rest Stop' (aazex105:0)"),
    dict(id='board:rest_air', kind='board', space='room:air_corner', at=(27392, 17664), text="'Rest Stop'"),
    dict(id='board:rest_earth', kind='board', space='room:earth_corner', at=(27392, -17664), text="'Rest Stop'"),
    dict(id='board:rest_water', kind='board', space='room:water_corner', at=(-27392, -17664), text="'Rest Stop'"),
    dict(id='board:rest_north', kind='board', space='room:north_crossing', at=(-2560, 19456), text="'Rest Stop'"),
    dict(id='board:rest_east', kind='board', space='room:east_rest', at=(16384, 19456), text="'Rest Stop' (aazex105:0)"),
    dict(id='board:rest_junction', kind='board', space='room:east_junction', at=(29184, -4608), text="'Rest Stop'"),
    dict(id='board:rest_south', kind='board', space='room:south_rest', at=(16384, -17408), text="'Rest Stop' (aazex108:0)"),
    dict(id='board:rest_rope', kind='board', space='room:rope_head', at=(-25088, -4864), text="'Rest Stop'"),
    # boards
    dict(id='board:skyroad_board', kind='board', space='room:rope_head', at=(-23552, -5120),
         text="'XEEN Skyroad' (aaze0092:1), at the inner road's start, facing the rope"),
    dict(id='board:joes_rope', kind='board', space='room:rope_head', at=(-27648, -7680), text="'Eat at Joe's' (aaze0091:0)"),
    dict(id='board:joes_south', kind='board', space='room:south_toll', at=(-6656, -17408), text="'Eat at Joe's' (aazex100:0)"),
    dict(id='board:joes_camp', kind='board', space='room:skywaymen_camp', at=(-17664, -17408), text="'Eat at Joe's' (aaze0096:0)"),
    dict(id='board:speeding_north', kind='board', space='room:north_toll', at=(6912, 19456), text="'Speeding??' (aazex101:0)"),
    dict(id='board:speeding_east', kind='board', space='room:east_junction', at=(27136, -7168), text="'Speeding???' (aazex109:1)"),
    dict(id='board:danger_road', kind='board', space='room:smoke_post', at=(-26880, 5376),
         text="'DANGER!  Mega Dragon' (aaze0090:0) at the dragon road's foot"),
    dict(id='board:danger_watch', kind='board', space='room:griffin_watch', at=(-16384, 17152),
         text="'DANGER!  Mega Dragon' (aaze0093:0) on the south lip, facing the roost"),
    dict(id='board:lake_board', kind='board', space='room:sky_lake', at=(13824, -3584), text="'Sky Lake' (aazex107:0)"),
    # tolls (A3 hooks to ask for; the bandits a placed peaceful group each, question 3)
    dict(id='poi:toll_north', kind='toll', space='room:north_toll', at=(5632, 18432),
         text="'Pay us 10,000 gold or else!' / '1) OK. 2) Or else WHAT?' (aaze0097:2-3)"),
    dict(id='poi:toll_east', kind='toll', space='room:mud_wharf', at=(28160, 6656),
         text="'You have invaded our territory.  Appease us with 10,000 gold or face our wrath!' (aazex109:3-4)"),
    dict(id='poi:toll_south', kind='toll', space='room:south_toll', at=(-5632, -18432),
         text="'Many apologies, good folks, but this is a robbery. ...' (aazex100:2-3)"),
    dict(id='poi:toll_west', kind='toll', space='room:west_toll', at=(-28160, -12288),
         text="'Hold!  The toll for passing this part of the road is 10,000 gold!' (aaze0092:3-4)"),
    # the merchants of the elements (riddles)
    dict(id='poi:merchant_smoke', kind='merchant', space='room:smoke_post', at=(-29440, 3328),
         text="'Between Fire and Air I constantly travel ... What's my cargo?' smoke (aaze0090:4-10)"),
    dict(id='poi:merchant_dust', kind='merchant', space='room:north_crossing', at=(-128, 19712),
         text="'Between Air and Earth ...' dust (aaze0097:4-10)"),
    dict(id='poi:merchant_steam', kind='merchant', space='room:steam_post', at=(6912, -19456),
         text="'Between Fire and Water ...' steam (aazex104:4-10)"),
    dict(id='poi:merchant_mud', kind='merchant', space='room:mud_wharf', at=(29440, 4352),
         text="'Between Water and Earth ...' mud (aazex110:0-6)"),
    # genie lamps (Q-D27)
    dict(id='poi:lamp_tired', kind='lamp', space='room:griffin_watch', at=(-17408, 19456),
         text="'(yawn)  The people before you used up two wishes.  There's one left.' (aaze0093:11-14)"),
    dict(id='poi:lamp_kind', kind='lamp', space='room:east_rest', at=(17664, 17664),
         text="'Thank you for releasing me.  I like you, and I will grant you one wish.' (aazex105:11-14)"),
    dict(id='poi:lamp_angry', kind='lamp', space='room:genie_rock', at=(-10240, -7168),
         text="'What took you so long? ... Two thousand years is simply unacceptable.' (aaze0099:0-7); a wish trap"),
    # bottles
    dict(id='poi:bottle_genies', kind='bottle', space='room:broken_launch', at=(-14080, -4864),
         text="'Evil Genies NEVER let their victims off the hook--they will always kill someone.' (aazex103:1)"),
    dict(id='poi:bottle_test', kind='bottle', space='room:south_rest', at=(17408, -19456),
         text="'The test of the elements is merely difficult, not impossible.' (aazex103:2)"),
    dict(id='poi:bottle_a2', kind='bottle', space='room:sky_lake', at=(14336, -7424),
         text="'Help!  I'm stranded on an air island in A2 at 12,14.' (aazex107:2)"),
    dict(id='poi:bottle_c3', kind='bottle', space='room:sky_lake', at=(18432, -7936),
         text="'Help!  I'm stranded on an air island in C3 at 7,0.' (aazex107:3)"),
    # scarab sellers (question 5)
    dict(id='poi:scarab_rahib', kind='scarab', space='room:sky_lake', at=(13568, -6272),
         text="Rahib the Scarab Merchant, Fire scarab 300 gems (aazex107:4-5)"),
    dict(id='poi:scarab_wardoz', kind='scarab', space='room:sky_lake', at=(13568, -5888),
         text="Wardoz the Blue, electricity (aazex107:6-7)"),
    dict(id='poi:scarab_clara', kind='scarab', space='room:sky_lake', at=(13568, -5504),
         text="Clara the Cold (aazex107:8-9)"),
    dict(id='poi:scarab_dorion', kind='scarab', space='room:sky_lake', at=(13568, -6656),
         text="Dorion the Energy Merchant, Kinetic Scarab 600 gems (aazex107:10-11)"),
    # roof hatches and doors to other maps
    dict(id='poi:hatch_dd08', kind='hatch', space='room:north_tower_hatch', at=(5632, 14592),
         text="'Descend to the North Tower?' (aazex101:4)"),
    dict(id='poi:hatch_dd06', kind='hatch', space='room:south_tower_hatch', at=(5632, -14336),
         text="'Descend into the South Tower?' (aazex104:0)"),
    dict(id='poi:hatch_dd07', kind='hatch', space='room:east_junction', at=(29440, -6912),
         text="'Descend to the East Tower?' (aazex111:4)"),
    dict(id='poi:hatch_dd14', kind='hatch', space='room:blackfang_hatch', at=(23296, 13568),
         text="'Descend to Castle Blackfang?' (aazex109:5)"),
    dict(id='poi:hatch_dd05', kind='hatch', space='room:rope_head', at=(-28416, -6144),
         text="'Enter West Tower?' (aaze0091:1)"),
    dict(id='poi:hatch_dd02', kind='hatch', space='room:water_corner', at=(-27136, -17920),
         text="'Descend into Ellinger's Tower?' (aaze0092:5)"),
    dict(id='poi:hatch_dd03', kind='hatch', space='room:water_corner', at=(-26624, -19456),
         text="'Descend into Castle Kalindra?' (aaze0092:6)"),
    dict(id='poi:hatch_dd17', kind='hatch', space='room:roost', at=(-19456, 9216), hook='q-d26 (new)',
         text="'Descend to Castle Alamar?' / 'The door is locked.  Scratched on the surface are some words: The "
              "Megadragon has the key!' (aaze0089:4-5)"),
    dict(id='poi:sky_door', kind='door', space='room:pyramid_cap', at=(9984, 3584),
         text="'Enter the Pyramid?' (aazex102:0); DD-15's sky door"),
    dict(id='poi:rope', kind='rope', space='room:rope_head', at=(-25088, -6656), hook='m30.grove_rope (D1 side)',
         text="'Pull up the rope?' (aaze0091:6); 'Descend to the Darkness Below?' (:5); 'Bucket o' Darkness' (:7)"),
    # chests (treasure level 6)
    dict(id='poi:chest_hoard', kind='chest', space='room:roost', at=(-18176, 10240),
         text="the Megadragon's hoard (Q-D26's artifact, A2/A3)"),
    dict(id='poi:chest_stranded_west', kind='chest', space='room:stranded_west', at=(-24320, 12800),
         text="the stranded traveller's strongbox, by his bones"),
    dict(id='poi:chest_stranded_south', kind='chest', space='room:stranded_south', at=(-5888, -10752),
         text="the second castaway's strongbox, under a lean-to"),
    dict(id='poi:chest_camp', kind='chest', space='room:skywaymen_camp', at=(-15360, -19200),
         text="the skywaymen's strongbox"),
    dict(id='poi:chest_launch', kind='chest', space='room:broken_launch', at=(-16384, -2560),
         text="a lost traveller's pack on the jetty"),
    # Olympus (A4's doors are added from BUILDINGS; these are the map's own)
    dict(id='poi:mirror', kind='mirror', space='zone:olympus', at=(-4608, 7168), hook='house 4807 (thing:ol_mirror)',
         text="The Mirror of Olympus (A4 house 4807; qbit 119012)"),
    dict(id='poi:statue_1', kind='statue', space='zone:olympus', at=(-5632, 8192), hook='m31.statue_1', text="prophecy 1"),
    dict(id='poi:statue_2', kind='statue', space='zone:olympus', at=(-3584, 8192), hook='m31.statue_2', text="prophecy 2"),
    dict(id='poi:statue_3', kind='statue', space='zone:olympus', at=(-5632, 6144), hook='m31.statue_3', text="prophecy 3"),
    dict(id='poi:statue_4', kind='statue', space='zone:olympus', at=(-3584, 6144), hook='m31.statue_4', text="prophecy 4"),
    dict(id='poi:soul_storage', kind='vault', space='zone:olympus', at=(-6400, 9472), hook='m31.soul_storage',
         text="Soul Storage's vault door (needs m30.done); the box on the last shelf"),
    dict(id='poi:true_name', kind='plaque', space='zone:olympus', at=(-6400, 10496), hook='m31.true_name_plaque',
         text="'All beings have a true name. Alamar's true name, for instance, is Sheltem.'"),
    dict(id='poi:sewer_stair', kind='sewer', space='zone:olympus', at=(-8704, 8704),
         text="the Olympus Sewer's stair under a marble grate (DD-26, Q-D28)"),
]

# the six Olympus house doors and the dock become POIs too (d7_brief adds them from BUILDINGS)

# ------------------------------------------------------------------------------------------------ monsters
ROWS = {11562: ('Griffin', 48, 2784, 'fly'), 11594: ('Sky Golem', 75, 6375, 'walk'),
        11650: ('Cloud Dragon', 70, 5600, 'fly'), 11592: ('Cloud Golem', 50, 3000, 'walk'),
        11654: ('Megadragon', 125, 16875, 'fly')}
GROUPS = [  # placed, hostile at load; space for the census; at: the group's middle
    dict(id='pop:watch_griffins', actor=11562, count=3, space='room:griffin_watch', at=(-16896, 18944)),
    dict(id='pop:watch_griffins_b', actor=11562, count=2, space='room:griffin_watch', at=(-15616, 17920)),
    dict(id='pop:lookout_griffins', actor=11562, count=2, space='room:west_lookout', at=(-27648, 12800)),
    dict(id='pop:south_griffins', actor=11562, count=2, space='link:s3', at=(1024, -17920)),
    dict(id='pop:rope_griffins', actor=11562, count=3, space='link:w3', at=(-27648, -2048)),
    dict(id='pop:launch_golems', actor=11594, count=3, space='room:broken_launch', at=(-15360, -3072)),
    dict(id='pop:air_road_golems', actor=11594, count=2, space='link:n5', at=(22528, 18432)),
    dict(id='pop:east_road_golems', actor=11594, count=3, space='link:e1', at=(28160, 10752)),
    dict(id='pop:cap_dragons', actor=11650, count=3, space='room:pyramid_cap', at=(6144, 6144)),
    dict(id='pop:cap_dragons_b', actor=11650, count=2, space='room:pyramid_cap', at=(11776, 1536)),
    dict(id='pop:east_dragons', actor=11650, count=3, space='link:e1', at=(24576, 9216)),
    dict(id='pop:fire_road_golems', actor=11592, count=3, space='link:n1', at=(-22272, 18432)),
    dict(id='pop:north_road_golems', actor=11592, count=3, space='link:n4', at=(9728, 18432)),
    dict(id='pop:mud_road_golems', actor=11592, count=3, space='link:e2', at=(28160, 0)),
    dict(id='pop:earth_road_golems', actor=11592, count=3, space='link:e3', at=(28160, -12288)),
    dict(id='pop:earth_south_golems', actor=11592, count=2, space='link:s1', at=(22528, -18432)),
    dict(id='pop:steam_road_golems', actor=11592, count=3, space='link:s2', at=(10752, -18432)),
    dict(id='pop:camp_golems', actor=11592, count=3, space='room:skywaymen_camp', at=(-16384, -18176)),
    dict(id='pop:water_road_golems', actor=11592, count=2, space='link:s5', at=(-23040, -18432)),
]
BOSS = dict(id='pop:megadragon', actor=11654, count=1, space='room:roost', at=(-19456, 9216), leash=1024)
BREATH_MARGIN = 5888          # D-54: Ice Blast's 5,120 + 768, kept from every walkable place but its own road
BANDITS = [  # placed peaceful at the tolls; hostile on a refusal (question 3); not counted at load
    dict(id='pop:bandits_north', space='room:north_toll', at=(5632, 19200), count=2),
    dict(id='pop:bandits_east', space='room:mud_wharf', at=(28928, 6656), count=2),
    dict(id='pop:bandits_south', space='room:south_toll', at=(-5632, -19200), count=2),
    dict(id='pop:bandits_west', space='room:west_toll', at=(-28928, -12288), count=2),
]

# ------------------------------------------------------------------------------------------------ arrivals
# kind: town (keeps the town buffer, D-15), arrival, return, both. facing: compass letter. z: floor.
ARRIVALS = [
    dict(id='entrance:olympus_dock', space='zone:olympus', at=(-640, 3200), facing='n', kind='town',
         neighbour='house:lucio', how="Lucio's celestial boats from Castleview's and Sandcaster's jetties and "
         "Lakeside's dock (D-5.3, routes 424-426, after m30.done): the jetty's town end, facing into town. The boats "
         "only sail up. m31.arrival on the first landing."),
    dict(id='entrance:olympus_square', space='zone:olympus', at=(-4608, 6400), facing='n', kind='town',
         neighbour='mirror', how="The Darkside mirrors (Olympus' 4807 once touched) and Town Portal: by the mirror."),
    dict(id='entrance:d1_rope', space='room:rope_head', at=(-24576, -6656), facing='e', kind='both',
         neighbour='rope:d1', how="D1's Dark Grove rope (m30.grove_rope, D-23): the top of the rope, facing east "
         "down the inner road. 'Pull up the rope?' here goes back down to D1's rope foot."),
    dict(id='entrance:p1_return', space='room:fire_corner', at=(-27136, 17408), facing='se', kind='return',
         neighbour='plane:p1', how="P1's way out after the sleeper (corners.yml): by the Fire Corner's Rest Stop."),
    dict(id='entrance:p2_return', space='room:air_corner', at=(27136, 17408), facing='sw', kind='return',
         neighbour='plane:p2', how="P2's way out (corners.yml): by the Air Corner's Rest Stop."),
    dict(id='entrance:p3_return', space='room:earth_corner', at=(27136, -17408), facing='nw', kind='return',
         neighbour='plane:p3', how="P3's way out (corners.yml): by the Earth Corner's Rest Stop."),
    dict(id='entrance:p4_return', space='room:water_corner', at=(-27136, -17408), facing='ne', kind='return',
         neighbour='plane:p4', how="P4's way out (corners.yml): by the Water Corner's Rest Stop."),
    dict(id='entrance:dd08_roof', space='room:north_tower_hatch', at=(5632, 15104), facing='n', kind='arrival',
         neighbour='roof:dd08', how="DD-08 Northern Tower's roof stair (A8), one way up."),
    dict(id='entrance:dd06_roof', space='room:south_tower_hatch', at=(5632, -14848), facing='s', kind='arrival',
         neighbour='roof:dd06', how="DD-06 Southern Tower's roof stair (A7), one way up."),
    dict(id='entrance:dd07_roof', space='room:east_junction', at=(29184, -6656), facing='w', kind='arrival',
         neighbour='roof:dd07', how="DD-07 Eastern Tower's roof (A7), one way up."),
    dict(id='entrance:dd14_roof', space='room:blackfang_hatch', at=(23552, 14080), facing='ne', kind='arrival',
         neighbour='roof:dd14', how="DD-14 Castle Blackfang's roost trapdoor (A8), one way up."),
    dict(id='entrance:dd05_roof', space='room:rope_head', at=(-28416, -5632), facing='e', kind='arrival',
         neighbour='roof:dd05', how="DD-05 Western Tower's roof (A8), one way up."),
    dict(id='entrance:dd02_roof', space='room:water_corner', at=(-27136, -18432), facing='ne', kind='arrival',
         neighbour='roof:dd02', how="DD-02 Ellinger's Tower's top floor (A8), one way up."),
    dict(id='entrance:dd03_roof', space='room:water_corner', at=(-26624, -19968), facing='ne', kind='arrival',
         neighbour='roof:dd03', how="DD-03 Castle Kalindra's third floor (A8; stage 4), one way up."),
    dict(id='entrance:dd15_sky', space='room:pyramid_cap', at=(10752, 3584), facing='w', kind='both',
         neighbour='door:dd15', how="DD-15 Great Pyramid's sky door (A8), both ways after m30.done."),
    dict(id='entrance:dd17_roof', space='room:roost', at=(-18688, 8448), facing='w', kind='both',
         neighbour='door:dd17', how="DD-17 Castle Alamar's roof hatch (A8): down with the Megadragon's key (Q-D26); "
         "up from Alamar's top floor once it is open."),
    dict(id='entrance:dd26_stair', space='zone:olympus', at=(-8704, 8192), facing='e', kind='town',
         neighbour='door:dd26', how="DD-26 Olympus Sewer (A8, Q-D28): its stair under the marble grate."),
]

# ------------------------------------------------------------------------------------------------ falls
# The sky over the Darkside: 3 x 2 zones by the source squares. Each lands on its surface map at entrance:d7_fall.
# landing: the proposed point on that map (map units of the surface map), z its ground, facing; near: why there.
FALLS = [
    dict(id='fall:d6', map='xeen_d6.odm', key='D6', owner='A6', squares='A1-B2', x=(-HALF[0], -SQUARE[0]), y=(0, HALF[1]),
         landing=(13824, -7680, 1664), facing='s', near="before the Necropolis' gate (entrance:necropolis_gate "
         "(13824, -6656)), 1,024 south: the mirror inside (pass) leads back to Olympus"),
    dict(id='fall:d5', map='xeen_d5.odm', key='D5', owner='A6', squares='C1-D2', x=(-SQUARE[0], SQUARE[0]), y=(0, HALF[1]),
         landing=(0, -8704, 1248), facing='n', near="1,536 south of the Great Pyramid's door (entrance:dd15_door "
         "(0, -7168)): its sky door leads back up after m30.done"),
    dict(id='fall:d4', map='xeen_d4.odm', key='D4', owner='A6', squares='E1-F2', x=(SQUARE[0], HALF[0]), y=(0, HALF[1]),
         landing=(5632, -13312, 1120), facing='w', near="Lakeside's square, 1,024 east of entrance:lakeside_square "
         "(4608, -13312): the ferry dock's Olympus slot (route 426) and the mirror"),
    dict(id='fall:d1', map='xeen_d1.odm', key='D1', owner='A6', squares='A3-B4', x=(-HALF[0], -SQUARE[0]), y=(-HALF[1], 0),
         landing=(-6656, 6144, 1152), facing='s', near="1,024 north of Lucio's Jetty (entrance:lucio_jetty (-6656, "
         "5120)), outside Castleview's Queen's Gate side: the boats go back up, and the Dark Grove rope is 8,300 "
         "north (the grove itself is full of electrapedes, 7 within 3,072 of the rope's foot)"),
    dict(id='fall:d2', map='xeen_d2.odm', key='D2', owner='A6', squares='C3-D4', x=(-SQUARE[0], SQUARE[0]), y=(-HALF[1], 0),
         landing=(15872, -6656, 1056), facing='s', near="1,024 before the Southern Tower's door (entrance:dd06_door "
         "(15872, -7680)): its roof leads up"),
    dict(id='fall:d3', map='xeen_d3.odm', key='D3', owner='A5', squares='E3-F4', x=(SQUARE[0], HALF[0]), y=(-HALF[1], 0),
         landing=(-15360, 11776, 1440), facing='e', near="outside Sandcaster's south gate (entrance:south_gate "
         "(-14336, 12800)), 1,400 south-west of it, by the Sky Stair and Lucio's Jetty (house 4649)"),
]


def fall_zone(x, y):
    for f in FALLS:
        if f['x'][0] <= x < f['x'][1] and f['y'][0] <= y < f['y'][1]:
            return f
    return FALLS[-1]


# ------------------------------------------------------------------------------------------------ cameras
CAMERAS = {
    # the arrival: the top of the Dark Grove rope, looking east down the inner road to Olympus far off
    'arrival': dict(at=(-24576, -6656), z=1024 + 176, yaw_deg=24, pitch_deg=-3, fov_deg=72,
                    note="entrance:d1_rope, eye 176 over the cloud, facing east-north-east down the inner road"),
    # the signature: Olympus across the cloud roads, from the Pyramid's Door looking west up at the city
    'signature': dict(at=(6144, 4608), z=1440 + 176, yaw_deg=164, pitch_deg=0, fov_deg=72,
                      note="on the east causeway at the Pyramid's Door, eye 176, facing west at Olympus 11,000 away"),
}

TEXTURES = [  # (name, where, status)
    ('xccloud', 'cloud tops of every island and road (X8, X9)', 'shipped (world)'),
    ('xccloudsd', 'cloud sides, undersides and hanging roots', 'shipped (world)'),
    ('7tws1f', "the Skyroad's paved band, rest-stop pads, Olympus' streets (Celeste marble, as X9's flags)", 'MM7'),
    ('t66floor', 'rope-bridge decks (X8)', 'MM7'),
    ('Hwm2WALL', "Olympus' white marble walls (MM7 Celeste)", 'MM7'),
    ('Hwm1b', "Olympus' marble base and plinths", 'MM7'),
    ('Hwp1bWALL', "Olympus' pale panels, the temple", 'MM7'),
    ('HWM2RF', "Olympus' roofs (and X8's rope rails)", 'MM7'),
    ('T3S2B', "gold band and capitals", 'MM7'),
    ('7trimda', 'trim', 'MM7'),
    ('CWDL', "Olympus' gates, left leaf (CWDR the right, mirrored)", 'MM7'),
    ('CWDR', "Olympus' gates, right leaf", 'MM7'),
    ('Hwm2d', "Olympus' house doors", 'MM7'),
    ('sgWEAPON', 'the Forge of the Gods sign', 'MM7'),
    ('7sgtvrn', 'the Nectar House sign', 'MM7'),
    ('7sgtrain', 'the Hall of Heroes sign', 'MM7'),
    ('sgLIGHT', 'the Light guild sign', 'MM7'),
    ('sgspirit', 'the Spirit guild sign', 'MM7'),
    ('(liquid) water', "the Sky Lake's water: the engine's indoor liquid (engine/liquids/liquids.yml), L3 names it",
     'engine'),
    ('xwcloudst', "the hatches' cloud-stone surrounds (XD-04/XD-12's sky openings)", 'shipped (world)'),
    ('xdpyrdor', "the Pyramid's sky door (D5's pyramid door)", 'shipped (world)'),
]
NEW_TEXTURES = [
    ('xsroadln', "the Skyroad's dashed lane band (cloud-stone flags with a worn white dash), as P5's road if it has one; "
                 "else 7tws1f only", 'only if P5 has none to share'),
    ('xsbarge', "the elemental merchants' barges: a gilded sky-barge hull, four tints by element in one sheet", 'new'),
    ('xsglow', "under the corners: a soft element glow on the cloud's underside (red, white, grey, blue), one sheet", 'new'),
]

# ================================================================================================ D-58 (2026-11-21)
# The decider's changes (briefs/d7/L1/D58_DECISION.md), applied here so the data above stays the L1 that was reviewed.
# D-1: along the ring and the inner road no stretch longer than 8,192 without a group or a POI, and every POI spot
# within 8,192 of another (the nearest-neighbour gap was 13,096): 11 groups moved, 16 POIs moved (no monster added).
# D-2: the first castaway's island moved west of the West Lookout, out of the Megadragon's reach, its bridge re-routed.
# The Blackfang hatch island and the Pyramid's Door moved a little so their POIs have neighbours. D58_MOVES records
# every move for the NOTES table: (id, before, after, why).
D58_MOVES = []


def _move(items, iid, at, why, **kw):
    for it in items:
        if it['id'] == iid:
            D58_MOVES.append((iid, tuple(it['at']), tuple(at), why))
            it['at'] = tuple(at)
            it.update(kw)
            return
    raise KeyError(iid)


# D-2: the first castaway's island west of the West Lookout, outside the ring (its bridge from the Lookout re-routed)
_move(SPACES, 'room:stranded_west', (-31104, 15104), 'D-2: out of the breath (leash circle >= 5,888 from it)',
      purpose="'Help! I'm stranded on an air island in A2 at 12,14.' (a bottle at the Sky Lake): a skeleton and his "
              "strongbox, on a lone cloud west of the West Lookout, out of the Megadragon's reach (D-58 D-2).")
_move(POINTS, 'poi:chest_stranded_west', (-31104, 15104), 'D-2: with its island')
# islands moved so their POIs have a neighbour within 8,192 (D-1)
_move(SPACES, 'room:blackfang_hatch', (25088, 15104), 'D-1: the hatch within 8,192 of the Air Corner tip',
      extent=(2048, 1792))
_move(POINTS, 'poi:hatch_dd14', (25088, 15104), 'D-1: with its island')
_move(ARRIVALS, 'entrance:dd14_roof', (25088, 14592), 'D-1: beside the moved hatch')
_move(SPACES, 'room:pyramid_cap', (9728, 2560), "D-1: the sky door within 8,192 of the Sky Lake's stalls")
_move(POINTS, 'poi:sky_door', (11008, 2560), 'D-1: with the capstone')
_move(ARRIVALS, 'entrance:dd15_sky', (11776, 2560), 'D-1: with the capstone')
# POIs moved within their islands (D-1)
_move(POINTS, 'poi:merchant_dust', (-1536, 17024), 'D-1: toward the causeway head and the North Toll')
_move(POINTS, 'poi:lamp_tired', (-17152, 17408), "D-1: on the Watch's south lip, 7,241 from the hoard")
_move(POINTS, 'poi:lamp_kind', (17664, 17408), 'D-1: toward the Blackfang hatch')
_move(POINTS, 'poi:hatch_dd07', (26624, -5632), "D-1: the junction's west side, toward the Sky Lake")
_move(ARRIVALS, 'entrance:dd07_roof', (27136, -6144), 'D-1: beside the moved hatch')
_move(POINTS, 'poi:bottle_test', (28160, -17920), "D-1: to the Earth Corner's Rest Stop bench (the corner had no "
      "neighbour)", space='room:earth_corner')
_move(POINTS, 'poi:toll_south', (-6912, -18432), "D-1: Joe's Corner's west side")
_move(POINTS, 'poi:chest_camp', (-14848, -18944), "D-1: the camp's east side")
_move(POINTS, 'poi:merchant_smoke', (-28928, 3200), "D-1: the Smoke Post's south side")
_move(POINTS, 'poi:hatch_dd05', (-27648, -4608), "D-1: the Rope's Head's north side")
_move(ARRIVALS, 'entrance:dd05_roof', (-27136, -5120), 'D-1: beside the moved hatch')
for _k, (_pid, _xy) in enumerate((('poi:scarab_dorion', (14080, -3840)), ('poi:scarab_rahib', (14336, -3584)),
                                  ('poi:scarab_wardoz', (14592, -3328)), ('poi:scarab_clara', (14848, -3072)))):
    _move(POINTS, _pid, _xy, "D-1: the stalls on the lake's north-west shore, toward the Pyramid's Door")
_move(POINTS, 'board:skyroad_board', (-24576, -7168), "L2: off the launch road's walking line, facing the rope")
_move(POINTS, 'poi:bottle_a2', (15360, -2816), 'D-1: by the stalls (on the cloud, off the water)')
_move(POINTS, 'poi:bottle_c3', (19840, -4480), "D-1: the lake's east shore, toward the junction")
# groups moved along the roads (D-1)
_move(GROUPS, 'pop:watch_griffins_b', (-9216, 18432), 'D-1: onto the north road (n2)', space='link:n2')
_move(GROUPS, 'pop:east_road_golems', (28160, 12800), 'D-1: north on the east road (e1)')
_move(GROUPS, 'pop:earth_south_golems', (21504, -18432), 'D-1: along s1')
_move(GROUPS, 'pop:steam_road_golems', (14080, -18432), 'D-1: along s2, by the South Rest Stop')
_move(GROUPS, 'pop:south_griffins', (1024, -18432), 'D-1: along s3 (5,538 from the Southern Tower roof arrival)')
_move(GROUPS, 'pop:lookout_griffins', (-28160, 11072), "D-1: just south of the Lookout (w4)", space='link:w4')
_move(GROUPS, 'pop:east_dragons', (-20736, -4864), 'D-1: over the launch road (the inner road had 9,395 empty)',
      space='link:launch_road')
_move(GROUPS, 'pop:launch_golems', (-11264, 768), "D-1: guarding the causeway up to Olympus' south-west gate",
      space='link:olympus_west')
_move(GROUPS, 'pop:cap_dragons', (4608, 4768), "D-1: over the east causeway")
_move(GROUPS, 'pop:cap_dragons_b', (13056, -1024), "D-1: with the capstone, over the lake road (3,328 from the sky door)")
_move(GROUPS, 'pop:earth_road_golems', (28160, -11776), 'first fight from entrance:dd07_roof 5,724 (was 6,229 after D-1)')
_move(GROUPS, 'pop:rope_griffins', (-27264, -2048), 'L2: over the road (w3) itself')
_move(GROUPS, 'pop:watch_griffins', (-16640, 19456), 'L2: off the paved bands across the Watch')
SPACE = {s['id']: s for s in SPACES}

# ================================================================================================ D-69 (2026-11-21)
# Q67 (b): FD-01 Alamar Depths' way up names its own point on D7, at the hatch's point (the one DD-17's roof hatch
# names), facing w. DD-17 is gone after M33, so FD-01 does not name dd17_roof.
ARRIVALS.append(dict(id='entrance:fd01_roof', space='room:roost', at=(-18688, 8448), facing='w', kind='both',
                     neighbour='door:fd01', how="FD-01 Alamar Depths' rubble shaft (A8, D-69 Q67): up the ladder "
                     "after M33 once Q-D26's roof is unlocked; down by Alamar's roof hatch."))

# ================================================================================================ A6 s24 (2026-11-21)
# S's sky-barges and the celestial boat (level_generation/decorations/xeen_skybarge_claude, rows 4051-4055) replace
# the stand-in barge blocks. Each barge lies along its island's rim fully over the void, its port gangplank on the
# island (S's scripts/placement.py: at, the island floor as floor_height, facing = the prow's way; port = facing + 90).
# Not boardable: each merchant stands on the island at the gangplank's foot (`keep`: not snapped 384 inside the rim).
BARGES = {
    'smoke': dict(decoration='xeen_skybarge_fire', at=(-29277, 2797), floor=1152, facing=325, merchant=(-29021, 3165)),
    'dust': dict(decoration='xeen_skybarge_air', at=(-1553, 20276), floor=1280, facing=184, merchant=(-1518, 19830)),
    'steam': dict(decoration='xeen_skybarge_water', at=(6976, -19504), floor=768, facing=56, merchant=(6606, -19252)),
    'mud': dict(decoration='xeen_skybarge_earth', at=(29449, 4231), floor=1152, facing=22.5, merchant=(29277, 4645)),
}
# Lucio's celestial boat alongside the jetty's north-east side, prow out to the void (the jetty's own direction)
SKYBOAT = dict(decoration='xeen_skyboat', at=(1429, 2423), floor=1780, facing=327)
SKYBOAT_RAIL_OPEN = 832      # jetty rail1 ends this far short of the jetty's end: the open stretch lies by the boat
for _cargo, _b in BARGES.items():
    _move(POINTS, 'poi:merchant_' + _cargo, _b['merchant'], "A6 s24: at the foot of S's barge's gangplank"
          + (" (off the Olympus causeway's mouth)" if _cargo == 'dust' else ''), keep=True)
