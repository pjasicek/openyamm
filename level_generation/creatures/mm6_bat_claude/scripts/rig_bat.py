"""Bat: import the Meshy Smart Topology mesh, ground it (lowest point z=0), build a bat skeleton and skin it with
Blender automatic (heat) weights. Joints in the wings are given as top-view (x, y); z is sampled from the membrane
(mean z of mesh vertices in a 1.5 cm column), so the bones lie inside the sheet. Saves work/rig_v1.blend.
Forward -Y, up +Z, character left +X."""
import bpy, os
import numpy as np
from mathutils import Vector

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.join(HERE, 'meshy/smart_topology_v1/model_urls_glb.glb'))
mesh = next(o for o in bpy.data.objects if o.type == 'MESH')
for o in list(bpy.data.objects):
    if o is not mesh:
        bpy.data.objects.remove(o, do_unlink=True)
mesh.parent = None
bpy.context.view_layer.objects.active = mesh
mesh.select_set(True)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
co = np.array([tuple(v.co) for v in mesh.data.vertices])
Z0 = co[:, 2].min()
mesh.location.z -= Z0
bpy.ops.object.transform_apply(location=True)
mesh.name = mesh.data.name = 'Bat'
for p in mesh.data.polygons:
    p.use_smooth = True
co = np.array([tuple(v.co) for v in mesh.data.vertices])


def zcol(x, y, r=0.015):
    m = (np.abs(co[:, 0] - x) < r) & (np.abs(co[:, 1] - y) < r)
    if m.sum() < 2:
        m = np.linalg.norm(co[:, :2] - (x, y), axis=1) < 0.04
    return float(co[m, 2].mean())


def B(x, y, z):                      # body joints: z given in the original Meshy frame
    return Vector((x, y, z - Z0))


def W(x, y):                         # wing joints: z sampled from the membrane
    return Vector((x, y, zcol(x, y)))


CHAINS = {'Spine': (None, [B(0, 0.05, -0.05), B(0, -0.02, 0.0), B(0, -0.08, 0.035)]),
          'Neck': ('Spine2', [B(0, -0.08, 0.035), B(0, -0.13, 0.06)]),
          'Head': ('Neck1', [B(0, -0.13, 0.06), B(0, -0.255, 0.045)])}
NAMES = {'Spine': ['Spine1', 'Spine2'], 'Neck': ['Neck1'], 'Head': ['Head']}
for side, s in (('L', 1), ('R', -1)):
    sh = B(s * 0.055, -0.085, 0.035)
    CHAINS['Arm_' + side] = ('Spine2', [sh, W(s * 0.17, -0.105), W(s * 0.31, -0.145)])
    NAMES['Arm_' + side] = [f'UpperArm_{side}', f'ForeArm_{side}']
    for k, (mid, tip) in enumerate((((0.42, 0.01), (0.495, 0.175)), ((0.36, -0.02), (0.38, 0.095)),
                                    ((0.27, -0.03), (0.21, 0.09)))):
        CHAINS[f'Finger{k + 1}_{side}'] = (f'ForeArm_{side}', [W(s * 0.31, -0.145), W(s * mid[0], mid[1]),
                                                                W(s * tip[0], tip[1])])
        NAMES[f'Finger{k + 1}_{side}'] = [f'Finger{k + 1}a_{side}', f'Finger{k + 1}b_{side}']
    CHAINS['Leg_' + side] = ('Spine1', [B(s * 0.04, 0.06, -0.07), B(s * 0.045, 0.13, -0.10), B(s * 0.03, 0.225, -0.12)])
    NAMES['Leg_' + side] = [f'Thigh_{side}', f'Shin_{side}']
    CHAINS['Ear_' + side] = ('Head', [B(s * 0.035, -0.16, 0.10), B(s * 0.07, -0.15, 0.165)])
    NAMES['Ear_' + side] = [f'Ear_{side}']

arm_data = bpy.data.armatures.new('Bat_Rig')
rig = bpy.data.objects.new('Bat_Rig', arm_data)
bpy.context.scene.collection.objects.link(rig)
bpy.context.view_layer.objects.active = rig
for o in bpy.data.objects:
    o.select_set(o == rig)
bpy.ops.object.mode_set(mode='EDIT')
eb = arm_data.edit_bones
order = ['Spine', 'Neck', 'Head'] + [f'{k}_{s}' for s in 'LR' for k in ('Arm', 'Finger1', 'Finger2', 'Finger3', 'Leg', 'Ear')]
for key in order:
    parent, pts = CHAINS[key]
    prev = eb[parent] if parent else None
    for i, name in enumerate(NAMES[key]):
        b = eb.new(name)
        b.head = pts[i]; b.tail = pts[i + 1]
        b.align_roll(Vector((0, 0, 1)))
        b.parent = prev
        b.use_connect = prev is not None and i > 0
        prev = b
bpy.ops.object.mode_set(mode='OBJECT')
for o in bpy.data.objects:
    o.select_set(o in (mesh, rig))
bpy.context.view_layer.objects.active = rig
bpy.ops.object.parent_set(type='ARMATURE_AUTO')
empty = [v.index for v in mesh.data.vertices if not v.groups]
print('RIGGED bones', len(arm_data.bones), 'unweighted verts', len(empty))
for k in ('Arm_L', 'Finger1_L', 'Finger2_L', 'Finger3_L'):
    print('JOINTS', k, [tuple(round(c, 3) for c in p) for p in CHAINS[k][1]])
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'rig_v1.blend'))
