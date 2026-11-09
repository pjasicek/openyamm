"""Relax sharp ticks of the reduced skin (little creases left where the Meshy layers met) before the mouth is cut:
vertices whose offset from their neighbours' mean exceeds THRESH x their mean edge length move toward that mean, a few
passes, skin only (no pieces), never on ears, horns or other parts excluded by SKIP_ABOVE (z) or the ear bones.
CAP 'z0,scale,y0,y1': heights above z0 between y0 and y1 are compressed (the cow's pointed poll).
Args: <in blend> <out blend> <report json>   Env: THRESH (0.35), PASSES (6), SKIP_ABOVE, CAP"""
import bpy, bmesh, sys, os, json
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rigcfg
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])
ob = bpy.data.objects['Body']
TH = float(os.environ.get('THRESH', '0.35'))
PASSES = int(os.environ.get('PASSES', '6'))
SKIP = float(os.environ.get('SKIP_ABOVE', '1e9'))
bm = bmesh.new(); bm.from_mesh(ob.data)
dl = bm.verts.layers.deform.active
pl = bm.verts.layers.int.get('piece')
ears = {ob.vertex_groups[n].index for n in rigcfg.EAR_BONES if n in ob.vertex_groups}
tail = {ob.vertex_groups[n].index for n in rigcfg.CHAINS['tail'] if n in ob.vertex_groups}
if os.environ.get('CAP'):
    z0, sc, y0, y1 = (float(x) for x in os.environ['CAP'].split(','))
    for v in bm.verts:
        if v.co.z > z0 and y0 < v.co.y < y1 and v[pl] == 0:
            v.co.z = z0 + (v.co.z - z0) * sc
moved = 0
for _ in range(PASSES):
    new = {}
    for v in bm.verts:
        if v[pl] != 0 or v.co.z > SKIP or not v.is_manifold:
            continue
        d = v[dl]
        if sum(d.get(g, 0) for g in ears) > 0.3 or sum(d.get(g, 0) for g in tail) > 0.3:
            continue
        nb = [e.other_vert(v) for e in v.link_edges]
        m = sum((o.co for o in nb), Vector()) / len(nb)
        el = sum((o.co - v.co).length for o in nb) / len(nb)
        if (v.co - m).length > TH * el:
            new[v] = v.co.lerp(m, 0.6)
    for v, p in new.items():
        v.co = p
    moved += len(new)
bm.to_mesh(ob.data); bm.free()
bpy.ops.wm.save_as_mainfile(filepath=argv[1])
json.dump({'moved': moved}, open(argv[2], 'w'))
print('DESPIKE', moved)
