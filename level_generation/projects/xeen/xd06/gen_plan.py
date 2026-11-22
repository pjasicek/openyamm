#!/usr/bin/env python3
"""XD-06 Temple of Yak: writes the briefs L1 (plan), L2 (specification) and L3 (sketch: plan + rooms.yml shell) in
devdocs/xeen/briefs/xd06/L1..L3, and L4's plan.yml (L3's plan, kept). The L3 shell is L4's rooms.yml (gen.py)."""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import copy
from pathlib import Path

import yaml

R = Path(_REPO_ROOT)
B = R / 'devdocs/xeen/briefs/xd06'

PITCH = ("An ancient temple of the evil clerics of Yak, backed into a rise at the dark south end of the fairy woods, "
         "opened by Mirabeth's Yak Stone. Above, a temple of brick and red torchlight: a narthex, a pillared nave "
         "where Yak's idol glowers from its dais, chapels, the clerics' dormitory and refectory, their library and "
         "vestry, and behind the idol a treasury gate held by two iron bars whose buttons lie apart. Below, crypts and "
         "a bone-house lead to a cave flooded by the Yak Pool, green, bubbling and sickening; three buttons on its "
         "shore raise a causeway of stone blocks out of the water, if set right. Beyond it the liches' crypt and the "
         "sanctum, where the Yak Master guards the reliquary of the Elixir of Restoration; his own stair climbs back "
         "up to the vestry.")
PURPOSE = ("Story step M10 (King's Megacredits for Newcastle's walls: the first five of the fifteen come from here) "
           "and Mirabeth's quest Q-C12 (the Elixir of Restoration). A return visit on X2 at party level 14 to 16, "
           "like MM6's Gharik's Forge: clerics, skeletons and liches of levels 14 to 28, the Yak Master 35. Two switch "
           "puzzles worked out in the game (the treasury's two bars, the pool's causeway), a pool that sickens, the "
           "Elixir. About 30 minutes.")
MOOD = ("A cult's house that still works: red torchlight on old brick, the idol's glow, the clerics' beds and books in "
        "use. Below, cold rock and bones, then the pool's sick green light and its stench, then the green-black "
        "sanctum lit red over the altar. The deeper the party goes, the darker and quieter.")


def sp(id, name, kind='room', size='M', **kw):
    d = {'id': id, 'name': name, 'kind': kind, 'size': size}
    d.update(kw)
    return d


def pop_slot(slot, groups, rank, strength, notes=None, per=(2, 3)):
    d = {'slot': slot, 'groups': groups, 'per_marker': list(per), 'strength': strength, 'rank': rank}
    if notes:
        d['notes'] = notes
    return d


spaces = [
    sp('room:porch', 'Temple porch', size='S', extent=[1280, 1152], floor=0, clear_height=640, relief='flat',
       where="South edge, centre.", purpose="Arrival from X2 and the way out. Safe.", empty=True,
       shape="A plain brick porch inside the temple's front door; the Yak door north."),
    sp('room:narthex', 'Narthex', size='M', extent=[2560, 768], floor=0, clear_height=768, relief='flat',
       where="South, across the temple's width.", purpose="The cross hall: west to the clerics' wing, east to the library, the nave north.",
       empty=True, shape="A long cross hall."),
    sp('room:nave', 'Nave of Yak', size='XL', extent=[2560, 3584], floor=0, clear_height=[1088, 1344], relief='flat',
       where="Centre of the temple.", islands=8,
       features=[{'kind': 'colonnade', 'count': 8, 'where': "Two rows of four brick pillars"},
                 {'kind': 'dais', 'rise': 32, 'where': "North end, with Yak's idol on its plinth"}],
       shape="A long pillared hall with a raised middle ceiling.",
       purpose="Signature room: the cult at worship (the first fight), Yak's idol, the treasury gate in the north wall.",
       population=[pop_slot(1, 3, 'b', 'pack', "Clerics at worship round the hall.")]),
    sp('room:chapel_w', 'West chapel', size='S', extent=[832, 1280], floor=0, clear_height=768, relief='flat',
       where="West of the nave.", purpose="The west bar's button (set:twin_bars); a side altar.",
       population=[pop_slot(1, 1, 'b', 'light')]),
    sp('room:chapel_e', 'East chapel', size='S', extent=[832, 1280], floor=0, clear_height=768, relief='flat',
       where="East of the nave.", purpose="A side altar; the way to the vestry.", population=[pop_slot(1, 1, 'b', 'light')]),
    sp('room:passage_w', 'West passage', kind='corridor', size='S', extent=[1664, 1152], floor=0, clear_height=448,
       relief='flat', where="South-west.", purpose="Narthex to the dormitory.", empty=True, shape="An L-shaped passage."),
    sp('room:passage_e', 'East passage', kind='corridor', size='S', extent=[1664, 1152], floor=0, clear_height=448,
       relief='flat', where="South-east.", purpose="Narthex to the library.", empty=True, shape="An L-shaped passage."),
    sp('room:dormitory', 'Dormitory', size='M', extent=[1600, 1152], floor=0, clear_height=576, relief='flat',
       where="West wing, south.", purpose="The clerics' cots; a secret door to a hidden cell.",
       population=[pop_slot(1, 1, 'b', 'light', "Clerics resting.")]),
    sp('room:hidden_cell', 'Hidden cell', size='S', extent=[576, 448], floor=0, clear_height=448, relief='flat',
       where="West of the dormitory.", secret=True, empty=True, purpose="A cleric's private hoard.",
       treasure=[{'kind': 'chest', 'count': 1, 'tier': 2, 'items': [3, 3]}]),
    sp('room:refectory', 'Refectory', size='M', extent=[1600, 1600], floor=0, clear_height=640, relief='flat',
       where="West wing, north.", purpose="The clerics' table; the stair down to the crypts leaves north.",
       population=[pop_slot(1, 1, 'b', 'light')]),
    sp('room:library', 'Library', size='M', extent=[1600, 1152], floor=0, clear_height=640, relief='flat',
       where="East wing, south.", purpose="The east bar's button (set:twin_bars); the clerics' scrolls.",
       population=[pop_slot(1, 1, 'b', 'light')], treasure=[{'kind': 'chest', 'count': 1, 'tier': 2, 'items': [4, 4]}]),
    sp('room:vestry', 'Vestry', size='M', extent=[1600, 1600], floor=0, clear_height=640, relief='flat',
       where="East wing, north.", purpose="Robe cabinets; an elder; the top of the Master's stair (opens from below).",
       population=[pop_slot(1, 1, 'b', 'light'),
                   {'actor': 'Yak Elder', 'role': 'elder', 'groups': 1, 'levels': [28, 28], 'placed': True, 'strength': 'heavy'}]),
    sp('room:treasury', 'Treasury', size='S', extent=[896, 960], floor=0, clear_height=512, relief='flat',
       where="North of the nave, behind the barred gate.", empty=True,
       purpose="Goal: the strongbox with five King's Megacredits.",
       treasure=[{'kind': 'chest', 'count': 1, 'tier': 2, 'items': [7, 7], 'notes': "Five Megacredits, gold and two rolls of level 2."}]),
    sp('room:stair_w', 'West stair', kind='corridor', size='S', extent=[576, 1536], floor=[-768, 0], clear_height=448,
       relief='steps', where="North-west.", purpose="Down from the refectory to the crypts.", empty=True),
    sp('room:master_stair', "Master's stair", kind='corridor', size='M', extent=[576, 3712], floor=[-768, 0],
       clear_height=448, relief='steps', where="East, from the lich crypt up to the vestry.",
       purpose="The return: the Yak Master's own stair up to the vestry; its door opens from below only.", empty=True),
    sp('room:crypt', 'Crypt of the clergy', size='M', extent=[1728, 1536], floor=-768, clear_height=704, relief='flat',
       where="Undercroft, west.", islands=2, purpose="Coffins and tombs; the dead rise.",
       population=[pop_slot(2, 2, 'c', 'pack', "Skeletons among the tombs.")],
       treasure=[{'kind': 'chest', 'count': 1, 'tier': 2, 'items': [3, 3], 'notes': "A heavy coffin: a might test."}]),
    sp('room:ossuary', 'Ossuary', size='M', extent=[1472, 1344], floor=-768, clear_height=640, relief='flat',
       where="Undercroft, north-west.", purpose="A bone-house; the passage east to the pool.",
       population=[pop_slot(2, 2, 'c', 'pack')]),
    sp('room:near_bank', 'Yak Pool, near bank', size='M', extent=[832, 1984], floor=-768, clear_height=[704, 832],
       relief='flat', where="Undercroft, west of centre.",
       purpose="The pool's west shore: the three bridge buttons, the basin 'Yak Pool' (drink).",
       population=[pop_slot(2, 1, 'c', 'light')]),
    sp('room:yak_pool', 'Yak Pool', kind='room', size='M', extent=[1024, 1344], floor=-928, clear_height=864,
       relief='pit', where="Undercroft, centre.",
       features=[{'kind': 'platform', 'count': 3, 'rise': 160, 'where': "A line of three stone blocks across the pool, east-west (lifts)"},
                 {'kind': 'stair', 'rise': 160, 'where': "Steps up out of the water onto the near bank, at the south end"}],
       purpose="Set piece: the pool that sickens and the causeway puzzle.", empty=True),
    sp('room:far_bank', 'Yak Pool, far bank', size='L', extent=[1600, 1856], floor=-768, clear_height=[768, 960],
       relief='flat', where="Undercroft, centre-east.", purpose="Skeletons waiting across the pool; ways north and east.",
       population=[pop_slot(2, 2, 'c', 'pack', "They wait across the water until the causeway rises.")]),
    sp('room:lich_crypt', 'Lich crypt', size='M', extent=[1600, 1280], floor=-768, clear_height=640, relief='flat',
       where="Undercroft, east.", purpose="Liches; the foot of the Master's stair.",
       population=[pop_slot(3, 2, 'a', 'heavy', "The source's Yak Liches.", per=(1, 2))]),
    sp('room:sanctum_way', 'Sanctum way', kind='corridor', size='S', extent=[512, 576], floor=-768, clear_height=512,
       relief='flat', where="Undercroft, north of the far bank.", purpose="To the sanctum's doors.", empty=True),
    sp('room:sanctum', "The Yak Master's sanctum", size='L', extent=[2432, 2432], floor=-768, clear_height=960,
       relief='flat', where="Undercroft, far north.", islands=8,
       features=[{'kind': 'colonnade', 'count': 8, 'where': "A ring of eight pillars"},
                 {'kind': 'dais', 'rise': 32, 'where': "North, the black altar on it"}],
       shape="An octagon.", purpose="Boss: the Yak Master and two elders; his death opens the reliquary.",
       population=[{'actor': 'Yak Master', 'role': 'boss', 'groups': 1, 'levels': [35, 35], 'placed': True, 'strength': 'boss',
                    'notes': "Boss hit points (three times the row); carries the sixth Megacredit."},
                   {'actor': 'Yak Elder', 'role': 'elder', 'groups': 2, 'levels': [28, 28], 'placed': True, 'strength': 'heavy'},
                   pop_slot(1, 1, 'b', 'light')]),
    sp('room:reliquary', 'Reliquary', size='S', extent=[512, 512], floor=-768, clear_height=448, relief='flat',
       where="Behind the altar.", empty=True, purpose="Goal: the Elixir of Restoration.",
       treasure=[{'kind': 'chest', 'count': 1, 'tier': 2, 'items': [1, 1], 'notes': "The Elixir."}]),
    sp('room:master_cell', "Master's cell", size='S', extent=[640, 512], floor=-768, clear_height=448, relief='flat',
       where="East of the sanctum.", empty=True, purpose="The Yak Master's bed and his hoard (one step up).",
       treasure=[{'kind': 'chest', 'count': 1, 'tier': 3, 'items': [3, 3]}]),
]


def link(id, frm, to, kind='open', **kw):
    d = {'id': id, 'from': frm, 'to': to, 'kind': kind}
    d.update(kw)
    return d


links = [
    link('link:porch_narthex', 'room:porch', 'room:narthex', 'door', motion='rise', notes="The Yak door: plain."),
    link('link:narthex_nave', 'room:narthex', 'room:nave', width=1280, notes="A wide arch."),
    link('link:narthex_passage_w', 'room:narthex', 'room:passage_w', 'door', motion='rise'),
    link('link:narthex_passage_e', 'room:narthex', 'room:passage_e', 'door', motion='rise'),
    link('link:passage_w_dormitory', 'room:passage_w', 'room:dormitory'),
    link('link:passage_e_library', 'room:passage_e', 'room:library'),
    link('link:dormitory_hidden_cell', 'room:dormitory', 'room:hidden_cell', 'secret_door', motion='sink'),
    link('link:dormitory_refectory', 'room:dormitory', 'room:refectory'),
    link('link:refectory_chapel_w', 'room:refectory', 'room:chapel_w'),
    link('link:chapel_w_nave', 'room:chapel_w', 'room:nave', width=640, notes="An arch."),
    link('link:chapel_e_nave', 'room:chapel_e', 'room:nave', width=640, notes="An arch."),
    link('link:library_vestry', 'room:library', 'room:vestry'),
    link('link:vestry_chapel_e', 'room:vestry', 'room:chapel_e'),
    link('link:nave_treasury', 'room:nave', 'room:treasury', 'door', motion='rise',
         condition={'all': [{'map_var': 'bar_w'}, {'map_var': 'bar_e'}]}, opened_by='set:twin_bars',
         notes="The treasury gate: both bars sunk (the west chapel's button and the library's)."),
    link('link:refectory_stair_w', 'room:refectory', 'room:stair_w'),
    link('link:stair_w_crypt', 'room:stair_w', 'room:crypt', 'stairs', rise=-768),
    link('link:vestry_master_stair', 'room:vestry', 'room:master_stair', 'door', motion='rise', one_way=False,
         opens_from='room:master_stair', notes="The Master's door: opened from the stair only; a shortcut back once opened."),
    link('link:master_stair_lich_crypt', 'room:master_stair', 'room:lich_crypt', 'stairs', rise=-768),
    link('link:crypt_ossuary', 'room:crypt', 'room:ossuary'),
    link('link:ossuary_near_bank', 'room:ossuary', 'room:near_bank'),
    link('link:near_bank_pool', 'room:near_bank', 'room:yak_pool', 'drop', rise=-160, width=1024,
         notes="The near bank's edge: a drop of 160 into the water (steps lead back up)."),
    link('link:far_bank_pool', 'room:far_bank', 'room:yak_pool', 'bridge', width=512, opened_by='set:causeway',
         notes="The causeway's far landing: only on the three raised blocks."),
    link('link:far_bank_lich_crypt', 'room:far_bank', 'room:lich_crypt'),
    link('link:far_bank_sanctum_way', 'room:far_bank', 'room:sanctum_way'),
    link('link:sanctum_way_sanctum', 'room:sanctum_way', 'room:sanctum', 'double_door', motion='slide'),
    link('link:sanctum_reliquary', 'room:sanctum', 'room:reliquary', 'door', motion='rise',
         condition={'kills': {'monster': 'Yak Master'}}, notes="Held by the Yak Master's will: it rises when he dies."),
    link('link:sanctum_master_cell', 'room:sanctum', 'room:master_cell', 'door', motion='rise'),
]

plan_common = {
    'format': 0, 'pitch': PITCH, 'purpose': PURPOSE, 'mood': MOOD, 'datum': 'arrival', 'spaces': spaces,
    'regions': [
        {'id': 'region:temple', 'name': 'The temple', 'where': 'South half, floor 0',
         'spaces': ['room:porch', 'room:narthex', 'room:nave', 'room:chapel_w', 'room:chapel_e', 'room:passage_w',
                    'room:passage_e', 'room:dormitory', 'room:hidden_cell', 'room:refectory', 'room:library',
                    'room:vestry', 'room:treasury'],
         'theme': "MM7 Temple of Baa (d04): brick, flags, coffered ceilings, the skull frieze"},
        {'id': 'region:undercroft', 'name': 'The undercroft', 'where': 'North half, 768 down',
         'spaces': ['room:stair_w', 'room:crypt', 'room:ossuary', 'room:near_bank', 'room:yak_pool', 'room:far_bank',
                    'room:lich_crypt', 'room:master_stair'],
         'theme': "MM7 Barrow I (mdt03): sandy rock, grey rock floors, green-black roofs, plastered crypts"},
        {'id': 'region:sanctum', 'name': "The Master's sanctum", 'where': 'Far north, 768 down',
         'spaces': ['room:sanctum_way', 'room:sanctum', 'room:reliquary', 'room:master_cell'],
         'theme': "d04's green-black slabs under the skull frieze"},
    ],
    'links': links,
    'loops': [
        {'id': 'loop:west_wing', 'spaces': ['room:narthex', 'room:passage_w', 'room:dormitory', 'room:refectory', 'room:chapel_w', 'room:nave'],
         'notes': "Round the clerics' wing and back through the west chapel."},
        {'id': 'loop:east_wing', 'spaces': ['room:narthex', 'room:passage_e', 'room:library', 'room:vestry', 'room:chapel_e', 'room:nave'],
         'notes': "Round the library and vestry and back through the east chapel."},
        {'id': 'loop:undercroft', 'spaces': ['room:refectory', 'room:stair_w', 'room:crypt', 'room:ossuary', 'room:near_bank', 'room:yak_pool',
                                             'room:far_bank', 'room:lich_crypt', 'room:master_stair', 'room:vestry', 'room:chapel_e',
                                             'room:nave', 'room:chapel_w'],
         'closed_until': {'map_var': 'master_door'},
         'notes': "Down the west stair, across the causeway, up the Master's stair: closed until the Master's door is opened from below."},
    ],
    'entrances': [
        {'id': 'entrance:woods', 'space': 'room:porch', 'kind': 'both', 'neighbour': 'door:x2_woods', 'facing': 'n',
         'how': "The temple's front door in the porch's south wall, from the fairy woods' dark south end on X2 (its outside needs the Yak Stone)."},
    ],
    'critical_path': ['room:porch', 'room:narthex', 'room:nave', 'room:chapel_w', 'room:nave', 'room:chapel_e', 'room:vestry',
                      'room:library', 'room:vestry', 'room:chapel_e', 'room:nave', 'room:treasury', 'room:nave', 'room:chapel_w',
                      'room:refectory', 'room:stair_w', 'room:crypt', 'room:ossuary', 'room:near_bank', 'room:yak_pool',
                      'room:far_bank', 'room:sanctum_way', 'room:sanctum', 'room:reliquary'],
    'return_path': ['room:reliquary', 'room:sanctum', 'room:sanctum_way', 'room:far_bank', 'room:lich_crypt',
                    'room:master_stair', 'room:vestry', 'room:chapel_e', 'room:nave', 'room:narthex', 'room:porch'],
    'goals': [
        {'id': 'goal:megacredits', 'space': 'room:treasury', 'kind': 'take', 'story': 'M10',
         'what': "Take the King's Megacredits from the cult's treasury (five; a sixth on the Yak Master).",
         'handed_in_at': 'Newcastle (X3): Emerson builds the walls for five', 'gives': {'qbit': 'treasury_opened'}},
        {'id': 'goal:elixir', 'space': 'room:reliquary', 'kind': 'take', 'story': 'Q-C12',
         'what': "Take the Elixir of Restoration from the reliquary behind the sanctum's altar.",
         'handed_in_at': 'Mirabeth (X3)', 'gives': {'qbit': 'elixir_found'}},
        {'id': 'goal:yak_master', 'space': 'room:sanctum', 'kind': 'kill', 'what': "Kill the Yak Master: it opens the reliquary.",
         'gives': {'qbit': 'yak_master_slain'}},
    ],
    'keys': [
        {'id': 'key:bars', 'grants': {'all': [{'map_var': 'bar_w'}, {'map_var': 'bar_e'}]}, 'found_in': 'room:chapel_w',
         'how': "button: the west chapel's and the library's buttons each sink one bar of the treasury gate"},
        {'id': 'key:causeway', 'grants': {'map_var': 'causeway'}, 'found_in': 'room:near_bank',
         'how': "button: the three buttons in the kerb at the near bank's edge raise the causeway when set right"},
    ],
    'points_of_interest': [
        {'id': 'poi:yak_pool', 'space': 'room:near_bank', 'kind': 'pool',
         'behaviour': "'Yak Pool': drinking gives +2 Endurance (permanent) once per character and disease every time; wading into the pool diseases the party.",
         'uses': {'times': 1, 'per': 'character', 'reset': 'never'}},
        {'id': 'poi:beds', 'space': 'room:dormitory', 'count': 6, 'kind': 'bed',
         'behaviour': "'There is nothing on, in, or under the bed.' (the source's stock line)"},
        {'id': 'poi:coffins', 'spaces': ['room:crypt', 'room:lich_crypt'], 'count': 3, 'kind': 'coffin',
         'behaviour': "'There is nothing in the coffin.'; the heavy coffin (a chest) wants Might 25: 'You are not strong enough to open the coffin.'"},
        {'id': 'poi:crate', 'space': 'room:refectory', 'kind': 'crate', 'behaviour': "'There is nothing in the crate.'"},
    ],
    'landmarks': [
        {'id': 'landmark:idol', 'space': 'room:nave', 'what': "Yak's idol on its dais in a red glow, seen down the nave from the narthex's arch.",
         'seen_from': ['room:narthex', 'room:chapel_w', 'room:chapel_e']},
        {'id': 'landmark:pool', 'space': 'room:yak_pool', 'what': "The green, bubbling pool in its cave, the blocks under the surface, the far shore.",
         'seen_from': ['room:near_bank', 'room:far_bank']},
    ],
    'sightlines': [
        {'id': 'sight:gate', 'from': 'room:nave', 'to': ['room:treasury'], 'what': "The treasury gate and its two bars, west of the dais."},
        {'id': 'sight:causeway', 'from': 'room:near_bank', 'to': ['room:yak_pool', 'room:far_bank'],
         'what': "From the buttons the three blocks and the far landing: every button's effect is seen."},
    ],
    'set_pieces': [
        {'id': 'set:twin_bars', 'kind': 'puzzle', 'spaces': ['room:nave', 'room:chapel_w', 'room:library'],
         'rule': "Two iron bars stand before the treasury gate. The west chapel's button sinks the west bar, the library's button the east bar; each press says so ('Out in the nave, iron grinds on stone: the west bar ... sinks'). Clicked, the gate says which bar still stands and that the buttons are in a chapel and among the books.",
         'inputs': ['button, west chapel', 'button, library'], 'states': ['bars up', 'one bar sunk', 'both sunk: the gate lifts'],
         'solution': "Press both buttons (any order), then open the gate.", 'gives': {'qbit': 'treasury_opened'},
         'notes': "The source's switches that work in pairs to open a wall, as MM7's push buttons (d04's 7t1butt blocks) whose effect is seen and told."},
        {'id': 'set:causeway', 'kind': 'puzzle', 'spaces': ['room:near_bank', 'room:yak_pool'],
         'rule': "Three stone blocks lie in a line under the pool's surface. Button 1 (south) moves blocks 1 and 2, button 2 blocks 2 and 3, button 3 block 3: each press raises a sunk block and sinks a raised one, in plain view of the buttons. All three raised make a causeway to the far landing.",
         'inputs': ['button 1', 'button 2', 'button 3'], 'states': ['each block down or up (8 states)'],
         'solution': "Buttons 1 and 3 (pressing all three leaves only block 1 up). Found by watching the blocks; any state can be undone.",
         'gives': {'map_var': 'causeway'}},
        {'id': 'set:pool', 'kind': 'trap', 'spaces': ['room:yak_pool'],
         'rule': "The Yak Pool sickens: wading in diseases the whole party ('The pool makes you ill.'). The tell: green bubbling water, a green glow, a stench in the bank's first line, bones at the rim. Steps lead out on the near side.",
         'notes': "MM6-8 style pool: a condition with a visible tell."},
        {'id': 'set:master', 'kind': 'boss', 'spaces': ['room:sanctum'],
         'rule': "The Yak Master and two elders before the altar; the reliquary's slab rises when he dies.",
         'gives': {'qbit': 'yak_master_slain'}},
    ],
    'diagram': {'file': 'diagram.txt'},
}

L2_EXTRA = {
    'mechanisms': [
        {'kind': 'door', 'count': 8, 'notes': "Yak door, two narthex doors, the treasury gate, the Master's door (one-sided), the sanctum's double door, the reliquary slab, the Master's cell; plus one secret door."},
        {'kind': 'button', 'count': 5, 'notes': "Two for the treasury bars, three for the causeway."},
        {'kind': 'mover', 'count': 2, 'notes': "The treasury gate's bars (sink)."},
        {'kind': 'lift', 'count': 3, 'notes': "The causeway blocks."},
        {'kind': 'chest', 'count': 6, 'notes': "Treasury, heavy coffin, library, hidden cell, hoard, reliquary."},
    ],
    'height_bands': [
        {'id': 'band:temple', 'level': 0, 'spaces': ['room:porch', 'room:narthex', 'room:nave', 'room:chapel_w', 'room:chapel_e',
                                                     'room:passage_w', 'room:passage_e', 'room:dormitory', 'room:hidden_cell',
                                                     'room:refectory', 'room:library', 'room:vestry', 'room:treasury'],
         'partly': ['room:stair_w', 'room:master_stair']},
        {'id': 'band:undercroft', 'level': -768, 'spaces': ['room:crypt', 'room:ossuary', 'room:near_bank', 'room:far_bank',
                                                            'room:lich_crypt', 'room:sanctum_way', 'room:sanctum', 'room:reliquary',
                                                            'room:master_cell'],
         'partly': ['room:stair_w', 'room:master_stair']},
        {'id': 'band:pool', 'level': -928, 'spaces': ['room:yak_pool']},
    ],
    'atmosphere': ("Above: red torchlight (d04's red torches, torch07) along the walls, a red pulsing glow over Yak's "
                   "idol, ambient dark (about 22 of 31; the porch lighter with the woods' grey daylight). Below: fewer "
                   "torches and braziers in the crypts, the pool's sick green glow pulsing slowly over the water and the "
                   "basin, the sanctum dark green-black with a red glow over the altar and a cold light in the "
                   "reliquary. Sound: the map's stone-hall environment and MM7's track 28; the pool bubbles (the liquid "
                   "shader's own); no placed sounds."),
    'totals': {'sectors': 26, 'floor_area_millions': 48, 'doors': 9, 'chest_events': 6, 'spawn_points': 19,
               'fixed_actors': 4, 'loops': 3},
}

NOTES_L1 = ("Size M (MAPS.md: 20-45 sectors, 30-90 M units², 45-75 monsters; section 0: 50 monsters, levels 14-28, the "
            "Yak Master 35, groups 2-3, treasure level 2). About 26 spaces and 48 M units²: the temple above (13 "
            "spaces) and the undercroft 768 below (13). Monsters about 50: clerics in the temple, skeletons in the "
            "crypts and on the far bank, two lich groups, the Yak Master with two elders, an elder in the vestry. "
            "Original lines kept (aaze0079): 'Leave the Temple of Yak?', 'There is nothing on, in, or under the "
            "bed.', 'There is nothing in the crate.', 'There is nothing in the coffin.', 'You are not strong enough "
            "to open the coffin.', 'Yak Pool', 'The pool makes you ill.', 'King's Megacredit!', 'You have found the "
            "Elixir of Restoration!'. No riddles: both switch puzzles show and tell what each button did.")


def write(level, plan, project, extra_files=None):
    d = B / level
    d.mkdir(parents=True, exist_ok=True)
    (d / 'plan.yml').write_text(yaml.safe_dump(plan, sort_keys=False, allow_unicode=True, width=120))
    (d / 'project.yml').write_text(yaml.safe_dump(project, sort_keys=False, allow_unicode=True, width=120))
    for name, text in (extra_files or {}).items():
        (d / name).write_text(text)


DIAGRAM = """                         [Reliquary: ELIXIR]
                                 |  (slab: opens when the Yak Master dies)
     [Master's cell $]--[ SANCTUM: YAK MASTER + 2 elders, altar ]
                                 |
                          [Sanctum way]
                                 |
 [Ossuary]--[Near bank: 3 BUTTONS, basin]==(YAK POOL: 3 blocks, sickens)==[Far bank]--[Lich crypt]
     |                                                                                     |
 [Crypt $ coffins]                                                              [Master's stair, up]
     |                                                                                     |
 [West stair, down]                  [Treasury $ MEGACREDITS]                    (Master's door, opens
     |                                  |  =gate, 2 bars=                         from below only)
 [Refectory]--[West chapel: BUTTON W]--[ NAVE: pillars, Yak's idol ]--[East chapel]--[Vestry: elder]
     |                                  |                                               |
 [Dormitory]-#-[Hidden cell $]          |                                          [Library: BUTTON E $]
     |                              [Narthex]                                           |
 [West passage]-----------------------/    \\---------------------------------[East passage]
                                       [Porch] -> X2, the fairy woods' dark south end

 # secret door   $ chest   = barred gate   == drop into the pool / causeway when raised
 Loops: west wing, east wing, and the undercroft ring (down the west stair, up the Master's stair).
"""

project_xeen = {
    'format': 0, 'id': 'xeen_xd06', 'name': 'Temple of Yak', 'world': 'xeen', 'kind': 'indoor', 'profile': 'dungeon',
    'map_code': 'XD-06', 'units': {'plan_grid': 512}, 'extent': {'footprint_cells': [17, 29], 'climbs': 's'},
    'map_stats': {'id': 9139, 'encounter_chance': 10, 'treasure_level': 2, 'trap_dice': 2, 'perception_difficulty': 2,
                  'refill_days': 672, 'music': 'temple_dark', 'environment': 'stone hall', 'lock_difficulty': 2,
                  'slots': [{'monster': 'Cultists', 'tier': 2, 'per_marker': [2, 3], 'weight': 45},
                            {'monster': 'Skeletons', 'tier': 3, 'per_marker': [2, 3], 'weight': 45},
                            {'monster': 'Liches', 'tier': 1, 'per_marker': [1, 2], 'weight': 10}]},
    'neighbours': [{'id': 'door:x2_woods', 'to': 'X2', 'kind': 'door',
                    'arrival_hint': "In the fairy woods' dark south end on X2, in front of the Temple of Yak's door, facing away from it, north.",
                    'notes': "X2's door:xd06 (devdocs/xeen/briefs/x2/DOORS.md); its outside needs the Yak Stone (qbit 110101, Mirabeth's Q-C12)."}],
    'qbits': {'elixir_found': 110400, 'yak_master_slain': 110401, 'treasury_opened': 110402},
    'items': {'elixir': 12191, 'megacredit': 12192},
    'notes': ("Xeen design brief for a new map (no original). XD-06 Temple of Yak, class M, on X2 at the fairy woods' "
              "dark south end (moved from X1 on 2026-11-14): story step M10 and Q-C12. Encounter slots are Xeen "
              "families from MONSTERS_AND_ITEMS.md: 1 Cultists (Cleric of Yak 14 / Yak Priest 20 / Yak Elder 28), 2 "
              "Skeletons (16), 3 the source's Yak Liches; the Yak Master 35 as a boss row. Ids: map_stats 9139, qbits "
              "110400-110469, items 12190-12229 (the Elixir of Restoration 12191, the King's Megacredit 12192). The "
              "Yak Stone (12190 reserved) is X2's door condition, qbit 110101 there."),
}

if __name__ == '__main__':
    L1 = copy.deepcopy(plan_common)
    L1['level'] = 'L1'
    L1['notes'] = NOTES_L1
    for s in L1['spaces']:
        s.pop('features', None)
    write('L1', {'format': 0, 'level': 'L1', **{k: v for k, v in L1.items() if k not in ('format', 'level')}},
          project_xeen, {'diagram.txt': DIAGRAM})
    L2 = copy.deepcopy(plan_common)
    L2.update(copy.deepcopy(L2_EXTRA))
    L2['notes'] = NOTES_L1 + (" L2 adds the mechanisms, height bands, atmosphere and totals; positions are fixed in "
                              "L3's sketch (rooms.yml).")
    write('L2', {'format': 0, 'level': 'L2', **{k: v for k, v in L2.items() if k not in ('format', 'level')}},
          project_xeen, {'diagram.txt': DIAGRAM})
    L3 = copy.deepcopy(L2)
    L3['sketch'] = {'file': 'rooms.yml', 'grid': 64}
    L3['notes'] = L2['notes'].replace("positions are fixed in L3's sketch (rooms.yml).",
                                       "L3: the to-scale sketch is rooms.yml (the shell: rooms and openings, no objects).")
    write('L3', {'format': 0, 'level': 'L3', **{k: v for k, v in L3.items() if k not in ('format', 'level')}},
          project_xeen, {'diagram.txt': DIAGRAM})
    # L4 keeps L3's plan.
    (B / 'L4').mkdir(parents=True, exist_ok=True)
    (B / 'L4' / 'plan.yml').write_text(yaml.safe_dump({'format': 0, 'level': 'L3', **{k: v for k, v in L3.items() if k not in ('format', 'level')}},
                                                      sort_keys=False, allow_unicode=True, width=120))
    (B / 'L4' / 'diagram.txt').write_text(DIAGRAM)
    print('plans written')
