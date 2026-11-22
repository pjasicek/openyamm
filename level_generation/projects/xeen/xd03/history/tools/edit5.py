def edit(p, pairs):
    s=open(p).read()
    for a,b in pairs:
        assert a in s, a
        s=s.replace(a,b)
    open(p,'w').write(s)
edit('gen_rooms.py', [
 ("""     width=256, floor=0, ceiling=384, theme='theme:deep_rock', ambient=24,""",
  """     width=256, floor=0, ceiling=384, theme='theme:deep_rock', ambient=24,
     platforms=[{'at': p, 'size': [24, 24], 'rise': 340, 'surface': POST, 'top_surface': POST, 'notes': 'Timber set post'}
                for p in ([6420, 1820], [6636, 1820], [6420, 2060], [6636, 2060])] +
               [{'at': p, 'size': [24, 24], 'rise': 330, 'surface': POST, 'top_surface': POST, 'notes': 'Timber set post'}
                for p in ([5600, 2644], [5600, 2860])],
     beams=[{'path': [[6408, y], [6648, y]], 'width': 32, 'depth': 28, 'bottom': 340, 'surface': BEAM,
             'notes': 'Cap of a timber set'} for y in (1820, 2060)] +
           [{'path': [[5600, 2632], [5600, 2872]], 'width': 32, 'depth': 24, 'bottom': 240, 'surface': BEAM,
             'notes': 'Cap of a timber set'}],"""),
])
