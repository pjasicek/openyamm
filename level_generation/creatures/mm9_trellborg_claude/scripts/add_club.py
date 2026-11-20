"""Club on the rigged reduced body, rigid on Yclub. Hole of the right fist from hole.py's search (scripts/grip.json: centre, kn). The club is MM9's turned by RD (MM9's axis onto the knuckle line, the least turn), Yclub moves to the grip. Writes work/grip.json. Args: <in blend> <out blend>"""
import bpy, bmesh, sys, json
import numpy as np
from mathutils import Vector, Matrix, Quaternion
IN, OUT = sys.argv[sys.argv.index('--') + 1:]
Z = np.load('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm9_trellborg_claude/work/club.npz'); G0 = json.load(open('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm9_trellborg_claude/scripts/grip.json'))
bpy.ops.wm.open_mainfile(filepath=IN)
body = bpy.data.objects['Body']; rig = body.parent; me = body.data
U0 = np.array([-0.226, -0.952, 0.205]); U1 = np.array([-0.696, 0.305, 0.651]); U2 = np.array([0.682, -0.004, 0.731])
U0 /= np.linalg.norm(U0); U1 -= U0 * (U1 @ U0); U1 /= np.linalg.norm(U1); U2 = np.cross(U0, U1)
kn = np.array(G0['kn']); kn /= np.linalg.norm(kn); G = np.array(G0['G'])
v = np.cross(U0, kn); s = np.linalg.norm(v); c = U0 @ kn; th = np.arctan2(s, c)
RD = np.array(Matrix.Rotation(th, 3, Vector(v / s))); print('CLUB wrist turn deg', round(np.degrees(th), 1))
A, B, C = RD @ U0, RD @ U1, RD @ U2
TG = -0.635
P = G + np.outer(Z['V'][:, 0] - TG, A) + np.outer(Z['V'][:, 1], B) + np.outer(Z['V'][:, 2], C)
n0 = len(me.vertices)
bm = bmesh.new(); bm.from_mesh(me)
lay = bm.verts.layers.int['part']; dv = bm.verts.layers.deform.verify()
gi = body.vertex_groups.find('Yclub')
if gi < 0: gi = body.vertex_groups.new(name='Yclub').index
nv = [bm.verts.new(p.tolist()) for p in P]
for x in nv: x[lay] = 20; x[dv][gi] = 1.0
bm.verts.ensure_lookup_table()
flip = np.linalg.det(np.c_[A, B, C]) < 0
nf0 = len(bm.faces)
ful = bm.loops.layers.float_vector.get('x') if False else None
uvl = bm.loops.layers.uv.get('PartUV')
mt = bm.faces.layers.int.get('mat')
for f in Z['F']:
    tri = (f[0], f[2], f[1]) if flip else tuple(f)
    a, b, c_ = (nv[i] for i in tri)
    try:
        q = bm.faces.new((a, b, c_)); q.smooth = True
    except ValueError: continue
    if uvl is not None:
        for l, i in zip(q.loops, tri): l[uvl].uv = (float(Z['UV'][i, 0]), float(Z['UV'][i, 1]))
    if mt is not None: q[mt] = 3
bm.to_mesh(me); bm.free()
bpy.context.view_layer.objects.active = rig
for o in bpy.data.objects: o.select_set(o is rig)
bpy.ops.object.mode_set(mode='EDIT')
e = rig.data.edit_bones['Yclub']; d = e.tail - e.head; Mi = rig.matrix_world.inverted(); e.head = Mi @ Vector(G); e.tail = e.head + d
bpy.ops.object.mode_set(mode='OBJECT')
Bm = rig.matrix_world.to_3x3() @ rig.data.bones['Bip01 R Hand'].matrix_local.to_3x3()
json.dump(dict(RD=RD.astype(float).tolist(), G=G.tolist(), kn=kn.tolist()), open('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm9_trellborg_claude/work/grip.json', 'w'))
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print('CLUBADDED', n0, '->', len(me.vertices))
