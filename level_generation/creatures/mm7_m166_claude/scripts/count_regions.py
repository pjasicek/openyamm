"""Face counts per Meshy piece class in a blend. Args: blend."""
import bpy, os, sys
import numpy as np
P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(P, sys.argv[sys.argv.index('--') + 1]))
me = bpy.data.objects['Beholder'].data
if 'piece' in me.attributes:
    pc = np.array([d.value for d in me.attributes['piece'].data])
else:
    pc = np.load(os.path.join(P, 'work/piece_master.npy'))
cls = {}
for p in me.polygons:
    k = int(pc[p.vertices[0]]); c = 'head' if k == 0 else 'tent' if k in (1, 2, 3, 4, 5, 6, 9, 10, 14) else 'stalk' if k in (7, 8, 12, 13) else 'tongue' if k == 11 else 'teeth'
    cls[c] = cls.get(c, 0) + len(p.vertices) - 2
print('COUNT', cls, sum(cls.values()))
