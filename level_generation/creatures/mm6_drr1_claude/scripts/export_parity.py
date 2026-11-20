"""Reimport the delivered runtime GLB; compare all clips and effect sockets to the editable master."""
import bpy,json,numpy as np
from pathlib import Path
from mathutils.kdtree import KDTree
P=Path(__file__).resolve().parents[1];sc=bpy.context.scene
bpy.ops.wm.open_mainfile(filepath=str(P/'export/mm6_wyrm.blend'));sc=bpy.context.scene;sc.render.fps=24
rig=bpy.data.objects['Wyrm_Rig'];body=bpy.data.objects['Wyrm'];names=['Standing','Walking','Running','Fidget','Attack','Hit','Death','Dead'];saved={};sockets=['Socket_Mouth','Socket_Remains']
def socket(n):return rig.matrix_world @ rig.pose.bones[n].matrix if n in rig.pose.bones else bpy.data.objects[n].matrix_world
def coords(obj):
 e=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());m=e.to_mesh();a=np.array([obj.matrix_world@v.co for v in m.vertices]);e.to_mesh_clear();return a
for name in names:
 a=bpy.data.actions[name];rig.animation_data.action=a;lo,hi=a.frame_range
 saved[name]=[]
 for fraction in sorted(set([0,.2,.4,.6,.8,1]+([f/(hi-lo) for f in np.arange(0,24.01,.25)] if name=='Attack' else []))):
  f=lo+(hi-lo)*fraction;sc.frame_set(int(f),subframe=f-int(f));bpy.context.view_layer.update()
  saved[name].append((fraction,coords(body),{n:list(socket(n).translation) for n in sockets}))
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.context.scene.render.fps=24;bpy.ops.import_scene.gltf(filepath=str(P/'export/mm6_wyrm.glb'));sc=bpy.context.scene;sc.render.fps=24
rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');body=bpy.data.objects['Wyrm'];report={'clips':{},'actions':[a.name for a in bpy.data.actions]};print(report['actions'])
for name in names:
 a=next(a for a in bpy.data.actions if a.name==name or a.name.endswith('|'+name));rig.animation_data.action=a
 if len(a.slots):rig.animation_data.action_slot=a.slots[0]
 lo,hi=a.frame_range;errs=[];socketerrs=[]
 for fraction,ref,sock in saved[name]:
  f=lo+(hi-lo)*fraction;sc.frame_set(int(f),subframe=f-int(f));bpy.context.view_layer.update();cur=coords(body);tree=KDTree(len(cur))
  for i,c in enumerate(cur):tree.insert(c,i)
  tree.balance();errs.append(max(tree.find(c)[2] for c in ref));socketerrs.append(max(np.linalg.norm(np.array(socket(n).translation)-v) for n,v in sock.items()))
 report['clips'][name]={'max_surface_error_m':max(errs),'max_socket_error_m':max(socketerrs),'frame_range':list(a.frame_range)}
 assert max(errs)<.003,(name,errs)
 assert max(socketerrs)<.001,(name,socketerrs)
report['dense_floor']={}
for name in ['Standing','Walking','Running','Attack','Hit','Fidget','Death','Dead']:
 a=next(a for a in bpy.data.actions if a.name==name or a.name.endswith('|'+name));rig.animation_data.action=a
 if len(a.slots):rig.animation_data.action_slot=a.slots[0]
 lo,hi=a.frame_range;low=1e9
 for f in np.arange(lo,hi+.001,.2):
  sc.frame_set(int(f),subframe=f%1);low=min(low,float(coords(body)[:,2].min()))
 report['dense_floor'][name]={'minimum_z_m':low,'sample_rate_hz':120}
 assert low>-.003,(name,'floor',low)
# The initial death must stay supported; tail contact cannot push the hip upward.
a=next(a for a in bpy.data.actions if a.name=='Death' or a.name.endswith('|Death'));rig.animation_data.action=a
if len(a.slots):rig.animation_data.action_slot=a.slots[0]
lo,hi=a.frame_range;hips=[];floors=[]
for t in np.arange(0,.201,1/120):
 f=lo+t*24;sc.frame_set(int(f),subframe=f%1);bpy.context.view_layer.update()
 hips.append(float((rig.matrix_world@rig.pose.bones['Spine1'].head).z));floors.append(float(coords(body)[:,2].min()))
report['death_support']={'until_seconds':.2,'hip_rise_m':max(hips)-hips[0],'maximum_floor_gap_m':max(floors)}
assert max(hips)-hips[0]<.003,report['death_support']
assert max(floors)<.003,report['death_support']
# Preserve the authored weight shift and cross-body sweep through the export.
a=next(a for a in bpy.data.actions if a.name=='Attack' or a.name.endswith('|Attack'));rig.animation_data.action=a
if len(a.slots):rig.animation_data.action_slot=a.slots[0]
lo,hi=a.frame_range;hips=[];heads=[]
for f in np.arange(lo,hi+.001,.2):
 sc.frame_set(int(f),subframe=f%1);bpy.context.view_layer.update()
 hips.append(tuple(rig.matrix_world@rig.pose.bones['Spine1'].head));heads.append(tuple(rig.matrix_world@rig.pose.bones['Head'].head))
report['attack_weight_shift']={'hip_fore_aft_range_m':float(np.ptp(np.array(hips)[:,1])),'head_lateral_min_max_m':[float(np.min(np.array(heads)[:,0])),float(np.max(np.array(heads)[:,0]))]}
assert report['attack_weight_shift']['hip_fore_aft_range_m']>.04,report['attack_weight_shift']
assert report['attack_weight_shift']['head_lateral_min_max_m'][0]<-.01 and report['attack_weight_shift']['head_lateral_min_max_m'][1]>.01,report['attack_weight_shift']
(P/'checks/export_parity.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
