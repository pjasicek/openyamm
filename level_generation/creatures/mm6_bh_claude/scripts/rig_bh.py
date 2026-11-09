"""Flying Eye rig from the Meshy Smart Topology mesh. Saves work/rig_v1.blend. Forward -Y, up +Z, left +X.

A flying head with no limbs. Bones: Body (root, hover pivot at the head centre), Head (horns, brow, upper teeth and
fangs, crest), Jaw (lower lip, lower teeth, chin; blended into the head across the mouth line), Eye (the separate
eyeball piece, for looking around), Tendrils (the hanging points under the chin, for sway).
Pieces come from work/components.json (components.py): 1 main head, 3 eyeball (the painted iris sits on its front),
2 lower lip, 7/11/14 lower teeth, the rest upper gum and teeth, fangs, eye socket ring and crest. The mesh is grounded so the tendril tips sit at z 0."""
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
mesh.name = mesh.data.name = 'Eye'
for p in mesh.data.polygons:
    p.use_smooth = True

label = np.load(os.path.join(HERE, 'work', 'component_labels.npy'))
co = np.array([tuple(v.co) for v in mesh.data.vertices])
MAIN, EYEBALL, LOWER = 1, 3, {2, 7, 11, 14}
main = co[label == MAIN]
centre = Vector(((main.min(0) + main.max(0)) / 2).tolist())
eyeball = co[label == EYEBALL]
eye = Vector(((eyeball.min(0) + eyeball.max(0)) / 2).tolist())
lower_teeth = co[np.isin(label, [7, 11])]
upper_teeth = co[np.isin(label, [5, 6, 9, 10])]
mouth_z = float((lower_teeth[:, 2].max() + upper_teeth[:, 2].min()) / 2)
front_y = float(co[label == 2][:, 1].mean())
chin = Vector((0.0, front_y + 0.05, float(lower_teeth[:, 2].min()) - 0.02))
tendril_top, tendril_tip = 0.20, 0.0

arm = bpy.data.armatures.new('Eye_Rig')
rig = bpy.data.objects.new('Eye_Rig', arm)
bpy.context.scene.collection.objects.link(rig)
bpy.context.view_layer.objects.active = rig
for o in bpy.data.objects:
    o.select_set(o == rig)
bpy.ops.object.mode_set(mode='EDIT')
eb = arm.edit_bones


def bone(name, head, tail, parent=None):
    b = eb.new(name); b.head = head; b.tail = tail; b.parent = parent
    b.align_roll(Vector((0, 0, 1)) if abs((tail - head).normalized().z) < 0.9 else Vector((0, -1, 0)))
    return b


body = bone('Body', centre, centre + Vector((0, 0, 0.15)))
head = bone('Head', centre, centre + Vector((0, -0.2, 0.0)), body)
jaw_pivot = Vector((0.0, front_y + 0.18, mouth_z + 0.02))
bone('Jaw', jaw_pivot, chin, head)
bone('EyeBall', eye + Vector((0, 0.06, 0)), eye, head)
bone('Tendrils', Vector((0.0, front_y + 0.06, tendril_top)), Vector((0.0, front_y + 0.06, tendril_tip)), head)
bpy.ops.object.mode_set(mode='OBJECT')


def smooth(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


groups = {b.name: mesh.vertex_groups.new(name=b.name) for b in arm.bones if b.name != 'Body'}
y, z = co[:, 1], co[:, 2]
front = smooth(front_y + 0.25, front_y + 0.12, y)               # 1 at the face, 0 behind it
jaw_w = smooth(mouth_z + 0.01, mouth_z - 0.05, z) * front
tendril_w = smooth(tendril_top, tendril_top - 0.10, z)
for index in range(len(co)):
    k = int(label[index])
    if k == EYEBALL:
        weights = {'EyeBall': 1.0}
    elif k in LOWER:
        weights = {'Jaw': 1.0}
    elif k == MAIN:
        t = float(tendril_w[index]); j = float(jaw_w[index]) * (1 - t)
        weights = {'Tendrils': t, 'Jaw': j, 'Head': max(0.0, 1 - t - j)}
    else:
        weights = {'Head': 1.0}
    for name, w in weights.items():
        if w > 1e-4:
            groups[name].add([index], w, 'REPLACE')
mod = mesh.modifiers.new('Armature', 'ARMATURE'); mod.object = rig
mesh.parent = rig
info = {'centre': list(centre), 'eye': list(eye), 'mouth_z': mouth_z, 'front_y': front_y,
        'height': float(co[:, 2].max()), 'zmin_offset': float(zmin)}
json.dump(info, open(os.path.join(HERE, 'work', 'rig_info.json'), 'w'), indent=1)
print('RIGGED bones', len(arm.bones), 'unweighted', sum(1 for v in mesh.data.vertices if not v.groups), json.dumps(info))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'rig_v1.blend'))
