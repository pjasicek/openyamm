"""Compare chest-relative shoulder travel and render the repaired shoulder pilot."""
import bpy,sys,json,numpy as np
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'))
report={}
for revision,path in [('before','work/shoulder_motion_v3/before/work/rig_uv.blend'),('after','work/rig_uv.blend')]:
 bpy.ops.wm.open_mainfile(filepath=str(P/path));sys.modules.pop('motion',None);import motion as M
 body=M.body;rig=M.rig;rest=np.array([v.co[:] for v in body.data.vertices]);masks={side:(rest[:,0]*sign>.16)&(rest[:,0]*sign<.245)&(rest[:,2]>.73)&(rest[:,2]<.81)&(rest[:,1]<.035) for side,sign in [('L',1),('R',-1)]}
 poses={}
 for clip,t in [('Standing',0),('Attack',.5),('Hit',.8),('Fidget',.3125)]:
  M.pose(clip,t);obj=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=obj.to_mesh();mat=rig.pose.bones['Chest'].matrix.inverted();a=np.array([mat@v.co for v in me.vertices]);obj.to_mesh_clear();poses[clip]=a
 report[revision]={side:{'vertices':int(mask.sum()),'upper_arm_owned':sum(any(body.vertex_groups[g.group].name=='UpperArm_'+side and g.weight>.99 for g in v.groups) for v in body.data.vertices if mask[v.index]),'chest_relative_rms_displacement_m':{clip:float(np.sqrt(np.mean(np.sum((a[mask]-poses['Standing'][mask])**2,axis=1)))) for clip,a in poses.items() if clip!='Standing'}} for side,mask in masks.items()}
 sc=bpy.context.scene;sc.render.engine='BLENDER_WORKBENCH';sc.display.shading.light='STUDIO';sc.display.shading.color_type='MATERIAL';sc.display.shading.show_cavity=True;sc.render.resolution_x=1000;sc.render.resolution_y=900;sc.render.resolution_percentage=100
 body.data.materials.clear()
 for name,col in [('Torso',(.42,.42,.42,1)),('Moving arm',(.85,.5,.16,1))]:
  mat=bpy.data.materials.new(name);mat.diffuse_color=col;body.data.materials.append(mat)
 for f in body.data.polygons:
  f.material_index=int(any(body.vertex_groups[g.group].name.startswith(('UpperArm_','Forearm_','Hand_')) and g.weight>.01 for i in f.vertices for g in body.data.vertices[i].groups))
 cam=bpy.data.objects.new('ShoulderCamera',bpy.data.cameras.new('ShoulderCamera'));sc.collection.objects.link(cam);sc.camera=cam;cam.data.type='ORTHO';cam.data.ortho_scale=.9
 for clip,t in [('Standing',0),('Attack',.5),('Hit',.8)]:
  M.pose(clip,t)
  for view,d in [('front',(0,-1,0)),('back',(0,1,0)),('side',(1,0,0))]:
   c=Vector((0,0,.78));cam.location=c+Vector(d)*3;cam.rotation_euler=(c-cam.location).to_track_quat('-Z','Y').to_euler();sc.render.filepath=str(P/f'review/shoulder_motion_v3/{revision}_{clip}_{view}.png');bpy.ops.render.render(write_still=True)
(P/'work/shoulder_motion_v3/motion_comparison.json').write_text(json.dumps(report,indent=2));print('SHOULDER_MOTION',report,flush=True)
