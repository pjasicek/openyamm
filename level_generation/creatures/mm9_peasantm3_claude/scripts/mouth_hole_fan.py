"""Fan-fill the small boundary loops left at the mouth (the 7-edge hole in the face shell at the lower lip's centre, which
bmesh holes_fill skipped: after mouth_close_pm3.py moved it forward it read as a dark diamond between the lips).
A centre vertex at the loop's mean (weights = the rim's average, deform layer), one triangle per rim edge; every new corner
takes one UV point per layer (a rim corner's own), a one-texel cap, face attributes and
material from the face beside the edge. Args (Blender): <in blend> <out blend> [box xmin,xmax,ymin,ymax,zmin,zmax]
[max edges 40]"""
import bpy, bmesh, sys, json
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
IN, OUT = a[0], a[1]
box = [float(v) for v in (a[2] if len(a) > 2 else '-0.04,0.04,-0.09,-0.03,0.73,0.77').split(',')]
MAXE = int(a[3]) if len(a) > 3 else 40
bpy.ops.wm.open_mainfile(filepath=IN)
body = bpy.data.objects['Body']; me = body.data
bm = bmesh.new(); bm.from_mesh(me)
dl = bm.verts.layers.deform.verify()
bnd = {e for e in bm.edges if e.is_boundary}
loops = []
while bnd:
    e = bnd.pop(); loop = [e]; st = [e]
    while st:
        x = st.pop()
        for v in x.verts:
            for f in v.link_edges:
                if f in bnd:
                    bnd.discard(f); loop.append(f); st.append(f)
    loops.append(loop)
done = []
for loop in loops:
    vs = list({v for e in loop for v in e.verts})
    c = sum((v.co for v in vs), Vector()) / len(vs)
    if len(loop) > MAXE or not (box[0] < c.x < box[1] and box[2] < c.y < box[3] and box[4] < c.z < box[5]):
        continue
    cv = bm.verts.new(c)
    w = {}
    for v in vs:
        for g, x in v[dl].items():
            w[g] = w.get(g, 0) + x / len(vs)
    for g, x in w.items():
        cv[dl][g] = x
    uvl = bm.loops.layers.uv.values()
    # every corner of the cap takes ONE uv point per layer (a rim corner's own uv): a cap whose corners took uvs from
    # different islands spanned half the atlas and texel rasterisers mapped the mouth onto hair texels (r2 lesson)
    cuv = {}
    # r3: the texel of the FRONTMOST face-shell corner near the loop (the lip's front surface, lip-coloured); the rim's own
    # texel was the dark inner lip edge (dark slivers in the albedo)
    cand = [l for f in bm.faces for l in f.loops if abs(l.vert.co.x - c.x) < 0.006 and abs(l.vert.co.z - c.z) < 0.006
            and not any(l.vert is v for v in vs)]
    rimloop = min(cand, key=lambda l: l.vert.co.y) if cand else next(l for v in vs for l in v.link_loops)
    for lay in uvl:
        cuv[lay.name] = rimloop[lay].uv.copy()
    for e in loop:
        ref = e.link_faces[0]
        v0, v1 = e.verts
        # wind like the neighbour face: the edge runs the other way in the new face
        lo = next(l for l in ref.loops if l.edge is e)
        if lo.vert is v0:
            v0, v1 = v1, v0
        f = bm.faces.new((v0, v1, cv))
        f.material_index = ref.material_index; f.smooth = True
        for lay in bm.faces.layers.int.values():
            f[lay] = ref[lay]
        for l in f.loops:
            for lay in uvl:
                l[lay].uv = cuv[lay.name]
    done.append({'edges': len(loop), 'centre': [round(x, 4) for x in c]})
bm.normal_update(); bm.to_mesh(me); me.update()
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print('MOUTHFAN ' + json.dumps(done))
