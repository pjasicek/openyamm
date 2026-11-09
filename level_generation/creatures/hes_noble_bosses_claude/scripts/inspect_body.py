"""Inspect the copied winged Kreegan body: objects, meshes, materials, bones, clips, rest dimensions.
Usage (Blender): inspect_body.py <glb> <out.json>"""
import bpy, sys, json
from mathutils import Vector

args = sys.argv[sys.argv.index('--') + 1:]
src, out = args[0], args[1]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=src)
info = {'objects': [], 'actions': {}, 'bones': []}
for o in bpy.data.objects:
    e = {'name': o.name, 'type': o.type, 'parent': o.parent.name if o.parent else None}
    if o.type == 'MESH':
        me = o.data
        e['verts'] = len(me.vertices)
        e['tris'] = sum(len(p.vertices) - 2 for p in me.polygons)
        e['materials'] = [m.name if m else None for m in me.materials]
        e['groups'] = len(o.vertex_groups)
        ws = [o.matrix_world @ v.co for v in me.vertices]
        if ws:
            e['min'] = [min(w[i] for w in ws) for i in range(3)]
            e['max'] = [max(w[i] for w in ws) for i in range(3)]
    info['objects'].append(e)
rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
for b in rig.data.bones:
    h = rig.matrix_world @ b.head_local
    info['bones'].append({'name': b.name, 'parent': b.parent.name if b.parent else None,
                          'head': [round(x, 4) for x in h], 'deform': b.use_deform})
for a in bpy.data.actions:
    info['actions'][a.name] = list(a.frame_range)
info['fps'] = bpy.context.scene.render.fps
open(out, 'w').write(json.dumps(info, indent=1))
print('DONE')
