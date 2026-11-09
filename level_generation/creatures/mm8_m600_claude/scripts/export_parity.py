import bpy,json,math,sys
import numpy as np
from pathlib import Path
from mathutils import Vector,kdtree
P=Path(__file__).resolve().parents[1]
def coords(ob):
 ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();co=np.array([tuple(ob.matrix_world@v.co) for v in me.vertices]);ev.to_mesh_clear();return co
bpy.ops.wm.open_mainfile(filepath=str(P/'work/nightmare_final.blend'));rig=bpy.data.objects['NightmareRig'];ob=bpy.data.objects['Nightmare'];base=np.array([tuple(ob.matrix_world@v.co) for v in ob.data.vertices]);samples={}
for act in bpy.data.actions:
 rig.animation_data.action=None
 for bone in rig.pose.bones:bone.matrix_basis.identity()
 rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0];rows=[]
 for f in sorted(set([0.,float(act.frame_range[1]),*[float(x) for x in np.arange(0,act.frame_range[1],2.5)]])):
  bpy.context.scene.frame_set(int(f),subframe=f%1);rows.append((f,coords(ob)))
 samples[act.name]=rows
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.context.scene.render.fps=120;bpy.ops.import_scene.gltf(filepath=str(P/'export/mm8_m600_lod0.glb'));rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');ob=bpy.data.objects['Nightmare'];rest=np.array([tuple(ob.matrix_world@v.co) for v in ob.data.vertices]);tree=kdtree.KDTree(len(base))
for i,p in enumerate(base):tree.insert(Vector(p),i)
tree.balance();mapping=[];worst=0
for p in rest:_,i,d=tree.find(Vector(p));mapping.append(i);worst=max(worst,d)
assert worst<.0001,worst
report={}
for name,rows in samples.items():
 act=bpy.data.actions[name];rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0];m=0;mf=0;keymax=0
 for f,reference in rows:
  bpy.context.scene.frame_set(int(f),subframe=f%1);diff=np.linalg.norm(coords(ob)-reference[mapping],axis=1);v=float(diff.max())
  if v>m:m,mf=v,f
  if f%1==0:keymax=max(keymax,v)
 report[name]={'max_surface_error_mm':m*1000,'worst_frame':mf,'integer_frame_error_mm':keymax*1000};print('PARITY',name,report[name],flush=True)
# Between 120Hz export samples, sub-millimetre slerp/Blender interpolation differences are below a native texel.
assert max(v['max_surface_error_mm'] for v in report.values())<1.0
assert max(v['integer_frame_error_mm'] for v in report.values())<.1
(P/'work/export_parity.json').write_text(json.dumps({'rest_correspondence_mm':worst*1000,'clips':report},indent=2))
