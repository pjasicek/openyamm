"""Labels and symbols for X5's MU-3 drawing (plan_render.py). Positions come from the brief's sketch.yml."""

KINDS = {
    'entrance:east_road': 'entrance', 'entrance:north_road': 'entrance', 'entrance:winterkill_square': 'entrance',
    'entrance:xd09_door': 'dungeon', 'entrance:xd10_north': 'dungeon', 'entrance:xd10_south': 'dungeon',
    'entrance:xd22_pagoda': 'dungeon', 'entrance:xd23_warren': 'dungeon', 'entrance:fd03_tower': 'dungeon',
    'poi:frozen_sledge': 'chest', 'poi:trapper': 'chest', 'poi:frozen_pack': 'chest', 'poi:giants_cairn': 'chest',
    'poi:ogre_camp': 'camp', 'poi:archer_camp': 'camp', 'poi:barbarian_camp': 'camp', 'poi:hunting_camp': 'camp',
    'poi:cyclops_outpost': 'camp',
    'poi:randon': 'npc', 'poi:thickbark': 'npc', 'poi:winter_druid': 'npc', 'poi:freeda': 'npc',
    'poi:signposts': 'junction',
    'junction:lagoon_fork': 'junction', 'junction:pass_crest': 'junction', 'junction:monastery_foot': 'junction',
    'junction:steppe_cross': 'junction', 'junction:glom_fork': 'junction',
    'landmark:darkstone': 'landmark', 'landmark:monastery': 'landmark', 'landmark:pagoda': 'landmark',
    'landmark:halon_clock': 'landmark', 'landmark:glacier': 'landmark', 'landmark:frostspine': 'landmark',
}

NAMES = {
    'entrance:east_road': 'from X3 Lifeforce Lagoon',
    'entrance:north_road': 'from X6 Desert',
    'entrance:xd09_door': 'XD-09 Golem Dungeon',
    'entrance:xd10_north': 'XD-10 Cave of Illusion (N)',
    'entrance:xd10_south': 'XD-10 (S mouth)',
    'entrance:xd22_pagoda': 'XD-22 Ninja Pagoda',
    'entrance:xd23_warren': 'XD-23 Troll Warren',
    'entrance:fd03_tower': 'FD-03 Darkstone Tower (sealed)',
    'junction:lagoon_fork': 'Lagoon fork',
    'junction:pass_crest': 'Frostspine pass',
    'junction:monastery_foot': 'Monastery foot',
    'junction:steppe_cross': 'Steppe Cross',
    'junction:glom_fork': "Glom's fork",
    'poi:obelisk': 'Obelisk',
    'poi:fountain_great_protection': 'Fountain of Great Protection',
    'poi:waters_great_magic': 'Waters of Great Magic',
    'poi:shrine_cold': 'Shrine of Cold',
    'poi:well_intellect': 'Well of Intellect',
    'poi:well_accuracy': 'Well of Accuracy',
    'poi:hot_spring': 'Hot spring',
    'poi:thickbark': 'Thickbark',
    'poi:winter_druid': 'Winter Druid',
    'poi:freeda': 'Freeda (Body Building)',
    'poi:holy_book': 'Holy Book (Q-C18)',
    'poi:earth_reflector': 'Earth Reflector',
    'poi:cyclops_outpost': 'Cyclops outpost (burn)',
    'poi:barbarian_camp': 'Barbarian camp (burn)',
    'poi:hunting_camp': 'Hunting camp',
    'poi:ogre_camp': 'Ogre camp (burn)',
    'poi:archer_camp': 'Archers\' camp (burn)',
    'poi:frozen_sledge': 'Lost sledge',
    'poi:trapper': "Trapper's lean-to",
    'poi:frozen_pack': 'Pack in the ice',
    'poi:giants_cairn': "Giant's cairn",
    'poi:giant_stones': "Giants' Stones (Might)",
    'poi:ice_fishing': "Knut's fishing hole",
    'poi:edge_watch': 'Edge Watch',
    'landmark:monastery': "Kai Wu's monastery",
    'landmark:halon_clock': "Halon's workshop",
    'landmark:glacier': 'Glacier over the rim',
    'landmark:frostspine': 'THE FROSTSPINE',
}

OFFSETS = {
    'entrance:east_road': (-4, -14, 'end'),
    'entrance:north_road': (12, 4, 'start'),
    'entrance:xd10_south': (10, 14, 'start'),
    'entrance:fd03_tower': (0, 22, 'middle'),
    'entrance:xd22_pagoda': (10, -6, 'start'),
    'junction:pass_crest': (-10, -10, 'end'),
    'junction:monastery_foot': (10, 14, 'start'),
    'junction:lagoon_fork': (-10, 16, 'end'),
    'junction:glom_fork': (-10, 4, 'end'),
    'poi:freeda': (-10, 16, 'end'),
    'poi:hot_spring': (-10, -8, 'end'),
    'poi:well_intellect': (10, -12, 'start'),
    'poi:obelisk': (10, -4, 'start'),
    'poi:well_accuracy': (-10, 4, 'end'),
    'poi:edge_watch': (-10, 4, 'end'),
    'poi:fountain_great_protection': (10, 4, 'start'),
    'poi:winter_druid': (-4, -10, 'middle'),
    'poi:thickbark': (-10, 4, 'end'),
    'poi:shrine_cold': (10, 4, 'start'),
    'poi:giant_stones': (-10, 4, 'end'),
    'poi:giants_cairn': (10, 4, 'start'),
    'poi:earth_reflector': (10, 4, 'start'),
    'poi:waters_great_magic': (10, 4, 'start'),
    'poi:cyclops_outpost': (10, -6, 'start'),
    'landmark:glacier': (-10, 4, 'end'),
    'landmark:monastery': (12, -10, 'start'),
    'landmark:halon_clock': (12, 2, 'start'),
    'landmark:frostspine': (-12, 4, 'end'),
    'poi:hunting_camp': (10, 4, 'start'),
    'poi:frozen_sledge': (-8, -10, 'end'),
}

ARROWS = {'entrance:east_road': True, 'entrance:north_road': True}

ENCOUNTERS = {
    'pop:pocket_hills': {'colour': '#e07a1f'},
    'pop:pocket_marsh': {'colour': '#e07a1f'},
    'pop:trolls': {'colour': '#c0282d'},
    'pop:barbarians': {'colour': '#c0282d'},
    'pop:snow_beasts': {'colour': '#c0282d'},
    'pop:giant_markers': {'colour': '#7a0a2a'},
}

CAPTIONS = [
    ('E1 Ogre Hills: 20 (Act II, A tier: 16-18)', (98, 21), 13, '#8a3c00'),
    ('E2 Lagoon Marches: 19 (Act II, A tier: 8-16)', (98, 99.5), 13, '#8a3c00'),
    ('E3 Troll Forest: 28 (18-38)', (70, 79), 13, '#7a1010'),
    ('E4 Barbarian steppe: 26 (14-28)', (56, 18), 13, '#7a1010'),
    ('E5 Snowfields: 24 (16-28)', (31, 70), 13, '#7a1010'),
    ('E6 Land of the Giants: 19 (36-50, trap)', (38, 106.5), 13, '#5a0018'),
    ('WINTERKILL', (37, 32.4), 15, '#222'),
    ('Winterkill Mere (ice)', (52, 55.5), 13, '#234'),
    ('ACT II POCKET', (97, 64.8), 15, '#8a3c00'),
    ('the world rim:', (11, 44), 13, '#ccd'),
    ('a cliff above', (11, 46), 13, '#ccd'),
    ('the stars', (11, 48), 13, '#ccd'),
    ('the world rim', (80, 112), 13, '#ccd'),
    ('Lagoon Water', (116, 64.6), 12, '#123'),
    ('to X6 (north edge)', (50, 4), 12, '#222'),
    ('to X3 (east edge)', (118, 57.5), 12, '#222'),
]


def extra_svg(scale):
    """The frozen gorge's mark and the pocket's west boundary."""
    s = scale
    return (f'<polyline points="{86 * s},{19 * s} {86 * s},{60 * s} {85 * s},{66 * s} {85 * s},{104 * s}" '
            'fill="none" stroke="#e07a1f" stroke-width="3" stroke-dasharray="12 6" stroke-opacity="0.9"/>')


LABELS = {'kinds': KINDS, 'names': NAMES, 'offsets': OFFSETS, 'arrows': ARROWS, 'encounters': ENCOUNTERS,
          'captions': CAPTIONS}

# Blockout models: (cell x, cell y, base height or None for the ground, height, half width in cells, colour)
MODELS = [
    (55, 61, None, 2400, 0.9, (28, 26, 32)),        # Darkstone Tower
    (96.5, 49, None, 900, 0.4, (90, 70, 60)),       # Halon's water clock tower
    (95, 50, None, 420, 1.0, (96, 74, 62)),         # Halon's workshop
    (69, 31, None, 700, 2.5, (120, 112, 104)),      # monastery
    (64, 48, None, 1400, 0.9, (60, 40, 36)),        # pagoda
    (37, 41, None, 450, 7.0, (110, 96, 86)),        # Winterkill roofs
    (40, 103, None, 500, 0.3, (200, 170, 90)),      # Earth Reflector
    (44, 93, None, 260, 1.5, (90, 70, 56)),         # cyclops outpost
    (44, 81, None, 200, 1.0, (100, 90, 80)),        # Glom's burrows
]

# Where named things fall in each MU-4 view: (label, cell x, cell y, height above the ground).
ANNOTATIONS = {
    'view:arrival': [  # camera looks toward the pass road; FOV 80
        ('gorge: river into the Frostspine', 81, 62, 100),
        ('pass notch', 82, 46, 200),
        ('Frostspine peak 3,600', 82, 36, 0),
        ("Halon's water clock tower", 96.5, 49, 700),
        ('pass road climbing', 86, 51, 60),
        ('lagoon fork, signpost', 98, 60, 60),
        ('hot spring (steam)', 93, 61, 60),
        ('Lagoon Marches, sedge, firs', 96, 70, 60),
        ('Ogre Hills', 96, 48, 300),
    ],
    'view:glacier': [
        ('glacier tongue breaks off the rim', 33, 102, 100),
        ('Earth Reflector on its spur', 40, 103, 500),
        ('west crags 3,400', 28, 88, 0),
        ('glacier head', 36, 87, 0),
        ('rim cliff edge', 44, 104, 0),
        ('stars below the rim', 36, 116, 0),
        ('cyclopes pair', 33, 91, 100),
    ],
}
