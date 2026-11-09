"""MM7 bat rig: import the Meshy Smart Topology return, ground it (lowest point z=0), build the skeleton from joints
measured on the mesh (work/raw_st1.npz plots), skin it with Blender automatic weights and give every leftover
vertex the weights of its nearest weighted vertex. Wing joints are top-view (x, y) with z sampled from the wing
sheet, so the bones lie in the membrane. Forward -Y, up +Z, character left +X. Saves work/rig_v1.blend."""
import bpy, os
import numpy as np
from mathutils import Vector
from mathutils.kdtree import KDTree

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
mesh.data.materials.clear()
for p in mesh.data.polygons:
    p.use_smooth = True
co = np.array([tuple(v.co) for v in mesh.data.vertices])


def zcol(x, y, r=0.015):
    m = (np.abs(co[:, 0] - x) < r) & (np.abs(co[:, 1] - y) < r)
    if m.sum() < 2:
        m = np.linalg.norm(co[:, :2] - (x, y), axis=1) < 0.04
    return float(co[m, 2].mean())


def B(x, y, z):                      # body joints, z in the Meshy frame
    return Vector((x, y, z - Z0))


def W(x, y):                         # wing joints, z from the sheet
    return Vector((x, y, zcol(x, y)))


CX = 0.008
CHAINS = {'Spine': (None, [B(CX, 0.06, -0.08), B(CX, 0.0, -0.078), B(CX, -0.06, -0.075)]),
          'Neck': ('Spine2', [B(CX, -0.06, -0.075), B(0.015, -0.098, -0.062)]),
          'Head': ('Neck1', [B(0.015, -0.098, -0.062), B(0.03, -0.172, -0.076)])}
NAMES = {'Spine': ['Spine1', 'Spine2'], 'Neck': ['Neck1'], 'Head': ['Head']}
FINGERS = ((0.465, -0.012), (0.437, 0.030), (0.395, 0.092), (0.335, 0.074))
LEG = {'L': [(0.018, 0.06, -0.092), (0.024, 0.105, -0.106), (0.022, 0.158, -0.134)],
       'R': [(-0.026, 0.06, -0.090), (-0.046, 0.105, -0.106), (-0.064, 0.150, -0.128)]}
for side, s in (('L', 1), ('R', -1)):
    sh = B(CX + s * 0.04, -0.06, -0.07)
    elbow, wrist = W(s * 0.13, -0.038), W(s * 0.215, -0.045)
    CHAINS['Arm_' + side] = ('Spine2', [sh, elbow, wrist])
    NAMES['Arm_' + side] = [f'UpperArm_{side}', f'ForeArm_{side}']
    for k, (tx, ty) in enumerate(FINGERS):
        mx, my = 0.215 + (tx - 0.215) * 0.55, -0.045 + (ty + 0.045) * 0.55
        CHAINS[f'Finger{k + 1}_{side}'] = (f'ForeArm_{side}', [wrist, W(s * mx, my), W(s * tx, ty)])
        NAMES[f'Finger{k + 1}_{side}'] = [f'Finger{k + 1}a_{side}', f'Finger{k + 1}b_{side}']
    CHAINS['Leg_' + side] = ('Spine1', [B(*p) for p in LEG[side]])
    NAMES['Leg_' + side] = [f'Thigh_{side}', f'Shin_{side}']
    CHAINS['Ear_' + side] = ('Head', [B(0.015 + s * 0.022, -0.105, -0.035), B(0.015 + s * 0.06, -0.095, 0.02)])
    NAMES['Ear_' + side] = [f'Ear_{side}']

arm_data = bpy.data.armatures.new('Bat_Rig')
rig = bpy.data.objects.new('Bat_Rig', arm_data)
bpy.context.scene.collection.objects.link(rig)
bpy.context.view_layer.objects.active = rig
for o in bpy.data.objects:
    o.select_set(o == rig)
bpy.ops.object.mode_set(mode='EDIT')
eb = arm_data.edit_bones
order = ['Spine', 'Neck', 'Head'] + [f'{k}_{s}' for s in 'LR'
                                     for k in ('Arm', 'Finger1', 'Finger2', 'Finger3', 'Finger4', 'Leg', 'Ear')]
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
socket = eb.new('HeadSocket'); socket.head = B(0.03, -0.165, -0.07); socket.tail = B(0.03, -0.185, -0.07)
socket.parent = eb['Head']; socket.use_deform = False
bpy.ops.object.mode_set(mode='OBJECT')
for o in bpy.data.objects:
    o.select_set(o in (mesh, rig))
bpy.context.view_layer.objects.active = rig
bpy.ops.object.parent_set(type='ARMATURE_AUTO')
# leftovers (heat weighting can miss loose pieces): copy the nearest weighted vertex
groups = {g.index: g.name for g in mesh.vertex_groups}
weighted = np.array([bool(v.groups) and sum(g.weight for g in v.groups) > 1e-4 for v in mesh.data.vertices])
empty = np.nonzero(~weighted)[0]
if len(empty):
    idx = np.nonzero(weighted)[0]; tree = KDTree(len(idx))
    for i, j in enumerate(idx):
        tree.insert(co[j], i)
    tree.balance()
    for e in empty:
        s = idx[tree.find(co[e])[1]]
        for g in mesh.data.vertices[s].groups:
            mesh.vertex_groups[g.group].add([int(e)], g.weight, 'REPLACE')
print('RIGGED bones', len(arm_data.bones), 'filled', len(empty))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'rig_v1.blend'))
