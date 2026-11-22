"""Open edges of the v2 foot per part and culled views (back faces hidden): -- <blend> <object> <prefix>"""
import bpy, bmesh, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C
import numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', a[0]))
ob = bpy.data.objects[a[1]]
names = {g.index: g.name for g in ob.vertex_groups}
bm = bmesh.new(); bm.from_mesh(ob.data); bm.verts.ensure_lookup_table()
dl = bm.verts.layers.deform.active
cnt = {}
for e in bm.edges:
    if len(e.link_faces) == 1:
        v = e.verts[0]; g = names[max(v[dl].items(), key=lambda x: x[1])[0]]
        cnt[g] = cnt.get(g, 0) + 1
print('OPEN edges by group', cnt)
co = np.array([ob.matrix_world @ v.co for v in ob.data.vertices]); c = (co.min(0) + co.max(0)) / 2
s = float(np.ptp(co, 0).max()) * 1.15
bpy.context.scene.display.shading.show_backface_culling = True
_setup = C.setup
def setup(textured=False, bones=False):
    _setup(textured, bones); bpy.context.scene.display.shading.show_backface_culling = True
C.setup = setup
V = {'front': (0, -3, 0), 'side': (3, 0, 0), 'top': (0, 0.001, 3), 'quarter': (2, -2.4, 1.4), 'under': (0, 0.001, -3),
     'oside': (-3, 0, 0)}
for k, off in V.items():
    C.render(tuple(c + off), tuple(c), s, os.path.join(HERE, 'review', f'{a[2]}_{k}.png'), res=(520, 420), floor=False,
             extra=(ob.name,))
print('VIEWS', a[2])
