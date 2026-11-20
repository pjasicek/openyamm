"""Rat: import the Meshy Smart Topology mesh, ground it, build a quadruped deform skeleton from joints traced on
the mesh (leg/body slices), skin it with Blender automatic (heat) weights. Saves work/rig_v1.blend.
Forward is -Y, up +Z, character left +X."""
import bpy, os, sys
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
zmin = min((mesh.matrix_world @ v.co).z for v in mesh.data.vertices)
mesh.location.z -= zmin
bpy.ops.object.transform_apply(location=True)
mesh.name = mesh.data.name = 'Rat'
for p in mesh.data.polygons:
    p.use_smooth = True
Z = -zmin                                              # joint z values below are in the original Meshy frame


def P(x, y, z):
    return Vector((x, y, z + Z))


CHAINS = {
    # name: (parent, [joint points...]) -> bones name1..nN between consecutive points
    'Spine': (None, [P(0, 0.10, 0.0), P(0, 0.02, 0.0), P(0, -0.08, 0.01), P(0, -0.18, 0.01)]),
    'Neck': ('Spine3', [P(0, -0.18, 0.01), P(0, -0.27, 0.0)]),
    'Head': ('Neck1', [P(0, -0.27, 0.0), P(0, -0.49, 0.0)]),
    'Tail': ('Spine1', [P(0, 0.12, -0.015), P(0, 0.18, -0.086), P(0, 0.24, -0.108), P(0, 0.31, -0.110),
                       P(0, 0.38, -0.111), P(0, 0.44, -0.110), P(0, 0.50, -0.095)]),
}
for side, s in (('L', 1), ('R', -1)):
    CHAINS['Front_' + side] = ('Spine3', [P(s * 0.065, -0.20, 0.015), P(s * 0.085, -0.15, -0.04),
                                          P(s * 0.10, -0.15, -0.10), P(s * 0.115, -0.27, -0.12)])
    CHAINS['Hind_' + side] = ('Spine1', [P(s * 0.07, 0.05, 0.01), P(s * 0.09, -0.04, -0.04),
                                         P(s * 0.085, 0.0, -0.11), P(s * 0.09, -0.13, -0.125)])
NAMES = {'Spine': ['Spine1', 'Spine2', 'Spine3'], 'Neck': ['Neck1'], 'Head': ['Head'],
         'Tail': [f'Tail{i}' for i in range(1, 7)]}
for side in ('L', 'R'):
    NAMES['Front_' + side] = [f'UpperArm_{side}', f'ForeArm_{side}', f'FrontPaw_{side}']
    NAMES['Hind_' + side] = [f'Thigh_{side}', f'Shin_{side}', f'HindPaw_{side}']

arm_data = bpy.data.armatures.new('Rat_Rig')
rig = bpy.data.objects.new('Rat_Rig', arm_data)
bpy.context.scene.collection.objects.link(rig)
bpy.context.view_layer.objects.active = rig
for o in bpy.data.objects:
    o.select_set(o == rig)
bpy.ops.object.mode_set(mode='EDIT')
eb = arm_data.edit_bones
order = ['Spine', 'Neck', 'Head', 'Tail', 'Front_L', 'Front_R', 'Hind_L', 'Hind_R']
for key in order:
    parent, pts = CHAINS[key]
    prev = eb[parent] if parent else None
    for i, name in enumerate(NAMES[key]):
        b = eb.new(name)
        b.head = pts[i]; b.tail = pts[i + 1]
        b.align_roll(Vector((0, 0, 1)) if key in ('Spine', 'Neck', 'Head', 'Tail') else Vector((0, -1, 0)))
        b.parent = prev
        b.use_connect = prev is not None and i > 0
        prev = b
bpy.ops.object.mode_set(mode='OBJECT')
# automatic (heat) weights
for o in bpy.data.objects:
    o.select_set(o in (mesh, rig))
bpy.context.view_layer.objects.active = rig
bpy.ops.object.parent_set(type='ARMATURE_AUTO')
empty = [v.index for v in mesh.data.vertices if not v.groups]
print('RIGGED bones', len(arm_data.bones), 'unweighted verts', len(empty))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'rig_v1.blend'))
