"""After the paint (UVs frozen): nothing here touches painted faces or their UVs. The mouth ring, open where Meshy's teeth were, gets a plug set 3 mm back, on the head set's dark texel: no jaw bone in MM9, the mouth stays shut.
Args: <in blend> <out blend>"""
import bpy, bmesh, sys, json, os
from mathutils import Vector
IN, OUT = sys.argv[sys.argv.index('--') + 1:]
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=IN)
body = bpy.data.objects['Body']; me = body.data
DT = json.load(open(os.path.join(HERE, 'work', 'dark_texel.json')))
bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table()
part = bm.faces.layers.int['part']; mat = bm.faces.layers.int['mat']; uvp = bm.loops.layers.uv['PartUV']
dv = bm.verts.layers.deform.verify()
seen = set(); comps = []
for e in [e for e in bm.edges if e.is_boundary]:
    if e in seen: continue
    st = [e]; seen.add(e); cur = []
    while st:
        x = st.pop(); cur.append(x)
        for v in x.verts:
            for y in v.link_edges:
                if y.is_boundary and y not in seen: seen.add(y); st.append(y)
    comps.append(cur)
ring = [c for c in comps if len(c) >= 30 and all(0.71 < v.co.z < 0.76 and v.co.y < 0 for e in c for v in e.verts)]
assert len(ring) == 1, [len(c) for c in ring]
vs = list({v for e in ring[0] for v in e.verts})
cen = sum((v.co for v in vs), Vector()) / len(vs)
nv = bm.verts.new(cen + Vector((0, 0.004, 0)))
nv[dv] = {k: w for k, w in vs[0][dv].items()} if False else nv[dv]
hd = body.vertex_groups['Bip01 Head'].index
nv[dv][hd] = 1.0
new = []
for e in ring[0]:
    a, b = e.verts
    f = bm.faces.new((a, b, nv)); f[part] = 20; f[mat] = 2; f.smooth = True; new.append(f)
    if (f.normal.dot(Vector((0, -1, 0)))) < 0: f.normal_flip()
    for l in f.loops: l[uvp].uv = (DT['head']['u'], 1 - DT['head']['v'])
print('FINISH plug', len(new), 'centre', [round(x, 3) for x in cen])
# the legs' hidden top runs up inside the belt: they only touched the skirt, which swings away from them, and the audit saw the legs part from the body (Hit2, 1.4 cm). Rigid on the Spine, as the belt is.
n = 0
for v in {v for f in bm.faces if f[part] == 5 for v in f.verts}:
    if v.co.z > 0.12:
        u = (v.co.z - 0.12) / 0.09
        k = 1 + 0.12 * min(1.0, u)
        v.co = Vector((v.co.x * k, v.co.y * k, v.co.z + 0.08 * u)); n += 1
print('FINISH leg top verts', n)
bm.to_mesh(me); bm.free()
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print('FINISH', len(me.polygons), 'tris')
