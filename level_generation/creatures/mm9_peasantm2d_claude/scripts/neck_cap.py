"""Cap the head shell's open neck (2026-11-02, see-through gate: views into the tunic's collar of the lying corpse met the
inside of the head through the open bottom of its neck tube). The head-face boundary loops of more than MIN_EDGES edges
whose vertices are mostly weighted to Neck/Head, whose mean radius exceeds MIN_R and whose centroid lies 5 cm or more
below the head faces' centroid (the neck bottom, 28 edges, r 0.10 m; not the scalp's opening under the hair)
get a triangle fan to a centre vertex (the loop's centroid, the loop's mean weights), facing out of the head (away from
the head shell's centroid). UVs: every cap loop takes the centre UV (HeadUV and UVMap) of the rim face whose texel is
nearest the rim's median colour (skin of the neck base). Geometry is added only. Args (Blender): <in blend> <out blend>
<head base colour png> [min_edges 20] [min_r 0.06]"""
import bpy, bmesh, sys, json
import numpy as np
from mathutils import Vector

a = sys.argv[sys.argv.index('--') + 1:]
IN, OUT, HEADPNG = a[0], a[1], a[2]
MIN_EDGES = int(a[3]) if len(a) > 3 else 20
MIN_R = float(a[4]) if len(a) > 4 else 0.06
bpy.ops.wm.open_mainfile(filepath=IN)
body = bpy.data.objects['Body']; rig = body.parent
if rig.animation_data:
    rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.update()
me = body.data
names = [g.name for g in body.vertex_groups]
img = bpy.data.images.load(HEADPNG)
W, H = img.size
PX = np.array(img.pixels[:], np.float32).reshape(H, W, 4)[..., :3]
bm = bmesh.new(); bm.from_mesh(me)
dl = bm.verts.layers.deform.active
lh, lk = bm.faces.layers.int['head'], bm.faces.layers.int['hand']
uvb, uvh = bm.loops.layers.uv['UVMap'], bm.loops.layers.uv['HeadUV']
head_faces = [f for f in bm.faces if f[lh]]
head_c = sum((f.calc_center_median() for f in head_faces), Vector()) / len(head_faces)


def dominant(v):
    w = v[dl]
    return names[max(w.items(), key=lambda kv: kv[1])[0]] if len(w) else ''


def cuv(f, layer):
    return sum((Vector(tuple(l[layer].uv)) for l in f.loops), Vector((0, 0))) / len(f.loops)


seen, loops = set(), []
for e in bm.edges:
    if not e.is_boundary or e in seen or not e.link_faces[0][lh]:
        continue
    lp, st = [], [e]; seen.add(e)
    while st:
        x = st.pop(); lp.append(x)
        for v in x.verts:
            for y in v.link_edges:
                if y.is_boundary and y not in seen and y.link_faces[0][lh]:
                    seen.add(y); st.append(y)
    loops.append(lp)
rep = []
for lp in loops:
    vs = list({v for x in lp for v in x.verts})
    c = sum((v.co for v in vs), Vector()) / len(vs)
    r = float(np.mean([(v.co - c).length for v in vs]))
    neckish = sum(any(k in dominant(v) for k in ('Neck', 'Head')) for v in vs)
    if len(lp) < MIN_EDGES or r < MIN_R or neckish < 0.6 * len(vs) or c.z > head_c.z - 0.05:
        continue
    rim = [x.link_faces[0] for x in lp]
    cols = np.array([PX[min(H - 1, int(cuv(f, uvh).y * H)), min(W - 1, int(cuv(f, uvh).x * W))] for f in rim])
    med = np.median(cols, 0)
    ref = rim[int(np.argmin(np.linalg.norm(cols - med, axis=1)))]
    uv_h, uv_b = tuple(cuv(ref, uvh)), tuple(cuv(ref, uvb))
    cv = bm.verts.new(c)
    acc = {}
    for v in vs:
        for g, wt in v[dl].items():
            acc[g] = acc.get(g, 0.0) + wt
    tot = sum(acc.values())
    for g, wt in acc.items():
        cv[dl][g] = wt / tot
    new = []
    for x in lp:
        f = bm.faces.new((x.verts[0], x.verts[1], cv))
        f.normal_update()
        if f.normal.dot(c - head_c) < 0:
            f.normal_flip()
        f[lh] = 1; f[lk] = 0; f.material_index = ref.material_index; f.smooth = ref.smooth
        for l in f.loops:
            l[uvh].uv = uv_h; l[uvb].uv = uv_b
        new.append(f)
    rep.append({'edges': len(lp), 'radius': round(r, 3), 'cap_faces': len(new),
                'texel': [round(float(x), 3) for x in med]})
bm.to_mesh(me); bm.free(); me.update()
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print('NECK_CAP', json.dumps(rep))
