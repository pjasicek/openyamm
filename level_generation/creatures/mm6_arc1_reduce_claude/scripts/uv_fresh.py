"""Fresh UVs for the body retexture of the reduced archer (work/ladder_<label>.blend, candidate REA_CAND).
Each face is head or body by where its installed UVs sit (from the source faces: the head set
keeps its accepted texture; work/headchart_label.npy), with the source component of the nearest source face (pieces.py ids, for the material
classes). UV layers on the candidate:
- OldUV: the installed atlas UVs (the head texels are remapped from them);
- Upload: body islands in [0, 0.94]^2, head islands in the 0.06 corner, so Meshy sees the whole figure;
- UVMap (runtime, 2048 x 1024 atlas): body islands in the left square, head islands in the right square.
Writes work/retex_<label>.blend, texturing/arc1_body_upload_<label>.glb (rest pose, Upload only), work/cand_export.glb
(skinned, UVMap only; for swap_lod0.py) and work/retex_faces_<label>.npz (per corner rest positions and the three UV
sets; per face head and component). Usage: blender -b -P uv_fresh.py -- <label> <cand object>"""
import bpy, bmesh, math, os, sys
import numpy as np
from mathutils.kdtree import KDTree
label, cand_name = sys.argv[sys.argv.index('--') + 1:][:2]
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W = lambda *p: os.path.join(HERE, *p)
bpy.ops.wm.open_mainfile(filepath=W('work', f'ladder_{label}.blend'))
rig = bpy.data.objects['Rig']; src = bpy.data.objects['Body']; cand = bpy.data.objects[cand_name]
rig.animation_data.action = None
for b in rig.pose.bones:
    b.matrix_basis.identity()
bpy.context.view_layer.update()
me = cand.data
for o in bpy.data.objects:
    if o.type == 'MESH' and o not in (cand, src):
        bpy.data.objects.remove(o, do_unlink=True)

# head/body by installed chart, component by nearest source face
labimg = np.load(W('work', 'headchart_label.npy'))
LH, LW = labimg.shape
old = me.uv_layers[0]; old.name = 'OldUV'
comp_src = np.load(W('work', 'components.npy'))
kd = KDTree(len(src.data.polygons))
for p in src.data.polygons:
    kd.insert(p.center, p.index)
kd.balance()
head = np.zeros(len(me.polygons), np.int32); comp = np.zeros(len(me.polygons), np.int32)
for p in me.polygons:
    uv = np.mean([tuple(old.data[li].uv) for li in p.loop_indices], axis=0)
    x = min(max(int(uv[0] % 1 * LW), 0), LW - 1); y = min(max(int((1 - uv[1] % 1) * LH), 0), LH - 1)
    head[p.index] = int(labimg[y, x])
    comp[p.index] = int(comp_src[kd.find(p.center)[1]])
for name, arr in (('head', head), ('comp', comp)):
    a = me.attributes.get(name) or me.attributes.new(name, 'INT', 'FACE')
    a.data.foreach_set('value', arr.tolist())
print('FACES head', int(head.sum()), 'body', int((head == 0).sum()))


def project(layer, sel, angle):
    """Smart UV Project + pack of the selected faces into their own 0..1 layout on a new layer."""
    me.uv_layers.new(name=layer); me.uv_layers.active = me.uv_layers[layer]
    for o in bpy.data.objects:
        o.select_set(o == cand)
    bpy.context.view_layer.objects.active = cand
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='DESELECT'); bpy.ops.object.mode_set(mode='OBJECT')
    for p in me.polygons:
        p.select = bool(sel[p.index])
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.uv.smart_project(angle_limit=math.radians(angle), island_margin=0.008, scale_to_bounds=False)
    bpy.ops.uv.pack_islands(shape_method='CONCAVE', margin=0.008)
    bpy.ops.object.mode_set(mode='OBJECT')


project('BodyLayout', head == 0, float(os.environ.get('REA_BODY_ANGLE', '70')))
project('HeadLayout', head == 1, float(os.environ.get('REA_HEAD_ANGLE', '66')))
BL, HL = me.uv_layers['BodyLayout'], me.uv_layers['HeadLayout']
for name in ('Upload', 'UVMap'):
    me.uv_layers.new(name=name)
up, rt = me.uv_layers['Upload'], me.uv_layers['UVMap']
for p in me.polygons:
    for li in p.loop_indices:
        if head[p.index]:
            u, v = HL.data[li].uv
            up.data[li].uv = (0.94 + 0.06 * u, 0.06 * v); rt.data[li].uv = (0.5 + 0.5 * u, v)
        else:
            u, v = BL.data[li].uv
            up.data[li].uv = (0.94 * u, 0.94 * v); rt.data[li].uv = (0.5 * u, v)

# per-corner data for the texture compose
me.calc_loop_triangles()
co = np.array([tuple(cand.matrix_world @ v.co) for v in me.vertices])
tris = list(me.loop_triangles)
# layers by name: a held layer reference goes stale once new layers are added
take = lambda layer: np.array([[tuple(layer.data[l].uv) for l in t.loops] for t in tris], np.float32)
np.savez_compressed(W('work', f'retex_faces_{label}.npz'), pos=np.array([[co[v] for v in t.vertices] for t in tris], np.float32),
                    old=take(me.uv_layers['OldUV']), upload=take(me.uv_layers['Upload']), runtime=take(me.uv_layers['UVMap']),
                    head=np.array([head[t.polygon_index] for t in tris]), comp=np.array([comp[t.polygon_index] for t in tris]))
bpy.ops.wm.save_as_mainfile(filepath=W('work', f'retex_{label}.blend'))

# upload: rest pose, no skin, Upload layer only
ob = cand.copy(); ob.data = me.copy(); bpy.context.scene.collection.objects.link(ob)
ob.parent = None; ob.matrix_world = cand.matrix_world.copy()
for m in list(ob.modifiers):
    ob.modifiers.remove(m)
ob.vertex_groups.clear()
for l in [l.name for l in ob.data.uv_layers if l.name != 'Upload']:
    ob.data.uv_layers.remove(ob.data.uv_layers[l])
mat = bpy.data.materials.new('Neutral'); mat.use_nodes = True
ob.data.materials.clear(); ob.data.materials.append(mat)
for o in bpy.data.objects:
    o.select_set(o == ob)
bpy.context.view_layer.objects.active = ob
os.makedirs(W('texturing'), exist_ok=True)
bpy.ops.export_scene.gltf(filepath=W('texturing', f'arc1_body_upload_{label}.glb'), use_selection=True, export_format='GLB',
                          export_yup=True, export_animations=False, export_skins=False, export_morph=False,
                          export_attributes=False)
print('UPLOAD', len(ob.data.polygons), 'faces')
bpy.data.objects.remove(ob, do_unlink=True)

# runtime candidate: skinned, UVMap only (export_cand.py with the new layout)
for l in [l.name for l in me.uv_layers if l.name != 'UVMap']:
    me.uv_layers.remove(me.uv_layers[l])
g = cand.vertex_groups.get('ReduceProtect')
if g:
    cand.vertex_groups.remove(g)
src.name = 'Source_Body'; cand.name = 'Archer'
bpy.ops.object.select_all(action='DESELECT'); cand.select_set(True); rig.select_set(True)
bpy.context.view_layer.objects.active = rig
bpy.ops.export_scene.gltf(filepath=W('work', 'cand_export.glb'), use_selection=True, export_format='GLB', export_yup=True,
                          export_animations=False, export_skins=True, export_attributes=False, export_morph=False,
                          export_image_format='NONE')
print('CAND', sum(len(p.vertices) - 2 for p in me.polygons))
