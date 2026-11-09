import bpy, json
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'master_weights.blend'))
rig=bpy.data.objects['Lizardman_Rig'];body=bpy.data.objects['Lizardman_Body'];sc=bpy.context.scene
sc.render.engine='BLENDER_WORKBENCH';sc.render.resolution_x=640;sc.render.resolution_y=640
sc.display.shading.light='STUDIO';sc.display.shading.color_type='SINGLE';sc.display.shading.single_color=(.6,.6,.6)
for t in rig.animation_data.nla_tracks:t.mute=True
for name,frame in [('Standing',0),('Walk',25),('Fidget',6),('Death',18),('Corpse',0)]:
    a=bpy.data.actions[name];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];sc.frame_set(frame)
    for view,d in [('front',(0,-5,0)),('quarter',(-3,-5,0)),('side',(-5,0,0))]:
        target=Vector((0,.2,.83));sc.camera.location=target+Vector(d)
        sc.camera.rotation_euler=(target-sc.camera.location).to_track_quat('-Z','Y').to_euler()
        sc.camera.data.ortho_scale=2.2;sc.render.filepath=str(P/f'review/weights_{name}_{view}.png')
        bpy.ops.render.render(write_still=True)
print('SOURCE',[(a.name,list(a.frame_range)) for a in bpy.data.actions if 'Source' in a.name],flush=True)
