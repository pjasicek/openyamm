"""Compare posed surfaces after GLB reimport, including the independently animated crossbow."""
import bpy,json,sys
import numpy as np
from pathlib import Path
from mathutils.kdtree import KDTree
P=Path(__file__).resolve().parents[1]
def coordinates(o):
 ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();co=np.array([tuple(o.matrix_world@v.co) for v in me.vertices]);ev.to_mesh_clear();return co
bpy.ops.wm.open_mainfile(filepath=str(P/'export/mm8_m632.blend'))
rig=bpy.data.objects['Rig'];mesh=bpy.data.objects['DarkDwarf'];sc=bpy.context.scene;expected={}
for a in bpy.data.actions:
 rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];poses=[]
 fractions=np.linspace(0,1,7)
 if a.name=='Attack':fractions=np.unique(np.r_[fractions,np.arange(44/48,1.05,1/240)/1.55])
 for f in a.frame_range[0]+fractions*(a.frame_range[1]-a.frame_range[0]):
  sc.frame_set(int(f),subframe=float(f%1));poses.append(coordinates(mesh))
 expected[a.name]=(fractions,poses)
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(P/'export/mm8_m632_runtime_lod0.glb'))
rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');mesh=bpy.data.objects['DarkDwarf'];sc=bpy.context.scene;report={}
for name,(fractions,poses) in expected.items():
 a=next(a for a in bpy.data.actions if a.name==name or a.name.endswith('_'+name) or a.name.startswith(name+'_'))
 rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];error=0
 for f,ref in zip(a.frame_range[0]+fractions*(a.frame_range[1]-a.frame_range[0]),poses):
  sc.frame_set(int(f),subframe=float(f%1));co=coordinates(mesh);tree=KDTree(len(ref))
  for i,v in enumerate(ref):tree.insert(v,i)
  tree.balance();error=max(error,max(tree.find(v)[2] for v in co))
 assert error<.003,(name,error)
 report[name]={'max_surface_error_m':error,'samples':len(poses),'duration_s':float((a.frame_range[1]-a.frame_range[0])/sc.render.fps)}
(P/'review/export_parity.json').write_text(json.dumps(report,indent=2));print('EXPORT PARITY',report,flush=True)
