import bpy,sys,math
import numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
P=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(P.parent/'mm6_rat_claude/scripts'))
import posing
bpy.ops.wm.open_mainfile(filepath=str(P/'export/mm8_wolf.blend'))
rig=bpy.data.objects['Wolf_Rig'];mesh=bpy.data.objects['Wolf'];sc=bpy.context.scene
sc.render.engine='BLENDER_WORKBENCH';sc.display.shading.color_type='TEXTURE';sc.display.shading.light='STUDIO'
sc.display.shading.show_cavity=True;sc.render.resolution_x=720;sc.render.resolution_y=500;sc.render.resolution_percentage=100
cam=bpy.data.objects.new('ReviewCamera',bpy.data.cameras.new('ReviewCamera'));sc.collection.objects.link(cam)
sc.camera=cam;cam.data.type='ORTHO';cam.data.ortho_scale=1.5
center=Vector((0,0,.15));cam.location=center+Vector((.8,-1,.5)).normalized()*4
cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler()
for i,angle in enumerate([0,-25,-45,-65]):
 rig.animation_data.action=bpy.data.actions['Dead'];sc.frame_set(1);bpy.context.view_layer.update()
 rig.animation_data.action=None
 for name in ['UpperArm_R','Thigh_R']:posing.rotate_world(rig,name,'Y',angle)
 if i:posing.rotate_world(rig,'Tail1','Y',-20)
 ev=mesh.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();co=np.array([v.co[:] for v in me.vertices]);ev.to_mesh_clear()
 root=rig.pose.bones['Spine1'];root.matrix=Matrix.Translation(Vector((0,0,.003-co[:,2].min())))@root.matrix
 bpy.context.view_layer.update()
 print('POSE',angle,[(b.name,tuple(round(x,3) for x in b.head)) for b in rig.pose.bones if 'Paw' in b.name],flush=True)
 sc.render.filepath=str(P/f'review/corpse_roll_{i}.png');bpy.ops.render.render(write_still=True)
