#!/usr/bin/env python3
"""XD-12 Darzog's Tower: what each room is for, who lives there, what lies there (the plan's spaces at L2/L3).
Population entries: slot 1 Magic constructs (Carnage Hand ...; MM7 Golem), slot 2 Wizards (Darzog's apprentices;
MM7 Mage), slot 3 Eyes (Darzog's watchers; MM7 Beholder)."""

POP_HANDS_B = {'slot': 1, 'per_marker': [2, 3], 'levels': [35, 35], 'rank': 'b', 'strength': 'pack'}
POP_HANDS_C = {'slot': 1, 'per_marker': [2, 3], 'levels': [48, 48], 'rank': 'c', 'strength': 'heavy'}
POP_MAGES_B = {'slot': 2, 'per_marker': [2, 3], 'levels': [36, 36], 'rank': 'b', 'strength': 'pack'}
POP_MAGES_C = {'slot': 2, 'per_marker': [2, 3], 'levels': [45, 45], 'rank': 'c', 'strength': 'heavy'}
POP_EYES_A = {'slot': 3, 'per_marker': [2, 3], 'levels': [30, 30], 'rank': 'a', 'strength': 'light'}
POP_EYES_B = {'slot': 3, 'per_marker': [2, 3], 'levels': [40, 40], 'rank': 'b', 'strength': 'pack'}


def P(base, groups, notes=None):
    d = dict(base)
    d['groups'] = groups
    if notes:
        d['notes'] = notes
    return d


# id: (kind, size, extent, floor, clear_height, shape, where, purpose, population, treasure, extra)
SPACES = {
    'room:gate_hall': dict(
        size='XL', extent=[1152, 3584], floor=0, clear_height=640, where='Gate floor, east',
        shape='Long hall along the east wall; the tower door in the middle of the east wall, a great arch west into the cloister.',
        purpose="Arrival from X2 (the tower door). Quiet: the first look through the arch into the Well and its lightning.",
        empty=True, theme='gate', light='torchlit: 4 wall torches, cold blue light from the arch',
        palette=['torch01: wall torch', 'bigbarel / smlbarel: barrels', 'Bucket'],
        furniture=['the tower door (an exit face, 128 x 256)', 'two benches by the door']),
    'room:cloister_n': dict(size='L', extent=[2816, 768], floor=0, clear_height=640, where='Gate floor, round the Well',
                            shape='Gallery of the cloister ring, north of the Well; an arch into it.',
                            purpose="The cloister's north walk; the disc comes down to the Well beside its arch.",
                            population=[P(POP_HANDS_B, 1, 'Two hands on guard by the arch.')], theme='gate'),
    'room:cloister_e': dict(size='L', extent=[768, 2816], floor=0, clear_height=640, where='Gate floor, round the Well',
                            shape='East walk of the cloister; the gate hall arch on its east side, the Well arch on its west.',
                            purpose="The first sight of the Well.", empty=True, theme='gate'),
    'room:cloister_s': dict(size='L', extent=[2816, 768], floor=0, clear_height=640, where='Gate floor, round the Well',
                            shape='South walk of the cloister.', purpose="To the cistern.",
                            population=[P(POP_EYES_A, 1, 'Eyes drifting out of the Well.')], theme='gate'),
    'room:cloister_w': dict(size='L', extent=[768, 2816], floor=0, clear_height=640, where='Gate floor, round the Well',
                            shape='West walk of the cloister; the west stair hall off its west side.',
                            purpose="To the west stair.", empty=True, theme='gate'),
    'room:well': dict(
        kind='room', size='XL', extent=[1792, 1792], floor=0, clear_height=4224, where='Centre of the keep, all floors',
        shape='Octagon 1,792 across rising from the gate floor through every floor to the open sky.',
        purpose="The tower's spine: every floor looks into it; a column of Darzog's lightning crackles up its axis; his disc rides its north face from the gate floor to his own floor (the way down after Darzog).",
        population=[],  # A8 session 25: no group at its foot, in line with the arrival (the cistern has two)
        theme='shaft', light='a column of pulsing blue-white light up the axis (5 lights from 64 to 3200), torches at each floor',
        palette=['brzier00: braziers round the rune circle'],
        furniture=['the rune circle on a low dais (td1, the School of Sorcery\'s summoning circle)', "Darzog's disc (a lift 384 square)"]),
    'room:hall_of_hands': dict(
        size='XL', extent=[3584, 1152], floor=0, clear_height=640, where='Gate floor, north',
        shape='Long hall with two rows of plinths where finished carnage hands stand waiting.',
        purpose="The first real fight: hands step down off their plinths.",
        population=[P(POP_HANDS_B, 2)], theme='gate', light='dim: 2 torches',
        furniture=['10 plinths in two rows (platforms 192 square, 64 high)', 'statues of hands (7dec54) on some plinths']),
    'room:guardroom': dict(size='M', extent=[1152, 1152], floor=0, clear_height=640, where='Gate floor, north-east',
                           shape='Square room with a table and racks.', purpose='Guards of the gate.',
                           population=[P(POP_HANDS_B, 1)],
                           treasure=[{'kind': 'chest', 'count': 1, 'tier': 4, 'items': [2, 3]}], theme='gate'),
    'room:storeroom': dict(size='M', extent=[1152, 1152], floor=0, clear_height=640, where='Gate floor, south-east',
                           shape='Square store of crates, barrels and sacks.', purpose='Supplies; a chest.',
                           empty=True, treasure=[{'kind': 'chest', 'count': 1, 'tier': 4, 'items': [2, 3]}], theme='gate'),
    'room:cistern': dict(
        size='XL', extent=[3584, 1152], floor=0, clear_height=640, where='Gate floor, south',
        shape='Hall with a sunken cistern 1,536 long (water 160 down) along its middle, walked round.',
        purpose="The tower's water; eyes over the cistern.", population=[P(POP_EYES_A, 2)], theme='gate',
        features=[{'kind': 'pit', 'rise': -160, 'notes': 'The cistern, water.'}]),
    'room:cells': dict(size='M', extent=[1152, 1152], floor=0, clear_height=640, where='Gate floor, south-west',
                       shape='Three barred cells off a guard walk.', purpose='Old prisoners: bones; one hand.',
                       population=[P(POP_HANDS_B, 1)], theme='gate'),
    'room:crypt': dict(size='M', extent=[1152, 1152], floor=0, clear_height=640, where='Gate floor, north-west',
                       shape='Vaulted room of six coffins on biers.', purpose="Darzog's failed apprentices, laid out; a coffin to rob.",
                       empty=True, treasure=[{'kind': 'chest', 'count': 1, 'tier': 4, 'items': [1, 2], 'notes': 'A coffin (Sarcophagus).'}],
                       theme='gate'),
    'room:west_stair': dict(
        size='XL', extent=[1152, 3584], floor=0, clear_height=1408, where='West side, gate floor to the works',
        shape='Two-storey hall: one long flight up the west wall to a hanging gallery at 768 across the north end and along the east wall; tall window over the lake.',
        purpose="The first climb: the gate floor to the works.", relief='steps',
        population=[P(POP_HANDS_B, 1, 'On the upper gallery, coming down the stair.')], theme='gate'),
    # ---- works (768)
    'room:works_n': dict(size='L', extent=[2816, 768], floor=768, clear_height=640, where='Works, round the Well',
                         shape='North walk; a railed window over the Well.', purpose='Walk of the works.',
                         empty=True, theme='works'),
    'room:works_e': dict(size='L', extent=[768, 2816], floor=768, clear_height=640, where='Works, round the Well',
                         shape='East walk; the works gate (a portcullis) into the east stair hall.',
                         purpose="The works gate: raised from the assembly hall.",
                         population=[P(POP_EYES_A, 1)], theme='works'),
    'room:works_s': dict(size='L', extent=[2816, 768], floor=768, clear_height=640, where='Works, round the Well',
                         shape='South walk; a railed window over the Well.', purpose='Walk of the works.',
                         empty=True, theme='works'),
    'room:works_w': dict(size='L', extent=[768, 2816], floor=768, clear_height=640, where='Works, round the Well',
                         shape='West walk; the west stair gallery opens off it.', purpose='Arrival on the works.',
                         empty=True, theme='works'),
    'room:forge': dict(
        size='XL', extent=[3584, 1152], floor=768, clear_height=640, where='Works, north',
        shape='The forge of the hands: a lava channel along its north wall behind a low kerb, anvils (blocks), two half-built hands.',
        purpose="Where Darzog's carnage hands are made. Heavy fight.", population=[P(POP_HANDS_B, 2)], theme='works',
        light='red from the lava channel, 2 braziers',
        furniture=['the lava channel (sunken level, burning)', '3 anvils', 'half-built hands (statues)']),
    'room:assembly': dict(
        size='XL', extent=[3584, 1152], floor=768, clear_height=640, where='Works, south',
        shape='Assembly hall: racks of iron limbs (blocks), a winch lever for the works gate on its west wall.',
        purpose="The lever that raises the works gate (east walk) to the east stair.",
        population=[P(POP_HANDS_B, 2)], theme='works'),
    'room:smelter': dict(size='M', extent=[1152, 1152], floor=768, clear_height=640, where='Works, north-east',
                         shape='Square room round a sunken smelting pit of lava.', purpose='Heat; a chest by the pit.',
                         population=[P(POP_HANDS_B, 1)],
                         treasure=[{'kind': 'chest', 'count': 1, 'tier': 4, 'items': [2, 3]}], theme='works'),
    'room:scrap_hall': dict(size='M', extent=[1152, 1152], floor=768, clear_height=640, where='Works, north-west',
                            shape='Heaps of broken hands (trash heaps).', purpose='The hands that failed.',
                            population=[P(POP_HANDS_B, 1)], theme='works'),
    'room:parts_store': dict(size='M', extent=[1152, 1152], floor=768, clear_height=640, where='Works, south-east',
                             shape='Store of crates and barrels; trapdoor landing from the study above.',
                             purpose='Under the Study of the Arm (trapdoor).', empty=True, theme='works'),
    'room:quarters': dict(size='M', extent=[1152, 1152], floor=768, clear_height=640, where='Works, south-west',
                          shape="Four apprentices' beds and a table.", purpose="The apprentices' quarters; their chest.",
                          population=[P(POP_MAGES_B, 1)],
                          treasure=[{'kind': 'chest', 'count': 1, 'tier': 4, 'items': [2, 3]}], theme='works'),
    'room:east_stair': dict(
        size='XL', extent=[1152, 3584], floor=768, clear_height=1408, where='East side, the works to the library',
        shape='Two-storey hall: the flight up the east wall rises south to a hanging gallery at 1536; tall window over the lake.',
        purpose="The second climb, behind the works gate.", relief='steps', empty=True, theme='works'),
    # ---- library (1536)
    'room:library_n': dict(size='L', extent=[2816, 768], floor=1536, clear_height=640, where='Library, round the Well',
                           shape='North reading walk lined with bookcases; a railed window over the Well; a trapdoor.',
                           purpose='Walk of the library.', population=[P(POP_EYES_B, 1)], theme='library'),
    'room:library_e': dict(size='L', extent=[768, 2816], floor=1536, clear_height=640, where='Library, round the Well',
                           shape="East reading walk; the apprentice's warning note on the wall.",
                           purpose='Arrival on the library; the warning about the cracked flags.', empty=True,
                           theme='library'),
    'room:library_s': dict(size='L', extent=[2816, 768], floor=1536, clear_height=640, where='Library, round the Well',
                           shape='South reading walk lined with bookcases.', purpose='Walk of the library.',
                           population=[P(POP_MAGES_B, 1)], theme='library'),
    'room:library_w': dict(size='L', extent=[768, 2816], floor=1536, clear_height=640, where='Library, round the Well',
                           shape='West reading walk; the locked library stair door; a trapdoor.',
                           purpose="The library stair door (the Chief Librarian's key).", empty=True, theme='library'),
    'room:reading_room': dict(
        size='XL', extent=[3584, 1152], floor=1536, clear_height=640, where='Library, north',
        shape='Long reading room: four reading tables, bookcases along the walls, two windows over the lake; two trapdoors in its floor.',
        purpose="Apprentices at their books; the Book of Speed on a lectern at its west end.",
        population=[P(POP_MAGES_B, 2)], theme='library'),
    'room:great_library': dict(
        size='XL', extent=[3584, 1152], floor=1536, clear_height=640, where='Library, south',
        shape='The great library: three rows of free-standing bookcases, the Chief Librarian\'s desk, the Book of Accuracy on its lectern; one trapdoor.',
        purpose="The Chief Librarian (placed, carries the library stair key) and his apprentices.",
        population=[P(POP_MAGES_B, 1), {'actor': 'Wizard', 'role': 'Chief Librarian', 'groups': 1, 'levels': [45, 45],
                                         'placed': True, 'strength': 'heavy', 'drops': 'library_key'}],
        treasure=[{'kind': 'chest', 'count': 1, 'tier': 4, 'items': [2, 3], 'notes': "A bookcase to search."}],
        theme='library'),
    'room:study_ne': dict(size='M', extent=[1152, 1152], floor=1536, clear_height=640, where='Library, north-east',
                          shape='Study with a lectern and a summoning circle.', purpose='The Book of Personality.',
                          empty=True, theme='library'),
    'room:study_nw': dict(size='M', extent=[1152, 1152], floor=1536, clear_height=640, where='Library, north-west',
                          shape='Study with a lectern and a trapdoor.', purpose='The Book of Intellect.',
                          population=[P(POP_EYES_B, 1)], theme='library'),
    'room:study_se': dict(size='M', extent=[1152, 1152], floor=1536, clear_height=640, where='Library, south-east',
                          shape='Study with a lectern and a trapdoor.', purpose='The Book of Might.',
                          empty=True, theme='library'),
    'room:study_sw': dict(size='M', extent=[1152, 1152], floor=1536, clear_height=640, where='Library, south-west',
                          shape='Study with a lectern.', purpose='The Book of Endurance.',
                          population=[P(POP_MAGES_B, 1)], theme='library'),
    'room:library_stair': dict(
        size='XL', extent=[1152, 3584], floor=1536, clear_height=1408, where='West side, the library to Darzog\'s floor',
        shape='Two-storey hall: the flight up the west wall rises south to a hanging gallery at 2304.',
        purpose="The third climb, behind the locked library door.", relief='steps',
        population=[P(POP_EYES_B, 1)], theme='library'),
    # ---- Darzog's floor (2304)
    'room:state_n': dict(size='L', extent=[2816, 768], floor=2304, clear_height=640, where="Darzog's floor, round the Well",
                         shape="North state gallery: the arch into Darzog's hall; the disc's landing on the Well behind a black grille.",
                         purpose="Before Darzog's hall; the way down by the disc after him.", empty=True, theme='darzog'),
    'room:state_e': dict(size='L', extent=[768, 2816], floor=2304, clear_height=640, where="Darzog's floor, round the Well",
                         shape='East state gallery; the sky stair off its east side.', purpose='To the roof.',
                         empty=True, theme='darzog'),
    'room:state_s': dict(size='L', extent=[2816, 768], floor=2304, clear_height=640, where="Darzog's floor, round the Well",
                         shape='South state gallery.', purpose='Walk.', population=[P(POP_HANDS_C, 1)], theme='darzog'),
    'room:state_w': dict(size='L', extent=[768, 2816], floor=2304, clear_height=640, where="Darzog's floor, round the Well",
                         shape='West state gallery; the library stair gallery opens off it.', purpose="Arrival on Darzog's floor.",
                         empty=True, theme='darzog'),
    'room:darzog_hall': dict(
        size='XL', extent=[3584, 1152], floor=2304, clear_height=[640, 704], where="Darzog's floor, north",
        shape="Darzog's hall: the inlaid rug down its length, a dais with his chair at the east end, banners, two windows over the lake.",
        purpose="Baron Darzog and his six clones: the boss fight (set:darzog).",
        population=[{'actor': 'Darzog Clone', 'groups': 6, 'levels': [45, 45], 'placed': True, 'strength': 'heavy'},
                    {'actor': 'Darzog', 'role': 'Baron Darzog', 'groups': 1, 'levels': [55, 55], 'placed': True,
                     'strength': 'boss'}],
        theme='darzog', light="candlelit: 4 standing candelabra, 2 torches; cold light on the dais"),
    'room:darzog_study': dict(
        size='M', extent=[1152, 1152], floor=2304, clear_height=640, where="Darzog's floor, north-west",
        shape="Darzog's study: his desk with the journal, bookcases, his strongbox.",
        purpose="Darzog's journal names the portrait; his hoard.", empty=True,
        treasure=[{'kind': 'chest', 'count': 1, 'tier': 5, 'items': [3, 4], 'notes': "Darzog's hoard (one step up)."}],
        theme='darzog'),
    'room:bedchamber': dict(
        size='M', extent=[1152, 1152], floor=2304, clear_height=640, where="Darzog's floor, north-east",
        shape="L-shaped bedchamber round the cell; Darzog's own portrait on the north wall (the cell's door).",
        purpose="The portrait that hides Crodo's cell (set:crodo).", empty=True, theme='darzog'),
    'room:crodo_cell': dict(size='S', extent=[512, 512], floor=2304, clear_height=640, where="Behind the bedchamber's north wall",
                            shape='Bare cell, a stool and a bowl.', purpose="Crodo (goal).", secret=True, empty=True,
                            theme='darzog'),
    'room:clone_vats': dict(
        size='M', extent=[1152, 1152], floor=2304, clear_height=640, where="Darzog's floor, south-east",
        shape='Four vats of green brew on plinths where the clones were grown.', purpose='Where the clones come from.',
        population=[P(POP_MAGES_C, 1)], theme='darzog'),
    'room:guard_hall': dict(size='M', extent=[1152, 1152], floor=2304, clear_height=640, where="Darzog's floor, south-west",
                            shape='Guard hall with racks.', purpose='Elite hands.', population=[P(POP_HANDS_C, 1)],
                            treasure=[{'kind': 'chest', 'count': 1, 'tier': 4, 'items': [2, 3]}], theme='darzog'),
    'room:portrait_hall': dict(size='XL', extent=[3584, 1152], floor=2304, clear_height=640,
                               where="Darzog's floor, south",
                               shape="Gallery of the Baron's ancestors: portraits and tapestries on every wall, a window over the lake.",
                               purpose='Walk; apprentices.', population=[P(POP_MAGES_C, 1)], theme='darzog'),
    'room:sky_stair': dict(
        size='XL', extent=[1152, 3584], floor=2304, clear_height=1920, where="East side, Darzog's floor to the roof",
        shape='Stair hall open to the sky: the flight up the east wall rises north to the roof.',
        purpose='The way onto the roof.', relief='steps', empty=True, theme='darzog'),
    # ---- the roof (3072)
    'room:roof_n': dict(size='XL', extent=[6144, 2048], floor=3072, clear_height=1152, where='The roof, north',
                        shape='Battlemented terrace under the open sky; the cloud stair rises from its middle.',
                        purpose='The cloud stair (exit to X9).', population=[P(POP_EYES_B, 1)], theme='roof'),
    'room:roof_s': dict(size='XL', extent=[6144, 2048], floor=3072, clear_height=1152, where='The roof, south',
                        shape='Battlemented terrace; view over the lake.', purpose='Vista.',
                        population=[P(POP_EYES_B, 1)], theme='roof'),
    'room:roof_w': dict(size='L', extent=[2048, 2048], floor=3072, clear_height=1152, where='The roof, west',
                        shape='Terrace by the Well\'s rim.', purpose='Vista down the Well.', empty=True, theme='roof'),
    'room:roof_e': dict(size='M', extent=[896, 2048], floor=3072, clear_height=1152, where='The roof, east',
                        shape='Terrace between the Well and the sky stair.', purpose='Vista.', empty=True, theme='roof'),
}
for _k in ('n', 'e', 's', 'w'):
    SPACES[f'room:out_{_k}'] = dict(
        kind='room', size='XL', extent=[7680, 1024], floor=0, clear_height=4224, where='Outside the keep',
        shape="Band of open air outside the keep's wall: the island's grass at its foot, Lake Darzog beyond, the open sky.",
        purpose="Seen from the windows and the roof; a fall from the keep lands here and leaves for X2.", backdrop=True,
        empty=True, theme='outside', keep_clear=['spawns'])
