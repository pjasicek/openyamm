def edit(p, pairs):
    s=open(p).read()
    for a,b in pairs:
        assert a in s, a
        s=s.replace(a,b)
    open(p,'w').write(s)
edit('gen_rooms.py', [
 ("{'id': 'theme:geode', 'wall': GEODEWALL,", "{'id': 'theme:geode', 'wall': EARTHROCK,"),
 ("{'outline': r1, 'ceiling': 704, 'top_outline': r2, 'edge': CRACKED}", "{'outline': r1, 'ceiling': 704, 'top_outline': r2, 'edge': DEEP}"),
 ("ceiling_surfaces=[{'steeper_than': 1.2, 'surface': GEODEWALL}],", "ceiling_surfaces=[{'steeper_than': 1.2, 'surface': EARTHROCK}],"),
])
edit('gen_objects.py', [
 ("DARKIRON = S('vlcgnrc2', 256, 256)", "DARKIRON = S('swpipes', 256, 256)"),
 ("""    D('deco:line_lamp_1', 'room:deep_line', 'torch02', [7840, 1216], wall='north', height=150),
    D('deco:line_lamp_2', 'room:deep_line', 'torch02', [8000, 960], wall='south', height=150),""",
  """    D('deco:line_lamp_1', 'room:deep_line', 'torch01', [7800, 1216], height=150),
    D('deco:line_lamp_2', 'room:deep_line', 'torch01', [8260, 960], height=150),"""),
])
