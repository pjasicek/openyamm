def edit(p, pairs):
    s=open(p).read()
    for a,b in pairs:
        assert a in s, a
        s=s.replace(a,b)
    open(p,'w').write(s)
edit('gen_rooms.py', [
 ("gong_slabs.append({'at': [gong_x, gong_y], 'size': [w, 12], 'base': b + 32, 'rise': 32,",
  "gong_slabs.append({'at': [gong_x, gong_y], 'size': [w, 12], 'base': b + 32 + 384, 'rise': 32,"),
 ("{'at': [gong_x, gong_y], 'size': [320, 96], 'rise': 32, 'surface': BIGBLOCK,",
  "{'at': [gong_x, gong_y], 'size': [320, 96], 'base': 384, 'rise': 32, 'surface': BIGBLOCK,"),
 ("{'at': [gong_x - 136, gong_y], 'size': [24, 24], 'base': 32, 'rise': 320,",
  "{'at': [gong_x - 136, gong_y], 'size': [24, 24], 'base': 416, 'rise': 320,"),
 ("{'at': [gong_x + 136, gong_y], 'size': [24, 24], 'base': 32, 'rise': 320,",
  "{'at': [gong_x + 136, gong_y], 'size': [24, 24], 'base': 416, 'rise': 320,"),
 ("{'at': [3200, 6208], 'size': [448, 224], 'rise': 32,", "{'at': [3200, 6208], 'size': [448, 224], 'base': 192, 'rise': 32,"),
 ("'top_size': [208, 112], 'base': 32,", "'top_size': [208, 112], 'base': 224,"),
 ("{'at': [3200, 6304], 'size': [256, 32], 'base': 32, 'rise': 176,", "{'at': [3200, 6304], 'size': [256, 32], 'base': 224, 'rise': 176,"),
 ("{'at': [3200, 6304], 'size': [224, 40], 'base': 208, 'rise': 192,", "{'at': [3200, 6304], 'size': [224, 40], 'base': 400, 'rise': 192,"),
 ("{'at': [2944, 6200], 'size': [96, 96], 'rise': 48,", "{'at': [2944, 6200], 'size': [96, 96], 'base': 192, 'rise': 48,"),
 ("{'at': [3456, 6200], 'size': [96, 96], 'rise': 48,", "{'at': [3456, 6200], 'size': [96, 96], 'base': 192, 'rise': 48,"),
])
