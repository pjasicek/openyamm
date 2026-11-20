"""Reimport the delivered runtime GLB; compare all clips and effect sockets to the editable master."""
import bpy,json,numpy as np
from pathlib import Path
from mathutils.kdtree import KDTree
P=Path('level_generation/creatures/mm6_gst_codex').resolve();sc=bpy.context.scene
bpy.ops.wm.open_mainfile(filepath=str(P/'export/mm6_gst.blend'));sc=bpy.context.scene;sc.render.fps=60
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];names=['Standing','Walking','Running','Fidget','Attack','Hit','Death','Dead'];saved={};sockets=['Socket_Eye_Left','Socket_Eye_Right','Socket_Gaze','Socket_Palm_Left','Socket_Palm_Right']
def coords(obj):
 e=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());m=e.to_mesh();a=np.array([obj.matrix_world@v.co for v in m.vertices]);e.to_mesh_clear();return a
for name in names:
 a=bpy.data.actions[name];rig.animation_data.action=a;lo,hi=a.frame_range
 saved[name]=[]
 for fraction in sorted(set([0,.2,.4,.6,.8,1]+([f/(hi-lo) for f in np.arange(0,hi-lo+.01,.5)] if name=='Attack' else []))):
  f=lo+(hi-lo)*fraction;sc.frame_set(int(f),subframe=f-int(f));bpy.context.view_layer.update()
  saved[name].append((fraction,coords(body),{n:list(bpy.data.objects[n].matrix_world.translation) for n in sockets}))
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.context.scene.render.fps=60;bpy.ops.import_scene.gltf(filepath=str(P/'export/mm6_gst.glb'));sc=bpy.context.scene;sc.render.fps=60
rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');body=next(o for o in bpy.data.objects if o.type=='MESH');report={'clips':{},'actions':[a.name for a in bpy.data.actions]};print(report['actions'])
for name in names:
 a=next(a for a in bpy.data.actions if a.name==name or a.name.endswith('|'+name));rig.animation_data.action=a
 if len(a.slots):rig.animation_data.action_slot=a.slots[0]
 lo,hi=a.frame_range;errs=[];socketerrs=[]
 for fraction,ref,sock in saved[name]:
  f=lo+(hi-lo)*fraction;sc.frame_set(int(f),subframe=f-int(f));bpy.context.view_layer.update();cur=coords(body);tree=KDTree(len(cur))
  for i,c in enumerate(cur):tree.insert(c,i)
  tree.balance();errs.append(max(tree.find(c)[2] for c in ref));socketerrs.append(max(np.linalg.norm(np.array(bpy.data.objects[n].matrix_world.translation)-v) for n,v in sock.items()))
 report['clips'][name]={'max_surface_error_m':max(errs),'max_socket_error_m':max(socketerrs),'frame_range':list(a.frame_range)}
 assert max(errs)<.003,(name,errs)
 assert max(socketerrs)<.0001,(name,socketerrs)
(P/'review/export_parity.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
