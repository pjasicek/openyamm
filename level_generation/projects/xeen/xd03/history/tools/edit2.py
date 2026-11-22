p='gen_rooms.py'; s=open(p).read()
def rep(a,b):
    global s
    assert a in s, a
    s=s.replace(a,b)
rep("""     theme='theme:geode', ambient=24, rough={'step': 160, 'depth': 48},""",
"""     theme='theme:geode', ambient=24, rough={'step': 160, 'depth': 48},
     walls=[{'wall': 3, 'panels': [{'at': 'centre', 'length': 288, 'bottom': 16, 'height': 288, 'surface': GEMWALL}]},
            {'wall': 6, 'panels': [{'at': 'centre', 'length': 352, 'bottom': 0, 'height': 320, 'surface': GEMWALL}]},
            {'wall': 4, 'panels': [{'at': 'centre', 'length': 224, 'bottom': 64, 'height': 224, 'surface': GEMWALL}]}],
     ceiling_surfaces=[{'steeper_than': 1.2, 'surface': GEODEWALL}],""")
rep("""     theme='theme:geode', ambient=22, rough={'step': 160, 'depth': 40},""",
"""     theme='theme:geode', ambient=24, rough={'step': 160, 'depth': 40},
     walls=[{'wall': 0, 'panels': [{'at': 'centre', 'length': 384, 'bottom': 0, 'height': 320, 'surface': GEMWALL}]}],""")
open(p,'w').write(s)
p='gen_objects.py'; s=open(p).read()
rep("CHEST_IRON = S('ch1frntb', 64, 64)","CHEST_IRON = S('ch1frntb', 64, 64)\nDARKIRON = S('vlcgnrc2', 256, 256)\nGEMDOOR = S('d3ystlwl', 256, 256, fit=True)")
rep("""'bottom': 112, 'height': 32, 'travel': [0, 0, 240], 'speed': 48, 'surface': IRON, 'top_surface': IRON,""","""'bottom': 112, 'height': 32, 'travel': [0, 0, 240], 'speed': 48, 'surface': DARKIRON, 'top_surface': DARKIRON,""")
rep("""'bottom': 240, 'height': 32, 'travel': [0, 0, 176], 'speed': 48, 'surface': IRON, 'top_surface': IRON,""","""'bottom': 240, 'height': 32, 'travel': [0, 0, 176], 'speed': 48, 'surface': DARKIRON, 'top_surface': DARKIRON,""")
rep("""'secret': True,
     'surface': CRYSTAL,""","""'secret': True,
     'surface': GEMDOOR,""")
rep("""    D('deco:line_lamp_1', 'room:deep_line', 'torch02', wall='north', along=0.4, height=176),
    D('deco:line_lamp_2', 'room:deep_line', 'torch02', wall='south', along=0.6, height=176),""","""    D('deco:line_lamp_1', 'room:deep_line', 'torch02', [7840, 1216], wall='north', height=150),
    D('deco:line_lamp_2', 'room:deep_line', 'torch02', [8000, 960], wall='south', height=150),""")
open(p,'w').write(s)
