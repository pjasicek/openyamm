"""Reimport the delivered runtime GLB; compare all clips and effect sockets to the editable master."""
import bpy,json,numpy as np
from pathlib import Path
from mathutils.kdtree import KDTree
P=Path(__file__).resolve().parents[1];sc=bpy.context.scene
bpy.ops.wm.open_mainfile(filepath=str(P/'export/mm6_drg1.blend'));sc=bpy.context.scene;sc.render.fps=24
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];names=['Standing','Walking','Running','Fidget','Attack','Cast','Hit','Death','Dead'];saved={};sockets=['Socket_Mouth'];fire=bpy.data.objects['DeathFlames']
def socket(n):return rig.matrix_world @ rig.pose.bones[n].matrix if n in rig.pose.bones else bpy.data.objects[n].matrix_world
def coords(obj):
 e=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());m=e.to_mesh();a=np.array([obj.matrix_world@v.co for v in m.vertices]);e.to_mesh_clear();return a
for name in names:
 a=bpy.data.actions[name];rig.animation_data.action=a;lo,hi=a.frame_range
 saved[name]=[]
 for fraction in sorted(set([0,.2,.4,.6,.8,1]+([f/(hi-lo) for f in np.arange(0,36.01,.5)] if name=='Attack' else []))):
  f=lo+(hi-lo)*fraction;sc.frame_set(int(f),subframe=f-int(f));bpy.context.view_layer.update()
  saved[name].append((fraction,coords(body),{n:list(socket(n).translation) for n in sockets},coords(fire)))
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.context.scene.render.fps=24;bpy.ops.import_scene.gltf(filepath=str(P/'export/mm6_drg1.glb'));sc=bpy.context.scene;sc.render.fps=24
rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');body=next(o for o in bpy.data.objects if o.type=='MESH');fire=bpy.data.objects['DeathFlames'];report={'clips':{},'actions':[a.name for a in bpy.data.actions]};print(report['actions'])
for name in names:
 a=next(a for a in bpy.data.actions if a.name==name or a.name.endswith('|'+name));rig.animation_data.action=a
 if len(a.slots):rig.animation_data.action_slot=a.slots[0]
 lo,hi=a.frame_range;errs=[];socketerrs=[];fireerrs=[]
 for fraction,ref,sock,flames in saved[name]:
  f=lo+(hi-lo)*fraction;sc.frame_set(int(f),subframe=f-int(f));bpy.context.view_layer.update();cur=coords(body);tree=KDTree(len(cur))
  for i,c in enumerate(cur):tree.insert(c,i)
  tree.balance();errs.append(max(tree.find(c)[2] for c in ref));socketerrs.append(max(np.linalg.norm(np.array(socket(n).translation)-v) for n,v in sock.items()))
  curfire=coords(fire);ftree=KDTree(len(curfire))
  for i,c in enumerate(curfire):ftree.insert(c,i)
  ftree.balance();fireerrs.append(max(ftree.find(c)[2] for c in flames))
 report['clips'][name]={'max_surface_error_m':max(errs),'max_flame_error_m':max(fireerrs),'max_socket_error_m':max(socketerrs),'frame_range':list(a.frame_range)}
 assert max(fireerrs)<.003,(name,'flame export',max(fireerrs))
 assert max(errs)<.003,(name,errs)
 assert max(socketerrs)<.0001,(name,socketerrs)
(P/'review/export_parity.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
