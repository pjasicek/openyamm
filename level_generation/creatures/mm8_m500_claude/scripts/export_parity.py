"""Reimport the finished runtime GLB and compare motion, endpoints, grounding and socket placement."""
import bpy,json,sys,numpy as np
from pathlib import Path
from mathutils.kdtree import KDTree
P=Path(__file__).resolve().parents[1];names=['Standing','Walk','Running','Fidget','Attack','Cast','Hit','Death','Dead'];saved={};report={}
def coords(obj):
 e=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());m=e.to_mesh();a=np.array([obj.matrix_world@v.co for v in m.vertices]);e.to_mesh_clear();return a
bpy.ops.wm.open_mainfile(filepath=str(P/'export/mm8_m500.blend'));sc=bpy.context.scene;sc.render.fps=24;rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body']
# Keep the editable file's material settings consistent with the single-sided portable export.
for mat in body.data.materials:
 mat.use_backface_culling=True
bpy.ops.wm.save_as_mainfile(filepath=str(P/'export/mm8_m500.blend'))
for name in names:
 a=bpy.data.actions[name];rig.animation_data.action=a;lo,hi=a.frame_range;saved[name]=[];minimum=1e9;first=last=None;heights=[]
 for f in np.linspace(lo,hi,round((hi-lo)*4)+1):
  sc.frame_set(int(f),subframe=f-int(f));c=coords(body);minimum=min(minimum,float(c[:,2].min()));first=c if first is None else first;last=c;heights.append(float(np.ptp(c[:,2])))
 assert minimum>-.015,(name,minimum)
 loop=float(np.linalg.norm(last-first,axis=1).max())
 if name in ['Standing','Walk','Running','Dead']:assert loop<.002,(name,loop)
 report[name]={'min_z_dense_96hz':minimum,'loop_delta':loop,'duration':float((hi-lo)/24),'mean_height_m':float(np.mean(heights))}
 for fraction in [0,.125,.25,.375,.5,.625,.75,.875,1]:
  f=lo+(hi-lo)*fraction;sc.frame_set(int(f),subframe=f-int(f));saved[name].append((fraction,coords(body),{s:list(bpy.data.objects[s].matrix_world.translation) for s in ['Socket_Mouth','Socket_PalmL','Socket_PalmR']}))
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(P/('export/mm8_m500_runtime_lod0.glb' if '--lod0' in sys.argv else 'export/mm8_m500.glb')));sc=bpy.context.scene;sc.render.fps=24;rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');body=next(o for o in bpy.data.objects if o.type=='MESH');assert len(bpy.data.actions)==9
for name in names:
 a=next(a for a in bpy.data.actions if a.name==name or a.name.endswith('|'+name));rig.animation_data.action=a
 if len(a.slots):rig.animation_data.action_slot=a.slots[0]
 lo,hi=a.frame_range;errs=[];socketerrs=[]
 for fraction,ref,socket in saved[name]:
  f=lo+(hi-lo)*fraction;sc.frame_set(int(f),subframe=f-int(f));cur=coords(body);tree=KDTree(len(cur))
  for i,c in enumerate(cur):tree.insert(c,i)
  tree.balance();errs.append(max(tree.find(c)[2] for c in ref));socketerrs.append(max(float(np.linalg.norm(np.array(bpy.data.objects[s].matrix_world.translation)-value)) for s,value in socket.items()))
 assert max(errs)<.003,(name,errs)
 assert max(socketerrs)<.0001,(name,socketerrs)
 report[name].update(max_export_surface_error_m=max(errs),max_socket_error_m=max(socketerrs),export_duration=float((hi-lo)/24))
(P/'review/export_parity.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
