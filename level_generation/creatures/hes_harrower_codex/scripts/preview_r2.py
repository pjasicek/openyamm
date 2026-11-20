from pathlib import Path
import bpy,json,numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/revised_r2.blend'));sc=bpy.context.scene;rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body']
sc.render.engine='BLENDER_WORKBENCH';sc.display.shading.light='STUDIO';sc.display.shading.studio_light='paint.sl';sc.display.shading.color_type='MATERIAL';sc.display.shading.show_shadows=True;sc.display.shading.show_cavity=True;sc.display.shading.cavity_type='BOTH';sc.render.film_transparent=False;sc.display.shading.background_type='WORLD';sc.world=bpy.data.worlds.new('Review');sc.world.color=(.045,.045,.045);sc.render.resolution_x=sc.render.resolution_y=1024;sc.render.resolution_percentage=100
for ob in bpy.data.objects:
 if ob.type!='MESH':continue
 for i,m in enumerate(ob.data.materials):
  if m:
   m=m.copy();m.diffuse_color=(.42,.025,.095,1) if ob==body else (.75,.64,.44,1)
   if ob.name.startswith(('Cloth_','Mantle_')):m.diffuse_color=(.045,.035,.04,1) if 'Cloth' in ob.name or int(ob.name[-1])%2 else (.58,.52,.41,1)
   if 'Glow' in m.name:m.diffuse_color=(1,.16,.008,1)
   ob.data.materials[i]=m
cd=bpy.data.cameras.new('review');cam=bpy.data.objects.new('review',cd);sc.collection.objects.link(cam);cd.type='ORTHO';sc.camera=cam
for pose,f in [('Standing',0),('Attack2',2)]:
 a=bpy.data.actions['Harrower_'+pose];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];sc.frame_set(f)
 for boss in (False,True):
  for ob in bpy.data.objects:
   if ob.type=='MESH':ob.hide_render=(ob.name.startswith('Family_') if boss else ob.name.startswith(('Vreth_','Mantle_')))
  for name,centre,direction,scale in [('front',Vector((0,-.12,.92)),Vector((0,-4,1)),2.45),('quarter',Vector((0,-.12,.92)),Vector((3,-5,1)),2.6),('handR',rig.pose.bones['B_R_Hand'].head+Vector((0,0,.03)),Vector((0,-4,1)),.65)]:
   cam.location=centre+direction;cam.rotation_euler=(-direction).to_track_quat('-Z','Y').to_euler();cd.ortho_scale=scale;sc.render.filepath=str(P/f'review/r2/{pose}_{"boss" if boss else "a"}_{name}.png');bpy.ops.render.render(write_still=True)
 # Identify exactly which right-blade island contacts the native forearm.
 ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();C=[v.co.copy() for v in me.vertices];faces=[tuple(p.vertices) for p in me.polygons];ev.to_mesh_clear();bt=BVHTree.FromPolygons(C,faces);names={g.index:g.name for g in body.vertex_groups};dom=[names[max(v.groups,key=lambda g:g.weight).group] for v in body.data.vertices]
 ob=bpy.data.objects['Family_Blade_R'];ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();tree=BVHTree.FromPolygons([v.co.copy() for v in me.vertices],[tuple(p.vertices) for p in me.polygons]);pairs=[(bi,fi) for bi,fi in tree.overlap(bt) if any('Forearm' in dom[i] for i in faces[fi])];print('CONTACT',pose,[(bi,list(ob.data.polygons[bi].vertices)) for bi,fi in pairs],flush=True);ev.to_mesh_clear()
