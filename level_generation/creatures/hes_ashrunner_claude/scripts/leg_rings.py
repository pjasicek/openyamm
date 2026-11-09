"""hgd: knees and ankles from the leg piece's own cross-sections (after arm_rings.py; edits work/joints_final.json).
Meshy's knees sat ~9 cm in front of the leg, drawn by the separate knee plates. The legs piece (P00, plates excluded)
is sliced horizontally; per side the loop on that side gives a ring centre. KNEE = the ring centre at Meshy's knee
height, ANKLE = the ring centre at Meshy's ankle height (x, y only; heights kept). Args: -- <step1 blend>"""
import bpy, bmesh, sys, os, json
import numpy as np
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(sys.argv[sys.argv.index('--') + 1]))
ob = bpy.data.objects['Body']
pv = np.zeros(len(ob.data.vertices), np.int32); ob.data.attributes['piece'].data.foreach_get('value', pv)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cfg
# har: the knee ring from the trousers (P07, inside the boot tops), the ankle ring from the boots (P05/P06)
LEGP = cfg.C.get('leg_ring_pieces', {'Calf': [0], 'Foot': [0]})


def piece_mesh(keep):
    b = bmesh.new(); b.from_mesh(ob.data); b.verts.ensure_lookup_table()
    bmesh.ops.delete(b, geom=[v for v in b.verts if pv[v.index] not in keep], context='VERTS')
    return b


BMS = {j: piece_mesh(set(LEGP[j])) for j in ('Calf', 'Foot')}
p = os.path.join(HERE, 'work', 'joints_final.json'); d = json.load(open(p)); J = d['joints']


def loops(z, joint):
    bm = BMS[joint].copy()
    res = bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=Vector((0, 0, z)),
                                 plane_no=Vector((0, 0, 1)))
    es = [e for e in res['geom_cut'] if isinstance(e, bmesh.types.BMEdge)]
    adj = {}
    for e in es:
        a, b = e.verts; adj.setdefault(a, []).append(b); adj.setdefault(b, []).append(a)
    seen, out = set(), []
    for v in adj:
        if v in seen:
            continue
        comp, st = [], [v]
        while st:
            x = st.pop()
            if x in seen:
                continue
            seen.add(x); comp.append(x); st += adj[x]
        if len(comp) >= 6:
            out.append(np.array([tuple(x.co) for x in comp]))
    bm.free()
    return out


for s, sign in (('R', -1), ('L', 1)):
    for joint in ('Calf', 'Foot'):
        k = f'{s}_{joint}'; z = J[k][2]
        ls = [l for l in loops(z, joint) if np.sign(l[:, 0].mean()) == sign]
        if not ls:
            print('LEGRING', k, 'no loop at', z); continue
        l = max(ls, key=len)
        c = (l.min(0) + l.max(0)) / 2
        old = list(J[k]); J[k] = [round(float(c[0]), 5), round(float(c[1]), 5), J[k][2]]
        print('LEGRING', k, 'moved cm', round(float(np.linalg.norm(np.array(J[k]) - np.array(old))) * 100, 1),
              'ring depth cm', round(float(l[:, 1].max() - l[:, 1].min()) * 100, 1), 'new', J[k])
d.setdefault('report', {})['leg_rings'] = True
json.dump(d, open(p, 'w'), indent=1)
