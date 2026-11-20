"""Cap the open forearm ends of the grafted hand stubs (PeasantDM4 see-through gate, 2026-11-02: in AttackMelee the view
past the right hand into the cuff ran up the tucked stub and out of its open end, 144 px of background). Every boundary
loop of hand faces (attribute hand = 1) with >= MIN_EDGES edges gets two triangle fans to its centroid (both
orientations, so the cap is opaque from either side), on the HeadUV texel of the stub face nearest the loop (skin), with
the loop's mean weights; head/hand attributes copied. Faces added only. Args (Blender): <in blend> <out blend> [min_edges 8]"""
import bpy, bmesh, sys, json
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
IN, OUT = a[0], a[1]; MIN_EDGES = int(a[2]) if len(a) > 2 else 8
bpy.ops.wm.open_mainfile(filepath=IN)
body = bpy.data.objects['Body']; me = body.data
bm = bmesh.new(); bm.from_mesh(me)
dl = bm.verts.layers.deform.active
lh, lk = bm.faces.layers.int['head'], bm.faces.layers.int['hand']
uvs = list(bm.loops.layers.uv.values())
seen, loops = set(), []
for e in bm.edges:
    if not e.is_boundary or e in seen or not e.link_faces[0][lk]:
        continue
    lp, st = [], [e]; seen.add(e)
    while st:
        x = st.pop(); lp.append(x)
        for v in x.verts:
            for y in v.link_edges:
                if y.is_boundary and y not in seen and y.link_faces[0][lk]:
                    seen.add(y); st.append(y)
    loops.append(lp)
rep = []
for lp in loops:
    if len(lp) < MIN_EDGES:
        continue
    vs = list({v for x in lp for v in x.verts})
    c = sum((v.co for v in vs), Vector()) / len(vs)
    ref = lp[0].link_faces[0]
    cuv = {U: sum((Vector(tuple(l[U].uv)) for l in ref.loops), Vector((0, 0))) / len(ref.loops) for U in uvs}
    acc = {}
    for v in vs:
        for g, wt in v[dl].items():
            acc[g] = acc.get(g, 0.0) + wt
    tot = sum(acc.values())
    n = 0
    for flip in (False, True):
        cv = bm.verts.new(c)
        for g, wt in acc.items():
            cv[dl][g] = wt / tot
        for x in lp:
            vv = (x.verts[0], x.verts[1], cv) if not flip else (x.verts[1], x.verts[0], cv)
            try:
                f = bm.faces.new(vv)
            except ValueError:
                continue
            f[lh] = ref[lh]; f[lk] = 1; f.material_index = ref.material_index; f.smooth = ref.smooth
            for l in f.loops:
                for U in uvs:
                    l[U].uv = cuv[U]
            n += 1
    rep.append({'edges': len(lp), 'centre': [round(t, 3) for t in c], 'cap_faces': n})
bm.to_mesh(me); bm.free(); me.update()
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print('STUB_CAP', json.dumps(rep))
