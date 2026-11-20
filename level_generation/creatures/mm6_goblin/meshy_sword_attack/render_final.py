import bpy,json,traceback,math
import numpy as np
from mathutils import Vector
from pathlib import Path
ROOT=Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm6_goblin/meshy_sword_attack');out=ROOT/'review';s=bpy.data.scenes['Meshy Goblin Sword and Native Attack'];bpy.context.window.scene=s;r=bpy.data.objects['MM6 Meshy Goblin Rig'];actions=json.loads(s['authored_actions']);cam=s.camera
s.render.engine='CYCLES';s.cycles.device='CPU';s.cycles.samples=24;s.cycles.use_denoising=True;s.render.resolution_x=640;s.render.resolution_y=640;s.render.resolution_percentage=100;s.render.film_transparent=True;s.render.image_settings.color_mode='RGBA';s.view_settings.view_transform='AgX'
s.world.use_nodes=True;s.world.node_tree.nodes['Background'].inputs['Color'].default_value=(.3,.3,.3,1);s.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.65
for name,pos,power,size in [('Key',(-3,-4,5),700,4),('Fill',(3,-2,3),400,3),('Rim',(1,3,4),650,3)]:
 o=bpy.data.objects.get('Sword Studio '+name)
 if o is None:
  data=bpy.data.lights.new('Sword Studio '+name,'AREA');o=bpy.data.objects.new('Sword Studio '+name,data);s.collection.objects.link(o)
 o.location=pos;o.data.energy=power;o.data.shape='DISK';o.data.size=size;o.rotation_euler=(Vector((0,0,1))-o.location).to_track_quat('-Z','Y').to_euler()
# Evaluate final deformed mesh bounds at every native-rate frame, including the endpoint.
a=bpy.data.actions[actions['Attack']];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];report=[]
for frame in range(1,20):
 s.frame_set(frame);deps=bpy.context.evaluated_depsgraph_get();mins=[];maxs=[]
 for o in s.objects:
  if o.type!='MESH' or o.find_armature()!=r:continue
  ev=o.evaluated_get(deps);mesh=ev.to_mesh();ar=np.empty(len(mesh.vertices)*3);mesh.vertices.foreach_get('co',ar);ar=ar.reshape(-1,3);w=np.array(ev.matrix_world);ar=ar@w[:3,:3].T+w[:3,3];mins.append(ar.min(axis=0));maxs.append(ar.max(axis=0));ev.to_mesh_clear()
 report.append({'frame':frame,'min':np.min(mins,axis=0).tolist(),'max':np.max(maxs,axis=0).tolist()})
(out/'motion_bounds.json').write_text(json.dumps(report,indent=2));print({'min_height':min(x['min'][2] for x in report),'bounds_max_z':max(x['max'][2] for x in report)})
jobs=[('Attack',f,'pbr_front',(0,-5,0),f-1) for f in range(1,19)]
jobs.extend(('Attack',f,'pbr_quarter',(-3,-5,0),i) for i,f in enumerate([1,4,7,10,13,16]))
jobs.append(('Standing',1,'pbr_standing',(-3,-5,.35),0))
def step():
 try:
  if not jobs:(out/'final_render_done.txt').write_text('complete');return None
  name,f,view,vec,i=jobs.pop(0);a=bpy.data.actions[actions[name]];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];s.frame_set(f);cam.data.ortho_scale=2.65;target=Vector((0,0,1.10));cam.location=target+Vector(vec);cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();s.render.filepath=str(out/f'{view}_{i:02}.png');bpy.ops.render.render(write_still=True);(out/'final_progress.txt').write_text(str(len(jobs))+' remaining');return .1
 except Exception:(out/'final_render_error.txt').write_text(traceback.format_exc());return None
bpy.app.timers.register(step,first_interval=.5);print('scheduled '+str(len(jobs))+' material renders')
