import re
p='/home/pjasicek/github/OpenYAMM/output/studio_cal/mm8_d05/gen.py'
s=open(p).read()
def rep(a,b):
    global s
    assert a in s,(a[:70]); s=s.replace(a,b)
rep(""" {'id': 'theme:false_floor', 'wall': T('t65b02'), 'bands': [{'height': 128, 'surface': T('t65a02')}], 'floor': T('t65b03'), 'ceiling': T('t65a04'),
  'notes': "Sector 8, the hall of the false floor: t65b02 walls over a t65a02 base, t65a04 ceiling."},""",
""" {'id': 'theme:false_floor', 'wall': T('t65a02'), 'bands': [{'height': 640, 'surface': T('t65b02')}, {'height': 704, 'surface': T('t65o11a', (128, 64))}], 'floor': T('t65b03'), 'ceiling': T('t65a04'),
  'notes': "Sector 8, the hall of the false floor: t65b02 walls below the walkway's level, a t65o11a course 64 high at the level of the floor, t65a02 above it, t65a04 ceiling."},
 {'id': 'theme:stair', 'wall': T('t65b02'), 'floor': T('t65b14h2', (64, 128)), 'ceiling': T('t65b04'),
  'notes': "The stairs of sectors 6, 9, 10 and 19: treads t65b14h2 (t65b14h in 10 and 19), risers t65b14v."},
 {'id': 'theme:alcove', 'wall': T('t65b04'), 'floor': T('t65b03'), 'ceiling': T('t65b04'), 'notes': "The four button alcoves of sector 1: t65b04 on walls and ceiling."},""")
rep(""" {'id': 'theme:crusher', 'wall': T('t65b02'), 'floor': T('t65b02m'), 'ceiling': T('t65b02m'),""",""" {'id': 'theme:crusher', 'wall': T('t65b02'), 'bands': [{'height': 144, 'surface': T('t65a02')}, {'height': 208, 'surface': T('t65b11a', (128, 64))}], 'floor': T('t65c02'), 'ceiling': T('t65b02m'),""")
rep(""" {'id': 'theme:sanctum', 'wall': T('t65a01', (128, 256)), 'bands': [{'height': 128, 'surface': T('t65b02t')}], 'floor': T('t65c02'), 'ceiling': T('t65a04b'),""",""" {'id': 'theme:sanctum', 'wall': T('t65b02t'), 'bands': [{'height': 256, 'surface': T('t65a01', (128, 256))}], 'floor': T('t65c02'), 'ceiling': T('t65a04b'),""")
rep("t65a01 walls over a t65b02t base band","t65a01 panels 256 high with a t65b02t course above them")
for a in ("'stair6', 320, 1344, 2176, 2432, 160, 416, 'hall'","'stair9a', 512, 1472, 2560, 2816, -352, -96, 'hall'","'stair9b', 448, 832, 2176, 2432, -864, -608, 'hall'","'stair19a', 13952, 14208, 1152, 2176, -640, 128, 'hall'","'stair19b', 13568, 13824, 1152, 2176, -128, 640, 'hall'","-352, -96, 'hall', name='Slanting stair'"):
    rep(a,a.replace("'hall'","'stair'"))
s=re.sub(r"('steps': (16|6|8))\}", r"\1, 'riser': T('t65b14v', (128, 32))}", s)
rep("rect(nm, x0, x1, y0, y1, 0, 256, 'hall', name='Button alcove')","rect(nm, x0, x1, y0, y1, 0, 256, 'alcove', name='Button alcove')")
for o in ("R(-128, 256, -640, -384), 'floor': 160}","R(-512, -320, -640, -384), 'floor': 32}","R(448, 640, -640, -384), 'floor': 32}","R(-128, 256, 1280, 1408), 'floor': 160}"):
    rep(o,o[:-1]+", 'surface': T('t65b04'), 'edge': T('t65o02c')}")
a=s.index("PED = lambda x, y:"); b=s.index("# ---------------------------------------------------------------- sector 10")
new=open('/home/pjasicek/github/OpenYAMM/output/studio_cal/mm8_d05/hall8.txt').read()
s=s[:a]+new+s[b:]
a=s.index("ph('false_floor'"); b=s.index("ph('pit'")
s=s[:a]+'''ph('false_floor', 'hall8', [3264, 2304], "False floor: a floor of t65b03 right across the hall at -352, level with the walkway and not solid (the original's faces are flagged untouchable), with its underside (t65b04) seen from below; events 451 and 452 count the falls and after the third mark the walkway's faces.", [2048, 1920, 16], "No floor that is seen and not solid; no event run by stepping on a floor.")\n'''+s[b:]
rep("384, 768, 'pyramid', name='Back door chamber'","384, 640, 'pyramid', name='Back door chamber'")
rep("""     -640, 64, 'tunnel', name='Lake cave',""","""     -640, -200, 'tunnel', name='Lake cave',
     ceiling_levels=[{'outline': [[10000, -4600], [10500, -4850], [11400, -4850], [11900, -4600], [11900, -3980], [11400, -3730], [10500, -3730], [10000, -3980]], 'ceiling': 160}],""")
rep("flat here at an average height","two flat heights here: -200 round the rim, 160 over the middle")
open(p,'w').write(s)
