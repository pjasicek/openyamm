"""Split misplaced cap fans (work/hub_caps.json, scripts/hub_caps.py) in work/source.blend: every wedge of each listed
hub except the one nearest the hub gets its own centre vertex at its rim centroid, with the rim's mean bone weights
and, per face corner, the mean UV of that face's rim corners. Face order is unchanged (the keep masks stay valid).
Saves work/source.blend (run on work/source_pre_hubfix.blend)."""
import os, json, bpy, bmesh
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
caps = json.load(open(os.path.join(HERE, 'work/hub_caps.json')))
o = bpy.data.objects['Body']; me = o.data
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
uvl = bm.loops.layers.uv.active; dl = bm.verts.layers.deform.active
for h in sorted({c['hub'] for c in caps}):
    hub = bm.verts[h]; fs = list(hub.link_faces)
    par = {f.index: f.index for f in fs}
    def find(a):
        while par[a] != a: a = par[a]
        return a
    for a in fs:
        for b in fs:
            if a.index < b.index and ({v.index for v in a.verts} & {v.index for v in b.verts}) - {h}: par[find(b.index)] = find(a.index)
    wedges = {}
    for f in fs: wedges.setdefault(find(f.index), []).append(f)
    def rim(w): return list({v for f in w for v in f.verts if v is not hub})
    def cen(w): r = rim(w); return sum((v.co for v in r), Vector()) / len(r)
    order = sorted(wedges.values(), key=lambda w: (cen(w) - hub.co).length)
    for w in order[1:]:
        r = rim(w); c = cen(w)
        wsum = {}
        for v in r:
            for g, x in v[dl].items(): wsum[g] = wsum.get(g, 0) + x
        tot = sum(wsum.values())
        new = []
        for f in w:
            nv = bmesh.utils.face_vert_separate(f, hub) if len(hub.link_faces) > 1 else hub
            new.append(nv)
            for l in f.loops:
                if l.vert is nv:
                    others = [x[uvl].uv for x in f.loops if x.vert is not nv]
                    l[uvl].uv = (others[0] + others[1]) / 2
        new = list({v for v in new})
        bmesh.ops.pointmerge(bm, verts=new, merge_co=c)
        nv = next(v for v in bm.verts if (v.co - c).length < 1e-9 and v.is_valid)
        nv[dl].clear()
        for g, x in wsum.items(): nv[dl][g] = x / tot
        print('WEDGE', h, len(w), 'faces -> new centre', tuple(round(x, 3) for x in c))
bm.to_mesh(me); bm.free(); me.update()
print('FACES', len(me.polygons), 'VERTS', len(me.vertices))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'source.blend'))
