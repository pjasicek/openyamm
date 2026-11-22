p='gen_rooms.py'; s=open(p).read()
def rep(a,b):
    global s
    assert a in s, a
    s=s.replace(a,b)
rep("WEB = S('web32n735s', 128, 128)", "WEB = S('web32n735s', 128, 128)\nGEODEWALL = S('gcav2wal', 128, 256)\nCRACKED = S('hvceila', 128, 128)\nGEMWALL = S('d3ystlwl', 256, 256, fit=True)\nDARKFLAGS2 = S('d2flor5', 128, 128)\nDARKIRON = S('vlcgnrc2', 256, 256)")
rep("'bands': [{'height': 160, 'surface': BIGBLOCK}, {'height': 576, 'surface': SOOTBRICK}],",
    "'bands': [{'height': 128, 'surface': BIGBLOCK}, {'height': 448, 'surface': SOOTBRICK}],")
rep("""     'bands': [{'height': 96, 'surface': BIGBLOCK}, {'height': 576, 'surface': DRESSED},
               {'height': 640, 'surface': RUNEFRIEZE}],""",
    """     'bands': [{'height': 96, 'surface': BIGBLOCK}, {'height': 576, 'surface': DRESSED},
               {'height': 704, 'surface': S('runeeyvlij', 64, 64, scale=2)}],""")
rep("     'floor': INLAY, 'ceiling': ROCKCEIL, 'reveal': RUNES, 'door': S('d2lgdor', 256, 256, fit=True),\n     'notes': \"The Clan King's hall",
    "     'floor': DARKFLAGS2, 'ceiling': ROCKCEIL, 'reveal': RUNES, 'door': S('d2lgdor', 256, 256, fit=True),\n     'notes': \"The Clan King's hall")
rep("{'id': 'theme:geode', 'wall': CRYSTAL, 'floor': CRYSTALFLOOR, 'ceiling': CRYSTAL, 'reveal': DEEP,",
    "{'id': 'theme:geode', 'wall': GEODEWALL, 'floor': CRYSTALFLOOR, 'ceiling': CRACKED, 'reveal': DEEP,")
for e in ["{'outline': r1, 'ceiling': 704, 'top_outline': r2, 'edge': CRYSTAL}","{'outline': r2, 'ceiling': 928, 'top_outline': r3, 'edge': CRYSTAL}","{'outline': r3, 'ceiling': 1088, 'top_outline': r4, 'edge': CRYSTAL}","{'outline': r4, 'ceiling': 1152, 'top_scale': 0, 'edge': CRYSTAL}"]:
    rep(e, e.replace('CRYSTAL','CRACKED'))
rep("""         {'at': [3200, 6304], 'size': [256, 32], 'base': 32, 'rise': 352, 'surface': SKULL, 'end_surface': BIGBLOCK,
          'top_surface': BIGBLOCK, 'notes': "The throne's back: a slab carved with a skull."},""",
"""         {'at': [3200, 6304], 'size': [256, 32], 'base': 32, 'rise': 176, 'surface': BIGBLOCK,
          'top_surface': BIGBLOCK, 'notes': "The throne's back."},
         {'at': [3200, 6304], 'size': [224, 40], 'base': 208, 'rise': 192, 'surface': SKULL, 'end_surface': BIGBLOCK,
          'top_surface': BIGBLOCK, 'notes': "The throne's crest: a skull carved in the stone."},""")
rep("""         {'id': 'platform:furnace_mouth', 'at': [4224, 2160], 'size': [176, 16], 'base': 16, 'rise': 176,
          'surface': GLOW, 'end_surface': BIGBLOCK,
          'notes': "The smelter's cold furnace mouth on its north face, still glowing."},
         {'at': [4224, 2172], 'size': [240, 24], 'rise': 16, 'surface': IRON, 'top_surface': IRON,
          'notes': "The mouth's iron sill"},
         {'at': [4224, 2172], 'size': [240, 24], 'base': 192, 'rise': 32, 'surface': IRON, 'top_surface': IRON,
          'notes': "The mouth's iron lintel"},""",
"""         {'outline': octo(4224, 2048, 320, 132), 'rise': 192, 'surface': BIGBLOCK, 'top_surface': BIGBLOCK,
          'notes': "The smelter's furnace: a stone base round the stack."},
         {'id': 'platform:furnace_mouth', 'at': [4224, 2376], 'size': [176, 16], 'base': 16, 'rise': 144,
          'surface': GLOW, 'end_surface': BIGBLOCK,
          'notes': "The smelter's cold furnace mouth on its north face, still glowing."},
         {'at': [4224, 2388], 'size': [240, 24], 'base': 160, 'rise': 24, 'surface': DARKIRON,
          'top_surface': DARKIRON, 'notes': "The mouth's iron lintel"},""")
rep("""     parapets=[{'path': [[4900, 2444], [4716, 2444], [4716, 3764]], 'height': 80,""","""     parapets=[{'path': [[4900, 2444], [4716, 2444], [4716, 3764]], 'height': 64,""")
rep("""     beams=[{'path': [[gong_x - 160, gong_y], [gong_x + 160, gong_y]], 'width': 24, 'depth': 24, 'bottom': -128 + 352,
             'surface': BEAM, 'notes': "Gong frame beam"}],""",
"""     beams=[{'path': [[gong_x - 160, gong_y], [gong_x + 160, gong_y]], 'width': 24, 'depth': 24, 'bottom': -128 + 352,
             'surface': BEAM, 'notes': "Gong frame beam"}] +
           [{'path': [[x, 1536], [x, 3776]], 'width': 48, 'depth': 48, 'bottom': 160, 'surface': BEAM,
             'notes': "Soot-black roof timber"} for x in (3008, 3584)],""")
for a,b in [("theme='theme:deep_rock', ambient=20,\n     platforms=[\n         {'rise': 4, 'outline': rect(7744","theme='theme:deep_rock', ambient=22,\n     platforms=[\n         {'rise': 4, 'outline': rect(7744"),
            ("floor=0, ceiling=640, theme='theme:deep_rock', ambient=18,","floor=0, ceiling=640, theme='theme:deep_rock', ambient=22,"),
            ("floor=-512, ceiling=320, theme='theme:forge', ambient=14,","floor=-512, ceiling=320, theme='theme:forge', ambient=22,"),
            ("theme='theme:king_hall', ambient=14,","theme='theme:king_hall', ambient=21,"),
            ("theme='theme:geode', ambient=22, rough={'step': 160, 'depth': 48},","theme='theme:geode', ambient=24, rough={'step': 160, 'depth': 48},"),
            ("width=256, floor=0, ceiling=384, theme='theme:deep_rock', ambient=20,","width=256, floor=0, ceiling=384, theme='theme:deep_rock', ambient=24,"),
           ]:
    rep(a,b)
s=s.replace("'surface': CRYSTAL, 'notes': 'Crystal column'","'surface': CRACKED, 'notes': 'Crystal column'")
open(p,'w').write(s)
