import bpy,sys,json,math,numpy as np
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));from cloth_volume import capped_tree
code=(P/'scripts/extra_metrics.py').read_text();exec(code[code.index('def inside('):code.index('for f in np.linspace')])
report={}
for level in range(4):
 bpy.ops.wm.open_mainfile(filepath=str(P/f'work/export_reimport_lod{level}.blend'));r=bpy.data.objects['Rig'];b=bpy.data.objects['Body'];k=bpy.data.objects['KnifeAsset'];sc=bpy.context.scene;K=r.data.bones['Knife'].matrix_local.inverted();local=np.array([tuple(K@v.co)for v in k.data.vertices]);unique,indices,imap=np.unique(np.round(local,6),axis=0,return_index=True,return_inverse=True);faces=[tuple(imap[list(f.vertices)])for f in k.data.polygons if all(-.075<local[i,2]<.025 for i in f.vertices)];faces=[f for f in faces if len(set(f))==len(f)];counts={}
 for f in faces:
  for i,j in zip(f,list(f[1:])+[f[0]]):e=tuple(sorted((i,j)));counts[e]=counts.get(e,0)+1
 tree=capped_tree(local[indices],faces,[e for e,n in counts.items()if n==1]);gn={g.index:g.name for g in b.vertex_groups};ids=[v.index for v in b.data.vertices if sum(g.weight for g in v.groups if gn[g.group].startswith('B_R_Finger')or gn[g.group]=='B_R_Hand')>.5];worst=0.;witness=None;a=bpy.data.actions['Attack'];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0]
 for f in np.linspace(0,a.frame_range[1],math.ceil(a.frame_range[1]*48/30)+1):
  sc.frame_set(int(f),subframe=float(f%1));inverse=r.pose.bones['Knife'].matrix.inverted();ev=b.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
  for i in ids:
   point=inverse@me.vertices[i].co;loc,no,face,dist=tree.find_nearest(point,.02)
   if loc is not None and dist>worst and face<len(faces) and inside(tree,point):worst=dist;witness={'time':float(f/30),'vertex':i}
  ev.to_mesh_clear()
 def pose(name,frame):
  a=bpy.data.actions[name];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];sc.frame_set(int(frame),subframe=frame%1);return np.array([np.array(pb.matrix)for pb in r.pose.bones])
 death=pose('Death',float(bpy.data.actions['Death'].frame_range[1]));dead=pose('Dead',0);error=float(abs(death-dead).max());assert error<1e-5
 report[str(level)]={'sample_hz':48,'hand_handle_penetration_mm':worst*1000,'witness':witness,'death_to_dead_max_matrix_error':error,'pass':worst<=.002};print('HANDLE_CONTACT',level,report[str(level)],flush=True)
(P/'review/handle_contact.json').write_text(json.dumps(report,indent=2));assert all(v['pass']for v in report.values())
