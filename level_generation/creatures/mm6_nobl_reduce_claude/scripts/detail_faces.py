"""Choose the front-detail faces of the final mesh (work/ladder_body.blend): collar, neck/undershirt, capelet top,
chest and tabard front, clasp and belt front; report their area by group and current texture set.
The installed cloak/tunic class of each face is read where the faces still have their installed UVs
(work/ladder_chest.blend) and carried over by face centre; it is stored as face attribute inst_region (0 none, 1 cloak,
2 tunic) in work/ladder_body.blend. Writes work/detail_faces.json (polygon indices). Usage: blender -b -P detail_faces.py"""
import json, os, bpy
import numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
mask_path = os.path.join(HERE, 'work', 'region_mask.png')


def rest(cand_name='Cand_62'):
    rig = bpy.data.objects['Rig']; rig.animation_data.action = None
    for b in rig.pose.bones:
        b.matrix_basis.identity()
    bpy.context.view_layer.update()
    return bpy.data.objects[cand_name]


bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'ladder_chest.blend'))
o = rest(); me = o.data; mw = o.matrix_world
mask = bpy.data.images.load(mask_path); W, H = mask.size; px = np.array(mask.pixels[:], np.float32).reshape(H, W, 4)
uv = me.uv_layers[0].data
from mathutils import kdtree
cent = [mw @ p.center for p in me.polygons]; kd = kdtree.KDTree(len(cent))
for i, c in enumerate(cent):
    kd.insert(c, i)
kd.balance(); inst = []
for p in me.polygons:
    u = np.mean([uv[li].uv[0] for li in p.loop_indices]); v = np.mean([uv[li].uv[1] for li in p.loop_indices])
    s = px[min(int(v * H), H - 1), min(int(u * W), W - 1)] if u < .5 else np.zeros(4)
    inst.append(1 if s[0] > .5 else (2 if s[1] > .5 else 0))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'ladder_body.blend'))
o = rest(); me = o.data; mw = o.matrix_world; n3 = mw.to_3x3()
uv = me.uv_layers[0].data
region = []
for p in me.polygons:
    _, j, dist = kd.find(mw @ p.center)
    region.append(inst[j] if dist < 1e-5 else 0)     # new faces (buckle frame) have no installed class
attr = me.attributes.get('inst_region') or me.attributes.new('inst_region', 'INT', 'FACE')
attr.data.foreach_set('value', region)
part = [0] * len(me.polygons); me.attributes['chest_part'].data.foreach_get('value', part)
cx = -.0074
# small separate pieces in the torso (belts, belt gem, clasp): whole pieces join the belt/clasp group
import bmesh
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table(); seen, small = set(), set()
for v in bm.verts:
    if v.index in seen:
        continue
    stack, comp = [v], []
    seen.add(v.index)
    while stack:
        x = stack.pop(); comp.append(x)
        for e in x.link_edges:
            y = e.other_vert(x)
            if y.index not in seen:
                seen.add(y.index); stack.append(y)
    cc = sum((mw @ x.co for x in comp), (mw @ comp[0].co) * 0) / len(comp)
    if len(comp) < 200 and .9 < cc.z < 1.45 and abs(cc.x - cx) < .2:
        small |= {f.index for x in comp for f in x.link_faces}
bm.free()
# faces covered by other geometry along their normal (tunic back under the cloak, cloak top under the capelet) stay in
# the body set: no detail texels spent on them, and a seam there is out of sight
from mathutils.bvhtree import BVHTree
dg = bpy.context.evaluated_depsgraph_get(); bvh = BVHTree.FromObject(o, dg)
n3 = mw.to_3x3()


def covered(p):
    if (n3 @ p.normal).normalized().y < .2:          # only backward-facing faces can hide behind the cloak or hair
        return False
    n = p.normal.normalized(); hit = bvh.ray_cast(p.center + n * .002, n, .15 / mw.to_scale()[0])
    return hit[0] is not None
groups = {k: [] for k in ('collar_neck', 'capelet', 'chest', 'tabard', 'belt_clasp')}
area = {k: 0.0 for k in groups}; head_cnt = {k: 0 for k in groups}
for p in me.polygons:
    if part[p.index] or covered(p):
        continue                                    # flat colour parts stay on their squares; hidden faces in the body
    u = np.mean([uv[li].uv[0] for li in p.loop_indices]); v = np.mean([uv[li].uv[1] for li in p.loop_indices])
    head = u > .5
    if head:   # the head set keeps its own texture, except the collar and neck under the face
        pass
    c = mw @ p.center; nrm = (n3 @ p.normal).normalized()
    cloak, tunic = region[p.index] == 1, region[p.index] == 2
    g = None
    if cloak and c.z > 1.2:
        g = 'capelet'                 # whole capelet: the set boundary runs along its hem (cord), not across the cloth
    elif tunic and c.z >= .93:
        g = 'chest'                   # all tunic faces above the belt: boundary on the tunic/sleeve colour edge
    elif (tunic and c.z < .93) or (not cloak and .45 < c.z < .93 and abs(c.x - cx) < .14 and c.y < -.11 and nrm.y < 0):
        g = 'tabard'          # the installed mask leaves parts of the flap unclassed: front-most faces below the belt
    elif p.index in small:
        g = 'belt_clasp'              # whole belt, gem and clasp pieces
    elif not cloak and not tunic and ((1.36 < c.z < 1.56 and abs(c.x - cx) < .17 and (not head or c.z < 1.47))
                                      or (1.2 < c.z <= 1.36 and abs(c.x - cx) < .12 and c.y < -.05)):
        g = 'collar_neck'             # collar, neck, and the dark undershirt V below the clasp
    if g:
        groups[g].append(p.index); area[g] += p.area * 1e4; head_cnt[g] += head
print('DETAIL', {k: (len(v), round(area[k]), head_cnt[k]) for k, v in groups.items()}, 'total cm2', round(sum(area.values())))
json.dump(groups, open(os.path.join(HERE, 'work', 'detail_faces.json'), 'w'))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'ladder_body.blend'))
