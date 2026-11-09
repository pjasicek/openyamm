"""Reimport the delivered runtime GLB; compare all clips and effect sockets to the editable master."""
import bpy,json,numpy as np
from pathlib import Path
from mathutils.kdtree import KDTree
P=Path('level_generation/creatures/mm8_m624_claude').resolve();sc=bpy.context.scene
bpy.ops.wm.open_mainfile(filepath=str(P/'export/mm8_m624.blend'));sc=bpy.context.scene;sc.render.fps=24
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];names=['Standing','Walk','Running','Fidget','Attack','Cast','Hit','Death','Dead'];saved={};sockets=['Socket_Blade_L1','Socket_Blade_R1']
def coords(obj):
 e=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());m=e.to_mesh();a=np.array([obj.matrix_world@v.co for v in m.vertices]);e.to_mesh_clear();return a
for name in names:
 a=bpy.data.actions[name];rig.animation_data.action=a;lo,hi=a.frame_range
 saved[name]=[]
 for fraction in ([i/168 for i in range(169)] if name=="Attack" else sorted(set([0,.2,.4,.6,.8,1]+[round((hi-lo)*x)/(hi-lo) for x in [0,.2,.4,.6,.8,1]]))):
  f=lo+(hi-lo)*fraction;sc.frame_set(int(f),subframe=f-int(f));bpy.context.view_layer.update()
  saved[name].append((fraction,coords(body),{n:list(bpy.data.objects[n].matrix_world.translation) for n in sockets}))
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(P/'export/mm8_m624.glb'));sc=bpy.context.scene;sc.render.fps=24
rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');body=bpy.data.objects['Body'];report={'clips':{},'actions':[a.name for a in bpy.data.actions]};print(report['actions'])
for name in names:
 a=next(a for a in bpy.data.actions if a.name==name or a.name.endswith('|'+name));rig.animation_data.action=a
 if len(a.slots):rig.animation_data.action_slot=a.slots[0]
 lo,hi=a.frame_range;errs=[];socketerrs=[];keyerrs=[];keysock=[]
 for fraction,ref,sock in saved[name]:
  f=lo+(hi-lo)*fraction;sc.frame_set(int(f),subframe=f-int(f));bpy.context.view_layer.update();cur=coords(body);tree=KDTree(len(cur))
  for i,c in enumerate(cur):tree.insert(c,i)
  tree.balance();errs.append(max(tree.find(c)[2] for c in ref));socketerrs.append(max(np.linalg.norm(np.array(bpy.data.objects[n].matrix_world.translation)-v) for n,v in sock.items()))
  if abs(f-round(f))<1e-5:keyerrs.append(errs[-1]);keysock.append(socketerrs[-1])
 report['clips'][name]={'max_surface_error_m':max(errs),'max_socket_error_m':max(socketerrs),'baked_frame_surface_error_m':max(keyerrs),'baked_frame_socket_error_m':max(keysock),'frame_range':list(a.frame_range),'samples':len(saved[name])}

(P/'review/export_parity.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))

assert all(v['baked_frame_surface_error_m']<.003 and v['baked_frame_socket_error_m']<.0001 for v in report['clips'].values())

assert all(v['max_surface_error_m']<.003 and v['max_socket_error_m']<.0001 for v in report['clips'].values())
