"""Right arm head = mirrored left arm head (2026-10-30 rework).

The Meshy body has two different arm heads: the left (+X) one is the long open-jawed snake head of the masters, the
right one a short stub facing forward. Only the left one got a head-only retexture (10 credits); the right one is
replaced by its mirror image, so both match the masters and MM9's symmetric model, and the copy shares the left head's
HeadUV texels (the engine derives normal-map tangents per pixel, so mirrored UVs light correctly).

- copy the left head faces (head = 2), mirror x, flip the winding, rename every vertex group X..01 <-> X.. so the
  copy is driven by the right arm's bones (the MM9 rig is symmetric): head = 3;
- delete the old right head (its head = 3 faces from head_split_v2.py) where it lies inside the copy (every vertex
  inside or within INSIDE_TOL of the copy's surface) or past the copy's base ring (by BASE_MARGIN along the forearm
  axis: the stub's skull poking out of the copy), and all of its small pieces (the copy brings the left spike ring). The rest of it, the wrist between the right forearm and the copy's base (the Meshy right forearm ends about
  16 cm short of the mirrored head's base), stays with its own HeadUV charts and is marked head = 4: those texels are
  painted from the left arm head's retexture at the mirror image of each texel's surface point
  (armhead_mirror_map.py), so the forearm runs into the copy with no gap and no new geometry.
Args: <uv blend> <out blend> <report json>"""
import bpy, bmesh, json, sys
from mathutils.bvhtree import BVHTree

a = sys.argv[sys.argv.index('--') + 1:]
IN, OUT, REP = a
INSIDE_TOL = 0.01
BASE_MARGIN = 0.03
bpy.ops.wm.open_mainfile(filepath=IN)
body = bpy.data.objects['Body']
rig = body.parent
if rig.animation_data:
    rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.update()
me = body.data
for b in rig.data.bones:      # a bone the right arm never used (Xatongue) still needs its group for the copy
    if b.name not in body.vertex_groups:
        body.vertex_groups.new(name=b.name)
names = [g.name for g in body.vertex_groups]
idx = {n: i for i, n in enumerate(names)}


def mirror_name(n):
    if n.endswith('01') and n[:-2] in idx:
        return n[:-2]
    if n + '01' in idx:
        return n + '01'
    return n


gmap = {i: idx[mirror_name(n)] for i, n in enumerate(names)}
bm = bmesh.new(); bm.from_mesh(me)
hl = bm.faces.layers.int['head']
dl = bm.verts.layers.deform.active
pc = bm.verts.layers.int['piece']
old = [f for f in bm.faces if f[hl] == 3]
for f in old:
    f[hl] = 4
src = [f for f in bm.faces if f[hl] == 2]
dup = bmesh.ops.duplicate(bm, geom=src)
new_faces = [g for g in dup['geom'] if isinstance(g, bmesh.types.BMFace)]
new_verts = [g for g in dup['geom'] if isinstance(g, bmesh.types.BMVert)]
for v in new_verts:
    v.co.x = -v.co.x
    w = dict(v[dl])
    v[dl].clear()
    for gi, wt in w.items():
        v[dl][gmap[gi]] = wt
for f in new_faces:
    f[hl] = 3
bmesh.ops.reverse_faces(bm, faces=new_faces, flip_multires=False)
bm.normal_update()
pts, polys = [], []
for f in new_faces:
    polys.append(tuple(range(len(pts), len(pts) + len(f.verts))))
    pts += [v.co.copy() for v in f.verts]
bvh = BVHTree.FromPolygons(pts, polys)


def inside(v):
    loc, nrm, _, _ = bvh.find_nearest(v.co)
    return (v.co - loc).dot(nrm) < INSIDE_TOL


# the copy's base: the median position, along the right forearm axis, of its open boundary (the wrist ring)
J = lambda n: rig.matrix_world @ rig.data.bones[n].head_local
ax = (J('Xawrist') - J('Xarmmid')).normalized()
wr = J('Xawrist')
axial = lambda co: (co - wr).dot(ax)
base_ring = [v for f in new_faces for v in f.verts if v[pc] == 0 and v.is_boundary]
base_axial = sorted(axial(v.co) for v in base_ring)[len(base_ring) // 2]
# old faces go when they are small pieces, inside the copy, or past its base (the stub's skull poking out of it)
kill = [f for f in old if f.verts[0][pc] == 2 or all(inside(v) for v in f.verts)
        or all(axial(v.co) > base_axial + BASE_MARGIN for v in f.verts)]
rep = {'base_axial_m': round(base_axial, 4), 'old_right_head_faces': len(old), 'deleted_inside_or_pieces': len(kill), 'mirrored_faces': len(new_faces)}
bmesh.ops.delete(bm, geom=kill, context='FACES')
bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
rep['kept_wrist_faces_head4'] = sum(1 for f in bm.faces if f[hl] == 4)
rep['copy_groups_left_side'] = sorted({names[g] for v in new_verts if v.is_valid for g in v[dl].keys()
                                        if names[g].endswith('01') and names[g][:-2] in idx})
bm.to_mesh(me); bm.free()
me.validate()
bpy.ops.wm.save_as_mainfile(filepath=OUT)
rep['faces'] = len(me.polygons)
json.dump(rep, open(REP, 'w'), indent=1)
print('MIRROR', json.dumps(rep))
