"""Check final colour LOD contacts against the delivered clips."""
import bpy,sys,json,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parents[2]/'tools'))
from build_actor_lods import read_glb,write_glb
d,b=read_glb(P/'export/mm8_m516.glb');node=next(n for n in d['nodes'] if n.get('name')=='Body');ids=[node['mesh']]+d['meshes'][node['mesh']]['extras']['openyamm_lods'];dur=json.loads((P/'work/animation_audit.json').read_text());report={}
for level,mesh in enumerate(ids):
 node['mesh']=mesh;temp=P/'work/lod_motion_review.glb';write_glb(temp,d,b);bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(temp));rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');body=next(o for o in bpy.data.objects if o.type=='MESH');sc=bpy.context.scene;sc.render.fps=24;report[level]={}
 for role,meta in dur.items():
  a=next(a for a in bpy.data.actions if a.name==role or a.name.endswith('|'+role));rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];floor=10
  for t in np.linspace(0,meta['duration'],13):
   f=1+t*24;sc.frame_set(int(f),subframe=f%1);ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();z=min((ev.matrix_world@v.co).z for v in me.vertices);ev.to_mesh_clear();floor=min(floor,z)
  assert floor>-.035,(level,role,floor);report[level][role]=floor
(P/'review/checks/lod_motion.json').write_text(json.dumps(report,indent=2)+'\n');print('LOD FLOORS',report)
