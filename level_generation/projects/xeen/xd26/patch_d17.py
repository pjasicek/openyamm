"""One-off: rework gen.py to D-17 (ladder from the shaft floor; the fence's hoist). Run once on gen_before_d17.py."""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
src=_REPO_ROOT + '/level_generation/projects/xeen/xd26/gen_before_d17.py'
dst=_REPO_ROOT + '/level_generation/projects/xeen/xd26/gen.py'
s=open(src).read()
def rep(a,b):
    global s
    assert a in s, a[:90]
    s=s.replace(a,b,1)
rep("WELL = (3200, 1792, 3456, 2048)","HOIST = (2624, 2176, 3008, 2560)   # the hoist's foot under the high ledge's east end\nHX, HY = 2816, 2368                 # the hoist deck's middle (the notch in the high ledge)\nHOIST_DECK = S('gkp1ceil', 128, 128)")
rep("""     flights=[{'from': [832, 448], 'to': [0, 448], 'to_height': 512, 'width': 256, 'steps': 16, 'riser': ROCK,
               'tread': ROCKFLR, 'notes': "Sixteen rough steps cut up the west side to the first ledge."}],
""","")
rep("Sixteen rough steps climb its west side to the first ledge.\")","A pole ladder climbs its west wall to the first ledge.\")")
rep("the fence's door and the ladder cleft in its east wall.","the fence's door in its east wall, the way to the hoist's foot in its north wall.")
rep("""room('room:ladder_cleft', 'Ladder cleft', outline=rect(*WELL), floor=1024, ceiling=1856, theme='theme:rock',
     ambient=20,
     notes="A narrow cleft behind a plank shutter, 256 square: the fence's rope ladder up to the high ledge.")""",
"""room('room:hoist_foot', 'Hoist foot', outline=rect(*HOIST), floor=1024, ceiling=1504, theme='theme:rock',
     ambient=20,
     platforms=[{'at': [x, HY], 'size': [8, 8], 'rise': 480, 'surface': POLE, 'top_surface': POLE,
                 'notes': "A hoist rope beside the deck's way."} for x in (HX - 136, HX + 136)],
     notes="A low cave under the high ledge's east end, 384 square, off the east nests: the fence's hoist comes down here through a notch in the ledge above.")""")
rep("room('room:high_ledge', 'High ledge', outline=rect(-1024, 2176, 3456, 2560)","room('room:high_ledge', 'High ledge', outline=rect(-1024, 2176, 3072, 2560)")
rep("""     notes="A narrow shelf 384 wide along the shaft's north side, 4,480 long: open to the shaft in the middle, a gap over the west ledge (a 512 drop), the ladder cleft's top at its east end;""",
"""     platforms=[{'at': [x, HY], 'size': [8, 8], 'rise': 736, 'surface': POLE, 'top_surface': POLE,
                 'notes': "A hoist rope up to the beam."} for x in (HX - 136, HX + 136)],
     beams=[{'path': [[2560, HY], [3072, HY]], 'width': 32, 'depth': 32, 'bottom': 2272, 'surface': POLE,
             'notes': "The hoist beam over the notch, wedged into the east wall."}],
     notes="A narrow shelf 384 wide along the shaft's north side, 4,096 long: open to the shaft in the middle, a gap over the west ledge (a 512 drop), the fence's hoist in a notch at its east end under a hoist beam;""")
rep("""op('open:ledgee_cleft', 'room:ledge_e', 'room:ladder_cleft', link='link:ledgee_high', width=192, height=320,
   notes="The plank shutter over the ladder cleft (door:winch_ladder).")
op('open:cleft_high', 'room:ladder_cleft', 'room:high_ledge', link='link:ledgee_high', width=160, height=256,
   notes="The cleft's top, 512 up: out on to the high ledge.")""",
"""op('open:ledgee_hoist', 'room:ledge_e', 'room:hoist_foot', link='link:ledgee_hoist', width=256, height=320,
   notes="Into the hoist's foot under the high ledge.")
op('open:hoist_notch', 'room:high_ledge', 'room:hoist_foot', link='link:hoist_high', at=[HX, HY], size=[256, 256],
   notes="The notch in the high ledge the hoist's deck rides through.", **{'in': 'floor'})""")
rep("'room:ladder_cleft': 1024,","'room:hoist_foot': 1024,")
rep("""    ('room:ledge_e', 'East nests', 'room', 'M', "Nests of sticks and bones; the fence's door; the shuttered ladder cleft.", ('b', 3)),
    ('room:fence_cache', "The fence's cache", 'room', 'S', "Crates tagged for buyers; the winch that lowers the ladder.", ('c', 1)),
    ('room:ladder_cleft', 'Ladder cleft', 'corridor', 'S', "The fence's rope ladder up to the high ledge, behind a shutter the winch raises.", None),""",
"""    ('room:ledge_e', 'East nests', 'room', 'M', "Nests of sticks and bones; the fence's door; the way to the hoist's foot.", ('b', 3)),
    ('room:fence_cache', "The fence's cache", 'room', 'S', "Crates tagged for buyers; the winch that lowers the hoist.", ('c', 1)),
    ('room:hoist_foot', 'Hoist foot', 'corridor', 'S', "Where the fence's hoist comes down from the high ledge once the winch has lowered it.", None),""")
rep("""        {'id': 'link:shaft_ledgelow', 'from': 'room:shaft_floor', 'to': 'room:ledge_low', 'kind': 'stairs',
         'notes': "Steps cut up the shaft's west side (the graph's ladder; provisional, D-17)."},""",
"""        {'id': 'link:shaft_ledgelow', 'from': 'room:shaft_floor', 'to': 'room:ledge_low', 'kind': 'ladder',
         'notes': "A pole ladder up the shaft's west wall under the first ledge's lip (D-17)."},""")
rep("""        {'id': 'link:ledgee_high', 'from': 'room:ledge_e', 'to': 'room:high_ledge', 'kind': 'ladder',
         'condition': {'map_var': 'winch_down'},
         'notes': "Through the ladder cleft: its plank shutter rises when the fence's winch is turned (provisional, D-17)."},""",
"""        {'id': 'link:ledgee_hoist', 'from': 'room:ledge_e', 'to': 'room:hoist_foot', 'kind': 'open'},
        {'id': 'link:hoist_high', 'from': 'room:hoist_foot', 'to': 'room:high_ledge', 'kind': 'lift',
         'condition': {'qbit': 'hoist_winched'},
         'notes': "hoist: winch. The fence's hoist (D-17): it hangs at the high ledge until the winch in the fence's cache lowers it; then its deck or a call rope at either stop sends it."},""")
rep("'room:ledge_e', 'room:ladder_cleft', 'room:high_ledge',","'room:ledge_e', 'room:hoist_foot', 'room:high_ledge',")
rep("""        'keys': [{'id': 'key:winch', 'grants': {'map_var': 'winch_down'}, 'found_in': 'room:fence_cache',
                  'how': "The fence's winch raises the shutter of the ladder cleft."}],""",
"""        'keys': [{'id': 'key:winch', 'grants': {'qbit': 'hoist_winched'}, 'found_in': 'room:fence_cache',
                  'how': "The fence's winch lowers his hoist from the high ledge."}],""")
rep("""            {'id': 'set:winch', 'kind': 'scripted', 'spaces': ['room:fence_cache', 'room:ladder_cleft'],
             'rule': "The winch raises the cleft's shutter; the ladder behind it climbs to the high ledge."},""",
"""            {'id': 'set:winch', 'kind': 'scripted', 'spaces': ['room:fence_cache', 'room:hoist_foot', 'room:high_ledge'],
             'rule': "The winch lowers the fence's hoist the first time; then the deck or a call rope at either stop sends it up or down."},""")
rep("Provisional pending D-17: the shaft floor to the first ledge is a stair (not a ladder: solve and audit do not climb ladders), and the drawn-up ladder is a plank shutter over a ladder cleft (a door leaf the winch opens; at the ladder's top it would not stop the climb, NOTES). The bridge is a zone of the shaft (a platform), the rock ramp and the ladder cleft their own rooms (13).",
    "D-17: the graph's ladder from the shaft floor to the first ledge; the fence's winch drives a two-state hoist (XD-11's lift) between the east nests' hoist foot (1024) and the high ledge (1536). The bridge is a zone of the shaft (a platform), the rock ramp and the hoist's foot their own rooms (13).")
rep("'pitch': \"A cave mouth high on the Gargoyle Range opens into one tall shaft. Ledges climb its walls, joined by steps, ladders and a rope bridge 1,024 over the floor, and the gargoyles dive across the open air at whoever climbs. A fence who hires them to steal keeps his crates on the east side; his winch opens the cleft with the ladder to the high ledge.",
    "'pitch': \"A cave mouth high on the Gargoyle Range opens into one tall shaft. Ledges climb its walls, joined by ladders and a rope bridge 1,024 over the floor, and the gargoyles dive across the open air at whoever climbs. A fence who hires them to steal keeps his crates on the east side; his winch lowers the hoist from the high ledge.")
# diagram
rep("""  1536   moss=[====== HIGH LEDGE (along the shaft's north side) ======]--[cleft top]
                gap (drop 512)        |  lip                               | ladder
  1024   [ledge_w] ===== rope bridge (torn rail: fall) ===== [east nests] =door= [fence's cache: winch]
            |  ^ramp                                             '=shutter= [ladder cleft]
   512   [ledge_low]--[low nests]                                (winch raises the shutter)
            ^ steps""",
"""  1536   moss=[====== HIGH LEDGE (along the shaft's north side) ======][notch]
                gap (drop 512)        |  lip                           | hoist (the winch lowers it first)
  1024   [ledge_w] ===== rope bridge (torn rail: fall) ===== [east nests]-[hoist foot]
            |  ^ramp                                             =door= [fence's cache: winch]
   512   [ledge_low]--[low nests]
            ^ ladder""")
# objects
i=s.index("    {'id': 'door:winch_ladder'"); j=s.index("    {'id': 'door:moss'")
s=s[:i]+s[j:]
rep("    light('light:cleft', 'room:ladder_cleft', [3328, 1920], 1500, 500, [150, 150, 170]),",
    "    light('light:hoist', 'room:hoist_foot', [2700, 2250], 1400, 500, [150, 150, 170]),")
rep("objects['ladders'] = [\n","""objects['ladders'] = [
    {'id': 'ladder:ledge_low', 'room': 'room:shaft_floor', 'at': [4, 448], 'facing': 'w', 'height': 512,
     'exit': [-192, 448], 'grab_at_top': True, 'surface': RUNGS,
     'notes': "A pole ladder up the shaft's west wall to the first ledge's lip (the graph's ladder, D-17)."},
""")
i=s.index("    {'id': 'ladder:winch'"); j=s.index("    {'id': 'ladder:roost'")
s=s[:i]+s[j:]
rep("'exit': [-576, 1110], 'surface': RUNGS,","'exit': [-576, 1110], 'grab_at_top': True, 'surface': RUNGS,")
rep("'exit': [1280, 2780], 'surface': RUNGS,","'exit': [1280, 2780], 'grab_at_top': True, 'surface': RUNGS,")
rep("""     'notes': "The fence's winch: its crank on the north wall, the rope running through the rock to the cleft."},""",
"""     'notes': "The fence's winch: its crank on the north wall, the rope running through the rock to the hoist."},
    {'id': 'switch:hoist_bottom', 'room': 'room:hoist_foot', 'kind': 'button', 'at': [2624, 2290], 'height': 112,
     'notes': "The hoist's call rope at its foot, on the west wall beside the deck."},
    {'id': 'switch:hoist_top', 'room': 'room:high_ledge', 'kind': 'button', 'at': [3072, 2260], 'height': 112,
     'notes': "The hoist's call rope at the high ledge, on the east wall beside the notch."},""")
rep("objects['decorations'] = [","""objects['lifts'] = [
    {'id': 'lift:hoist', 'room': 'room:hoist_foot', 'at': [HX, HY], 'size': [256, 256], 'travel': 480,
     'thickness': 32, 'speed': 128, 'state': 'up', 'surface': HOIST_DECK,
     'notes': "The fence's hoist: a plank deck on ropes under the hoist beam. It starts at the upper stop, flush with the high ledge in its notch; the winch lowers it the first time, then its deck or a call rope at either stop sends it."},
]
objects['decorations'] = [""")
# wiring
i=s.index("    {'id': 'evt:winch', 'preset': 'switch'"); j=s.index("    {'id': 'evt:moss'")
s=s[:i]+'''    {'id': 'evt:winch', 'preset': 'switch', 'source': 'switch:winch', 'title': 'Winch',
     'condition': {'not': {'qbit': 'hoist_winched'}}, 'closes': ['lift:hoist'], 'sets': {'qbit': 'hoist_winched'},
     'effects': [{'message': "You crank the winch. A rope runs out through a hole in the rock, and beyond the wall a plank platform comes creaking down on its ropes from the high ledge."}],
     'else_effects': [{'message': "The winch is wound out; the hoist answers its deck and its call ropes now."}],
     'notes': "link:hoist_high (hoist: winch): lowers the hoist the first time and sets hoist_winched."},
    {'id': 'evt:hoist', 'preset': 'switch', 'source': 'lift:hoist', 'title': 'Hoist',
     'condition': {'qbit': 'hoist_winched'}, 'toggles': ['lift:hoist'],
     'effects': [{'message': "The platform creaks on its ropes and moves."}],
     'else_effects': [{'message': "The platform hangs on its ropes at the ledge above. Its winch must be in the cave beside you."}]},
    {'id': 'evt:hoist_bottom', 'preset': 'switch', 'source': 'switch:hoist_bottom', 'title': 'Call rope',
     'condition': {'qbit': 'hoist_winched'}, 'toggles': ['lift:hoist'],
     'effects': [{'message': "You pull the rope; the platform creaks on its ropes and moves."}],
     'else_effects': [{'message': "The platform hangs on its ropes at the ledge above. Its winch must be in the cave beside you."}]},
    {'id': 'evt:hoist_top', 'preset': 'switch', 'source': 'switch:hoist_top', 'title': 'Call rope',
     'condition': {'qbit': 'hoist_winched'}, 'toggles': ['lift:hoist'],
     'effects': [{'message': "You pull the rope; the platform creaks on its ropes and moves."}],
     'else_effects': [{'message': "The rope will not run: the hoist's winch in the fence's cave below is still locked."}]},
'''+s[j:]
rep("wiring = {'format': 0, 'variables': ['winch_down'], 'events': events}","wiring = {'format': 0, 'events': events}")
rep("QBITS = {'scarab_found': 112202}","QBITS = {'hoist_winched': 110880, 'scarab_found': 112202}")
rep("Map qbits 110880-110919 (none used: the winch is a map variable)","Map qbits 110880-110919 (used: hoist_winched 110880)")
open(dst,'w').write(s)
print('ok')
