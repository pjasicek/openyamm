"""Export the Codex body (body + horns, rest pose, purple A material) without wings, struts or effects as an
unrigged GLB for a Meshy rigging job; also render a front check. Writes claude_v2/meshy_upload/body_rest.glb."""
import bpy, os
import numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
rig = bpy.data.objects['Flying_Demon_Rig']
rig.data.pose_position = 'REST'
bpy.context.view_layer.update()
keep = ['Flying_Demon_Body', 'Flying_Horn_Left', 'Flying_Horn_Right']
dups = []
for name in keep:
    src = bpy.data.objects[name]
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(src.evaluated_get(dg))
    o = bpy.data.objects.new(name + '_static', me); o.matrix_world = src.matrix_world.copy()
    bpy.context.scene.collection.objects.link(o); dups.append(o)
for o in bpy.data.objects:
    o.select_set(o in dups)
bpy.context.view_layer.objects.active = dups[0]
bpy.ops.object.join()
body = bpy.context.view_layer.objects.active
co = np.array([tuple(body.matrix_world @ v.co) for v in body.data.vertices])
print('BBOX', co.min(0).round(3), co.max(0).round(3), 'verts', len(co))
out = os.path.join(HERE, 'meshy_upload', 'body_rest.glb')
bpy.ops.export_scene.gltf(filepath=out, use_selection=True, export_format='GLB', export_yup=True,
                          export_skins=False, export_animations=False, export_apply=True)
print('EXPORTED', out)
