"""Append the delivered v3 into an isolated live scene, preserving all existing work."""
import bpy
import json
from pathlib import Path

STAGE = Path(__file__).resolve().parent
assert 'MM6_Demon_Native_Animations' not in bpy.data.scenes, 'Scene already exists; inspect before resuming'
with bpy.data.libraries.load(str(STAGE.parent / 'attack_animation_v3/mm6_demon_attack.blend'), link=False) as (src, dst):
    dst.scenes = ['MM6_Demon_Attack']
scene = dst.scenes[0]
scene.name = 'MM6_Demon_Native_Animations'
bpy.context.window.scene = scene
rig = next(o for o in scene.objects if o.type == 'ARMATURE')
mesh = next(o for o in scene.objects if o.type == 'MESH')
rig.name = 'Demon_Native_Rig'
mesh.name = 'Demon_Native_Mesh'
rig.hide_set(False)
mesh.hide_set(False)
rig.hide_render = True
for t in rig.animation_data.nla_tracks:
    t.mute = True
    t.strips[0].action.name = 'DemonNative_Existing_' + t.name
scene.render.fps = 48
scene.frame_set(0)
scene.render.resolution_x = 900
scene.render.resolution_y = 850
scene.camera.name = 'Demon_Native_Review_Camera'
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type == 'VIEW_3D':
            area.spaces.active.shading.type = 'SOLID'
            area.spaces.active.region_3d.view_perspective = 'CAMERA'
print(json.dumps({'scene': scene.name, 'objects': [o.name for o in scene.objects],
                  'bones': len(rig.data.bones), 'vertices': len(mesh.data.vertices)}))
