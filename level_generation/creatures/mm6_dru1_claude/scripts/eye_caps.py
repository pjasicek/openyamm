"""Eyeball caps for the druidess (in place on work/rig_v6.blend, after transfer_uv.py).
step1_clean.py removed Meshy's eyeball shells (P12/P13), which left an open boundary loop in the face skin at each
eye: in the lit close-up the eyes were dark holes into the head. Each loop is closed by a cap: one ring halfway to the
centre and a centre vertex, pushed forward to a shallow dome in front of the lid opening (EYE_BULGE). Cap vertices copy
the weights of the nearest loop vertex; cap faces are head faces (attribute 'head' = 1, piece 0) and their HeadUV is a
disc (centre = the cap centre) in a free corner of the head atlas (work/eye_disc.json from eye_disc.py), where
compose_dru1.py paints the eye (iris toward the disc centre).
Args: -- <blend>"""
import bpy, bmesh, sys, os, json, math
import numpy as np
from mathutils import Vector
blend = sys.argv[sys.argv.index('--') + 1]
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EYES = [Vector((0.017, -0.107, 1.573)), Vector((-0.030, -0.107, 1.573))]   # removed eye shells P12/P13 (mean)
EYE_BULGE = 0.004
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data
rig.animation_data_create(); rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
if 'eye_cap' in me.attributes:
    print('EYECAPS already present'); sys.exit(0)
dd = json.load(open(os.path.join(HERE, 'work', 'eye_disc.json')))      # eye_disc.py (free corner of the head atlas)
DISC = (dd['u'], dd['v'], dd['r'])
bm = bmesh.new(); bm.from_mesh(me)
bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
pl = bm.verts.layers.int['piece']
hl = bm.faces.layers.int['head']
uvl = {l.name: l for l in bm.loops.layers.uv.values()} if False else {n: bm.loops.layers.uv[n] for n in ('UVMap', 'HeadUV')}
dvl = bm.verts.layers.deform.active
ec = bm.faces.layers.int.get('eye_cap') or bm.faces.layers.int.new('eye_cap')
added = 0
for e_i, c in enumerate(EYES):
    bedges = [e for e in bm.edges if e.is_boundary and all(v[pl] == 0 for v in e.verts)
              and all((v.co - c).length < 0.025 for v in e.verts)]
    if not bedges:
        raise RuntimeError(f'no boundary loop at eye {e_i}')
    # order the loop
    adj = {}
    for e in bedges:
        a, b = e.verts
        adj.setdefault(a, []).append(b); adj.setdefault(b, []).append(a)
    start = bedges[0].verts[0]; loop = [start]; prev = None
    while True:
        nxt = [v for v in adj[loop[-1]] if v is not prev and v is not loop[0]]
        if not nxt:
            break
        prev = loop[-1]; loop.append(nxt[0])
        if len(loop) > len(bedges) + 1:
            raise RuntimeError('open loop')
    cen = sum((v.co for v in loop), Vector()) / len(loop)
    front = min(v.co.y for v in loop)
    centre = Vector((cen.x, front - EYE_BULGE, cen.z))
    # weights of the nearest loop vertex (all head)
    wsrc = dict(loop[0][dvl])
    mid = []
    for v in loop:
        p = v.co.lerp(centre, 0.5); p.y = min(p.y, front - EYE_BULGE * 0.75)
        m = bm.verts.new(p); m[pl] = 0; mid.append(m)
        for g_, w_ in v[dvl].items():
            m[dvl][g_] = w_
    cv = bm.verts.new(centre); cv[pl] = 0
    for g_, w_ in wsrc.items():
        cv[dvl][g_] = w_
    # UVs: angle around the cap centre in the eye's own frame (x right, z up), radius 1 at the loop
    def disc_uv(p, r):
        a = math.atan2(p.z - cen.z, (p.x - cen.x) * (1 if c.x > 0 else -1))
        return (DISC[0] + math.cos(a) * r * DISC[2], DISC[1] + math.sin(a) * r * DISC[2])
    n = len(loop)
    faces = []
    for i in range(n):
        a, b = loop[i], loop[(i + 1) % n]; ma, mb = mid[i], mid[(i + 1) % n]
        f1 = bm.faces.new((a, ma, mb, b)) if True else None
        f2 = bm.faces.new((ma, cv, mb))
        for f, rs in ((f1, (1.0, 0.5, 0.5, 1.0)), (f2, (0.5, 0.0, 0.5))):
            f[hl] = 1; f[ec] = 1
            for l, r in zip(f.loops, rs):
                l[uvl['HeadUV']].uv = disc_uv(l.vert.co if r > 0 else loop[0].co, r) if r > 0 else (DISC[0], DISC[1])
                l[uvl['UVMap']].uv = (DISC[0], DISC[1])
            faces.append(f)
    # face winding outward (toward -Y)
    for f in faces:
        f.normal_update()
        if f.normal.y > 0:
            f.normal_flip()
    added += len(faces)
    print('EYECAP', e_i, 'loop', n, 'centre', [round(x, 4) for x in centre], 'faces', len(faces))
bm.to_mesh(me); bm.free()
me.update()
bpy.ops.wm.save_mainfile()
print('EYECAPS faces added', added)
