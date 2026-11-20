import bpy,sys,json,runpy,importlib.util
from pathlib import Path
import numpy as np
P=Path(__file__).resolve().parents[1];R=P/'review/round6';sys.dont_write_bytecode=True
spec=importlib.util.spec_from_file_location('shared',P.parent/'claude_shared/gates/run_gates.py');g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
c=json.loads((P/'gates.json').read_text());glb=g.Glb(P/'export/mm6_arc1.glb');meshes=g.load_meshes(glb);report=g.Report(c)
for m in meshes:g.configure_mesh(m,c,report)
joints=sorted(set(j for skin in glb.doc['skins']for j in skin['joints']));out={}
for name,a,start,end in glb.clips():
 if name not in ['Walking','Standing','Fidget']:continue
 times=np.array([start,end,np.floor((end-1e-6)*48)/48]);poses=glb.pose(a,times);delta=poses[0,joints]-poses[1,joints]
 local_delta={};rot=0.
 for ch in a['channels']:
  s=a['samplers'][ch['sampler']];v=glb.accessor(s['output']);path=ch['target']['path'];local_delta[path]=max(local_delta.get(path,0.),float(np.max(abs(v[0]-v[-1]))))
  if path=='rotation' and not np.array_equal(v[0],v[-1]):rot=max(rot,float(np.degrees(2*np.arccos(np.clip(abs(np.dot(v[0],v[-1])/(np.linalg.norm(v[0])*np.linalg.norm(v[-1]))),0,1)))))
 assert np.array_equal(poses[0],poses[1]),name
 row={'duration_s':float(end-start),'joint_count':len(joints),'max_world_position_difference_mm':float(np.linalg.norm(delta[:,:3,3],axis=1).max()*1000),'max_world_matrix_difference':float(abs(delta).max()),'max_local_rotation_difference_deg':rot,'max_world_rotation_difference_deg':0.,'max_local_component_difference':local_delta,'sole_samples':[]}
 for m in meshes:
  samples=[]
  for t,pose in zip(times,poses):
   vertices=m.posed(pose);sides={}
   for side,(ids,heel,toe)in m.feet.items():
    sides[side]={'lowest_mm':float(vertices[ids,2].min()*1000),'heel_mm':float(vertices[heel,2].mean()*1000),'toe_mm':float(vertices[toe,2].mean()*1000)}
   samples.append({'time_s':float(t),'feet':sides})
  row['sole_samples'].append({'lod':m.label,'first':samples[0],'last':samples[1],'last_48hz_sample_before_wrap':samples[2]})
 out[name]=row
out['Running']={'alias':'Walking','reason':'animation.run: Walking on all three tiers','same_endpoint_results':True}
(R/'loop_endpoints.json').write_text(json.dumps(out,indent=2));print('LOOP_ENDPOINTS',json.dumps({k:{x:v[x]for x in v if x!='sole_samples'}for k,v in out.items()}),flush=True)
# Update editable source clocks without altering pose values, geometry or materials.
for rel in ['work/rig_equipped.blend','work/rig_textured.blend']+[f'work/round2/lod{i}.blend'for i in range(4)]:
 bpy.ops.wm.open_mainfile(filepath=str(R/'baseline'/rel))
 for name in ['Attack','Cast']:
  a=bpy.data.actions[name]
  for layer in a.layers:
   for strip in layer.strips:
    for bag in strip.channelbags:
     for fc in bag.fcurves:
      for k in fc.keyframe_points:
       k.co.x/=1.5;k.handle_left.x/=1.5;k.handle_right.x/=1.5
      fc.update()
  if a.use_frame_range:a.frame_start/=1.5;a.frame_end/=1.5
 bpy.ops.wm.save_as_mainfile(filepath=str(P/rel))
runpy.run_path(str(P/'scripts/round6_gates.py'),run_name='__main__')
# Save the runtime authoring scene from the actual final viewer export.
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.context.scene.render.fps=30
bpy.ops.import_scene.gltf(filepath=str(P/'review/viewer/mm6_arc1_a.glb'))
rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');a=bpy.data.actions['Standing'];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];bpy.context.scene.frame_set(0)
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/runtime_authoring.blend'))
# Endpoint and new timing evidence, CPU rendering only.
sys.path.insert(0,str(P/'scripts'));import common
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=8;scene.render.threads_mode='FIXED';scene.render.threads=4
scene.world=bpy.data.worlds.new('Review6World');scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.7,.7,.7,1);scene.world.node_tree.nodes['Background'].inputs[1].default_value=.8;scene.view_settings.view_transform='Standard'
frames=json.loads((P/'review/clips/frames.json').read_text())
for role in ['Attack','Cast']:
 a=bpy.data.actions[role];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];frames[role]=[]
 for i,f in enumerate(np.array([0,6,12,22,30,36,37,44,52])/1.5):
  scene.frame_set(int(f),subframe=float(f-int(f)))
  for view in ['front','left','three_quarter']:
   path=common.render_views(str(P/f'review/clips/{role}_{i}'),.95,2.6,views=(view,),resolution=(300,420))[0];frames[role].append({'view':view,'seconds':float(f/30),'path':str(Path(path).relative_to(P))})
(P/'review/clips/frames.json').write_text(json.dumps(frames,indent=2))
for role in ['Walking','Standing','Fidget']:
 a=bpy.data.actions[role];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0]
 for label,f in [('first',float(a.frame_range[0])),('last',float(a.frame_range[1]))]:
  scene.frame_set(int(f),subframe=f-int(f));common.render_views(str(R/f'{role}_{label}'),.92,2.15,views=('front','left'),resolution=(320,440))
print('ROUND6 AUDIT AND RENDERS COMPLETE',flush=True)
