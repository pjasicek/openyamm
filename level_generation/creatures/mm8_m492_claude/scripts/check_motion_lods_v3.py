"""Sample the exported lower LODs through the revised Attack/Cast clips."""
import bpy,json,sys,copy
import numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parents[2]/'tools'))
from build_actor_lods import read_glb,write_glb
D,B=read_glb(P/'export/mm8_m492.glb');node=next(n for n in D['nodes'] if n.get('name')=='Body');levels=D['meshes'][node['mesh']]['extras']['openyamm_lods'];report={}
for level,index in enumerate(levels,1):
 d=copy.deepcopy(D);next(n for n in d['nodes'] if n.get('name')=='Body')['mesh']=index;path=P/'work'/f'lod{level}_review.glb';write_glb(path,d,B)
 bpy.ops.wm.read_factory_settings(use_empty=True);sc=bpy.context.scene;sc.render.fps=24;bpy.ops.import_scene.gltf(filepath=str(path));o=bpy.data.objects['Body'];rig=next(m.object for m in o.modifiers if m.type=='ARMATURE')
 item={};acts={a.name.rsplit('|',1)[-1]:a for a in bpy.data.actions}
 for name,act in acts.items():
  if name.rsplit('_',1)[-1] not in ('Attack','Cast'):continue
  rig.animation_data.action=act
  if act.slots:rig.animation_data.action_slot=act.slots[0]
  start,end=act.frame_range;minimum=10
  for f in np.arange(start,end+.1,.5):
   sc.frame_set(int(f),subframe=f%1);ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();co=np.array([tuple(ev.matrix_world@v.co) for v in me.vertices]);ev.to_mesh_clear();assert np.isfinite(co).all();minimum=min(minimum,float(co[:,2].min()))
  item[name]={'minimum_z':minimum}
 report[level]=item;print('LOD_FLOORS',level,item,flush=True)
(P/'review/motion_v3/lod_motion_checks.json').write_text(json.dumps(report,indent=2)+'\n')
assert all(v['minimum_z']>-.002 for r in report.values() for v in r.values()),'LOD penetrates floor'
