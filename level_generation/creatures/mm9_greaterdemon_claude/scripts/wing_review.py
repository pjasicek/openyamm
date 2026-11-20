"""Wing root review renders (2026-10-30 rework): the master blend in the bind pose and at the two flap extremes of the
MM9 clips (XwingD tips highest / lowest relative to XspineC, over every role clip at 30 fps), side, back and back
three-quarter views. Also writes the gap measure: the wing vertices buried in the body in the bind pose (membrane body
line, root tube) and how far any of them comes out of the posed body surface over every clip frame (every 2nd frame).

Args: <blend> <actions blend or -> <out dir> <prefix> [textured 0/1]
Colours (textured 0): body grey, membrane red, wing bones blue."""
import bpy, sys, os, json, numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index('--') + 1:]
BLEND, ACTS, OUT, PRE = a[:4]
TEX = len(a) > 4 and a[4] == '1'
os.makedirs(OUT, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=BLEND)
rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
body = next(o for o in bpy.data.objects if o.type == 'MESH' and o.parent == rig and len(o.data.polygons) > 1000)
if ACTS != '-':
    with bpy.data.libraries.load(ACTS) as (src, dst):
        dst.actions = list(src.actions)
acts = [x for x in bpy.data.actions if x.name in ('Standing', 'Walking', 'Running', 'Fidget', 'AttackMelee',
                                                  'AttackRanged', 'Hit', 'Death', 'Dead')]
rig.animation_data_create()
sc = bpy.context.scene
me = body.data
piece = np.array([d.value for d in me.attributes['piece'].data]) if 'piece' in me.attributes else None


def tip_metric():
    m = rig.matrix_world
    sp = m @ rig.pose.bones['XspineC'].head
    return sum((m @ rig.pose.bones[n].head).z - sp.z for n in ('XwingD', 'XwingD01')) / 2


ext = []
for act in acts:
    rig.animation_data.action = act
    f0, f1 = (int(x) for x in act.frame_range)
    for f in range(f0, f1 + 1):
        sc.frame_set(f)
        ext.append((tip_metric(), act.name, f))
ext.sort()
poses = {'bind': None, 'flap_down': ext[0][1:], 'flap_up': ext[-1][1:]}
print('EXTREMES', poses)
# gap measure: anchors = wing vertices (piece 3/4) that are inside or within 3 cm of the body in the bind pose
gap = {}
if piece is not None:
    rig.animation_data.action = None
    for pb in rig.pose.bones:
        pb.matrix_basis.identity()
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()

    def posed():
        ev = body.evaluated_get(dg).to_mesh()
        co = np.array([tuple(body.matrix_world @ v.co) for v in ev.vertices])
        ev.calc_loop_triangles()
        tris = [tuple(t.vertices) for t in ev.loop_triangles]
        body.evaluated_get(dg).to_mesh_clear()
        return co, tris
    co, tris = posed()
    t0 = [t for t in tris if all(piece[i] == 0 for i in t)]
    bvh = BVHTree.FromPolygons([tuple(c) for c in co], t0)
    wing = np.where((piece == 3) | (piece == 4))[0]
    def signed(bv, co, idx):
        out = []
        for i in idx:
            loc, nrm, _, dd = bv.find_nearest(Vector(co[i]))
            out.append(dd if (Vector(co[i]) - loc).dot(nrm) > 0 else -dd)
        return np.array(out)
    # anchors: the attachment vertices (build_wings_v2.py 'anchor': membrane body line, buried root of the arm)
    anc = np.zeros(len(me.vertices), np.int32)
    me.attributes['anchor'].data.foreach_get('value', anc)
    anchors = np.where(anc == 1)[0]
    d0 = signed(bvh, co, anchors)
    print('ANCHORS bind: n', len(anchors), 'outside', int((d0 > 0.005).sum()), 'max', round(float(d0.max()), 4))
    worst = (0, None, 0, [])
    per = {}
    for act in acts:
        rig.animation_data.action = act
        f0, f1 = (int(x) for x in act.frame_range)
        for f in range(f0, f1 + 1, 2):
            sc.frame_set(f); dg = bpy.context.evaluated_depsgraph_get()
            co, _ = posed()
            bv = BVHTree.FromPolygons([tuple(c) for c in co], t0)
            d = signed(bv, co, anchors)
            for pc in (3, 4):
                key = f'{act.name}_{"membrane" if pc == 3 else "root"}'
                m = piece[anchors] == pc
                per[key] = max(per.get(key, 0.0), round(float(d[m].max()), 4) if m.any() else 0.0)
            if d.max() > worst[0]:
                worst = (float(d.max()), (act.name, f), int((d > 0.005).sum()),
                         [(int(piece[anchors[k]]), np.round(co[anchors[k]], 2).tolist()) for k in np.where(d > 0.005)[0]])
    gap = {'buried_anchor_verts': int(len(anchors)), 'max_outside_m': round(worst[0], 4), 'at': worst[1:], 'per_clip_max_outside_m': per}
    print('GAP', json.dumps(gap))
# materials
if not TEX:
    mats = []
    for i, c in enumerate([(0.62, 0.62, 0.62, 1), (0.85, 0.3, 0.22, 1), (0.25, 0.45, 0.9, 1)]):
        m = bpy.data.materials.new(f'k{i}'); m.diffuse_color = c; mats.append(m)
    me.materials.clear()
    for m in mats:
        me.materials.append(m)
    if piece is not None:
        pf = np.array([max(piece[i] for i in p.vertices) for p in me.polygons])
        me.polygons.foreach_set('material_index', np.select([pf == 3, pf == 4], [1, 2], 0).tolist())
sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'TEXTURE' if TEX else 'MATERIAL'
sh.show_backface_culling = False
sc.render.resolution_x = sc.render.resolution_y = 640
sc.world = bpy.data.worlds.new('W'); sc.world.color = (0.33, 0.35, 0.38)
cd = bpy.data.cameras.new('c'); cd.type = 'ORTHO'; cd.ortho_scale = 3.6
cam = bpy.data.objects.new('c', cd); sc.collection.objects.link(cam); sc.camera = cam
views = {'side': Vector((1, 0, 0.05)), 'back': Vector((0, 1, 0.1)), 'q34b': Vector((0.8, 0.9, 0.35))}
for pn, pose in poses.items():
    if pose is None:
        rig.animation_data.action = None
        for pb in rig.pose.bones:
            pb.matrix_basis.identity()
    else:
        rig.animation_data.action = bpy.data.actions[pose[0]]
        sc.frame_set(pose[1])
    bpy.context.view_layer.update()
    c = rig.matrix_world @ rig.pose.bones['XspineC'].head + Vector((0, 0.4, 0.15))
    for vn, d in views.items():
        cam.location = c + d.normalized() * 10
        cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
        sc.render.filepath = os.path.join(OUT, f'{PRE}_{pn}_{vn}.png')
        bpy.ops.render.render(write_still=True)
json.dump({'poses': poses, 'gap': gap}, open(os.path.join(OUT, f'{PRE}_wing_review.json'), 'w'), indent=1)
