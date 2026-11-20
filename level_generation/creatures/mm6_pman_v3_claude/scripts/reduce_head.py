"""Triangle reduction of the grafted head on the textured master (work/rig_v6.blend, edited in place; run by
build_runtime.sh before the export). The head (face attribute 'head') keeps its own UV layer and texture, so it can be
reduced without touching the body or its Meshy retexture. Only the hair is collapsed: the face below the brows
(creature.json head_reduce.protect_above_eye over the eye line in the front half; protect_all_around over it
all round: ears, nape), the neck band above the graft
(protect_neck over work/graft.json z_seam) and the seam itself stay. The step only acts above head_reduce.target
triangles, so running it again changes nothing. Seam vertices are re-merged with the body after the join, so the
neck keeps one smooth normal. Args: none"""
import bpy, bmesh, os, sys, json
import numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CJ = json.load(open(os.path.join(HERE, 'creature.json'))); HR = CJ['head_reduce']
G = json.load(open(os.path.join(HERE, 'work', 'graft.json'))); ZS = G.get('z_seam', G['z_cut'])
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'rig_v6.blend'))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data
rig.animation_data_create(); rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.update()
hd = np.zeros(len(me.polygons), np.int32); me.attributes['head'].data.foreach_get('value', hd)
tris = sum(len(p.vertices) - 2 for p in me.polygons if hd[p.index])
co = np.array([tuple(v.co) for v in me.vertices])
hv = sorted({v for p in me.polygons if hd[p.index] for v in p.vertices})
body_v = {v for p in me.polygons if not hd[p.index] for v in p.vertices}
seam = set(hv) & body_v
cy = (co[hv, 1].min() + co[hv, 1].max()) / 2
AR = HR.get('protect_all_around', -1.0)               # pm3: the ears and nape too (they stretched with front-only)
keep = {v for v in hv if (co[v, 2] < CJ['eye_z'] + HR['protect_above_eye'] and co[v, 1] < cy)
        or co[v, 2] < CJ['eye_z'] + AR or co[v, 2] < ZS + HR['protect_neck']} | seam
if HR.get('lod_protect'):                             # the face also survives the LOD builder (--protect-points)
    json.dump([[round(float(x), 6) for x in (body.matrix_world @ me.vertices[v].co)] for v in sorted(keep)],
              open(os.path.join(HERE, 'work', 'lod_protect_points.json'), 'w'))
if tris <= HR['target']:
    print('HEADREDUCE head', tris, 'triangles, at or below the target', HR['target'], ': nothing to do')
    sys.exit(0)
allow = body.vertex_groups.new(name='_reduce_allow')
allow.add([v for v in hv if v not in keep], 1.0, 'REPLACE')
for o in bpy.data.objects:
    o.select_set(o == body)
bpy.context.view_layer.objects.active = body
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='DESELECT'); bpy.ops.object.mode_set(mode='OBJECT')
for p in me.polygons:
    p.select = bool(hd[p.index])
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.separate(type='SELECTED'); bpy.ops.object.mode_set(mode='OBJECT')
head = next(o for o in bpy.context.selected_objects if o is not body)
dec = head.modifiers.new('dec', 'DECIMATE'); dec.decimate_type = 'COLLAPSE'
dec.ratio = HR['target'] / tris; dec.vertex_group = '_reduce_allow'; dec.vertex_group_factor = 1.0
for o in bpy.data.objects:
    o.select_set(o == head)
bpy.context.view_layer.objects.active = head
bpy.ops.object.modifier_move_to_index(modifier='dec', index=0)
bpy.ops.object.modifier_apply(modifier='dec')
after = sum(len(p.vertices) - 2 for p in head.data.polygons)
for o in bpy.data.objects:
    o.select_set(o in (body, head))
bpy.context.view_layer.objects.active = body
bpy.ops.object.join()
me = body.data
bm = bmesh.new(); bm.from_mesh(me)
seam_co = co[sorted(seam)] if seam else np.zeros((0, 3))
from mathutils.kdtree import KDTree
kd = KDTree(len(seam_co))
for i, c in enumerate(seam_co):
    kd.insert(c, i)
kd.balance()
near = [v for v in bm.verts if len(seam_co) and kd.find(v.co)[2] < 1e-5]
bmesh.ops.remove_doubles(bm, verts=near, dist=1e-5)
bm.to_mesh(me); bm.free()
body.vertex_groups.remove(body.vertex_groups['_reduce_allow'])
me.uv_layers.active = me.uv_layers['UVMap']
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'rig_v6.blend'))
print('HEADREDUCE head triangles', tris, '->', after, 'protected verts', len(keep), 'seam verts re-merged', len(near))
