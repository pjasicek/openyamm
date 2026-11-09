"""Gate copy + the held forearm: imports an attachment GLB (node 'Sword'), places it by the body GLB's 'Sword' joint
(the engine's attachment rule: the attachment's node space = the joint's global bind transform), converts glTF to
Blender axes, skins it 100 % to the 'Sword' bone and joins it into Body as piece 1000 / garment 9 (what the m438
g6_prop.py samples as the prop). Args: -- <gate blend> <body glb> <forearm glb>"""
import bpy, sys, os, json, struct
import numpy as np
from mathutils import Matrix, Quaternion, Vector
gate, body_glb, prop_glb = [os.path.abspath(p) for p in sys.argv[sys.argv.index('--') + 1:]]
raw = open(body_glb, 'rb').read(); doc = json.loads(raw[20:20 + struct.unpack_from('<I', raw, 12)[0]])
parent = {c: i for i, n in enumerate(doc['nodes']) for c in n.get('children', [])}


def local(n):
    t = Matrix.Translation(Vector(n.get('translation', (0, 0, 0))))
    x, y, z, w = n.get('rotation', (0, 0, 0, 1)); r = Quaternion((w, x, y, z)).to_matrix().to_4x4()
    s = Matrix.Diagonal(Vector(n.get('scale', (1, 1, 1)) + [1]) if False else (*n.get('scale', (1, 1, 1)), 1))
    return t @ r @ s


i = next(k for k, n in enumerate(doc['nodes']) if n.get('name') == 'Sword'); G = Matrix.Identity(4)
while i is not None:
    G = local(doc['nodes'][i]) @ G; i = parent.get(i)
C = Matrix(((1, 0, 0, 0), (0, 0, -1, 0), (0, 1, 0, 0), (0, 0, 0, 1)))       # glTF (x, y, z) -> Blender (x, -z, y)
bpy.ops.wm.open_mainfile(filepath=gate)
body = bpy.data.objects['Body']; rig = bpy.data.objects['Rig']
before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=prop_glb)
new = [o for o in bpy.data.objects if o not in before]
prop = next(o for o in new if o.type == 'MESH' and o.name.startswith('Sword') and '_LOD' not in o.name)
for o in new:
    if o is not prop:
        bpy.data.objects.remove(o, do_unlink=True)
prop.parent = None
prop.data.transform(C @ G @ C.inverted() @ prop.matrix_world); prop.matrix_world = rig.matrix_world.copy()
prop.data.transform(rig.matrix_world.inverted()); prop.matrix_world = Matrix.Identity(4)
body.data.transform(body.matrix_world); body.matrix_world = Matrix.Identity(4)
n = len(prop.data.vertices)
prop.vertex_groups.new(name='Sword').add(list(range(n)), 1.0, 'REPLACE')
for at, val in (('piece', 1000), ('garment', 9), ('finger', 0)):
    (prop.data.attributes.get(at) or prop.data.attributes.new(at, 'INT', 'POINT')).data.foreach_set('value', [val] * n)
if 'Sword' not in body.vertex_groups:
    body.vertex_groups.new(name='Sword')
for o in bpy.data.objects:
    o.select_set(o in (body, prop))
bpy.context.view_layer.objects.active = body
bpy.ops.object.join()
print('GATEPROP verts', n, 'Sword bone deform', rig.data.bones['Sword'].use_deform, 'joint at', [round(x, 3) for x in (C @ G).translation])
bpy.ops.wm.save_as_mainfile(filepath=gate)
