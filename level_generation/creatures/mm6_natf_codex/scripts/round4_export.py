"""Bake a non-deforming landmark on the inward envelope of the actual uneven hem.
The shared gate still performs containment; this supplies its garment opening frame.
"""
import bpy,json,sys,numpy as np
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parent/'claude_shared/gates'));import run_gates as g
cfg=json.loads((P/'gates.json').read_text());gb=g.Glb(P/'export/mm6_natf.glb');meshes=g.load_meshes(gb)[:4];loops=[]
for m in meshes:
 mask=m.select(cfg['regions']['skirt']);surf=g.Surface(m,mask,cap=True,opening={'axis':[0,0,-1]});loops.append(m.weld_first[surf.loops[surf.opening]])
bpy.ops.wm.open_mainfile(filepath=str(P/'work/accepted_master.blend'));rig=bpy.data.objects['Rig'];sc=bpy.context.scene;rig.animation_data.action=None;bpy.context.view_layer.objects.active=rig
if 'HemOpening' not in rig.data.bones:
 bpy.ops.object.mode_set(mode='EDIT');b=rig.data.edit_bones.new('HemOpening');b.head=(0,0,0);b.tail=(0,1,0);bpy.ops.object.mode_set(mode='OBJECT')
pb=rig.pose.bones['HemOpening'];pb.rotation_mode='QUATERNION';report={'geometry_source_sha256':gb.sha256,'definition':'Actual hem plane, displaced to the most inward boundary vertex across all four LODs; conservative opening envelope for a non-planar hem.','clips':{}}
for a in bpy.data.actions:
 ga=next(x for x in gb.doc['animations']if x['name']==a.name);frames=np.arange(int(a.frame_range[1])+1);rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];prev=None;offsets=[]
 for f in frames:
  sc.frame_set(int(f));pose=gb.rest.copy()
  for bone in rig.pose.bones:
   if bone.name in gb.names:pose[gb.names[bone.name]]=np.array(bone.matrix@rig.data.bones[bone.name].matrix_local.inverted())@gb.rest[gb.names[bone.name]]
  hems=[m.posed(pose)[ids]for m,ids in zip(meshes,loops)];h=hems[0];center=h.mean(0);normal=-g.unit(np.cross(h-center,np.roll(h,-1,axis=0)-center).sum(0));down=(pose[gb.names['B_Pelvis']]@np.linalg.inv(gb.rest[gb.names['B_Pelvis']]))[:3,:3]@np.array([0,0,-1])
  if np.dot(normal,down)<0:normal=-normal
  d=float(((np.concatenate(hems)-center)@normal).min());point=center+normal*d;offsets.append(-d);q=Vector((0,0,1)).rotation_difference(Vector(normal))
  if prev is not None and q.dot(prev)<0:q=-q
  prev=q.copy();pb.location=point;pb.rotation_quaternion=q;pb.keyframe_insert('location',frame=int(f));pb.keyframe_insert('rotation_quaternion',frame=int(f))
  assert np.max((point-np.concatenate(hems))@normal)<1e-8
 report['clips'][a.name]={'max_mean_to_inward_hem_m':max(offsets)}
 for layer in a.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    for fc in bag.fcurves:
     if 'HemOpening' in fc.data_path:
      for k in fc.keyframe_points:k.interpolation='LINEAR'
rig.animation_data.action=None
for b in rig.pose.bones:b.matrix_basis.identity()
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/accepted_master.blend'));(P/'review/round4/hem_opening.json').write_text(json.dumps(report,indent=2))

import runpy
runpy.run_path(str(P/"scripts/export_runtime.py"),run_name="__main__")
