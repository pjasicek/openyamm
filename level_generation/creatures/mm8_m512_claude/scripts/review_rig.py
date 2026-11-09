"""Render local quadruped stress poses before authoring motion."""
import bpy
import sys
import json
import subprocess
from pathlib import Path
import numpy as np
from mathutils import Vector

PROJECT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(PROJECT.parent/'mm6_rat_claude/scripts'))
import posing
bpy.ops.wm.open_mainfile(filepath=str(PROJECT/'work/rig_v1.blend'))
rig=bpy.data.objects['Wolf_Rig'];mesh=bpy.data.objects['Wolf']
sc=bpy.context.scene;sc.render.engine='BLENDER_WORKBENCH'
sc.display.shading.light='STUDIO';sc.display.shading.show_cavity=True
sc.display.shading.color_type='SINGLE';sc.display.shading.single_color=(.7,.7,.7)
sc.world=bpy.data.worlds.new('ReviewWorld');sc.world.color=(.12,.12,.12)
sc.render.resolution_x=650;sc.render.resolution_y=500;sc.render.resolution_percentage=100
cam=bpy.data.objects.new('ReviewCamera',bpy.data.cameras.new('ReviewCamera'))
sc.collection.objects.link(cam);sc.camera=cam;cam.data.type='ORTHO'
poses={
 'rest':[],
 'stride':[('UpperArm_L','X',-28),('UpperArm_R','X',28),('Thigh_L','X',25),('Thigh_R','X',-25)],
 'rear':[('Spine1','X',-40),('Spine2','X',-10),('UpperArm_L','X',-45),('UpperArm_R','X',-45),('Jaw','X',-20)],
 'tail_head':[('Tail1','X',-25),('Tail2','Z',20),('Tail3','Z',20),('Neck1','Z',20),('Head','Z',15),('Jaw','X',-20)],
 'roll':[('Spine1','Y',100),('UpperArm_L','X',30),('Thigh_R','X',20)]}
cells=[]
for name,ops in poses.items():
 posing.reset(rig)
 for bone,axis,angle in ops:posing.rotate_world(rig,bone,axis,angle)
 ev=mesh.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
 co=np.array([mesh.matrix_world@v.co for v in me.vertices]);ev.to_mesh_clear()
 assert np.isfinite(co).all()
 center=Vector((co.min(0)+co.max(0))/2)
 for view,direction in [('side',(1,0,.08)),('quarter',(.8,-1,.4))]:
  cam.location=center+Vector(direction).normalized()*4
  cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler()
  cam.data.ortho_scale=1.65
  path=PROJECT/f'review/stress_{name}_{view}.png';sc.render.filepath=str(path)
  bpy.ops.render.render(write_still=True);cells.append(str(path))
subprocess.run(['/usr/bin/python3','-c',
 "from PIL import Image,ImageDraw;import sys;ps=sys.argv[2:];out=Image.new('RGB',(1300,500*(len(ps)//2)));d=ImageDraw.Draw(out);[(out.paste(Image.open(p),((i%2)*650,(i//2)*500)),d.text(((i%2)*650+10,(i//2)*500+10),p.split('/')[-1],fill='white')) for i,p in enumerate(ps)];out.save(sys.argv[1])",
 str(PROJECT/'review/stress_sheet.png'),*cells],check=True)
