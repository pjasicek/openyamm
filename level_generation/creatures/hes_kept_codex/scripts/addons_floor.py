"""Half-frame final floor fit using every boot vertex, or every body vertex during a fall."""
import bpy,sys,os,json
from pathlib import Path
import numpy as np
from mathutils import Matrix
src,out=sys.argv[sys.argv.index('--')+1:];kind=os.environ['KEPT_BODY'];P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Kept'];sc=bpy.context.scene
pc=np.array([a.value for a in body.data.attributes['piece'].data]);feet=np.isin(pc,(5,6) if kind=='male' else (5,7));report={}
for a in list(bpy.data.actions):
 if not a.name.startswith('Kept_Club') or 'Dead' in a.name:continue
 rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];keys=[]
 for f in np.arange(0,a.frame_range[1]+.01,.5):
  sc.frame_set(int(f),subframe=float(f%1));ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();z=np.array([(body.matrix_world@v.co).z for v in m.vertices]);ev.to_mesh_clear()
  low=float(z.min() if 'Death' in a.name else z[feet].min());dz=max(-low,0) if 'Running' in a.name else -low
  pb=rig.pose.bones['B_Pelvis'];M=pb.matrix.copy();M.translation.z+=dz;pb.matrix=M;bpy.context.view_layer.update();keys.append((f,pb.location.copy(),dz))
 for f,l,dz in keys:
  pb=rig.pose.bones['B_Pelvis'];pb.location=l;pb.keyframe_insert('location',frame=float(f))
 report[a.name]={'floor_shift_m':[min(x[2] for x in keys),max(x[2] for x in keys)]}
 if 'Death' in a.name:
  dead=bpy.data.actions[a.name.replace('Death','Dead')];sc.frame_set(int(a.frame_range[1]));snapshot={p.name:(p.rotation_quaternion.copy(),p.location.copy()) for p in rig.pose.bones}
  rig.animation_data.action=dead;rig.animation_data.action_slot=dead.slots[0]
  for f in (0,1):
   for n,(q,l) in snapshot.items():
    pb=rig.pose.bones[n];pb.rotation_mode='QUATERNION';pb.rotation_quaternion=q;pb.location=l;pb.keyframe_insert('rotation_quaternion',frame=f)
    if n=='B_Pelvis':pb.keyframe_insert('location',frame=f)
rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
(P/'review/addons_v2/floor_fit.json').write_text(json.dumps(report,indent=2)+'\n')
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))

sys.stdout.flush();sys.stderr.flush();os._exit(0)
