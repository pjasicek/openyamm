"""Compare the delivered body and Crossbow bone with the packed animated master, including fractional attack samples."""
from pathlib import Path
import bpy,json,numpy as np
from mathutils.kdtree import KDTree
p=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(p/'export/mm8_m416.blend'));sc=bpy.context.scene;sc.render.fps=30
rig=bpy.data.objects['Rig'];body=bpy.data.objects['PirateCrossbowwoman'];names=['Standing','Walking','Running','Attack','Hit','Fidget','Death','Dead'];saved={}
ids=[body.vertex_groups[n].index for n in ['Crossbow','Bolt','Quiver','StringL','StringR']];mask=np.array([sum(g.weight for g in v.groups if g.group in ids)<.5 for v in body.data.vertices])
used={v for f in body.data.polygons for v in f.vertices}
mask &= np.array([v.index in used for v in body.data.vertices])
print('MASTER non-surface vertices excluded',len(body.data.vertices)-len(used),flush=True)
def points(o):
 ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();co=np.array([o.matrix_world@v.co for v in m.vertices]);ev.to_mesh_clear();return co
def bone():return np.stack([np.array(rig.matrix_world@rig.pose.bones[n].matrix) for n in ['Crossbow','Bolt','Quiver','StringL','StringR','Socket_Bolt']])
for n in names:
 a=bpy.data.actions[n];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];lo,hi=a.frame_range;saved[n]=[]
 fs=sorted(set([lo+(hi-lo)*x for x in (0,.13,.33,.5,.79,1)]+(list(np.arange(27,34,.25)) if n=='Attack' else [])))
 for f in fs:
  sc.frame_set(int(f),subframe=f-int(f));saved[n].append((f/30,points(body)[mask],np.array(bone())))
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.context.scene.render.fps=30;bpy.ops.import_scene.gltf(filepath=str(p/'export/mm8_m416.glb'));sc=bpy.context.scene
rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');body=next(o for o in bpy.data.objects if o.type=='MESH' and o.name=='PirateCrossbowwoman');report={}
for n in names:
 a=next(a for a in bpy.data.actions if a.name==n or a.name.endswith('|'+n));rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];errors=[];bones=[]
 for sec,ref,bm in saved[n]:
  f=sec*30;sc.frame_set(int(f),subframe=f-int(f));co=points(body);tree=KDTree(len(co))
  for i,v in enumerate(co):tree.insert(v,i)
  tree.balance();dist=[tree.find(v)[2] for v in ref];errors.append(max(dist));bones.append(float(np.abs(np.array(bone())-bm).max()))
 report[n]={'samples':len(errors),'max_surface_error_m':max(errors),'max_equipment_bone_matrix_error':max(bones),'duration_s':a.frame_range[1]/30}
 assert max(errors)<.003,(n,errors)
 assert max(bones)<.0002,(n,bones)
(p/'review/export_parity.json').write_text(json.dumps(report,indent=2));print('EXPORT_PARITY',json.dumps(report))
