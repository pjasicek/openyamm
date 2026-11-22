"""The four elemental planes of Xeen (P1 Fire, P2 Air, P3 Earth, P4 Water): the phase 6 L1 design as data (A6's planes
sub-agent, session 15, 2026-11-21). One family: every plane has the same skeleton, so the four read as one set.

    arrival (entrance:d7_fall, quiet)  ->  the statue and its plaque (a Step)  ->  the test of the element (its arena:
    "Accept the test of X?" calls m38.test_x, the guardians rise)  ->  the sleeper's chamber (behind a gate the passed
    test opens; the couch, m38.sleeper_x, the test's chest)  ->  the return dais (to D7's entrance:pN_return)
    plus the way up at the arrival (always open), 27 placed hostiles in 10 groups of 2-3, two side places with a
    chest and a device, and the source's nine hazard cells as the plane's own hazard.

planes_geom.py measures it, planes_render.py draws it, planes_brief.py writes devdocs/xeen/briefs/pN/L1/ from it,
planes_concepts.py paints it, board_planes.py boards a pair. Units are map units (512 a cell), x east, y north, the
room's middle at (0, 0); floors are heights over the arrival (0). Nothing here is read by the game or the studio.

Pair 1 (now): p1, p2. Pair 2 (when resumed): add PLANES['p3'] and PLANES['p4'] in the same shape.
"""

# ------------------------------------------------------------------------------------------------ common
def xp(level):
    """A2's XP = L(L+10) (monsters.yml header), as D5 counted."""
    return level * (level + 10)


TARGET_KILL_XP_PER_MEMBER = 124100 / 4        # MAPS §0: P1-P4 124.1k per member for all four, 31.0k per plane
WALK_SPEED = 384                              # units a second, walking (P5's figure); running twice that

# Elemental family rows (A2's source/monsters.yml, block 11620; elemental golems 11590). New rows are requests.
ROWS = {
    # D-58 C6: one naming pattern per element: Lesser X Elemental (55), X Elemental (62), the source's name on the 70s
    # (Fire Blower, Whirlwind, Earth Blaster, Tidal Terror), Sleeper's Guardian of X (75). Fire's 11620-11623 exist (A2
    # renamed them); Air/Earth/Water's 55s are 11624-11626; the nine 62/70/75 rows are A2's, in monster_data.txt since
    # 2026-11-21: Air 11700-11702, Water 11710-11712, Earth 11720-11722.
    'fire_a': dict(actor='Lesser Fire Elemental (11620)', level=55, short='Lesser Fire Elemental', id=11620),
    'fire_b': dict(actor='Fire Elemental (11621)', level=62, short='Fire Elemental', id=11621),
    'fire_c': dict(actor='Fire Blower (11622)', level=70, short='Fire Blower', id=11622),
    'fire_d': dict(actor="Sleeper's Guardian of Fire (11623)", level=75, short="Sleeper's Guardian of Fire",
                   id=11623),
    'lava_golem': dict(actor='Lava Golem (11593)', level=55, short='Lava Golem', id=11593),
    'air_a': dict(actor='Lesser Air Elemental (11624)', level=55, short='Lesser Air Elemental', id=11624),
    'air_b': dict(actor='Air Elemental (11700)', level=62, short='Air Elemental', id=11700),
    'air_c': dict(actor='Whirlwind (11701)', level=70, short='Whirlwind', id=11701),
    'air_d': dict(actor="Sleeper's Guardian of Air (11702)", level=75,
                   short="Sleeper's Guardian of Air", id=11702),
    'earth_a': dict(actor='Lesser Earth Elemental (11626)', level=55, short='Lesser Earth Elemental', id=11626),
    'earth_b': dict(actor='Earth Elemental (11720)', level=62, short='Earth Elemental', id=11720),
    'earth_c': dict(actor='Earth Blaster (11721)', level=70, short='Earth Blaster', id=11721),
    'earth_d': dict(actor="Sleeper's Guardian of Earth (11722)", level=75,
                   short="Sleeper's Guardian of Earth", id=11722),
    'water_a': dict(actor='Lesser Water Elemental (11625)', level=55, short='Lesser Water Elemental', id=11625),
    'water_b': dict(actor='Water Elemental (11710)', level=62, short='Water Elemental', id=11710),
    'water_c': dict(actor='Tidal Terror (11711)', level=70, short='Tidal Terror', id=11711),
    'water_d': dict(actor="Sleeper's Guardian of Water (11712)", level=75,
                   short="Sleeper's Guardian of Water", id=11712),
    'octopod_b': dict(actor='Great Octopod (11471)', level=60, short='Great Octopod', id=11471),
}

# The common questions: asked once, in P1's NOTES; the other planes refer to them by number (C1 ...).
COMMON_QUESTIONS = [
    dict(id='C1', title='The plane as a map: size and form',
         options=["(a) One compact open-air BLV per plane (X9's and P5's route), a room of 26 x 26 cells with about "
                  "45-50 M units of walkable floor: a small M dungeon by floor and monsters, one element's form each "
                  "(Fire a lava crater, Air islands in open sky, Earth the `xeen_plane_earth` bowl, Water a flooded "
                  "hall).",
                  "(b) Smaller, S class (at most 20 M units, 15 sectors): the test and the chamber only.",
                  "(c) MM8's way: whole ODMs (1 ODM each)."],
         evidence="MAPS §3: 'S-M dungeon scale each; MM8's planes were whole ODMs; these are deliberately small'. "
                  "The source's planes are 16 x 16 squares each, the same as a dungeon level. 30 monsters sit between "
                  "S (15-30) and M (45-75).",
         default='(a)', depends='L2 geometry, the texture class (S cap 30), the walking length.'),
    dict(id='C2', title='The arrival from D7: falling damage',
         options=["(a) None: the party lands standing on the arrival shelf (`entrance:d7_fall`); the drop is told by "
                  "D7's corner text ('You step off.').",
                  "(b) A short real fall: the party appears 768 above the shelf and takes the engine's falling "
                  "damage (Feather Fall none), D-6.2's 'a third of HP at most' rule.",
                  "(c) Damage by script, one line."],
         evidence="The source's corner square moves the party to the plane's run position with no damage. D-6.2 and "
                  "D-56 test every sky fall for survivability; a fall into an unknown arena would add a test per plane.",
         default='(a)', depends="A3's corner hooks (m38.corner_x) and D7's corner script; the plane's arrival test."),
    dict(id='C3', title='What the test of the element is',
         options=["(a) 'Accept the test of X?' (A3's m38.test_x) raises the guardians in the arena: the Sleeper's "
                  "Guardian (75) and two Greater elementals (70), the source's own beast; killing the three passes "
                  "the test (a map variable) and opens the gate to the sleeper's chamber. Declining does nothing.",
                  "(b) The source's test: accepting costs every member 2,500 damage of the element (resistance "
                  "applies; at party level 56-60 that kills); the guardians stand in the arena from the start.",
                  "(c) (a), and the guardians also stand in the arena before the test (no click needed)."],
         evidence="Source maze0025/26: the test square asks 'Accept the test of Fire?' and deals 2,500 fire (2,500 "
                  "electric on Air), setting a flag that stops the chest burning. m38.yml: 'Yes calls the hook, the map "
                  "opens the test (its arena and guardians)'. MAPS: 'sleepers' guardians 75'.",
         default='(a)', depends="A3's m38.test_x text and the passed flag; A2's guardian rows; the arena's wiring."),
    dict(id='C4', title='What the passed test opens',
         options=["(a) The gate to the sleeper's chamber, where the couch and the test's chest stand: the test is "
                  "the way to the sleeper.",
                  "(b) The chest only, as the source (its chest burns until the test is passed); the sleeper's chamber "
                  "is open from the start.",
                  "(c) Both separately: the chamber open, the chest sealed in the arena until the test."],
         evidence="The source's sleeper does not check the test; only the chest does. The family names the guardians "
                  "'Sleeper's Guardian'. m38.sleeper_x needs only Chosen One and M37's four reflectors.",
         default="(a): the guardian guards the sleeper; one gate, no burning chest to explain.",
         depends='The chamber gate (a door with a state), A3 (no new hook: the gate reads the map variable).'),
    dict(id='C5', title='The way out (corners.yml default_way_out)',
         options=["(a) Two ways, both to D7's `entrance:pN_return` by the corner's rest stop: the way up at the "
                  "arrival, always open (the source's exit square, a fall back to its Skyroad corner), and the "
                  "sleeper's return dais, shown once the sleeper is awake (no walk back).",
                  "(b) The return dais only, after the sleeper (the corners.yml default as written); Town Portal and "
                  "Lloyd's Beacon before.",
                  "(c) The way up only (the source)."],
         evidence="maze0025 (13,2) and maze0026 (2,2) are fall squares to Skyroad A1 (3,13) and F1 (12,13): the "
                  "source's way back is always open. A party that cannot pass the test must not be stuck.",
         default='(a)', depends="D7's p1_return ... p4_return arrivals; one exit preset per way (D-24)."),
    dict(id='C6', title='The guardians and the greater elementals: rows and names',
         options=["(a) One family per element: A2 adds Air, Earth and Water rows for B (62), C (70) and the "
                  "Sleeper's Guardian (75) beside Fire's 11621-11623 (11624-11626 exist as XD-19's lesser "
                  "elementals at 55), named as the family ('Greater Air Elemental').",
                  "(b) As (a), with the source's names on the C rows: Fire Blower, Whirlwind, Earth Blaster, Tidal "
                  "Terror.",
                  "(c) One neutral Sleeper's Guardian row for all four planes, skinned by element."],
         evidence="monsters.yml: the family is Fire-typed (11620-11623); XD-19's lesser elementals of the other three "
                  "elements exist (D-47). XEEN_SYSTEMS: the source's planes hold eight of one greater elemental each.",
         default='(b): the names are the source\'s and read well in the Xeen voice.',
         depends="A2's rows; S's skins (MM6's air, MM7's water and earth elementals as in D-47)."),
    dict(id='C7', title='The sleepers and the statues: what stands there',
         options=["(a) One sleeper model for all four (a giant of the element lying in an Ancient stasis couch, its "
                  "element in the couch's glow), four skins; one statue model per element on a common plinth with "
                  "the plaque (S).",
                  "(b) The sleeper as a peaceful placed figure (an A2 row, unkillable as D-51) on a plain couch.",
                  "(c) Decorations from shipped MM6-MM8 statues only."],
         evidence="Source: the same object sprite (46) for all four sleepers and (40) for all four statues; the "
                  "sleepers speak of a 'Grunfeld field generator' (Ancient technology).",
         default='(a)', depends='S models (4 statues, 1 sleeper with 4 skins, the couch, the pedestal, the dais).'),
    dict(id='C8', title='Points of interest and chests per plane',
         options=["(a) The sparse-special band: 10-12 POIs (MAP_CRAFT §6: sparse special maps at least 10) and 2 "
                  "chests (S's 0-3; MM8's planes 0-2): the test's chest and one trapped cache, each with a reason, "
                  "plus one find (a camp, a wreck) and one buff device.",
                  "(b) The source: the test, the statue, the sleeper and one chest (4-5 POIs, 1 chest).",
                  "(c) MM8's planes: 0-3 POIs, 0-2 chests."],
         evidence="MM8 elemf 3 POIs and 2 chests, elema 1 and 1, elemw 0 and 0 (MAP_CRAFT_CALIBRATION); the source "
                  "has one chest a plane.",
         default='(a)', depends='The census in totals; A2 treasure 6.'),
]

# Requests common to all four (one line each in the report).
COMMON_REQUESTS = [
    ('A2', "landed 2026-11-21: map_stats rows 9115-9118 as D-58's ROWS, the nine C6 rows (Air 11700-11702, Water "
           "11710-11712, Earth 11720-11722) and the Fire family's new names (11620-11623); nothing more asked but "
           "treasure 6 for the two chests a plane."),
    ('A3', "written by the sixteenth session's start: m38.test_<element>_passed (qbits 111764-111767, through "
           "Xeen.planeTestCheck), m38.way_up_<element> and m38.dais_<element> (the exit presets' lines), "
           "Xeen.toPlane and Xeen.PlaneArrivals (C2), SkyFalls `p2`, and source/npcs/planes.yml (hazards, devices, "
           "finds, notes); still asked: ORIGINAL_LINES rows aaze0025:0, 2-8 and aaze0026-0028:0-7."),
    ('S', "C7: one sleeper and one couch with four element skins, four statues from the elemental models on one "
          "plinth with a plaque, the pedestal and the dais (P5's disc in each element's stone), the way-up effects, "
          "the per-plane devices; the nine elemental tier skins (C6). Until they land, L4 builds their spots by name "
          "and marks them blocked (no stand-ins)."),
    ('D7', "the four corners' drops land on entrance:d7_fall here (Xeen.PlaneArrivals, A3); both ways out land on "
           "D7's entrance:pN_return by the corner's rest stop (corners.yml), facing the road."),
    ('A1', "confirm only (D-58 relays 1, 2 and 4): hidden placed actors shown mid-visit in an open-air BLV, "
           "PressurePlate faces in an open-air sector, water volumes, constant currents and swimmers under an "
           "open-air BLV's outdoor view."),
    ('O', "openAirMaps for P1-P4 at install; MAPS §0 and §3's P rows as D-58's ROWS AND NUMBERS."),
]

# D-58 (devdocs/xeen/briefs/d7/L1/D58_DECISION.md, 2026-11-21): the answers to the common questions.
COMMON_DECISIONS = {
    'C1': "(a) One compact open-air BLV per plane, 26 x 26 cells, about 44-51 M walkable; Dungeon S for textures "
          "(cap 30, at most 4 new).",
    'C2': "(a) No falling damage: the party lands standing on the arrival shelf after D7's 'You step off.' "
          "(A3's m38.corner_<element> moves the party directly, without keepHeight: Xeen.toPlane).",
    'C3': "(a) 'Accept the test of X?' raises the Sleeper's Guardian (75) and two greater elementals (70) from the "
          "pit, a hidden group; when all three are dead the test is passed and its qbit set (P-1); declining does "
          "nothing; a party that leaves mid-fight finds the guardians still shown on return.",
    'C4': "(a) The gate to the sleeper's chamber, where the couch, the test's chest and the dais are.",
    'C5': "(a) Two ways out, both `exit` presets (D-24) to D7's entrance:pN_return: the way up at the arrival, "
          "always open, and the return dais after the sleeper. Town Portal and Lloyd's Beacon work; Fly is not cast.",
    'C6': "(b) Lesser X Elemental (55), X Elemental (62), the source's name on the 70s (Fire Blower, Whirlwind, Earth "
          "Blaster, Tidal Terror), Sleeper's Guardian of X (75); nine new rows (A2), Fire's 11620-11623 renamed.",
    'C7': "(a) One sleeper and one couch with four element skins; four statues from the elemental models on one "
          "plinth with a plaque; the pedestal and the dais P5's disc in the element's stone (S; no stand-ins at L4).",
    'C8': "(a) 10-12 POIs and 2 chests at treasure 6 (the test's chest and one trapped cache), one find and one buff "
          "device.",
}
# P-1 and the test qbits (decided numbers; A3 names them).
TEST_QBITS = {'fire': 111764, 'air': 111765, 'earth': 111766, 'water': 111767}
SLEEPER_QBITS = {'fire': 111760, 'air': 111761, 'earth': 111762, 'water': 111763}
# D-58's kill XP per member (ROWS AND NUMBERS) for each plane, checked against the measure.
D58_KILL_XP = {'p1': 31540, 'p2': 32040, 'p3': 32040, 'p4': 32380}
P2_MIN_LIP = 192            # P-2: every wall or lip on the approaches at least this high over whatever touches it
DROP_REACH = 1024           # P-2 "not by any drop": no higher floor within this of the protected floor

# ------------------------------------------------------------------------------------------------ P1 Fire
P1 = dict(
    key='p1', code='P1', element='fire', Element='Fire', stem='xeen_p1.blv', id='xeen_p1',
    name='Plane of Fire of Xeen', map_stats_id=9115, music=10, environment='mountains',
    source_map=25, source_text='aaze0025',
    source_lines=dict(sleeper='0, 2, 7-8', plaque='3-4', test='6', chest='5'), corner='north-west', corner_sky='Sky A1',
    room=(26, 26),
    form='lava field in a crater',
    form_why=("Fire is a lava field: a lake of lava in a ring of black cliffs, crossed by causeways of cooled crust "
              "between basalt shelves. The source's plane is all lava; MM8's elemf is 74 % lava. A crater closes "
              "the room without walls in the sky and keeps the map compact; the lava is the hazard and the floor."),
    pitch=("The Plane of Fire of Xeen: a lake of lava in a crater of black glass under a sky of red smoke. Causeways "
           "of cooled crust run between basalt shelves; vents flare underfoot. On its rise the Crucible, a ring of "
           "obsidian where the test of Fire waits; beyond it, in a hall cut into the tallest spire, the Fire Sleeper "
           "on his couch."),
    purpose=("M38 (Act VI, party 56-60): the plaque (Step One), the test of Fire, the Fire Sleeper (m38.sleeper_fire, "
             "award 412) and the test's chest. Reached by stepping off D7's north-west corner after answering "
             "'Fire'; left by the heat column at the arrival or the return dais by the sleeper, both to D7."),
    mood=("Hot, red and loud: the lava's slow churn, the crack of cooling crust, the roar of the vents. Danger "
          "played straight; the plaque and the sleeper's 'confidence is at 100%' are the world's wink."),
    sky=dict(preset='plane_fire', shipped=True,
             why=("MM8's red-smoke plane sky from the engine library (no sun, ember glow, storm clouds); the crater "
                  "rim hides the horizon, so no below_horizon is needed.")),
    daylight=dict(ambient_rgb=[150, 84, 60], sun_rgb=[255, 150, 90], night_scale_rgb=[255, 255, 255], sun_gain=2),
    view_distance_scale=1.0,
    datum='room:landing',
    lava_level=-64,
    low=dict(id='zone:lava', kind='lava', name='The lava lake', level=-64, banks='all',
             shape="the crater's floor round every shelf and causeway",
             purpose=("Walkable and burning (`lavtyl`: the engine's lava floor, fire damage while standing in it, "
                      "Levitate lifts the party); banks of crust along every causeway and shelf, so the party walks "
                      "out anywhere (question 1)."),
             rule=("The lava burns as MM's lava floors (`lavtyl`, D-40): crust banks within 64 of every lava edge "
                   "(a lip of at most 64 over the lava) and ramps up every shelf, so a party in the lava always walks "
                   "out; none to the Sleeper's Hall or its bridge, which stand 320-448 over the lava (P-2). No falls: "
                   "the crater wall closes the room.")),
    critical=['room:landing', 'room:statue', 'room:islet', 'room:arena', 'room:chamber'],
    gate_kind='portcullis',
    falls_text='none (the crater wall)',
    rim=dict(height=2400, kind='cliffs',
             text="a ring of black glassy cliffs 2,000-2,800 high round the lava, lava falls in two places"),
    spaces=[
        dict(id='room:landing', name='The Cinder Shelf', at=(4096, -4224), extent=(2560, 2304), floor=0, seed=1,
             safe=True, kind='crust',
             shape="a low shelf of cooled black crust in the crater's south-east, the heat column at its corner",
             purpose="Arrival from D7's north-west corner (entrance:d7_fall) and the way up (the heat column). Quiet."),
        dict(id='room:statue', name='The Flame Statue', at=(512, -2560), extent=(2304, 2048), floor=64, seed=2,
             kind='crust', shape="a round crust shelf, the statue of Fire on its plinth in the middle",
             purpose="The statue and its plaque (m38.plaque_fire, Step One); the causeways part here."),
        dict(id='room:islet', name='The Ember Islet', at=(-896, -256), extent=(1792, 1536), floor=96, seed=3,
             kind='crust', shape="a small crust islet in the lava, on the straight way north",
             purpose="The straight way to the Crucible; the Ember Font (a font of liquid fire)."),
        dict(id='room:spires', name='The Basalt Spires', at=(3968, 896), extent=(2560, 2816), floor=128, seed=4,
             kind='crust', shape="a shelf of basalt columns and spires, the long way round to the east",
             purpose="The east loop: lava golems and elementals among the columns."),
        dict(id='room:arena', name='The Crucible', at=(256, 3456), extent=(3328, 3072), floor=256, seed=5,
             kind='arena', shape="a round ring of black glass on a basalt rise, lava welling in a pit at its middle",
             purpose=("The test of Fire: the pedestal at the south gate asks 'Accept the test of Fire?'; the "
                      "guardians rise from the pit. The Sleeper's Gate on the west side.")),
        dict(id='room:chamber', name="The Sleeper's Hall", at=(-4096, 4480), extent=(2560, 2048), floor=384,
             seed=6, kind='hall', safe=True,
             shape=("a hall open to the sky, cut into the tallest spire of the crater wall, floored in black "
                    "glass, the spire's rock walling its back and sides (P-2)"),
             purpose=("The Fire Sleeper on his couch (m38.sleeper_fire); the test's chest; the return dais "
                      "(after the sleeper wakes).")),
        dict(id='room:west_shelf', name='The Glass Shelf', at=(-4480, 768), extent=(2304, 2816), floor=128,
             seed=7, kind='crust', shape="a shelf of black glass under the west wall, a lava fall beside it",
             purpose="The west loop: Fire Elementals and the Fire Blowers that roam it."),
        dict(id='room:vents', name='The Vent Field', at=(-3712, -3840), extent=(2816, 2304), floor=0, seed=8,
             kind='crust', shape="a crust field pocked with glowing vents (the source's nine)",
             purpose="The vents (the plane's hazard); the burnt camp of a fire-walker and his ember cache."),
    ],
    links=[
        dict(id='link:causeway_s', a='room:landing', b='room:statue', kind='path', width=768, style='crust'),
        dict(id='link:causeway_n', a='room:statue', b='room:islet', kind='path', width=640, style='crust'),
        dict(id='link:causeway_c', a='room:islet', b='room:arena', kind='path', width=640, style='crust',
             end_b=(256, 1920)),
        dict(id='link:causeway_e', a='room:statue', b='room:spires', kind='path', width=640, style='crust'),
        dict(id='link:causeway_ne', a='room:spires', b='room:arena', kind='path', width=640, style='crust'),
        dict(id='link:causeway_w', a='room:statue', b='room:vents', kind='path', width=640, style='crust'),
        dict(id='link:causeway_nw', a='room:vents', b='room:west_shelf', kind='path', width=640, style='crust'),
        dict(id='link:causeway_wn', a='room:west_shelf', b='room:arena', kind='path', width=640, style='crust'),
        dict(id='link:sleepers_gate', a='room:arena', b='room:chamber', kind='bridge', width=640, style='glass',
             gate=True, notes="an obsidian bridge from the Crucible's west gate; the gate opens on the passed test"),
    ],
    walk=[(3776, -3904), (512, -2560), (-896, -256), (256, 1792), (256, 3456), (-1408, 3968), (-4224, 4736),
          (-4736, 3968)],
    places=[
        dict(id='entrance:d7_fall', kind='arrival', space='room:landing', at=(3776, -3904), face='nw',
             text="Arrival from D7's north-west corner: on the Cinder Shelf, facing north-west over the lava."),
        dict(id='exit:way_up', kind='exit', space='room:landing', at=(4864, -4864), face='nw',
             text=("The heat column: a pillar of shimmering air rising from a ring of fire-stones in the shelf's "
                   "corner. An exit preset ('Ride the heat back to the Skyroads?'), always open, to D7's "
                   "entrance:p1_return (the source's (13,2), a fall back to Skyroad A1).")),
        dict(id='poi:statue', kind='statue', space='room:statue', at=(512, -2432), face='se',
             text=("The statue of Fire: a tall figure of flame in red stone on a black plinth. A3's m38.plaque_fire: "
                   "'A message at the base of the statue reads: Step One: When the time is right, activate the "
                   "machines in the four corners of the other side of the world.' (aaze0025:3-4)")),
        dict(id='poi:font', kind='device', space='room:islet', at=(-1152, -448), face='s',
             text=("The Ember Font: a basin of liquid fire on the islet. Drunk from: +20 Fire resistance for a day "
                   "(once a day; 'The fire is cool and refreshing.'), the world's wink on the stock well line.")),
        dict(id='poi:test', kind='pedestal', space='room:arena', at=(256, 2048), face='s',
             text=("The test pedestal at the Crucible's south gate: 'Accept the test of Fire?' (aaze0025:6). Yes "
                   "calls A3's m38.test_fire; the map raises the guardians from the pit (set:test).")),
        dict(id='landmark:pit', kind='landmark', space='room:arena', at=(256, 3584), face='s',
             text="The Crucible's pit: lava welling in a ring of black glass, where the guardians rise."),
        dict(id='gate:sleeper', kind='gate', space='room:arena', at=(-1536, 3904), face='w',
             text="The Sleeper's Gate: a portcullis of black glass at the Crucible's west side, open once the test "
                  "is passed (state:test_passed)."),
        dict(id='poi:sleeper', kind='sleeper', space='room:chamber', at=(-4352, 4864), face='se',
             text=("The Fire Sleeper on his couch: A3's m38.sleeper_fire, three states (not Chosen; 'Awaiting "
                   "Grunfeld field activation.'; awake, award 412, 10,500 XP).")),
        dict(id='poi:test_chest', kind='chest', space='room:chamber', at=(-3328, 5248), face='s',
             text="The test's chest (treasure 6): the source's chest, now behind the gate the test opens."),
        dict(id='exit:dais', kind='dais', space='room:chamber', at=(-4864, 3904), face='e',
             text=("The return dais: a disc of black glass, shown once the Fire Sleeper is awake (m38.fire); an exit "
                   "preset to D7's entrance:p1_return. No walk back.")),
        dict(id='poi:ember_cache', kind='chest', space='room:vents', at=(-4736, -4352), face='ne',
             text="The ember cache (treasure 6, a fire trap): a fire-walker's iron box by his burnt camp."),
        dict(id='poi:camp', kind='device', space='room:vents', at=(-3968, -4736), face='n',
             text=("The fire-walker's camp: a burnt bedroll, a kettle and a note: 'Day 3. The boots work. The "
                   "feet do not.' (ours) A find: Fire Resistance potions.")),
        dict(id='landmark:lava_fall', kind='landmark', space='room:west_shelf', at=(-6016, 1536), face='e',
             text="A lava fall pouring down the crater wall beside the Glass Shelf."),
        dict(id='poi:spire_glass', kind='device', space='room:spires', at=(4480, 1920), face='w',
             text=("A seam of red crystal in a spire: hit with a weapon, it rings ('The spire hums. Nothing else "
                   "happens.'); the first time, a shard: a red gem (a find)."),
             ),
    ],
    hazard=dict(kind='vents', count=9, rule=("The source's nine vent squares: glowing cracks in the crust (a small "
                                               "floor face each). Stepping on one: one time in three 50 fire damage "
                                               "to each member, 'A vent flares!' (resistance applies)."),
                cells=[(-4480, -3200), (-2816, -3328), (-3712, -4352), (-2432, -4224), (-4864, -3712),
                       (4480, 256), (3200, 1792), (-4864, 2048), (-3712, 128)]),
    groups=[
        dict(id='pop:statue_lesser', row='fire_a', count=2, at=(1408, -2944), space='room:statue', first=True),
        dict(id='pop:spires_golems', row='lava_golem', count=3, at=(3712, -384), space='room:spires'),
        dict(id='pop:spires_lesser', row='fire_a', count=3, at=(4352, 1408), space='room:spires'),
        dict(id='pop:spires_elementals', row='fire_b', count=3, at=(3584, 1792), space='room:spires'),
        dict(id='pop:arena_east', row='fire_b', count=3, at=(1408, 2816), space='room:arena'),
        dict(id='pop:vents_lesser', row='fire_a', count=3, at=(-3200, -3328), space='room:vents'),
        dict(id='pop:vents_golems', row='lava_golem', count=2, at=(-4480, -4224), space='room:vents'),
        dict(id='pop:shelf_elementals', row='fire_b', count=3, at=(-4608, 1408), space='room:west_shelf'),
        dict(id='pop:shelf_greater', row='fire_c', count=2, at=(-4224, -128), space='room:west_shelf'),
        dict(id='pop:islet_lesser', row='fire_a', count=3, at=(-640, 128), space='room:islet'),
    ],
    test_group=[dict(row='fire_d', count=1), dict(row='fire_c', count=2)],
    test_at=(256, 3584),
    camera=dict(at=(3712, -3840), eye=176, yaw_deg=130.0, pitch_deg=-6.0, fov=74.0,
                what=("The arrival: from the Cinder Shelf north-west over the lava, the causeway to the Flame Statue, "
                      "the Crucible's black ring on its rise beyond, the spires to the right, the Sleeper's spire "
                      "in the crater wall far left, the heat column behind.")),
    textures=dict(
        shipped=[('lavtyl', "MM8 lava (D6's; the engine burns a floor of this name)", 'the lava lake'),
                 ('gcav2flr', "MM8 Plane of Fire's black lava rock", 'crust causeways and shelves'),
                 ('6voltyl', "MM6 Gharik's Forge volcanic floor", 'the shelves round the statue and the vents'),
                 ('vlcwl1', "MM6 volcanic wall with lava seams", 'the crater cliffs'),
                 ('vlcwl3a', "MM6 dark volcanic rock", "basalt spires and the Crucible's rise"),
                 ('gnecwal1', "MM8 Plane of Fire's crackled dark stone", "the Sleeper's Hall walls"),
                 ('gcav1flr', "MM8 Plane of Fire's dark rock floor", "the Sleeper's Hall floor"),
                 ('orfyrlga', "MM6 molten lava", 'the two lava falls and the pit'),
                 ('xcorefire', "XD-19's fire core (A7)", "the sleeper couch's glow panel")],
        new=[('xpfvent', "a crack of glowing lava in black crust, one per vent face (the source's nine vents)"),
             ('xpfglass', "obsidian: black volcanic glass with red depths, the Crucible's ring and the gate")],
        estimate=16),
    questions=[
        dict(id='Q1', title='The lava: how much it hurts and how the party gets out',
             options=["(a) The lava is the floor: `lavtyl` faces burn as MM's lava (fire damage while standing in it, "
                      "Levitate none); every causeway and shelf edge within 64 of the lava has a crust bank to walk "
                      "out; the raised shelves have ramps.",
                      "(b) Lava kills (a death trigger, as the world rim).",
                      "(c) Lava is decoration under invisible walls."],
             evidence="D-40/D6: `lavtyl`, never water, burns. The engine burns a floor face named lava*/lavtyl "
                      "(IndoorMovementController) and Levitate lifts the party (as MM8).",
             default='(a)', depends='L2 banks and ramps; the measure lava_bank_max.'),
        dict(id='Q2', title='The vents',
             options=["(a) Nine small floor faces with the source's rule (1 in 3: 50 fire to each member), marked by "
                      "a glowing crack texture; five in the Vent Field, four on the loops; none on the critical "
                      "causeways.",
                      "(b) Vents erupt on a timer (a set piece every few seconds) with a visible spurt.",
                      "(c) No vents."],
             evidence="maze0025: nine squares call one event: random 1-3, on 3 Damage 50 fire.",
             default='(a)', depends="A3's line; A1's floor-event check; the new texture xpfvent."),
        dict(id='Q3', title='Sky',
             options=["(a) MM8's shipped `plane_fire` (engine library) by name.",
                      "(b) A new Xeen preset `xeen_plane_fire` (A6): plane_fire with a lower ember glow and "
                      "slow-drifting ash clouds.",
                      "(c) The Darkside amber day (xeendark1)."],
             evidence="WORLD_DESIGN §4: the planes' themes are plane_fire, plane_air, underwater and a new earth "
                      "preset. plane_fire has no sun and no stars: a timeless plane.",
             default='(a): shipped and cheapest to reverse.', depends="atmosphere.yml; A6's sky file."),
    ],
    requests=[
        ('A2', "row 9115: environment mountains, music 10; Lava Golem 11593 used at 55 (5 placed)."),
        ('A3', "P1's hazard line 'A vent flares!'; the Ember Font's line and buff (+20 Fire resistance, a day); the "
               "camp's note (ours) and the spire's line."),
        ('A6', "new textures xpfvent and xpfglass (Q2), registered in source/textures.yml; plane_fire or a Xeen "
               "preset (Q3)."),
        ('S', "the statue of Fire; the Ember Font (a basin of liquid fire); the fire-walker's camp (bedroll, kettle)."),
    ],
)

# ------------------------------------------------------------------------------------------------ P2 Air
P2 = dict(
    key='p2', code='P2', element='air', Element='Air', stem='xeen_p2.blv', id='xeen_p2',
    name='Plane of Air of Xeen', map_stats_id=9116, music=9, environment='plains',
    source_map=26, source_text='aaze0026',
    source_lines=dict(sleeper='0-1, 6-7', plaque='2-3', test='5', chest='4'), corner='north-east', corner_sky='Sky F1',
    room=(26, 26),
    form='islands in open sky',
    form_why=("Air is open sky over nothing: islands of wind-carved pale stone and packed cloud, linked by "
              "cloud-stone bridges, the sky above and below. The source's plane is all cloud; MM8's elema is islands "
              "with no terrain. X8 and X9 built this route; the plane is their small, stranger cousin."),
    pitch=("The Plane of Air of Xeen: islands of wind-carved white stone hanging in a sky with no ground under it. "
           "Bridges of cloud-stone cross the gaps; the wind sings in a ring of hollow stones. In the south-east the "
           "Eye of the Winds, a ring of standing stones where the test of Air waits; from it the Stair of Wind climbs "
           "to the Sleeper's Aerie, the highest island, where the Air Sleeper dreams."),
    purpose=("M38 (Act VI, party 56-60): the plaque (Step Two), the test of Air, the Air Sleeper (m38.sleeper_air, "
             "award 413) and the test's chest. Reached by stepping off D7's north-east corner after answering 'Air'; "
             "left by the updraft at the arrival or the return dais in the aerie, both to D7."),
    mood=("Bright, cold and roaring: wind in the ears, the stones' long notes, nothing under the bridges. The "
          "lightning out of a clear sky is played straight."),
    sky=dict(preset='plane_air', shipped=True,
             why=("MM8's open-sky plane preset from the engine library: deep blue zenith, pale horizon, cumulus, the "
                  "sky continuing below the horizon (below_horizon: sky), which the gaps need.")),
    daylight=dict(ambient_rgb=[118, 122, 134], sun_rgb=[255, 250, 240], night_scale_rgb=[255, 255, 255], sun_gain=3),
    view_distance_scale=1.5,
    datum='room:landing',
    critical=['room:landing', 'room:statue', 'room:arena', 'room:chamber'],
    gate_kind='stairs',
    falls_text='caught: back to entrance:d7_fall (Q1)',
    fall=dict(below=-1500, to='in-map',
              text=("A fall off any island (below -1,500): the wind throws the party back onto the Gale Landing: "
                    "Xeen.skyFallTo(\"p2\") moves it to entrance:d7_fall in this map from Xeen.SkyFallHeight (850) "
                    "above it, with falling damage (D-6.2's third of HP at most; Feather Fall none; D-58 P2 Q1). "
                    "Tested in D-54's shape: from three islands, two runs each, HP checked after 20 s.")),
    spaces=[
        dict(id='room:landing', name='The Gale Landing', at=(-4096, -4352), extent=(2560, 2304), floor=0, seed=11,
             safe=True, kind='isle', shape="a flat island of white stone, the updraft's ring at its west edge",
             purpose="Arrival from D7's north-east corner (entrance:d7_fall) and the way up (the updraft). Quiet."),
        dict(id='room:statue', name='The Wind Statue', at=(-384, -1920), extent=(2560, 2304), floor=128, seed=12,
             kind='isle', shape="a round island of packed cloud, the statue of Air on a stone plinth",
             purpose="The statue and its plaque (m38.plaque_air, Step Two); bridges part here."),
        dict(id='room:stones', name='The Singing Stones', at=(0, 1920), extent=(2560, 2560), floor=256, seed=13,
             kind='isle', shape="a high island crowned by a ring of hollow standing stones that sing in the wind",
             purpose="The Singing Stones (a device); the middle of the plane."),
        dict(id='room:kite_isle', name='The Kite Isle', at=(-4224, 3584), extent=(2560, 2560), floor=320, seed=14,
             kind='isle', shape="a ragged island of wind-carved stone, a wrecked basket in its rocks",
             purpose=("The source's chest corner: a balloonist's basket with no balloon and his cache; the Whirlwinds "
                      "that roam it.")),
        dict(id='room:arena', name='The Eye of the Winds', at=(3968, -3072), extent=(3328, 3328), floor=256,
             seed=15, kind='arena', shape="a round island ringed by twelve standing stones, the wind circling inside",
             purpose=("The test of Air: the pedestal at the west gate asks 'Accept the test of Air?'; the guardians "
                      "form in the eye. The foot of the Stair of Wind on the north side.")),
        dict(id='room:chamber', name="The Sleeper's Aerie", at=(4224, 3456), extent=(2560, 2304), floor=768,
             seed=16, kind='hall', safe=True, shape="the highest island, a pale dome open on all sides over the couch",
             purpose=("The Air Sleeper on his couch (m38.sleeper_air); the test's chest; the return dais (after the "
                      "sleeper wakes).")),
    ],
    links=[
        dict(id='link:bridge_s', a='room:landing', b='room:statue', kind='bridge', width=768, style='cloudstone'),
        dict(id='link:bridge_e', a='room:statue', b='room:arena', kind='bridge', width=640, style='cloudstone',
             end_b=(2176, -3072)),
        dict(id='link:bridge_n', a='room:statue', b='room:stones', kind='bridge', width=640, style='cloudstone'),
        dict(id='link:bridge_w', a='room:stones', b='room:kite_isle', kind='bridge', width=640, style='cloudstone'),
        dict(id='link:bridge_se', a='room:stones', b='room:arena', kind='bridge', width=640, style='cloudstone'),
        dict(id='link:stair_of_wind', a='room:arena', b='room:chamber', kind='bridge', width=768, style='stair',
             gate=True, notes="the Stair of Wind: cloud-stone steps climbing 512 north; its gate opens on the test"),
    ],
    walk=[(-4096, -4096), (-384, -1920), (2304, -3072), (3968, -3072), (3968, -1408), (4096, 2560), (4864, 3840),
          (3456, 2944)],
    places=[
        dict(id='entrance:d7_fall', kind='arrival', space='room:landing', at=(-4096, -4096), face='ne',
             text="Arrival from D7's north-east corner: on the Gale Landing, facing north-east across the gap."),
        dict(id='exit:way_up', kind='exit', space='room:landing', at=(-5248, -4864), face='ne',
             text=("The updraft: a ring of white stones where the wind blows straight up, mist streaming skyward. An "
                   "exit preset ('Ride the wind back to the Skyroads?'), always open, to D7's entrance:p2_return (the "
                   "source's (2,2), a fall back to Skyroad F1).")),
        dict(id='poi:statue', kind='statue', space='room:statue', at=(-384, -1792), face='sw',
             text=("The statue of Air: a winged figure of white stone, robes streaming, on a plinth. A3's "
                   "m38.plaque_air: 'A message at the base of the statue reads: Step Two: Awaken the Four Sleepers "
                   "of Darkside.' (aaze0026:2-3)")),
        dict(id='poi:singing_stones', kind='device', space='room:stones', at=(0, 2176), face='s',
             text=("The Singing Stones: a ring of hollow stones. Clicked: they sing; +20 Air resistance and +10 Speed "
                   "for a day, once a day ('The stones sing. You feel lighter.').")),
        dict(id='poi:test', kind='pedestal', space='room:arena', at=(2432, -3072), face='w',
             text=("The test pedestal at the Eye's west gate: 'Accept the test of Air?' (aaze0026:5). Yes calls A3's "
                   "m38.test_air; the map forms the guardians in the eye (set:test).")),
        dict(id='landmark:eye', kind='landmark', space='room:arena', at=(3968, -3072), face='s',
             text="The eye: a calm circle in the middle of the standing stones, dust and leaves turning round it."),
        dict(id='gate:sleeper', kind='gate', space='room:arena', at=(3968, -1408), face='n',
             text="The Stair of Wind's gate: a curtain of roaring wind between two stones at the Eye's north side, "
                  "stilled once the test is passed (state:test_passed)."),
        dict(id='poi:sleeper', kind='sleeper', space='room:chamber', at=(4864, 3840), face='sw',
             text=("The Air Sleeper on his couch under the dome: A3's m38.sleeper_air, three states (not Chosen; "
                   "'Awaiting Grunfeld field activation.'; awake, award 413, 10,500 XP).")),
        dict(id='poi:test_chest', kind='chest', space='room:chamber', at=(3584, 4224), face='s',
             text="The test's chest (treasure 6): the source's chest, now in the aerie the test opens."),
        dict(id='exit:dais', kind='dais', space='room:chamber', at=(3456, 2944), face='e',
             text=("The return dais: a disc of white stone, shown once the Air Sleeper is awake (m38.air); an exit "
                   "preset to D7's entrance:p2_return.")),
        dict(id='poi:basket_cache', kind='chest', space='room:kite_isle', at=(-3824, 4400), face='sw',
             text="The balloonist's cache (treasure 6, a lightning trap): his strongbox wedged in the basket."),
        dict(id='poi:basket', kind='device', space='room:kite_isle', at=(-3712, 4224), face='s',
             text=("The basket with no balloon: a wicker gondola wedged in the rocks, a logbook: 'Wind fair. Balloon "
                   "fairer. Balloon gone.' (ours) A find: Air Resistance potions.")),
        dict(id='poi:storm_cairn', kind='device', space='room:statue', at=(1024, -2560), face='w',
             text=("The storm cairn: a cairn of fused stones. Clicked: 'Lightning has struck here. Often.' The first "
                   "time, a blue gem in the glass (a find).")),
    ],
    hazard=dict(kind='storm', count=9, rule=("The source's nine storm squares: scorched patches on the islands (a "
                                               "small floor face each). Stepping on one: one time in three 50 "
                                               "electrical damage to each member, 'Lightning strikes from a clear "
                                               "sky!' (resistance applies)."),
                cells=[(-1408, -1408), (256, -1152), (-1024, 1280), (1152, 2560), (-4736, 3072), (-3456, 4480),
                       (-640, -896), (768, 1280), (-768, 2816)]),
    groups=[
        dict(id='pop:statue_west', row='air_a', count=2, at=(-1664, -2432), space='room:statue', first=True),
        dict(id='pop:statue_east', row='air_a', count=3, at=(640, -2176), space='room:statue'),
        dict(id='pop:stones_elementals', row='air_b', count=3, at=(-512, 2560), space='room:stones'),
        dict(id='pop:stones_north', row='air_a', count=3, at=(640, 3072), space='room:stones'),
        dict(id='pop:stones_lip', row='air_a', count=2, at=(1024, 1024), space='room:stones'),
        dict(id='pop:kite_elementals', row='air_b', count=3, at=(-3584, 3200), space='room:kite_isle'),
        dict(id='pop:kite_south', row='air_a', count=2, at=(-4480, 2560), space='room:kite_isle'),
        dict(id='pop:kite_greater', row='air_c', count=3, at=(-4608, 4224), space='room:kite_isle'),
        dict(id='pop:arena_approach', row='air_a', count=3, at=(4992, -4224), space='room:arena'),
        dict(id='pop:arena_rim', row='air_b', count=3, at=(5248, -2176), space='room:arena'),
    ],
    test_group=[dict(row='air_d', count=1), dict(row='air_c', count=2)],
    test_at=(3968, -3072),
    camera=dict(at=(-3584, -3712), eye=176, yaw_deg=45.0, pitch_deg=-7.0, fov=74.0,
                what=("The arrival: from the Gale Landing north-east across the gap, the bridge to the Wind Statue, "
                      "the Singing Stones' ring on its high island beyond, the Eye's standing stones to the right, "
                      "the Sleeper's Aerie high and far, the sky above and below.")),
    textures=dict(
        shipped=[('xccloud', "X8's walkable cloud top (A6)", 'the cloud island tops'),
                 ('xccloudsd', "X8's cloud sides (A6)", 'the cloud islands\' sides and undersides'),
                 ('7tws1f', "X9's cloud-stone (MM7 marble)", 'bridges, the plinth, the aerie floor'),
                 ('gwspotwl', "MM8's blue-grey rough rock", 'the stone islands\' rock'),
                 ('gwsphlfl', "MM8's pale wind-carved stone", 'the stone islands\' tops'),
                 ('t09a01', "MM8 Plane of Air's pale brick", 'the aerie dome\'s base, the stair\'s cheeks'),
                 ('gn_mtl01', "MM8 Plane of Air's grey stone", 'the standing stones'),
                 ('xcoreair', "XD-19's air core (A7)", "the sleeper couch's glow panel")],
        new=[('xpascorch', "a lightning scorch on pale stone, one per storm face (the source's nine)"),
             ('xpastone', "a hollow singing stone, pierced and wind-worn (the Singing Stones' faces)")],
        estimate=14),
    questions=[
        dict(id='Q1', title='Falls off the islands',
             options=["(a) In the map: below -1,500 the wind throws the party back onto the Gale Landing "
                      "(entrance:d7_fall) with falling damage (D-6.2's rule); the test and the plane are not lost.",
                      "(b) Out to D7's entrance:p2_return with falling damage (as the way up, the hard way).",
                      "(c) To the surface under D7's north-east corner (D6), as every sky map falls to its surface."],
             evidence="The plane is not over the world: the source has no fall from it but its exit square (to "
                      "Skyroad F1). X8, X9 and P5 fall to the surface because they hang over it.",
             default='(a)', depends="A3's Xeen.skyFall with an in-map target; P2's fall tests (D-54's shape)."),
        dict(id='Q2', title='The storm cells',
             options=["(a) Nine scorched floor faces with the source's rule (1 in 3: 50 electrical to each member); "
                      "none on bridges or in the Eye.",
                      "(b) Lightning on a timer at the storm cairn only (a set piece).",
                      "(c) None."],
             evidence="maze0026: nine squares call one event: random 1-3, on 3 Damage 50 type 3 (electrical).",
             default='(a)', depends="A3's line; xpascorch; A1's floor-event check."),
        dict(id='Q3', title='Sky',
             options=["(a) MM8's shipped `plane_air` (engine library) by name: below_horizon sky.",
                      "(b) `xeencloud` (xeen_cloud_sea) as every Xeen sky map.",
                      "(c) A new Xeen preset `xeen_plane_air` (A6): plane_air with no cloud sea below, only blue."],
             evidence="WORLD_DESIGN §4 names plane_air for the plane. The plane must not look like X8/X9/D7's cloud "
                      "sea: there is no world under it.",
             default='(a)', depends="atmosphere.yml; A6's sky file."),
        dict(id='Q4', title='Only elementals on P2?',
             options=["(a) Yes: Lesser Air Elementals (55), Air Elementals (62), Greater Air Elementals (70), as the "
                      "source (eight Whirlwinds); variety from the islands and the storm.",
                      "(b) Add a pair of Sky Golems (11594, 75) guarding the Stair of Wind's foot (over the band).",
                      "(c) Add Cloud Golems (11592, 50) as the A tier (under the band)."],
             evidence="monsters.yml: no other Air family at 55-70; rocs and griffins stop at 48.",
             default='(a)', depends="A2's rows (C6); kill XP."),
    ],
    requests=[
        ('A2', "row 9116: environment plains, music 9; the Air rows of C6 (62, 70, the guardian 75); Lesser Air "
               "Elemental 11624 used on P2 (15 placed)."),
        ('A3', "P2's hazard line 'Lightning strikes from a clear sky!'; the Singing Stones' line and buff; the "
               "logbook (ours) and the cairn's line; Xeen.skyFall to an in-map entrance (Q1)."),
        ('A6', "new textures xpascorch and xpastone, registered; plane_air or a Xeen preset (Q3)."),
        ('S', "the statue of Air; the Singing Stones (a ring of hollow standing stones); the wrecked basket; the "
              "Eye's twelve standing stones (shipped menhirs if they fit)."),
    ],
)

# ------------------------------------------------------------------------------------------------ P3 Earth
P3 = dict(
    key='p3', code='P3', element='earth', Element='Earth', stem='xeen_p3.blv', id='xeen_p3',
    name='Plane of Earth of Xeen', map_stats_id=9117, music=3, environment='mountains',
    source_map=27, source_text='aaze0027',
    source_lines=dict(sleeper='0-1, 6-7', plaque='2-3', test='5', chest='4'),
    source_summary=("MM5 maze 27, the Elemental Plane of Earth (`dark/aaze0027`, 16 x 16, every square earth; decoded, "
                    "nothing copied):\n\n"
                    "- the run position (9,9); the statue and its plaque (7,8);\n"
                    "- the test (3,4): 'Accept the test of Earth?'; yes costs 2,500 physical damage and sets a flag;\n"
                    "- the chest (13,12): 250 physical unless the flag is set; gold and three items;\n"
                    "- the Earth Sleeper (12,3), the same three answers;\n"
                    "- nine squares of falling rock: one time in three 50 physical damage;\n"
                    "- eight Earth Blasters (the greater earth elemental);\n"
                    "- the exit (2,13): a fall back to Skyroad F4 (map x112) at (13,2)."),
    corner='south-east', corner_sky='Sky F4',
    room=(26, 26),
    form='a cavern-like bowl under a dust sky',
    form_why=("Earth is a bowl of rock: terraces stepping down a great pit whose walls rise like a cavern's, under the "
              "`xeen_plane_earth` sky of brown dust with no sun and no stars. The source's plane is all earth; MM8's "
              "eleme is a cave (a BLV). The bowl keeps the cavern's weight and closure while the open-air route keeps "
              "one sky and one view; the party goes down into the earth as it went up into the air on P2."),
    pitch=("The Plane of Earth of Xeen: a bowl of raw stone under a ceiling of brown dust, its walls leaning in like a "
           "cavern's. Terraces step down the pit past a quarry no one finished, a hall of split geodes and a field of "
           "stone pillars; at the bottom the Anvil, a floor of bare bedrock ringed by monoliths where the test of "
           "Earth waits, and below it, down the Root Stair, the Sleeper's Hollow."),
    purpose=("M38 (Act VI, party 56-60): the plaque (Step Three), the test of Earth, the Earth Sleeper "
             "(m38.sleeper_earth, award 414) and the test's chest. Reached by stepping off D7's south-east corner "
             "after answering 'Earth'; left by the dust shaft at the arrival or the return dais by the sleeper, both "
             "to D7."),
    mood=("Heavy, dim and still: dust hanging in brown light, the grind of stone settling, now and then a fall of "
          "rock. The quarry's unfinished slate is the world's wink."),
    sky=dict(preset='xeen_plane_earth', shipped=True,
             why=("A6's Xeen preset (assets_dev/worlds/xeen/rendering/sky/sky.yml, corners.yml): a cavern-brown sky "
                  "of dust, no sun, no stars, dim crystal light; the bowl's walls hide its horizon.")),
    daylight=dict(ambient_rgb=[120, 104, 88], sun_rgb=[200, 176, 150], night_scale_rgb=[255, 255, 255], sun_gain=2),
    view_distance_scale=1.0,
    datum='room:landing',
    low=dict(id='zone:scree', kind='scree', name='The scree', level=-1024, banks='terraces',
             shape="the bowl's floor of loose scree and boulders between the terraces, 300-1,000 below them",
             purpose=("Walkable rubble under the terraces' cliffs: a party that drops off a terrace takes the "
                      "engine's falling damage and walks back up a scree slope on the outer side of any terrace or "
                      "under any ramp (question 1); no slope climbs to the Anvil or the Hollow."),
             rule=("A drop from a terrace into the scree is a real fall (300-1,000, the engine's falling damage; "
                   "Feather Fall none); scree slopes climb back to every terrace and ramp, none to the Anvil or the "
                   "Hollow, so the test cannot be bypassed. The bowl's wall closes the room.")),
    rim=dict(height=2600, kind='bowl', text="the bowl's leaning walls of raw stone 2,200-3,000 high"),
    critical=['room:landing', 'room:statue', 'room:pillars', 'room:arena', 'room:chamber'],
    gate_kind='stairs',
    falls_text='into the scree (falling damage), scree slopes back up (Q1)',
    spaces=[
        dict(id='room:landing', name='The Dust Ledge', at=(-4096, 4224), extent=(2560, 2304), floor=0, seed=21,
             safe=True, kind='crust', shape="a ledge of packed earth high on the bowl's north-west wall",
             purpose="Arrival from D7's south-east corner (entrance:d7_fall) and the way up (the dust shaft). Quiet."),
        dict(id='room:statue', name='The Stone Statue', at=(-512, 1792), extent=(2560, 2304), floor=-128, seed=22,
             kind='crust', shape="a broad terrace of flat stone, the statue of Earth at its middle",
             purpose="The statue and its plaque (m38.plaque_earth, Step Three); the ramps part here."),
        dict(id='room:quarry', name="The Giants' Quarry", at=(4096, 3840), extent=(2560, 2560), floor=-64, seed=23,
             kind='crust', shape="a terrace cut into steps by an old quarry, half-cut blocks still standing",
             purpose="The source's chest corner: the quarrymen's strongbox and their last block."),
        dict(id='room:geodes', name='The Geode Hall', at=(4352, 0), extent=(2304, 2816), floor=-256, seed=24,
             kind='crust', shape="a terrace of split boulders lined with amethyst and quartz",
             purpose="The Heart-geode (a device); the east loop."),
        dict(id='room:pillars', name='The Pillar Field', at=(512, -1536), extent=(2560, 2304), floor=-320, seed=25,
             kind='crust', shape="a terrace of tall stone pillars like petrified trees, the Echo Stone among them",
             purpose="The way down to the Anvil; the Echo Stone (a device)."),
        dict(id='room:west_ledge', name='The Fault Ledge', at=(-5376, 1024), extent=(1792, 2560), floor=-192,
             seed=26, kind='crust', shape="a narrow ledge along a fault in the west wall",
             purpose="The west loop from the arrival down to the Anvil; Earth Blasters roam it."),
        dict(id='room:arena', name='The Anvil', at=(-3840, -1792), extent=(3328, 3072), floor=-384, seed=27,
             kind='arena', shape="a round floor of bare bedrock ringed by twelve monoliths, cracked at its middle",
             purpose=("The test of Earth: the pedestal at the east gate asks 'Accept the test of Earth?'; the "
                      "guardians rise out of the cracked bedrock. The Root Stair's head at the south-east.")),
        dict(id='room:chamber', name="The Sleeper's Hollow", at=(-1792, -5120), extent=(2560, 2048), floor=-768,
             seed=28, kind='hall', safe=True,
             shape="a hollow at the bowl's bottom under an overhang of the wall, roots of stone hanging from it",
             purpose=("The Earth Sleeper on his couch (m38.sleeper_earth); the test's chest; the return dais (after "
                      "the sleeper wakes).")),
    ],
    links=[
        dict(id='link:ramp_n', a='room:landing', b='room:statue', kind='ramp', width=768, style='ramp'),
        dict(id='link:arch_e', a='room:statue', b='room:quarry', kind='bridge', width=640, style='arch',
             notes="a natural arch of stone over the scree"),
        dict(id='link:ramp_q', a='room:quarry', b='room:geodes', kind='ramp', width=640, style='ramp'),
        dict(id='link:ramp_g', a='room:geodes', b='room:pillars', kind='ramp', width=640, style='ramp'),
        dict(id='link:ramp_c', a='room:statue', b='room:pillars', kind='ramp', width=640, style='ramp'),
        dict(id='link:ramp_a', a='room:pillars', b='room:arena', kind='ramp', width=640, style='ramp',
             end_b=(-2304, -1792)),
        dict(id='link:fault_n', a='room:landing', b='room:west_ledge', kind='path', width=512, style='ramp'),
        dict(id='link:fault_s', a='room:west_ledge', b='room:arena', kind='ramp', width=512, style='ramp'),
        dict(id='link:root_stair', a='room:arena', b='room:chamber', kind='stairs', width=640, style='rootstair',
             gate=True, notes="the Root Stair down the bowl's bottom; a slab of stone across its head sinks on the test"),
    ],
    walk=[(-3840, 3968), (-512, 1792), (512, -1536), (-2304, -1792), (-3840, -1792), (-2816, -3200), (-2048, -5376),
          (-2816, -4736)],
    places=[
        dict(id='entrance:d7_fall', kind='arrival', space='room:landing', at=(-3840, 3968), face='se',
             text="Arrival from D7's south-east corner: on the Dust Ledge, facing south-east down into the bowl."),
        dict(id='exit:way_up', kind='exit', space='room:landing', at=(-4864, 4864), face='se',
             text=("The dust shaft: a column of pale light where dust streams upward out of the bowl. An exit preset "
                   "('Rise with the dust to the Skyroads?'), always open, to D7's entrance:p3_return (the source's "
                   "(2,13), a fall back to Skyroad F4).")),
        dict(id='poi:statue', kind='statue', space='room:statue', at=(-512, 1920), face='nw',
             text=("The statue of Earth: a squat giant of rough-hewn granite, hands on its knees, on a plinth. A3's "
                   "m38.plaque_earth: 'A message at the base of the statue reads: Step three: Bring together the Cube "
                   "of Power and the Scepter of Temporal Distortion.' (aaze0027:2-3)")),
        dict(id='poi:geode', kind='device', space='room:geodes', at=(4608, 256), face='w',
             text=("The Heart-geode: a split boulder lined with amethyst. Touched: +20 Earth resistance for a day "
                   "(once a day; 'The stone is warm.').")),
        dict(id='poi:echo', kind='device', space='room:pillars', at=(1152, -896), face='w',
             text=("The Echo Stone: a hollow pillar. Clicked: 'You shout into the stone. The plane answers, "
                   "slowly.' The first time, a find in its hollow: a sapphire.")),
        dict(id='poi:test', kind='pedestal', space='room:arena', at=(-2432, -1792), face='e',
             text=("The test pedestal at the Anvil's east gate: 'Accept the test of Earth?' (aaze0027:5). Yes calls "
                   "A3's m38.test_earth; the map raises the guardians out of the bedrock (set:test).")),
        dict(id='landmark:anvil', kind='landmark', space='room:arena', at=(-3840, -1792), face='s',
             text="The Anvil's crack: a split in the bedrock at its middle, where the guardians rise."),
        dict(id='gate:sleeper', kind='gate', space='room:arena', at=(-2816, -3200), face='se',
             text="The Root Stair's slab: a block of stone across the stair's head, sunk once the test is passed "
                  "(state:test_passed)."),
        dict(id='poi:sleeper', kind='sleeper', space='room:chamber', at=(-2048, -5504), face='n',
             text=("The Earth Sleeper on his couch under the overhang: A3's m38.sleeper_earth, three states (not "
                   "Chosen; 'Awaiting Grunfeld field activation.'; awake, award 414, 10,500 XP).")),
        dict(id='poi:test_chest', kind='chest', space='room:chamber', at=(-896, -5376), face='n',
             text="The test's chest (treasure 6): the source's chest, now in the hollow the test opens."),
        dict(id='exit:dais', kind='dais', space='room:chamber', at=(-2816, -4736), face='e',
             text=("The return dais: a disc of grey granite, shown once the Earth Sleeper is awake (m38.earth); an "
                   "exit preset to D7's entrance:p3_return.")),
        dict(id='poi:quarry_cache', kind='chest', space='room:quarry', at=(4736, 4480), face='sw',
             text="The quarrymen's strongbox (treasure 6, a falling-block trap) by their hut's ruin."),
        dict(id='poi:last_block', kind='device', space='room:quarry', at=(3584, 3200), face='s',
             text=("The last block: half-cut, a pick still in it, a slate: 'Nearly done. Back after lunch.' (ours) A "
                   "find: Earth Resistance potions.")),
    ],
    hazard=dict(kind='rockfall', count=9, rule=("The source's nine squares of falling rock: patches of fresh rubble "
                                                  "under overhangs (a small floor face each). Stepping on one: one "
                                                  "time in three 50 physical damage to each member, 'Rocks fall from "
                                                  "above!', with a short camera shake (evt.CameraShake)."),
                cells=[(3328, 4224), (4864, 3456), (3712, 4736), (3840, 512), (4864, -896), (1664, -2048),
                       (-128, -2176), (-5248, 256), (-5504, 1920)]),
    groups=[
        dict(id='pop:statue_west', row='earth_a', count=2, at=(-1408, 2304), space='room:statue', first=True),
        dict(id='pop:statue_east', row='earth_a', count=3, at=(384, 1280), space='room:statue'),
        dict(id='pop:quarry_elementals', row='earth_b', count=3, at=(3840, 3584), space='room:quarry'),
        dict(id='pop:quarry_north', row='earth_a', count=3, at=(4480, 4352), space='room:quarry'),
        dict(id='pop:geodes_south', row='earth_a', count=2, at=(4096, -768), space='room:geodes'),
        dict(id='pop:geodes_north', row='earth_b', count=3, at=(4608, 896), space='room:geodes'),
        dict(id='pop:pillars_south', row='earth_a', count=3, at=(896, -2048), space='room:pillars'),
        dict(id='pop:pillars_west', row='earth_a', count=2, at=(-384, -1152), space='room:pillars'),
        dict(id='pop:anvil_north', row='earth_b', count=3, at=(-4224, -512), space='room:arena'),
        dict(id='pop:fault_greater', row='earth_c', count=3, at=(-5376, 1024), space='room:west_ledge'),
    ],
    test_group=[dict(row='earth_d', count=1), dict(row='earth_c', count=2)],
    test_at=(-3840, -1792),
    camera=dict(at=(-3456, 3584), eye=176, yaw_deg=-62.0, pitch_deg=-8.0, fov=74.0,
                what=("The arrival: from the Dust Ledge south-east down into the bowl, the ramp to the Stone Statue, "
                      "the Pillar Field below, the Anvil's monoliths to the right at the bottom, the quarry's cut "
                      "steps and the geodes far left, the bowl's leaning walls round it all under the dust sky.")),
    textures=dict(
        shipped=[('gwspotwl', "MM8's blue-grey rough rock", "the bowl's walls"),
                 ('gwsphlfl', "MM8's pale carved stone", 'the terraces and ramps'),
                 ('vlcflora', "MM6 brown rock floor", 'the scree'),
                 ('cwb1', "MM7 Nighon Tunnels rock (DD-10's)", "the overhang over the Hollow"),
                 ('cfb1', "MM7 Nighon Tunnels floor", "the Hollow's floor"),
                 ('t19a02', "MM8 grey ashlar", 'the plinth and the monoliths'),
                 ('xdvsaph', "DD-10's sapphire vein (A6)", 'the Echo Stone'),
                 ('xdvruby', "DD-10's ruby vein (A6)", 'geode linings'),
                 ('xcoreearth', "XD-19's earth core (A7)", "the sleeper couch's glow panel")],
        new=[('xperubble', "fresh rubble under an overhang, one per rockfall face (the source's nine)"),
             ('xpegeode', "a split geode's amethyst lining (the Geode Hall's boulders, the Heart-geode)")],
        estimate=15),
    questions=[
        dict(id='Q1', title='The form: a cavern-like bowl or open sky under xeen_plane_earth',
             options=["(a) A bowl: terraces stepping down a pit whose walls lean in like a cavern's, open to the "
                      "`xeen_plane_earth` dust sky (open-air BLV); drops into the scree hurt, scree slopes lead back up.",
                      "(b) A true cavern: a closed BLV with a rock ceiling and no sky (MM8's eleme is a BLV); the "
                      "preset unused.",
                      "(c) Floating rock islands in the dust sky, as P2 but heavy (falls caught)."],
             evidence="corners.yml and lanes README give P3 the `xeen_plane_earth` preset (dust, no sun); MM8's "
                      "eleme is a cave; the source's plane is open ground.",
             default='(a): the preset, the closure and the way down into the earth.',
             depends="L2 geometry; the preset; the drop rule."),
        dict(id='Q2', title='Falling rock or quakes',
             options=["(a) The source's nine rockfall cells (1 in 3: 50 physical to each member) with a short camera "
                      "shake when one hits.",
                      "(b) Quakes: every few minutes the whole plane shakes (evt.CameraShake) and rock falls on the "
                      "nine cells for a few seconds (a timed set piece).",
                      "(c) No hazard beyond the drops."],
             evidence="maze0027: nine squares call one event: random 1-3, on 3 Damage 50 type 0 (physical). "
                      "evt.CameraShake exists (MM9 cutscenes).",
             default='(a)', depends="A3's line; xperubble; A1's floor-event check."),
        dict(id='Q3', title='Only elementals on P3?',
             options=["(a) Yes: Lesser Earth Elementals (55, 11626), Earth Elementals (62) and Greater Earth "
                      "Elementals (70), as the source (eight Earth Blasters).",
                      "(b) Add two Onyx Golems (11584, 85) as the Root Stair's wardens (over the band).",
                      "(c) Add Diamond Golems (11583, 50) in the quarry (under the band)."],
             evidence="monsters.yml: no other earth family at 55-70 (material golems stop at 50, then 85).",
             default='(a)', depends="A2's rows (C6); kill XP."),
    ],
    requests=[
        ('A2', "row 9117: environment quarry, music 3; the Earth rows of C6 (62, 70, the guardian 75); Lesser Earth "
               "Elemental 11626 used on P3 (15 placed)."),
        ('A3', "P3's hazard line 'Rocks fall from above!' with evt.CameraShake; the Heart-geode's line and buff; the "
               "slate (ours) and the Echo Stone's line."),
        ('A6', "new textures xperubble and xpegeode, registered; xeen_plane_earth checked under an open-air BLV."),
        ('S', "the statue of Earth; the Heart-geode; the quarry's half-cut blocks with a pick; the Anvil's twelve "
              "monoliths (shipped standing stones if they fit)."),
    ],
)

# ------------------------------------------------------------------------------------------------ P4 Water
P4 = dict(
    key='p4', code='P4', element='water', Element='Water', stem='xeen_p4.blv', id='xeen_p4',
    name='Plane of Water of Xeen', map_stats_id=9118, music=7, environment='underwater',
    source_map=28, source_text='aaze0028',
    source_lines=dict(sleeper='0-1, 6-7', plaque='2-3', test='5', chest='4'),
    source_summary=("MM5 maze 28, the Elemental Plane of Water (`dark/aaze0028`, 16 x 16, every square water; "
                    "decoded, nothing copied):\n\n"
                    "- the run position (9,9); the statue and its plaque (8,8);\n"
                    "- the test (4,11): 'Accept the test of Water?'; yes costs 2,500 cold damage and sets a flag;\n"
                    "- the chest (9,1): 250 cold unless the flag is set; gold and three items;\n"
                    "- the Water Sleeper (3,3), the same three answers;\n"
                    "- nine squares of freezing waves: one time in three 50 cold damage;\n"
                    "- eight Tidal Terrors (the greater water elemental);\n"
                    "- the exit (13,13): a fall back to Skyroad A1 (map 89) at (2,13), not A4 (the source's own "
                    "oddity; corners.yml returns the party to its own corner)."),
    corner='south-west', corner_sky='Sky A4',
    room=(26, 26),
    form='a drowned temple in a shallow sea',
    form_why=("Water is a sea with a drowned temple standing in it: the tops of its walls and colonnades are the "
              "paths, the courts between them are flooded basins the party swims across (MM9's water volumes: "
              "swimming at the surface costs no breath), and the open sea all round runs to a fog horizon with a "
              "current that carries swimmers back. The source's plane is all water; MM8's elemw is a sea bed."),
    pitch=("The Plane of Water of Xeen: a temple drowned in a sea with no shore, its colonnades standing out of green "
           "water under a sky the colour of the sea. Spray blows over the walks; a ship lies wrecked in the south "
           "court though there is no coast to wreck on. In the west the Whirlpool Court, where the test of Water "
           "turns in the pool, and beyond a falling veil of water, the Sleeper's Grotto."),
    purpose=("M38 (Act VI, party 56-60): the plaque (Step Four), the test of Water, the Water Sleeper "
             "(m38.sleeper_water, award 415) and the test's chest. Reached by stepping off D7's south-west corner "
             "after answering 'Water'; left by the waterspout at the arrival or the return dais by the sleeper, both "
             "to D7."),
    mood=("Cool, green and restless: the slap of waves on stone, spray in the light, the long hush of the swell. A "
          "shipwreck on a sea with no coast is the world's wink."),
    sky=dict(preset='xeen_plane_water', shipped=True,
             why=("A6's Xeen preset (D-58 P4 Q3; assets_dev/worlds/xeen/rendering/sky/sky.yml by make_sky.py): a "
                  "sea-green zenith over an aquamarine horizon, no sun disc, a bright diffuse light, slow cloud, "
                  "below_horizon sky so the fog horizon reads as more sea; plane_air if it fails to resolve.")),
    daylight=dict(ambient_rgb=[96, 128, 132], sun_rgb=[210, 240, 236], night_scale_rgb=[255, 255, 255], sun_gain=2),
    view_distance_scale=1.0,
    datum='room:landing',
    low=dict(id='zone:sea', kind='sea', name='The sea', level=-64, banks='terraces',
             shape="deep water round every walk and court: MM9 water volumes, surface at -64, bottom about -1,024",
             purpose=("Swum, not walked: a party in the water swims at the surface (no breath lost while the eye is "
                      "above it); under water breath lasts 15 s, then drowning; no falling damage into water; steps "
                      "rise out of the water along every walk and terrace; the outer sea's edge volumes push "
                      "swimmers back toward the temple with a constant inward current of 256 (D-58 P4 Q1)."),
             rule=("MM9's water rules (devdocs/mm9_rework/MM9_WATER_SWIMMING_DESIGN.md, already in the engine): "
                   "surface swimming free, breath 15 s under, drowning 1/6 of maximum HP every 2 s; steps out "
                   "along every walk and terrace; the walls of the Whirlpool Court and the Grotto stand 192-256 out of the "
                   "water with no steps, so the test cannot be bypassed (P-2); past the stacks, edge volumes each "
                   "with a constant inward `current` of 256 push swimmers back (the radial current is open engine "
                   "work, not used). Nothing on the critical path needs swimming; no diving anywhere (Q2); Water "
                   "Walk does nothing on a volume yet (recorded, accepted).")),
    rim=dict(height=1400, kind='stacks', text="a ring of sea stacks and broken arches, open sea and fog beyond"),
    critical=['room:landing', 'room:statue', 'room:arena', 'room:chamber'],
    gate_kind='colonnade',
    falls_text='none: the sea (swimming, current back), steps out (Q1)',
    spaces=[
        dict(id='room:landing', name='The Spray Terrace', at=(4224, 4224), extent=(2560, 2304), floor=0, seed=31,
             safe=True, kind='crust', shape="a terrace of green-veined marble, the waterspout at its corner",
             purpose="Arrival from D7's south-west corner (entrance:d7_fall) and the way up (the waterspout). Quiet."),
        dict(id='room:statue', name='The Sea Statue', at=(256, 768), extent=(2560, 2560), floor=32, seed=32,
             kind='crust', shape="the temple's drowned forecourt, the statue of Water rising from a fountain basin",
             purpose="The statue and its plaque (m38.plaque_water, Step Four); the Drowned Bell; the walks part here."),
        dict(id='room:reef', name='The Coral Garden', at=(4352, -512), extent=(2304, 2816), floor=32, seed=33,
             kind='crust', shape="a terrace grown over with coral and shells, tide pools in its stone",
             purpose="The Tide Pool (a device); the east loop."),
        dict(id='room:wreck', name='The Wreck', at=(640, -4224), extent=(2560, 2304), floor=0, seed=34,
             kind='crust', shape="the temple's south court, a sailing ship wrecked across it, its hold half flooded",
             purpose="The source's chest corner: the ship's strongbox in the hold and its log."),
        dict(id='room:arena', name='The Whirlpool Court', at=(-4096, 1280), extent=(3328, 3072), floor=128, seed=35,
             kind='arena', shape="a round court ringed by broken columns round a pool where the water turns",
             purpose=("The test of Water: the pedestal at the east gate asks 'Accept the test of Water?'; the "
                      "guardians rise from the whirlpool. The Veil's colonnade leaves at the south.")),
        dict(id='room:chamber', name="The Sleeper's Grotto", at=(-4096, -4224), extent=(2560, 2304), floor=192,
             seed=36, kind='hall', safe=True, shape="a grotto under a sea arch, its floor a raised shelf of shell and stone",
             purpose=("The Water Sleeper on his couch (m38.sleeper_water); the test's chest; the return dais (after "
                      "the sleeper wakes).")),
    ],
    links=[
        dict(id='link:walk_ne', a='room:landing', b='room:statue', kind='colonnade', width=640, style='walk'),
        dict(id='link:walk_w', a='room:statue', b='room:arena', kind='colonnade', width=640, style='walk',
             end_b=(-2560, 1280)),
        dict(id='link:walk_e', a='room:statue', b='room:reef', kind='colonnade', width=640, style='walk'),
        dict(id='link:walk_s', a='room:reef', b='room:wreck', kind='colonnade', width=640, style='walk'),
        dict(id='link:walk_c', a='room:wreck', b='room:statue', kind='colonnade', width=512, style='walk'),
        dict(id='link:walk_l', a='room:landing', b='room:reef', kind='colonnade', width=512, style='walk'),
        dict(id='link:veil', a='room:arena', b='room:chamber', kind='colonnade', width=640, style='veil', gate=True,
             notes="the Veil: a colonnade under a falling sheet of water that bars it, stilled on the test"),
    ],
    walk=[(3968, 3968), (256, 768), (-2560, 1280), (-4096, 1280), (-4096, -512), (-4096, -2944), (-4480, -4608),
          (-4864, -3712)],
    places=[
        dict(id='entrance:d7_fall', kind='arrival', space='room:landing', at=(3968, 3968), face='sw',
             text="Arrival from D7's south-west corner: on the Spray Terrace, facing south-west over the drowned temple."),
        dict(id='exit:way_up', kind='exit', space='room:landing', at=(4992, 4864), face='sw',
             text=("The waterspout: a column of water rising from the sea into the sky. An exit preset ('Ride the "
                   "spout back to the Skyroads?'), always open, to D7's entrance:p4_return (the source's (13,13), a "
                   "fall back to the Skyroads).")),
        dict(id='poi:statue', kind='statue', space='room:statue', at=(256, 896), face='ne',
             text=("The statue of Water: a woman of green stone pouring a jar into the fountain basin at her feet. "
                   "A3's m38.plaque_water: 'A message at the base of the statue reads: Step Four: Travel to the shrine "
                   "on the Cloud above Darkstone Tower.' (aaze0028:2-3)")),
        dict(id='poi:bell', kind='device', space='room:statue', at=(1152, -128), face='n',
             text=("The Drowned Bell: a temple bell half under the water on a fallen frame. Clicked: it tolls under "
                   "the waves; the first time, a find in its mouth: an emerald.")),
        dict(id='poi:tide_pool', kind='device', space='room:reef', at=(4864, -128), face='w',
             text=("The Tide Pool: a clear pool in the coral. Drunk from: +20 Water resistance for a day (once a day; "
                   "'The water is cool and refreshing.', the stock line, for once true).")),
        dict(id='poi:test', kind='pedestal', space='room:arena', at=(-2688, 1280), face='e',
             text=("The test pedestal at the Whirlpool Court's east gate: 'Accept the test of Water?' (aaze0028:5). "
                   "Yes calls A3's m38.test_water; the map raises the guardians from the whirlpool (set:test).")),
        dict(id='landmark:whirlpool', kind='landmark', space='room:arena', at=(-4096, 1280), face='s',
             text="The whirlpool: a pool at the court's middle where the water turns, and the guardians rise."),
        dict(id='gate:sleeper', kind='gate', space='room:arena', at=(-4096, -256), face='s',
             text="The Veil: a falling sheet of water across the colonnade's head, stilled once the test is passed "
                  "(state:test_passed)."),
        dict(id='poi:sleeper', kind='sleeper', space='room:chamber', at=(-4480, -4608), face='ne',
             text=("The Water Sleeper on his couch in the grotto: A3's m38.sleeper_water, three states (not Chosen; "
                   "'Awaiting Grunfeld field activation.'; awake, award 415, 10,500 XP).")),
        dict(id='poi:test_chest', kind='chest', space='room:chamber', at=(-3200, -4864), face='n',
             text="The test's chest (treasure 6): the source's chest, now in the grotto the test opens."),
        dict(id='exit:dais', kind='dais', space='room:chamber', at=(-4864, -3712), face='e',
             text=("The return dais: a disc of green-veined marble, shown once the Water Sleeper is awake (m38.water); "
                   "an exit preset to D7's entrance:p4_return.")),
        dict(id='poi:wreck_cache', kind='chest', space='room:wreck', at=(1280, -4736), face='n',
             text="The ship's strongbox (treasure 6, a cold trap) in the half-flooded hold, waded to (question 2)."),
        dict(id='poi:log', kind='device', space='room:wreck', at=(-128, -3840), face='e',
             text=("The ship's log on the wreck's deck: 'Day 40. Still no land. Day 41. Found land. It was this.' "
                   "(ours) A find: Water Resistance potions.")),
    ],
    hazard=dict(kind='waves', count=9, question="the source's rule, as P1's Q2 (a)", rule=("The source's nine squares of freezing waves: wet stone where spray "
                                               "breaks over the walks (a small floor face each). Stepping on one: "
                                               "one time in three 50 cold damage to each member, 'A freezing wave "
                                               "breaks over you!' (resistance applies)."),
                cells=[(3712, -256), (4864, -1536), (3968, 512), (-128, -4608), (1152, -3328), (256, -5056),
                       (640, -256), (-3712, 2688), (-5248, 640)]),
    groups=[
        dict(id='pop:statue_north', row='water_a', count=3, at=(1152, 1536), space='room:statue'),
        dict(id='pop:statue_west', row='water_a', count=3, at=(-640, 384), space='room:statue'),
        dict(id='pop:reef_elementals', row='water_b', count=3, at=(4096, -1280), space='room:reef'),
        dict(id='pop:reef_north', row='water_a', count=3, at=(4736, 768), space='room:reef', first=True),
        dict(id='pop:sea_octopods_e', row='octopod_b', count=3, at=(2304, -1152), space='zone:sea', swims=True),
        dict(id='pop:sea_octopods_n', row='octopod_b', count=2, at=(-1024, 4224), space='zone:sea', swims=True),
        dict(id='pop:wreck_lesser', row='water_a', count=3, at=(128, -3584), space='room:wreck'),
        dict(id='pop:wreck_elementals', row='water_b', count=2, at=(1536, -3584), space='room:wreck'),
        dict(id='pop:court_north', row='water_b', count=2, at=(-4480, 2560), space='room:arena'),
        dict(id='pop:wreck_greater', row='water_c', count=3, at=(896, -4992), space='room:wreck'),
    ],
    test_group=[dict(row='water_d', count=1), dict(row='water_c', count=2)],
    test_at=(-4096, 1280),
    camera=dict(at=(3328, 3328), eye=176, yaw_deg=213.0, pitch_deg=-4.0, fov=74.0,
                what=("The arrival: from the Spray Terrace south-west over the drowned temple, the colonnade walk to "
                      "the Sea Statue in its fountain, the Whirlpool Court's broken columns beyond to the right, the "
                      "Coral Garden left, the wreck's masts far off, the sea stacks and the fog horizon round it.")),
    textures=dict(
        shipped=[('gtempw1', "MM8 pale marble (Prison of the Lord of Fire's family)", 'the temple walls and walks'),
                 ('gtempflr', "MM8 blue-grey flags", 'the courts and terraces'),
                 ('gtemprf', "MM8 gold-blue mosaic", 'the Whirlpool Court floor ring (once per face)'),
                 ('gtempw2', "MM8 marble panel", 'the Grotto shelf (once per face)'),
                 ('7wtrtyl', "MM7 water", 'the sea surface faces'),
                 ('gwspotwl', "MM8's blue-grey rough rock", 'the sea stacks and the grotto arch'),
                 ('cdb', "MM8 Plane of Air's brick", 'the wreck court walls'),
                 ('xcorewater', "XD-19's water core (A7)", "the sleeper couch's glow panel")],
        new=[('xpwspray', "wet marble under breaking spray, one per wave face (the source's nine)"),
             ('xpwcoral', "coral and shells grown over marble (the Coral Garden), seamless"),
             ('xpwhull', "the wrecked ship's weathered planking (shipped ship planks first if one fits)")],
        estimate=16),
    questions=[
        dict(id='Q1', title='How water works for a party without Water Walk',
             options=["(a) MM9's water volumes, already in the engine for BLVs: the party swims at the surface with "
                      "no breath lost, dives at will (breath 15 s, then 1/6 of maximum HP every 2 s), no falling "
                      "damage into water; steps out at every walk's foot; the outer sea's current carries swimmers "
                      "back; Water Walk does nothing yet (the engine's open item); nothing on the critical path "
                      "needs swimming.",
                      "(b) MM6-MM8's rule: deep water drowns without Water Walk (the outdoor tiles' damage); the "
                      "party keeps to the walks.",
                      "(c) The sea as decoration under invisible walls: walks only."],
             evidence="devdocs/mm9_rework/MM9_WATER_SWIMMING_DESIGN.md (done: swim, dive, breath, drowning, current; "
                      "open: Water Walk on a volume). The source's plane is all water and walkable.",
             default='(a)', depends="L2 water volumes; A1 only if Water Walk should lift the party onto the sea."),
        dict(id='Q2', title='Diving',
             options=["(a) No dive anywhere: the wreck's hold is half flooded and waded; diving is only for whoever "
                      "falls in.",
                      "(b) One optional dive: the ship's strongbox lies in the flooded hold, 6 s under at most "
                      "(breath 15 s).",
                      "(c) The Grotto reached by a dive under the sea arch instead of the Veil."],
             evidence="MM9's breath is 15 s; drowning is 1/6 HP every 2 s. A plane at party 56-60 can take a short "
                      "dive; a required one would be the world's first.",
             default='(a)', depends="The wreck's L2 shape."),
        dict(id='Q3', title='Sky (no shipped plane_water)',
             options=["(a) A new Xeen preset `xeen_plane_water` (A6, data only, after approval): sea-green zenith, "
                      "aquamarine horizon, no sun disc, a bright diffuse light, slow caustic cloud, below_horizon sky.",
                      "(b) The engine's `underwater` (no sky drawn, flat fog): reads as the sea bed, at odds with "
                      "swimming at a surface.",
                      "(c) Shipped `plane_air` (blue open sky)."],
             evidence="WORLD_DESIGN §4 names `underwater` for the water plane; the engine library has no plane_water; "
                      "`underwater` draws no sky at all.",
             default='(a); (c) until A6 writes it', depends="atmosphere.yml; A6's sky file (a new preset)."),
        dict(id='Q4', title='Octopods on the Plane of Water',
             options=["(a) Two groups of Great Octopods (11471, 60, the swimmer profile of D-36) in the open water "
                      "between the walks: a reason not to swim.",
                      "(b) Elementals only, as the source (eight Tidal Terrors).",
                      "(c) Krakens (70) instead."],
             evidence="monsters.yml: octopods are this world's only swimmers at 50-70; D-36 gave them MM9's swimmer AI.",
             default='(a)', depends="A2 (the D4 row reused), S (none new)."),
    ],
    requests=[
        ('A2', "row 9118: environment underwater, music 7; the Water rows of C6 (62, 70, the guardian 75); Lesser "
               "Water Elemental 11625 (12 placed) and Great Octopod 11471 (5 placed, swimmers) used on P4."),
        ('A3', "P4's hazard line 'A freezing wave breaks over you!'; the Tide Pool's line and buff; the bell's line "
               "and the log (ours)."),
        ('A6', "the new preset xeen_plane_water (Q3); new textures xpwspray, xpwcoral, xpwhull, registered."),
        ('S', "the statue of Water in a fountain basin; the Drowned Bell; the wrecked ship (hull, masts, hold); the "
              "Whirlpool Court's broken columns; the waterspout effect."),
        ('A1', "confirm water volumes, their current and the swimmer AI run under an open-air BLV with an outdoor "
               "view (MM9's were all roofed or regions)."),
    ],
)

P1['concept_notes'] = (
    "`planes_concepts.py p1`: one `codex exec`, first attempt, 65 s; raw `planes/raw/p1_arrival_v1.png` with its "
    "prompt (.txt) and log (.log). References: the arrival blockout, D6's lava concept (this world's lava), MM6's "
    "`orfyrlga` and MM8's `gcav2flr`. It shows the Cinder Shelf's cracked crust, the causeway left to the statue of "
    "flame on its plinth, the lava lake with crust plates and spurts, the hall's ring of columns at the foot of the "
    "tallest spire, the Crucible's black ring right of it, the basalt columns right and a lava fall in the crater wall. "
    "Against the plan (the plan wins at L2-L3): the crater wall reads as cut slabs (the blockout's), L3 makes it "
    "ragged cliffs; the statue stands nearer and larger than drawn (about 3,700 away); two small gold boxes are the "
    "blockout's pedestal and couch, not props; the Crucible's ring is lower than the plan's rise.")
P2['concept_notes'] = (
    "`planes_concepts.py p2`: one `codex exec`, first attempt, 69 s; raw `planes/raw/p2_arrival_v1.png` with its "
    "prompt and log. References: the arrival blockout, X9's approved concept (D-50: this world's sky and cloud-stone), "
    "MM8's `gwsphlfl`. It shows the Gale Landing's wind-scoured stone, the cloud-stone bridge to the winged statue of "
    "Air, the Singing Stones' pierced ring on its island left, the aerie's open dome with the couch beyond, and the Eye "
    "of the Winds' standing stones right with leaves circling, every island on a tapering rock underside over open sky. "
    "Against the plan: the aerie stands too low (the plan puts it 768 over the arrival, the highest island); the gold "
    "posts and pennants along the bridge are not in the plan (L3 dressing may keep posts by the edge, never on the "
    "walk); the statue's plinth stands on the bridge's end, the plan puts it in the island's middle.")

P3['concept_notes'] = (
    "`planes_concepts.py p3`: one `codex exec`, first attempt, 62 s; raw `planes/raw/p3_arrival_v1.png` with its "
    "prompt and log. References: the arrival blockout, the Darkside day sky (for the manner of dim amber light), MM8's "
    "`gwspotwl` and `gwsphlfl`. It shows the Dust Ledge's packed earth, the seated granite giant on its plinth left, a "
    "field of standing stones in the middle, the Anvil's cracked bedrock ringed by monoliths right, the Sleeper's "
    "Hollow glowing amber under the overhang between them, scree and boulders in the drops, crystals in the walls and "
    "a brown dust sky. Against the plan (the plan wins at L2-L3): the bowl reads shallow (the scree lies 1,024 under "
    "the arrival, the Hollow 768); the walls read as quarried steps rather than leaning cavern walls; the Pillar Field "
    "is squared monoliths, the plan's are rough pillars like petrified trees.")
P4['concept_notes'] = (
    "`planes_concepts.py p4`: one `codex exec`, first attempt, 59 s; raw `planes/raw/p4_arrival_v1.png` with its "
    "prompt and log. References: the arrival blockout, X9's approved concept (light and stone), MM8's `gtempw1` and "
    "`gtempflr`. It shows the colonnade walk with steps down to clear green water on both sides, the statue of Water "
    "pouring her jar into the fountain, the Sleeper's Grotto glowing blue under its arch, the Whirlpool Court's broken "
    "columns round a turning pool right, the coral terrace and the wrecked ship left, sea stacks and arches in the "
    "mist. Against the plan: the sky is painted as a rippling sea surface seen from below (an underwater ceiling): "
    "striking, but it says 'under the sea' while the party swims at a surface; question 3 decides the preset; the "
    "grotto stands nearer and larger than drawn; the statue stands at the walk's end, the plan puts it mid-forecourt.")

# ------------------------------------------------------------------------------------------------ D-58
# Each plane's own answers (the question ids of its `questions`), its concept corrections for L3, and the gate's flanks:
# the gate stands at the arena's rim between two walls this high over the arena floor and this long along the rim, so
# nobody steps round it onto the gate's link (P-2).
P1['decisions'] = {
    'Q1': "(a) Walkable `lavtyl` that burns as MM lava does: crust banks within 64 of every lava edge, ramps up every "
          "shelf; P-2 holds.",
    'Q2': "(a) Nine small PressurePlate faces, the source's rule: one time in three 50 fire to each member, resistance "
          "applies, 'A vent flares!'; none on the critical path; marked by `xpfvent` (A3 the event, A6 the faces).",
    'Q3': "(a) The shipped `plane_fire`.",
}
P1['corrections'] = ["the crater wall is ragged cliffs, not cut slabs",
                     "the statue stands about 3,700 away (along the walk), not nearer",
                     "the Crucible stands on its rise"]
P1['gate_flank'] = dict(height=384, length=512, what="two obsidian piers either side of the gate's two leaves")
P2['decisions'] = {
    'Q1': "(a) Below -1,500 the wind throws the party back onto the Gale Landing: the fall goes to entrance:d7_fall in "
          "this map from Xeen.SkyFallHeight above it, with falling damage (D-6.2); D-54's tests from three islands.",
    'Q2': "(a) Nine plates: one time in three 50 electrical, 'Lightning strikes from a clear sky!'; none on bridges or "
          "in the Eye.",
    'Q3': "(a) The shipped `plane_air` (below_horizon sky).",
    'Q4': "(a) Elementals only, 32.04k.",
}
P2['corrections'] = ["the aerie is the highest island (768)",
                     "no posts or pennants on the walking line; L3 dressing may put them at the edges only",
                     "the statue's plinth stands in the middle of its island"]
P2['gate_flank'] = dict(height=384, length=512, what="two standing stones of the Eye's ring either side of the stair's "
                                                     "foot, the stilled wind between them")
P3['decisions'] = {
    'Q1': "(a) A bowl open to the `xeen_plane_earth` sky: drops into the scree are real falls, scree slopes lead back "
          "up to every terrace; P-2 holds.",
    'Q2': "(a) Nine plates: one time in three 50 physical, 'Rocks fall from above!', a short evt.CameraShake when one "
          "hits.",
    'Q3': "(a) Elementals only, 32.04k.",
}
P3['corrections'] = ["the bowl reads deep: the scree 1,024 under the arrival, the Hollow 768",
                     "the walls lean in like a cavern's, not quarried steps",
                     "the Pillar Field is rough pillars like petrified trees"]
P3['gate_flank'] = dict(height=384, length=512, what="two monoliths of the Anvil's ring either side of the Root "
                                                     "Stair's slab")
P4['decisions'] = {
    'Q1': "(a) MM9's water volumes: surface swimming free, 15 s of breath under water, then drowning; no falling "
          "damage into water; steps out at every walk; the outer sea's push-back from edge volumes with a constant "
          "inward current of 256; nothing on the critical path needs swimming; Water Walk does nothing on a volume "
          "(recorded, accepted).",
    'Q2': "(a) No diving anywhere; the wreck's hold is half flooded and waded.",
    'Q3': "(a) A new preset `xeen_plane_water` (A6, make_sky.py, data only); plane_air until it lands.",
    'Q4': "(a) Two groups of Great Octopods (11471, 60, 5 in all) as swimmers in the volumes, homes at least 1,024 "
          "from the arrival terrace, the test's court and the Grotto; fallback D-52's stationary row in the two "
          "deepest basins.",
}
P4['corrections'] = ["the sky is an open sky (Q3), not an underwater ceiling",
                     "the Grotto is at the plan's scale",
                     "the statue stands in the middle of its forecourt"]
P4['gate_flank'] = dict(height=384, length=512, what="two broken columns of the court's ring either side of the "
                                                     "Veil's head")

for _plane in (P1, P2, P3, P4):      # D-58: A3's per-plane lines are written (planes.yml)
    _plane['requests'] = [r for r in _plane['requests'] if r[0] != 'A3']

PLANES = {'p1': P1, 'p2': P2, 'p3': P3, 'p4': P4}
PAIRS = {'p12': ['p1', 'p2'], 'p34': ['p3', 'p4']}
