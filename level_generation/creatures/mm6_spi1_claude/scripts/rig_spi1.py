"""Spider rig from the Meshy Smart Topology mesh. Saves work/rig_v1.blend. Forward -Y, up +Z, spider's left +X.

The mesh arrives as separate rigid pieces (work/components.json from components.py): one body (cephalothorax +
abdomen), an abdomen shell, two chelicerae, small head bumps, and per leg a femur, tibia and tarsus piece. That is an
exoskeleton, so every piece is bound 100 % to one bone: leg joints sit where consecutive pieces meet, the body piece
blends Thorax -> Abdomen over the waist (pedicel).
Bones: Thorax (root), Abdomen, Fang_L/R, per leg L1..L4 / R1..R4 (front to back): Femur, Tibia, Tarsus."""
import bpy, os, json
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
zmin = min(v.co.z for v in mesh.data.vertices)
for v in mesh.data.vertices:
    v.co.z -= zmin
mesh.name = mesh.data.name = 'Spider'
for p in mesh.data.polygons:
    p.use_smooth = True

info = json.load(open(os.path.join(HERE, 'work', 'components.json')))
label = np.load(os.path.join(HERE, 'work', 'component_labels.npy'))
co = np.array([tuple(v.co) for v in mesh.data.vertices])
# Leg pieces front to back (femur, tibia, tarsus), from components.json.
LEGS = {'L1': (10, 17, 19), 'L2': (20, 22, 8), 'L3': (13, 25, 24), 'L4': (4, 28, 2),
        'R1': (3, 18, 7), 'R2': (11, 30, 16), 'R3': (6, 23, 21), 'R4': (15, 29, 0)}
BODY, SHELL, FANG = 1, 9, {'L': 5, 'R': 12}


def pts(k):
    return co[label == k]


def junction(a, b):
    """Joint between two consecutive pieces: midpoint of the 20 closest vertex pairs."""
    pa, pb = pts(a), pts(b)
    d = np.linalg.norm(pa[:, None, :] - pb[None, :, :], axis=2)
    flat = np.argsort(d, axis=None)[:20]
    i, j = np.unravel_index(flat, d.shape)
    return Vector(((pa[i] + pb[j]) / 2).mean(0))


body = pts(BODY)
pedicel = Vector((0.0, 0.0, float(np.median(body[np.abs(body[:, 1]) < 0.02, 2]))))
thorax_front = Vector((0.0, -0.20, 0.27))
abdomen_end = Vector((0.0, 0.37, 0.47))
JOINTS = {}
for leg, (femur, tibia, tarsus) in LEGS.items():
    # Hip: where the femur meets the body or a side bump (coxa), whichever is closer.
    hip = min((junction(piece, femur) for piece in (BODY, 14, 26)),
              key=lambda j: min(np.linalg.norm(pts(femur) - np.array(j), axis=1)))
    knee, ankle = junction(femur, tibia), junction(tibia, tarsus)
    q = pts(tarsus)
    foot = Vector(q[np.argsort(q[:, 2])[:8]].mean(0))
    JOINTS[leg] = [hip, knee, ankle, foot]

arm = bpy.data.armatures.new('Spider_Rig')
rig = bpy.data.objects.new('Spider_Rig', arm)
bpy.context.scene.collection.objects.link(rig)
bpy.context.view_layer.objects.active = rig
for o in bpy.data.objects:
    o.select_set(o == rig)
bpy.ops.object.mode_set(mode='EDIT')
eb = arm.edit_bones


def bone(name, head, tail, parent=None, connect=False):
    b = eb.new(name); b.head = head; b.tail = tail; b.parent = parent; b.use_connect = connect
    b.align_roll(Vector((0, 0, 1)) if abs((tail - head).normalized().z) < 0.9 else Vector((0, -1, 0)))
    return b


thorax = bone('Thorax', pedicel, thorax_front)
bone('Abdomen', pedicel, abdomen_end, thorax)
for side, k in FANG.items():
    p = pts(k)
    top = Vector(p[np.argsort(-p[:, 2])[:10]].mean(0)); tip = Vector(p[np.argsort(p[:, 2])[:10]].mean(0))
    bone(f'Fang_{side}', top, tip, thorax)
for leg, (hip, knee, ankle, foot) in JOINTS.items():
    f = bone(f'Femur_{leg}', hip, knee, thorax)
    t = bone(f'Tibia_{leg}', knee, ankle, f, True)
    bone(f'Tarsus_{leg}', ankle, foot, t, True)
bpy.ops.object.mode_set(mode='OBJECT')

# Rigid weights per piece; the body piece blends Thorax -> Abdomen across the waist.
groups = {b.name: mesh.vertex_groups.new(name=b.name) for b in arm.bones}
owner = {SHELL: 'Abdomen', FANG['L']: 'Fang_L', FANG['R']: 'Fang_R'}
for leg, pieces in LEGS.items():
    for piece, part in zip(pieces, ('Femur', 'Tibia', 'Tarsus')):
        owner[piece] = f'{part}_{leg}'
for index, v in enumerate(mesh.data.vertices):
    k = int(label[index])
    if k == BODY:
        w = float(np.clip((v.co.y - (pedicel.y - 0.02)) / 0.06, 0, 1))
        if w < 1: groups['Thorax'].add([index], 1 - w, 'REPLACE')
        if w > 0: groups['Abdomen'].add([index], w, 'REPLACE')
    else:
        groups[owner.get(k, 'Thorax')].add([index], 1.0, 'REPLACE')
mod = mesh.modifiers.new('Armature', 'ARMATURE'); mod.object = rig
mesh.parent = rig
json.dump({leg: [list(map(lambda x: round(x, 4), p)) for p in pts_] for leg, pts_ in JOINTS.items()},
          open(os.path.join(HERE, 'work', 'joints.json'), 'w'), indent=1)
print('RIGGED bones', len(arm.bones), 'unweighted', sum(1 for v in mesh.data.vertices if not v.groups),
      'pedicel', tuple(round(x, 3) for x in pedicel))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'rig_v1.blend'))
