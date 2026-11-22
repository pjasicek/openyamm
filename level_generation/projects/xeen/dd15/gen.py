#!/usr/bin/env python3
"""Writes DD-15 Great Pyramid's project folders: `gen.py L1 L2 L3 L4` writes devdocs/xeen/briefs/dd15/<level>.

L1: plan.yml (the graph devdocs/xeen/mockups/act5_graphs/dd15.graph.yml with decider D-61,
mockups/act5_a8_decisions.md, which wins), project.yml, diagram.txt. L2 adds positions, L3 rooms.yml, L4
objects.yml, wiring.yml (dress.py).
"""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import geo  # noqa: E402

R = Path(_REPO_ROOT)
BR = R / 'devdocs/xeen/briefs/dd15'


class D(yaml.SafeDumper):
    pass


def _flow_list(dumper, data):
    flow = all(not isinstance(x, (dict, list)) for x in data) or all(
        isinstance(x, list) and all(not isinstance(y, (dict, list)) for y in x) for x in data)
    return dumper.represent_sequence('tag:yaml.org,2002:seq', data, flow_style=flow)


D.add_representer(list, _flow_list)


def dump(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        yaml.dump(data, f, Dumper=D, sort_keys=False, allow_unicode=True, width=120)


# Rows (assets_dev/worlds/xeen/source/monsters.yml, A2): the pyramid mummies; the Dragon Pharaoh (D-56)
TOMB, GUARD, ROYAL, GHOST = 11270, 11271, 11272, 11273
PHARAOH = 11919
LEVEL = {TOMB: 42, GUARD: 52, ROYAL: 65, GHOST: 62}

D5_DOOR = 'entrance:dd15_door'   # (0, -7168, 1248) facing 512 (assets_dev/worlds/xeen/maps/xeen_d5.studio.yml)
D7_SKY = 'entrance:dd15_sky'     # (11424, 2560, 1408) facing 1024 (assets_dev/worlds/xeen/maps/xeen_d7.studio.yml)

QBITS = {
    # map qbits 117560-117599 (A3 registers)
    'arrived_once': 117560,
    'torch_ne': 117561, 'torch_nw': 117562, 'torch_sw': 117563, 'torch_se': 117564,
    'niche_3': 117565, 'niche_4': 117566, 'niche_5': 117567, 'niche_6': 117568,
    'niche_7': 117569, 'niche_8': 117570, 'niche_9': 117571, 'niche_10': 117572,
    'vault_open': 117573, 'safe_open': 117574, 'button': 117575, 'maze_seen': 117576, 'throne_reached': 117577,
    'scarab_find': 117578,
    # A3's M28/M30 bits read here (the hooks set them)
    'torches': 111561, 'registry': 111562, 'm28_done': 111563, 'm30_done': 111600,
}

NOTES_PROJECT = (
    "Xeen design brief for a new map: DD-15 Great Pyramid (the source's dark maze0083-0086: the Royal Pyramid, the "
    "registry level, the Ancient pad maze and the Dragon Pharaoh's apartments) as one BLV of four stepped floors 768 "
    "apart on D5, entered by the green doors (m28.door, A6). Story M28 (A3's hooks m28.torch_plaque, m28.torches, "
    "m28.registry_plaque, m28.registry_lock, m28.maze, m28.prime_directive), M30 and M36 (the Pharaoh's topics, npc "
    "5453); D-58's sky door to D7 after m30.done (d7.sky_door_dd15). Class L: 50-75 sectors, 120-200 M units "
    "squared, levels 42-65, no boss, party 44-47, treasure 5, music 46. Graph "
    "devdocs/xeen/mockups/act5_graphs/dd15.graph.yml with decider D-61 (mockups/act5_a8_decisions.md, which wins): 70 "
    "Pyramid mummies (Tomb Mummy 11270 42 x34, Pyramid Guard 11271 52 x24, Ghost Mummy 11273 62 x6, Royal Mummy 11272 "
    "65 x6), 51.92k per member; four torches, each waking two hidden Tomb Mummies in its chapel; the number niches "
    "optional (the Overseer's vault); the registry (1701) on the path; four pads in the pad hall, a pad back from every "
    "cell; the Pharaoh's lift after the first entry into the throne hall (117577); the Brew burns on a second click; the "
    "wall safe 20-30-1; the scarab cell's find (117578). The Dragon Pharaoh 11919 (npc 5453, D-56): peaceful, immobile, "
    "uncounted, unkillable. Rest encounters 10 %: mummies Dif 2 [2, 3] w100 (D-61 Q10). Map qbits 117560-117578; "
    "map_stats 9168.")


def project(level):
    return {
        'format': 0, 'id': 'xeen_dd15', 'name': 'Great Pyramid', 'world': 'xeen', 'kind': 'indoor',
        'profile': 'dungeon', 'map_code': 'DD-15', 'units': {'plan_grid': 512},
        'extent': {'footprint_cells': [20, 20], 'climbs': 'n'},
        'map_stats': {
            'id': 9168, 'bolster': 'LowerToEqual', 'encounter_chance': 10, 'treasure_level': 5, 'trap_dice': 6,
            'perception_difficulty': 12, 'refill_days': 672, 'music': 46, 'environment': 'stoneroom',
            'lock_difficulty': 12,
            # D-61 Q10: one slot, Dif 2 (A2's row 9168)
            'slots': [{'monster': 'Xeen Mummy', 'tier': 2, 'per_marker': [2, 3], 'weight': 100}],
        },
        'neighbours': [
            {'id': 'exit:d5_door', 'to': 'xeen_d5.odm', 'kind': 'door', 'arrival': D5_DOOR,
             'arrival_hint': "Before the Great Pyramid's green door on D5, facing north away from it (A6's entrance:dd15_door, (0, -7168, 1248) facing 512).",
             'notes': "The green doors (D5's door:dd15, A6's: m28.door with the Key to the Ancient Pyramid) arrive at entrance:d5_door in the entrance hall; out by the exit preset ('Exit the Great Pyramid?', aaze0083:0, D-24)."},
            {'id': 'exit:d7_sky', 'to': 'xeen_d7.blv', 'kind': 'door', 'arrival': D7_SKY,
             'arrival_hint': "On D7's cloud beside the Great Pyramid's golden capstone, before its sky door, facing west (A6's entrance:dd15_sky, (11424, 2560, 1408) facing 1024).",
             'notes': "The sky door (D-58, D-61 Q9): after m30.done 'Step out onto the Skyroads?' (d7.sky_door_dd15) and out to D7; before it 'Access Denied!'. D7's door:dd15 comes back to entrance:d7_sky (after m30.done)."},
        ],
        'qbits': dict(QBITS),
        'notes': NOTES_PROJECT,
    }


def placed(actor, n, strength='pack', **kw):
    d = {'actor': actor, 'groups': n, 'levels': [LEVEL[actor], LEVEL[actor]], 'placed': True, 'strength': strength}
    d.update(kw)
    return d


T, G, GH, RM = TOMB, GUARD, GHOST, ROYAL
# space id: (name, kind, size, floor, purpose, population, treasure, extra, rooms)
SP = {
    # L1
    'porch': ("Porch", 'room', 'S', geo.L1, "Behind the green doors: the doors' depth; never entered (the doors' click is the exit).",
              [], [], {'empty': True}, ['porch']),
    'entry': ("Entrance hall", 'room', 'M', geo.L1,
              "Inside the green doors (two leaves): the arrival (entrance:d5_door), the welcome statue (aaze0083:6), the exit ('Exit the Great Pyramid?', aaze0083:0). Quiet.",
              [], [], {'empty': True}, ['entry']),
    'reception': ("Reception", 'room', 'M', geo.L1, "The door sign 'Reception' (aaze0083:1); benches, the history statue (aaze0083:8).",
                  [placed(T, 3)], [], {}, ['reception']),
    'chapel_nw': ("North-west chapel", 'room', 'S', geo.L1, "A torch lever; two Tomb Mummies hidden in the wall niches wake when it is lit (D-61 Q2).",
                  [placed(T, 2, notes='hidden in the niches, shown by the torch')], [], {}, ['chapel_nw']),
    'information': ("Information", 'room', 'M', geo.L1, "The door sign 'Information' (aaze0083:4); the visitors' strongbox.",
                    [placed(T, 2), placed(G, 1, 'heavy')], [{'kind': 'chest', 'count': 1, 'tier': 5}], {}, ['information']),
    'chapel_ne': ("North-east chapel", 'room', 'S', geo.L1, "A torch lever and the plaque by it (m28.torch_plaque); two hidden Tomb Mummies wake when it is lit.",
                  [placed(T, 2, notes='hidden in the niches, shown by the torch')], [], {}, ['chapel_ne']),
    'atrium': ("Visitor's Atrium", 'room', 'L', geo.L1,
               "The door sign 'Visitor's Atrium' (aaze0083:3): a court of gold hieroglyph columns with four cold braziers, each lit with its torch; the statue 'Don't forget to light four torches before trying the stairs.' (aaze0083:7, four for six); its south door onto the south gallery.",
               [placed(T, 2), placed(G, 2, 'heavy')], [], {'set_piece': True}, ['atrium_nw', 'atrium_ne', 'atrium_sw', 'atrium_se']),
    'west_gallery': ("West gallery", 'corridor', 'M', geo.L1, "The west side of the ring round the atrium.",
                     [placed(T, 2)], [], {}, ['west_gal_n', 'west_gal_s']),
    'chapel_sw': ("South-west chapel", 'room', 'S', geo.L1, "A torch lever; two hidden Tomb Mummies wake when it is lit; a Pyramid Guard keeps it.",
                  [placed(T, 2, notes='hidden in the niches, shown by the torch'), placed(G, 1, 'heavy')], [], {}, ['chapel_sw']),
    'south_gallery': ("South gallery", 'corridor', 'L', geo.L1,
                      "The ring's south side behind the atrium: the atrium's south door, the stair door (two leaves of xdpyrdor, shut until the four torches burn: 'Access denied!', aaze0083:12).",
                      [placed(T, 1), placed(G, 3, 'heavy')], [], {}, ['south_gal_w', 'south_gal_e']),
    'chapel_se': ("South-east chapel", 'room', 'S', geo.L1, "A torch lever; two hidden Tomb Mummies wake when it is lit; a Pyramid Guard keeps it; the Overseer's Office east.",
                  [placed(T, 2, notes='hidden in the niches, shown by the torch'), placed(G, 1, 'heavy')], [], {}, ['chapel_se']),
    'number_hall': ("Number hall", 'room', 'M', geo.L1,
                    "The ring's east side: eight niches each asking its number (aaze0083:13-38), the two rule statues (aaze0083:9-10); all eight open the Overseer's vault (optional, D-61 Q3).",
                    [placed(T, 2), placed(G, 2, 'heavy')], [], {}, ['number_s', 'number_n']),
    'overseer': ("Overseer's Office", 'room', 'S', geo.L1,
                 "The door sign 'Overseer's Office' (aaze0083:2): the desk and the note ('Three to ten. Every year I forget.'); the vault door.",
                 [], [], {'empty': True}, ['overseer']),
    'vault': ("Overseer's vault", 'room', 'S', geo.L1, "The chest (T5) and the visitors' fees.",
              [], [{'kind': 'chest', 'count': 1, 'tier': 5}], {'empty': True}, ['vault']),
    'stair_foot': ("Grand stair", 'room', 'M', [geo.L1, geo.L2],
                   "Behind the stair door: the grand stair up to L2, the Pharaoh's lift's cage beside it.",
                   [], [], {'empty': True}, ['stair_foot']),
    'lift_foot': ("Pharaoh's lift", 'room', 'S', [geo.L1, geo.L4],
                  "The gilded cage's shaft from the grand stair (L1) to the antechamber (L4): it runs both ways after the party's first entry into the throne hall (117577, D-61 Q4).",
                  [], [], {'empty': True}, ['shaft']),
    # L2
    'landing': ("Stair head", 'room', 'S', geo.L2, "The top of the grand stair.", [], [], {'empty': True}, ['landing']),
    'processional': ("Processional", 'corridor', 'L', geo.L2,
                     "A long gallery of four verse statues on plinths (aaze0084:1-4), ending at the registry door.",
                     [placed(G, 2, 'heavy')], [], {'set_piece': True}, ['proc_1', 'proc_2', 'proc_3']),
    'registry': ("Registry door", 'room', 'S', geo.L2,
                 "The bronze door with its lock ('Registry?', m28.registry_lock: 1701 or NCC-1701; else 'Incorrect!', aaze0084:7) and the brass plaque beside it (m28.registry_plaque, xdregplq).",
                 [], [], {'empty': True}, ['registry']),
    'registry_stair': ("Registry stair", 'room', 'S', [geo.L2, geo.L3], "Behind the registry door: the stair up to the Ancients' level.",
                       [], [], {'empty': True}, ['registry_stair']),
    'tomb_w': ("West tomb", 'room', 'M', geo.L2, "Six sarcophagi by the walls; a dead end with the grave goods' chest.",
               [placed(T, 3), placed(G, 2, 'heavy')], [{'kind': 'chest', 'count': 1, 'tier': 5}], {}, ['tomb_w']),
    'cloister': ("North cloister", 'corridor', 'M', geo.L2, "A pillared walk from the east tomb to the registry door's side: the level's loop.",
                 [placed(T, 2), placed(G, 2, 'heavy'), placed(GH, 1, 'heavy')], [], {}, ['cloister_s', 'cloister_n']),
    'tomb_e': ("East tomb", 'room', 'M', geo.L2, "A royal tomb: a gilded sarcophagus; through it the cloister.",
               [placed(T, 3), placed(G, 2, 'heavy')], [], {}, ['tomb_e']),
    'embalmers': ("Embalmers' room", 'room', 'S', geo.L2, "Off the stair head: tables, jars and linen; a dead end with a find (a jar of salts and a purse).",
                  [placed(T, 2), placed(GH, 1, 'heavy')], [], {}, ['embalmers']),
    # L3
    'maze_landing': ("Maze landing", 'room', 'S', geo.L3, "The top of the registry stair.", [], [], {'empty': True}, ['maze_landing']),
    'pad_hall': ("Pad hall", 'room', 'L', geo.L3,
                 "A hall of Ancient steel: four glyph pads in the floor (sun, eye, scarab, bird; D-61 corrects the graph's five), each a step plate moving the party to its cell; m28.maze on the first arrival (117576).",
                 [placed(GH, 2, 'heavy'), placed(T, 2)], [], {'set_piece': True}, ['pad_w', 'pad_c', 'pad_e']),
    'cell_a': ("Cell of the sun", 'room', 'S', geo.L3, "The sun pad's sealed cell: a chest; a pad back.",
               [], [{'kind': 'chest', 'count': 1, 'tier': 5}], {'empty': True}, ['cell_a']),
    'cell_b': ("Cell of the eye", 'room', 'S', geo.L3, "Two Ghost Mummies; the Overseer's lost map of the pads (the maze's answer-giver); a pad back.",
               [placed(GH, 2, 'heavy')], [], {}, ['cell_b']),
    'cell_c': ("Cell of the scarab", 'room', 'S', geo.L3, "A guard post (two Pyramid Guards) and its weapon rack: one random T5 weapon once (117578, D-61); a pad back.",
               [placed(G, 2, 'heavy')], [], {}, ['cell_c']),
    'cell_d': ("Cell of the bird", 'room', 'S', geo.L3, "The right way: two Pyramid Guards; a second bird pad on to the far cell, a pad back.",
               [placed(G, 2, 'heavy')], [], {}, ['cell_d']),
    'cell_e': ("Far cell", 'room', 'S', geo.L3, "Reached only by the second bird pad: the apex stair's door, a pad back.",
               [placed(T, 2)], [], {}, ['cell_e']),
    'apex_stair': ("Apex stair", 'room', 'S', [geo.L3, geo.L4], "From the far cell's door up to the Pharaoh's apartments.",
                   [], [], {'empty': True}, ['apex_stair']),
    # L4
    'apex_landing': ("Apex landing", 'room', 'S', geo.L4, "The top of the apex stair: two Royal Mummies on guard at the antechamber's door.",
                     [placed(RM, 2, 'heavy')], [], {}, ['apex_landing']),
    'antechamber': ("Antechamber", 'room', 'M', geo.L4,
                    "Gilded columns, the Prime Directive on its stand (m28.prime_directive), the throne hall's great doors (two leaves); the Pharaoh's lift arrives here.",
                    [placed(RM, 4, 'heavy'), placed(G, 2, 'heavy')], [], {}, ['ante_s', 'ante_n']),
    'throne_hall': ("Throne hall", 'room', 'L', geo.L4,
                    "Under the apex: the throne on its gilded dais, the Dragon Pharaoh at it (11919, npc 5453); the Brew of Pure Power in its vat (D-61 Q6 (b)). Quiet. The first entry sets 117577 (the lift wakes).",
                    [], [], {'empty': True, 'set_piece': True, 'goal': True}, ['throne_s', 'throne_c', 'throne_n']),
    'bedchamber': ("Bedchamber", 'room', 'S', geo.L4,
                   "The ornate bed ('Nothing here.', aaze0086:3), the tapestry (the safe's numbers), the wall safe (20-30-1, the chest), the carved button (the secret way to the sky corridor). Quiet.",
                   [], [{'kind': 'chest', 'count': 1, 'tier': 5}], {'empty': True}, ['bedchamber']),
    'sky_corridor': ("Sky door", 'corridor', 'S', geo.L4,
                     "Behind the throne: a short Ancient corridor to the sky door near the apex: 'Access Denied!' (aaze0086:5) before m30.done; after it 'Step out onto the Skyroads?' (d7.sky_door_dd15) and out to D7. Quiet.",
                     [], [], {'empty': True}, ['sky_corridor']),
}

LINKS = [
    # L1
    ('link:green', 'entry', 'porch', 'double_door', {'purpose': "The green doors (two leaves of xdpyrdor): clicked, 'Exit the Great Pyramid?'."}),
    ('link:entry_reception', 'entry', 'reception', 'door', {'purpose': "Door sign 'Reception'."}),
    ('link:entry_information', 'entry', 'information', 'door', {'purpose': "Door sign 'Information'."}),
    ('link:entry_atrium', 'entry', 'atrium', 'open', {'purpose': "Into the atrium (two arches)."}),
    ('link:reception_chapel_nw', 'reception', 'chapel_nw', 'double_door', {}),
    ('link:information_chapel_ne', 'information', 'chapel_ne', 'double_door', {}),
    ('link:reception_west', 'reception', 'west_gallery', 'open', {}),
    ('link:west_chapel_sw', 'west_gallery', 'chapel_sw', 'open', {}),
    ('link:chapel_sw_south', 'chapel_sw', 'south_gallery', 'open', {}),
    ('link:south_chapel_se', 'south_gallery', 'chapel_se', 'open', {}),
    ('link:south_atrium', 'south_gallery', 'atrium', 'double_door', {'purpose': "The atrium's south door."}),
    ('link:chapel_se_numbers', 'chapel_se', 'number_hall', 'open', {}),
    ('link:numbers_information', 'number_hall', 'information', 'door', {}),
    ('link:west_overseer', 'chapel_se', 'overseer', 'door', {'purpose': "Door sign 'Overseer's Office'."}),
    ('link:overseer_vault', 'overseer', 'vault', 'door', {'opened_by': 'poi:niches', 'purpose': "The vault door: all eight niches."}),
    ('link:atrium_stair', 'south_gallery', 'stair_foot', 'double_door',
     {'opened_by': 'poi:torches', 'purpose': "The stair door: all four torches (m28.torches)."}),
    ('link:stair_l2', 'stair_foot', 'landing', 'stairs', {'purpose': "The grand stair."}),
    ('link:stair_liftfoot', 'stair_foot', 'lift_foot', 'open', {}),
    ('link:lift', 'lift_foot', 'antechamber', 'lift', {'opened_by': 'poi:throne_reached', 'purpose': "The Pharaoh's lift: after the first entry into the throne hall."}),
    # L2
    ('link:landing_processional', 'landing', 'processional', 'open', {}),
    ('link:processional_registry', 'processional', 'registry', 'open', {}),
    ('link:registry_door', 'registry', 'registry_stair', 'door', {'opened_by': 'poi:registry_lock', 'purpose': "The bronze registry door (1701)."}),
    ('link:registry_up', 'registry_stair', 'maze_landing', 'stairs', {}),
    ('link:processional_tomb_w', 'processional', 'tomb_w', 'double_door', {}),
    ('link:processional_tomb_e', 'processional', 'tomb_e', 'double_door', {}),
    ('link:tomb_e_cloister', 'tomb_e', 'cloister', 'open', {}),
    ('link:cloister_registry', 'cloister', 'registry', 'door', {}),
    ('link:landing_embalmers', 'landing', 'embalmers', 'door', {}),
    # L3
    ('link:landing_pads', 'maze_landing', 'pad_hall', 'open', {}),
    ('link:pad_sun', 'pad_hall', 'cell_a', 'teleport', {'purpose': "Pad: sun."}),
    ('link:pad_eye', 'pad_hall', 'cell_b', 'teleport', {'purpose': "Pad: eye."}),
    ('link:pad_scarab', 'pad_hall', 'cell_c', 'teleport', {'purpose': "Pad: scarab."}),
    ('link:pad_bird', 'pad_hall', 'cell_d', 'teleport', {'purpose': "Pad: bird."}),
    ('link:pad_bird2', 'cell_d', 'cell_e', 'teleport', {'purpose': "The second bird."}),
    ('link:back_a', 'cell_a', 'pad_hall', 'teleport', {'purpose': "The pad back."}),
    ('link:back_b', 'cell_b', 'pad_hall', 'teleport', {'purpose': "The pad back."}),
    ('link:back_c', 'cell_c', 'pad_hall', 'teleport', {'purpose': "The pad back."}),
    ('link:back_d', 'cell_d', 'pad_hall', 'teleport', {'purpose': "The pad back."}),
    ('link:back_e', 'cell_e', 'pad_hall', 'teleport', {'purpose': "The pad back."}),
    ('link:apex_door', 'cell_e', 'apex_stair', 'door', {}),
    ('link:stair_l4', 'apex_stair', 'apex_landing', 'stairs', {'purpose': "The apex stair."}),
    # L4
    ('link:apex_ante', 'apex_landing', 'antechamber', 'door', {}),
    ('link:ante_throne', 'antechamber', 'throne_hall', 'double_door', {'purpose': "The great doors."}),
    ('link:throne_bed', 'throne_hall', 'bedchamber', 'door', {}),
    ('link:throne_sky', 'throne_hall', 'sky_corridor', 'open', {'purpose': "Behind the throne."}),
    ('link:bed_sky', 'bedchamber', 'sky_corridor', 'secret_door', {'opened_by': 'poi:button', 'purpose': "The carved button."}),
]

PITCH = ("The Dragon Pharaoh's pyramid in the Desert of Doom, a museum for visitors gone to dust: the green doors "
         "open on the Royal Pyramid's halls, where four torches round the atrium wake the wardens in their niches and "
         "unlock the grand stair; a processional of verse statues ends at a registry door that wants a starship's "
         "number; above it the Ancients' steel hall of glyph pads, where only the bird leads on; at the apex the "
         "Pharaoh waits in his gilded throne hall, beside a vat he warns you away from.")
PURPOSE = ("Story M28 (QUESTS.md): climb to the Dragon Pharaoh with his orb (npc 5453, The orb): the torches "
           "(m28.torches), the registry (m28.registry_lock), the pad maze (m28.maze), the Prime Directive "
           "(m28.prime_directive); M30 and M36 bring the party back (the Pharaoh's lift after the first audience); "
           "D-58's sky door to D7 after m30.done. Class L, party 44-47, monsters 42-65, no boss.")
MOOD = ("Sandstone and gold under hieroglyphs (MM6's Tomb of VARN), cold braziers that wake with the torches; one "
        "floor of rusted Ancient steel between the tombs and the apex; at the top, gold, blue tiles and a quiet hall.")


def plan(level):
    spaces = []
    for sid, (name, kind, size, fl, purpose, pop, tre, extra, rooms) in SP.items():
        s = {'id': 'room:' + sid, 'name': name, 'kind': kind, 'size': size, 'floor': fl, 'purpose': purpose}
        if level != 'L1':
            xs, ys = [], []
            for r in rooms:
                x0, y0, x1, y1 = geo.bbox(r)
                xs += [x0, x1]
                ys += [y0, y1]
            s['extent'] = [max(xs) - min(xs), max(ys) - min(ys)]
            s['at'] = [(min(xs) + max(xs)) // 2, (min(ys) + max(ys)) // 2]
            s['clear_height'] = geo.R[rooms[0]][3] - geo.R[rooms[0]][2]
            th = geo.R[rooms[0]][4]
            s['theme'] = next(t['notes'] for t in geo.THEMES if t['id'] == th)
        if extra.get('empty'):
            s['empty'] = True
        if pop:
            s['population'] = pop
        if tre:
            s['treasure'] = tre
        spaces.append(s)
    links = []
    for lid, a, b, kind, extra in LINKS:
        d = {'id': lid, 'from': 'room:' + a, 'to': 'room:' + b, 'kind': kind}
        d.update(extra)
        links.append(d)
    return {
        'format': 0, 'level': level if level in ('L1', 'L2') else 'L3', 'pitch': PITCH,
        'purpose': PURPOSE, 'mood': MOOD, 'datum': 'arrival', 'spaces': spaces, 'links': links,
        'loops': [
            {'id': 'loop:ring', 'spaces': ['room:entry', 'room:reception', 'room:west_gallery', 'room:chapel_sw',
                                           'room:south_gallery', 'room:chapel_se', 'room:number_hall', 'room:information'],
             'notes': "L1: the ring round the atrium, either way from the entrance hall."},
            {'id': 'loop:atrium', 'spaces': ['room:entry', 'room:atrium', 'room:south_gallery', 'room:chapel_sw',
                                             'room:west_gallery', 'room:reception'],
             'notes': "L1: through the atrium and out by its south door."},
            {'id': 'loop:tombs', 'spaces': ['room:processional', 'room:tomb_e', 'room:cloister', 'room:registry'],
             'notes': "L2: from the processional through the east tomb and the cloister to the registry door."},
            {'id': 'loop:apartments', 'spaces': ['room:throne_hall', 'room:bedchamber', 'room:sky_corridor'],
             'notes': "L4: once the button is pressed, from the bedchamber by the secret door to the sky corridor and back behind the throne."},
            {'id': 'loop:lift', 'spaces': ['room:stair_foot', 'room:lift_foot', 'room:antechamber'],
             'notes': "After the first audience: the Pharaoh's lift between the grand stair and the antechamber."},
        ],
        'entrances': [
            {'id': 'entrance:d5_door', 'space': 'room:entry', 'kind': 'both', 'neighbour': 'exit:d5_door', 'facing': 's',
             'how': "D5's green door (A6's door:dd15, m28.door with the key) into the entrance hall, about 384 inside the doors, facing south; out by the green doors' exit preset to D5's entrance:dd15_door."},
            {'id': 'entrance:d7_sky', 'space': 'room:sky_corridor', 'kind': 'both', 'neighbour': 'exit:d7_sky', 'facing': 's',
             'how': "D7's sky door (door:dd15, after m30.done, D-58) into the sky corridor about 256 inside the door, facing the throne; out by the sky door after m30.done to D7's entrance:dd15_sky."},
        ],
        'critical_path': ['room:entry', 'room:information', 'room:chapel_ne', 'room:information', 'room:entry',
                          'room:reception', 'room:chapel_nw', 'room:reception', 'room:west_gallery', 'room:chapel_sw',
                          'room:south_gallery', 'room:chapel_se', 'room:south_gallery', 'room:stair_foot',
                          'room:landing', 'room:processional', 'room:registry', 'room:registry_stair',
                          'room:maze_landing', 'room:pad_hall', 'room:cell_d', 'room:cell_e', 'room:apex_stair',
                          'room:apex_landing', 'room:antechamber', 'room:throne_hall'],
        'return_path': ['room:throne_hall', 'room:antechamber', 'room:lift_foot', 'room:stair_foot',
                        'room:south_gallery', 'room:atrium', 'room:entry'],
        'goals': [
            {'id': 'goal:pharaoh', 'space': 'room:throne_hall', 'kind': 'use',
             'what': "The Dragon Pharaoh (11919, npc 5453): A3's topics The orb (M28), Chosen Ones (M30), M36."},
        ],
        'keys': [
            {'id': 'key:torches', 'grants': {'qbit': 111561}, 'found_in': 'room:chapel_se', 'how': 'lever',
             'notes': "The four torch levers (any order): the last one lit calls m28.torches; the stair door opens."},
            {'id': 'key:registry', 'grants': {'qbit': 111562}, 'found_in': 'room:registry', 'how': 'lever',
             'notes': "The registry lock's answer (1701): m28.registry_lock; the registry door opens."},
            {'id': 'key:niches', 'grants': {'qbit': 117573}, 'found_in': 'room:number_hall', 'how': 'lever',
             'notes': "The eight niches' numbers (3 to 10): the vault door opens (optional)."},
            {'id': 'key:button', 'grants': {'qbit': 117575}, 'found_in': 'room:bedchamber', 'how': 'lever',
             'notes': "The carved button: the secret way to the sky corridor."},
            {'id': 'key:throne_reached', 'grants': {'qbit': 117577}, 'found_in': 'room:throne_hall', 'how': 'lever',
             'notes': "The first entry into the throne hall: the Pharaoh's lift runs."},
        ],
        'points_of_interest': [
            {'id': 'poi:torches', 'space': 'room:chapel_ne', 'kind': 'lever', 'count': 4,
             'behaviour': "Four one-way torch levers (one per corner chapel): each lights its torch and its atrium brazier and shows its chapel's two niche mummies; a second pull 'The lever is stuck.' (aaze0083:39); the last calls m28.torches."},
            {'id': 'poi:niches', 'space': 'room:number_hall', 'kind': 'lever', 'count': 8,
             'behaviour': "Eight niches, each asking its number (aaze0083:13-38): 'Correct!' / 'Wrong!'; all eight open the vault."},
            {'id': 'poi:registry_lock', 'space': 'room:registry', 'kind': 'lever',
             'behaviour': "'Registry?': 1701 or NCC-1701 calls m28.registry_lock; else 'Incorrect!' (aaze0084:7)."},
            {'id': 'poi:throne_reached', 'space': 'room:throne_hall', 'kind': 'lever',
             'behaviour': "The first entry into the throne hall (117577): the Pharaoh's lift wakes (D-61 Q4)."},
            {'id': 'poi:button', 'space': 'room:bedchamber', 'kind': 'lever',
             'behaviour': "The carved button: the secret door to the sky corridor opens and stays open (117575)."},
            {'id': 'poi:statues', 'space': 'room:processional', 'kind': 'sign', 'count': 4,
             'behaviour': "The four verse statues (aaze0084:1-4)."},
            {'id': 'poi:welcome', 'space': 'room:entry', 'kind': 'sign', 'behaviour': "The welcome statue (aaze0083:6)."},
            {'id': 'poi:history', 'space': 'room:reception', 'kind': 'sign', 'behaviour': "The history statue (aaze0083:8)."},
            {'id': 'poi:torch_statue', 'space': 'room:atrium', 'kind': 'sign',
             'behaviour': "'Don't forget to light four torches before trying the stairs.' (aaze0083:7, four for six)."},
            {'id': 'poi:rules', 'space': 'room:number_hall', 'kind': 'sign', 'count': 2,
             'behaviour': "The rule statues (aaze0083:9-10)."},
            {'id': 'poi:note', 'space': 'room:overseer', 'kind': 'sign', 'behaviour': "The Overseer's note: the numbers' answer."},
            {'id': 'poi:pad_map', 'space': 'room:cell_b', 'kind': 'sign', 'behaviour': "The Overseer's lost map of the pads: the maze's answer."},
            {'id': 'poi:book', 'space': 'room:antechamber', 'kind': 'sign', 'behaviour': "The Prime Directive (m28.prime_directive)."},
            {'id': 'poi:brew', 'space': 'room:throne_hall', 'kind': 'trap',
             'behaviour': "The Brew of Pure Power: the Pharaoh's warning (aaze0086:0); a second click in the same visit burns the member (50 fire), 'He did warn you.'."},
            {'id': 'poi:safe', 'space': 'room:bedchamber', 'kind': 'lever',
             'behaviour': "The wall safe: Left? 20, Right? 30, Left? 1 (aaze0086:20-29): the chest; 'No Luck.' (aaze0086:19)."},
            {'id': 'poi:tapestry', 'space': 'room:bedchamber', 'kind': 'sign', 'behaviour': "The tapestry: the safe's numbers."},
            {'id': 'poi:sky_door', 'space': 'room:sky_corridor', 'kind': 'sign',
             'behaviour': "'Access Denied!' (aaze0086:5) before m30.done; after it the question and the way out to D7 (entrance:dd15_sky)."},
            {'id': 'poi:rack', 'space': 'room:cell_c', 'kind': 'sign', 'behaviour': "The weapon rack: one random T5 weapon once (117578), then 'Nothing here.'."},
        ],
        'mechanisms': [
            {'kind': 'one-way torch lever showing hidden actors and lighting a brazier', 'count': 4},
            {'kind': 'typed-answer niche', 'count': 8}, {'kind': 'typed-answer lock', 'count': 1},
            {'kind': 'in-map pad (step plate)', 'count': 10}, {'kind': 'two-stop lift after a qbit', 'count': 1},
            {'kind': 'three-prompt wall safe', 'count': 1}, {'kind': 'secret door by a button', 'count': 1},
            {'kind': 'talking figure (the Dragon Pharaoh)', 'count': 1},
        ],
        'totals': {'chests': 5, 'doors': 21, 'rooms': len(SP), 'spawn_points': 0},
        'notes': "Graph: devdocs/xeen/mockups/act5_graphs/dd15.graph.yml; D-61 (mockups/act5_a8_decisions.md) wins where they differ: four pads in the pad hall (not five), a pad back from every cell; the scarab cell's find; the Pharaoh's lift after the first entry into the throne hall (117577), not m28.done; the Brew's second click; the Pharaoh is S's P5 figure 11919 (npc 5453). Changes from the graph (A8 L1): the porch behind the green doors (the doors' click is the exit); the registry stair and the apex stair are rooms of their own (the stairs between the floors); the lift_foot space is the lift's shaft. Floors 768 apart: L1 0, L2 768, L3 1536, L4 2304. All 70 monsters placed; eight of them hidden in the torch chapels' niches.",
    }


DIAGRAM = """L4 THE PHARAOH'S APARTMENTS (2304)
      [SKY DOOR: 'Access Denied!' / D7]          secret==[BEDCHAMBER: bed, tapestry, wall safe $, button]
             |  behind the throne                         |door
      [THRONE HALL x3: the Dragon Pharaoh, dais, vat] ----+
             ||great doors
      [ANTECHAMBER x2: Prime Directive, columns] -- door -- [APEX LANDING] <- apex stair
             |lift (after the first entry into the throne hall, 117577)
L3 THE PAD MAZE (1536, Ancient)
      [MAZE LANDING] -- [PAD HALL x3: pads sun, eye, scarab, bird]
          pad sun -> [CELL OF THE SUN $]     pad eye -> [CELL OF THE EYE: the Overseer's map]
          pad scarab -> [CELL OF THE SCARAB: weapon rack find]
          pad bird -> [CELL OF THE BIRD] -- second bird -> [FAR CELL] =door= [APEX STAIR] up
          (every cell: a pad back to the hall)
L2 THE REGISTRY LEVEL (768)
      [EMBALMERS] =door= [STAIR HEAD] -- [PROCESSIONAL x3: four verse statues] -- [REGISTRY: plaque, 'Registry?'] =bronze door= [REGISTRY STAIR] up
                               [WEST TOMB $] ==double== /   \\ ==double== [EAST TOMB] -- [NORTH CLOISTER x2] =door= [REGISTRY]
L1 THE ROYAL PYRAMID (0)
      [NW CHAPEL: torch]                 ==green doors== (exit)                 [NE CHAPEL: torch, plaque]
          ||                          [ENTRANCE HALL: welcome statue]                ||
      [RECEPTION: history statue] =door=        |  arches        =door= [INFORMATION $]
          |                          [VISITOR'S ATRIUM x4: four braziers]            |door
      [WEST GALLERY x2]                         ||south door              [NUMBER HALL x2: eight niches]
          |                                [SOUTH GALLERY x2]                         |
      [SW CHAPEL: torch] ---------------------/  ||stair door  \\---------- [SE CHAPEL: torch] =door= [OVERSEER] =door= [VAULT $]
                                         [GRAND STAIR] -- [PHARAOH'S LIFT shaft]
 $ chest   =door= door   x2/x3/x4 sectors
"""


def write(level):
    folder = BR / level
    folder.mkdir(parents=True, exist_ok=True)
    dump(folder / 'project.yml', project(level))
    dump(folder / 'plan.yml', plan(level))
    (folder / 'diagram.txt').write_text(DIAGRAM)
    if level in ('L3', 'L4'):
        rooms = []
        for r in geo.ORDER:
            doc = geo.room_doc(r)
            sp = next(s for s, v in SP.items() if r in v[8])
            if sp != r:
                doc['space'] = 'room:' + sp
            rooms.append(doc)
        dump(folder / 'rooms.yml', {
            'format': 0, 'themes': geo.THEMES, 'defaults': {'theme': 'theme:hall', 'ambient': 12},
            'rooms': rooms, 'openings': geo.OPENINGS,
            'notes': "DD-15 Great Pyramid: L1 at 0, L2 at 768, L3 at 1536, L4 at 2304, in one frame (x east, y north, z up). Written by output/studio_cal/dd15/tools/gen.py (geo.py).",
        })
    if level == 'L4':
        import dress
        dress.write(folder)


if __name__ == '__main__':
    for lv in sys.argv[1:]:
        write(lv)
