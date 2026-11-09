"""Replace the Dagrell's left arm pieces by a mirrored copy of its right arm pieces (bind space).

Args: <uv blend> <out blend> <report json>

Meshy's left front limb reached forward in its return while the right one matched the MM9 Stand pose, so the MM9
pose fit (fit_dagrell.py) placed the right arm bones well and the left ones poorly: in motion the left forearm and claws
drifted off the elbow. The MM9 skeleton is mirror-symmetric in its bind pose, so the right arm pieces (dominant bone in
the right arm/finger chain) are duplicated, mirrored x -> -x, their faces flipped back outward, and their weights moved
to the mirrored left bones (matched by mirrored bind head position); the old left arm pieces are deleted. UVs travel
with the copies (the mirrored arm samples the right arm's texels), so the retexture still applies.
"""
import bpy, bmesh, sys, json
import numpy as np
from mathutils import Vector

argv = sys.argv[sys.argv.index('--') + 1:]
IN, OUT, REP = argv
ARM_R = ['Xarmpiv', 'Xarm', 'Xarmlow', 'Xfinpiv', 'Xfin', 'Xfmid', 'Xfinpiv01', 'Xfin01', 'Xfmid01', 'Xfinpiv02', 'Xfin02',
         'Xfmid02']
ARM_L = ['Xarmpiv01', 'Xarm01', 'Xarmlow01', 'Xfinpiv03', 'Xfin04', 'Xfmid03', 'Xfinpiv04', 'Xfin03', 'Xfmid04',
         'Xfinpiv05', 'Xfin05', 'Xfmid05']

bpy.ops.wm.open_mainfile(filepath=IN)
rig = bpy.data.objects['MM9_Rig']
ob = bpy.data.objects['Body']
bones = rig.data.bones
mirror = {}
for r in ARM_R:
    h = bones[r].head_local
    target = Vector((-h.x, h.y, h.z))
    mirror[r] = min(ARM_L, key=lambda l: (bones[l].head_local - target).length)
assert len(set(mirror.values())) == len(ARM_L), mirror
for l in ARM_L:
    if l not in ob.vertex_groups:
        ob.vertex_groups.new(name=l)
gidx = {g.name: g.index for g in ob.vertex_groups}
gname = {g.index: g.name for g in ob.vertex_groups}
remap = {gidx[r]: gidx[l] for r, l in mirror.items() if r in gidx}

bm = bmesh.new(); bm.from_mesh(ob.data); bm.verts.ensure_lookup_table()
dl = bm.verts.layers.deform.active
seen = {}
comps = []
for v in bm.verts:
    if v.index in seen:
        continue
    st = [v]; seen[v.index] = 1; c = []
    while st:
        x = st.pop(); c.append(x)
        for e in x.link_edges:
            y = e.other_vert(x)
            if y.index not in seen:
                seen[y.index] = 1; st.append(y)
    comps.append(c)


def side(c):
    w = {}
    for v in c:
        for gi, wt in v[dl].items():
            w[gname[gi]] = w.get(gname[gi], 0) + wt
    top = max(w, key=w.get)
    return 'R' if top in ARM_R else 'L' if top in ARM_L else None


right = [c for c in comps if side(c) == 'R']
left = [c for c in comps if side(c) == 'L']
rep = {'mirror': mirror, 'right_pieces': len(right), 'right_verts': sum(len(c) for c in right),
       'left_pieces_removed': len(left), 'left_verts_removed': sum(len(c) for c in left)}
faces = list({f for c in right for v in c for f in v.link_faces})
res = bmesh.ops.duplicate(bm, geom=list({v for c in right for v in c}) + list({e for c in right for v in c for e in v.link_edges}) + faces)
new_verts = [g for g in res['geom'] if isinstance(g, bmesh.types.BMVert)]
new_faces = [g for g in res['geom'] if isinstance(g, bmesh.types.BMFace)]
for v in new_verts:
    v.co.x = -v.co.x
    d = v[dl]
    items = list(d.items())
    for gi, _ in items:
        del d[gi]
    for gi, wt in items:
        d[remap.get(gi, gi)] = wt
bmesh.ops.reverse_faces(bm, faces=new_faces)
# every mirrored piece must enclose positive volume (outward faces); flip any that does not
new_set = set(new_faces)
flipped = 0
seen_f = set()
for f0 in new_faces:
    if f0 in seen_f:
        continue
    comp_f, st = [], [f0]; seen_f.add(f0)
    while st:
        f = st.pop(); comp_f.append(f)
        for e in f.edges:
            for g in e.link_faces:
                if g in new_set and g not in seen_f:
                    seen_f.add(g); st.append(g)
    vol = 0.0
    for f in comp_f:
        vs = [v.co for v in f.verts]
        for k in range(1, len(vs) - 1):
            vol += vs[0].dot(vs[k].cross(vs[k + 1])) / 6.0
    if vol < 0:
        bmesh.ops.reverse_faces(bm, faces=comp_f)
        flipped += 1
bmesh.ops.delete(bm, geom=list({v for c in left for v in c}), context='VERTS')
bm.to_mesh(ob.data)
ob.data.update()
rep.update({'flipped_inverted': flipped, 'verts': len(ob.data.vertices), 'tris': sum(len(p.vertices) - 2 for p in ob.data.polygons)})
bpy.ops.wm.save_as_mainfile(filepath=OUT)
json.dump(rep, open(REP, 'w'), indent=1)
print('MIRROR ' + json.dumps(rep))
