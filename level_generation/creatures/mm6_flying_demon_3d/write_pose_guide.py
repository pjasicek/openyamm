"""Record actual final-rig anchor values as an inspectable reconstruction guide."""
from pathlib import Path
import bpy,json,math,importlib.util
from mathutils import Vector
P=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(P/'delivery/mm6_flying_demon.blend'))
scene=bpy.context.scene;rig=next(o for o in scene.objects if o.type=='ARMATURE')
spec=importlib.util.spec_from_file_location('flying_export',P/'export.py');ex=importlib.util.module_from_spec(spec);spec.loader.exec_module(ex)
study=json.loads((P/'motion_study.json').read_text())
names=[b.name for b in rig.pose.bones]
report={'coordinate_system':'Blender scene, metres; +Z up, -Y front, +X creature left. Local rotations relative to inherited rest bind.', 'evidence':'Numeric values below are the delivered 3D extrapolation, not measurements of invisible sprite depth.', 'clips':{}}
lines=['# Final flying-demon pose guide','',report['coordinate_system'],'',report['evidence'],'','Each anchor in `pose_manifest.json` includes all 89 joints, with local quaternions/XYZ degrees, world joint positions, elbow bend and palm normal. Every hand digit, forearm twist, wing control and jaw hinge is included. `animate.py` records authored targets, body contribution, secondary-arm balance and continuous local wrist profiles.','']
for clip,record in study['clips'].items():
 rows=[];anchors=record.get('anchors',[{'frame':0,'source':'m496xa','observation':'Held native ash'}])
 lines+=['## '+clip,'','| Frame / seconds | Native phase | Left wrist XYZ | Right wrist XYZ | Elbow bend L/R | Palm normal L/R |','| --- | --- | --- | --- | --- | --- |']
 for anchor in anchors:
  frame=anchor['frame'];ex.activate(scene,clip,frame);row={'frame':frame,'time_s':frame/48,'source':anchor['source'],'observation':anchor.get('observation'),'joints':{},'arms':{}}
  for name in names:
   b=rig.pose.bones[name];q=b.matrix_basis.to_quaternion();q.normalize()
   row['joints'][name]={'local_quaternion_wxyz':list(q),'local_xyz_degrees':[math.degrees(x) for x in q.to_euler('XYZ')],'world_head':list(rig.matrix_world@b.head),'world_tail':list(rig.matrix_world@b.tail)}
  for side in ('Left','Right'):
   a,b,c=[rig.pose.bones['mixamorig:'+side+part] for part in ('Arm','ForeArm','Hand')]
   digit=[rig.data.bones['mixamorig:'+side+'Hand'+d+'1'].head_local for d in ('Index','Middle','Pinky','Ring')]
   long=sum(digit,Vector())/4-c.bone.head_local;width=digit[-1]-digit[0];normal=width.cross(long).normalized()
   if side=='Left':normal.negate()
   posed=(rig.matrix_world.to_3x3()@(c.matrix@c.bone.matrix_local.inverted()).to_3x3()@normal).normalized()
   row['arms'][side]={'wrist_world':list(rig.matrix_world@c.head),'palm_normal_world':list(posed),'elbow_bend_degrees':math.degrees((b.head-a.head).angle(c.head-b.head))}
  rows.append(row)
  def vec(v):return ', '.join(f'{x:.3f}' for x in v)
  l,r=row['arms']['Left'],row['arms']['Right'];lines.append(f'| {frame} / {frame/48:.3f} | {anchor["source"]} | {vec(l["wrist_world"])} | {vec(r["wrist_world"])} | {l["elbow_bend_degrees"]:.1f} / {r["elbow_bend_degrees"]:.1f} | {vec(l["palm_normal_world"])} / {vec(r["palm_normal_world"])} |')
 report['clips'][clip]=rows;lines.append('')
(P/'pose_manifest.json').write_text(json.dumps(report,indent=2)+'\n');(P/'POSE_GUIDE.md').write_text('\n'.join(lines)+'\n')
