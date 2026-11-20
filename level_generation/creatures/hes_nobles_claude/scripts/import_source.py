"""Import the published winged Kreegan body (source/hes_kreegan_winged.glb, LOD0 only) into work/source.blend:
armature 'Rig', skinned mesh 'Body' (head and body materials), the seven Overseer clips as actions. Prints the rest
joints, bounds and clip ranges to work/source_info.json.
Run: blender --background --factory-startup -noaudio --python import_source.py"""
import bpy, json, os, sys
from pathlib import Path
P = Path(__file__).resolve().parents[1]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(P / 'source/hes_kreegan_winged.glb'))
rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
body = max((o for o in bpy.data.objects if o.type == 'MESH'), key=lambda o: len(o.data.vertices))
for o in [o for o in bpy.data.objects if o.type == 'MESH' and o is not body]:
    bpy.data.objects.remove(o, do_unlink=True)
rig.name = 'Rig'; rig.data.name = 'Rig'; body.name = 'Body'
scene = bpy.context.scene
info = {'fps': scene.render.fps, 'objects': [(o.name, o.type, o.parent.name if o.parent else None) for o in bpy.data.objects]}
rig.animation_data_create(); rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.update()
info['bones'] = {b.name: {'head': list(rig.matrix_world @ b.head_local), 'parent': b.parent.name if b.parent else None,
                          'deform': b.use_deform} for b in rig.data.bones}
co = [body.matrix_world @ v.co for v in body.data.vertices]
info['bounds'] = [[min(c[i] for c in co) for i in range(3)], [max(c[i] for c in co) for i in range(3)]]
info['tris'] = sum(len(p.vertices) - 2 for p in body.data.polygons)
info['materials'] = [m.name for m in body.data.materials]
info['uv_layers'] = [u.name for u in body.data.uv_layers]
info['groups'] = len(body.vertex_groups)
info['rig_matrix'] = [list(r) for r in rig.matrix_world]
info['actions'] = {a.name: list(a.frame_range) for a in bpy.data.actions}
info['images'] = {i.name: list(i.size) for i in bpy.data.images}
(P / 'work/source_info.json').write_text(json.dumps(info, indent=1))
bpy.ops.wm.save_as_mainfile(filepath=str(P / 'work/source.blend'))
print('IMPORTED', info['tris'], info['bounds'], info['actions'])
sys.stdout.flush(); os._exit(0)
