import bpy,json,math
import numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];out=P/'review/walk_posture_v2';samples={};report={};action_signatures={}
def signature(a):
 return [(fc.data_path,fc.array_index,[(tuple(k.co),k.interpolation) for k in fc.keyframe_points]) for layer in a.layers for strip in layer.strips for bag in strip.channelbags for fc in bag.fcurves]
for version,path in [('before',out/'before/export/mm6_ert.blend'),('after',out/'candidate.blend')]:
 bpy.ops.wm.open_mainfile(filepath=str(path));rig=bpy.data.objects['Rig'];body=bpy.data.objects['EarthElemental'];scene=bpy.context.scene
 action_signatures[version]={a.name:signature(a) for a in bpy.data.actions if a.name!='Walking'}
 a=bpy.data.actions['Walking'];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0]
 rest=np.array([v.co[:] for v in body.data.vertices]);edges=np.array([e.vertices[:] for e in body.data.edges]);length=np.linalg.norm(rest[edges[:,0]]-rest[edges[:,1]],axis=1)
 foot_ids={g.index for g in body.vertex_groups if 'Foot' in g.name or 'Toe' in g.name};feet=np.array([sum(g.weight for g in v.groups if g.group in foot_ids)>.8 for v in body.data.vertices])
 upper=(rest[:,2]>1.70)&(rest[:,2]<2.12);mask=upper[edges[:,0]]&upper[edges[:,1]];row=[];stretch=[];floor=[]
 for frame in np.linspace(0,86,173):
  scene.frame_set(math.floor(frame),subframe=frame%1);ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh();co=np.array([v.co[:] for v in mesh.vertices]);ev.to_mesh_clear();assert np.isfinite(co).all()
  assert all(max(abs(x-1) for x in b.scale)<1e-4 for b in rig.pose.bones)
  row.append(co);floor.append(float(co[:,2].min()));stretch.append(float(np.percentile((np.linalg.norm(co[edges[:,0]]-co[edges[:,1]],axis=1)/length)[mask],99)))
 samples[version]=np.array(row);report[version]={'floor_range': [min(floor),max(floor)],'upper_body_stretch_p99_max':max(stretch)}
assert action_signatures['before']==action_signatures['after'],'Unrelated clip changed'
foot_error=float(np.linalg.norm(samples['before'][:,feet]-samples['after'][:,feet],axis=2).max());assert foot_error<1e-6,foot_error
assert report['after']['floor_range'][0]>-.003 and report['after']['floor_range'][1]<.008
assert report['after']['upper_body_stretch_p99_max']<=report['before']['upper_body_stretch_p99_max']+.03
report.update(feet_max_change_m=foot_error,unchanged_other_clips=6,dense_samples=173)
(out/'deformation_audit.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
