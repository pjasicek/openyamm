"""Reimport the actual preview, compare new motion and check all shoulder poses at 192 Hz."""
from pathlib import Path
import bpy,sys,json,numpy as np,math
from mathutils.kdtree import KDTree
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'))
from shoulder_intersections import intersections
manifest=json.loads((P/'review/viewer/manifest.json').read_text())
routes={
 'mm6_fgt_motion_preview':('motion_preview','rig_motion_preview.blend',('Running','Attack')),
 'mm6_fgt_attack_options':('attack_options','rig_attack_options.blend',('Running','AttackRPG5','AttackRPG6','AttackOutward')),
 'mm6_fgt_attack_windup':('attack_windup','rig_attack_windup.blend',('Running','AttackRPG6')),
 'mm6_fgt_attack_body':('attack_body','rig_attack_body.blend',('Running','AttackRPG6')),
}
review,blend,ACTS=routes[manifest['revision']]
OUT=P/'review'/review;master='work/'+blend
bpy.ops.wm.open_mainfile(filepath=str(P/master))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];pv=np.array([v.value for v in body.data.attributes['piece'].data])
kd=KDTree(len(pv))
for v in body.data.vertices:kd.insert(body.matrix_world@v.co,v.index)
kd.balance();names=[b.name for b in rig.data.bones];samples={}
for name in ACTS:
 act=bpy.data.actions[name];rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0]
 rows=[]
 for t in np.linspace(0,act.frame_range[1]/30,round(act.frame_range[1]/30*48)+1):
  f=t*30;bpy.context.scene.frame_set(int(f),subframe=float(f%1))
  rows.append({'time':float(t),'positions':np.array([(rig.matrix_world@rig.pose.bones[n].head)[:] for n in names]).tolist()})
 samples[name]=rows
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(P/'review/viewer'/manifest['model']))
rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');body=next(o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith('Thug'))
me=body.data;me.calc_loop_triangles();parts=[]
for v in me.vertices:
 loc,i,d=kd.find(body.matrix_world@v.co);parts.append(int(pv[i]) if d<2e-5 else -1)
parts=np.array(parts);ids=np.where(parts==11)[0];si=np.where(parts==7)[0]
assert len(ids)>=60 and len(si)>=190,(len(ids),len(si))
def faces(ids):
 lookup={int(v):i for i,v in enumerate(ids)}
 return np.array([[lookup[v] for v in t.vertices] for t in me.loop_triangles if all(v in lookup for v in t.vertices)])
pf=faces(ids);sf=faces(si);rows={};fps=bpy.context.scene.render.fps
attribute=me.attributes.new('piece','INT','POINT');attribute.data.foreach_set('value',parts)
from g6_head_clearance import Clearance
head_check=Clearance(body)
for act in list(bpy.data.actions):
 rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0];f0,f1=act.frame_range
 row={'samples':0,'crossings':[],'head_depth_m':0}
 for f in np.arange(f0,f1+.0001,fps/192):
  bpy.context.scene.frame_set(int(f),subframe=float(f%1));ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();co=np.array([v.co[:] for v in m.vertices]);ev.to_mesh_clear()
  if manifest['revision']=='mm6_fgt_attack_body' and act.name=='AttackRPG6':
   matrix=np.array(body.matrix_world);row['floor_min_m']=min(row.get('floor_min_m',0),float((co@matrix[2,:3]+matrix[2,3]).min()))
  hits=intersections(co[si],sf,co[ids],pf);row['samples']+=1
  if hits:row['crossings'].append([float(f)/fps,len(hits)])
  if row['samples']%4==1:row['head_depth_m']=max(row['head_depth_m'],float(head_check.measure()[0]))
 if act.name in samples:
  maximum=0;positions=[]
  for ref in samples[act.name]:
   f=ref['time']*fps;bpy.context.scene.frame_set(int(f),subframe=float(f%1))
   pos=np.array([(rig.matrix_world@rig.pose.bones[n].head)[:] for n in names]);positions.append(pos)
   maximum=max(maximum,float(np.linalg.norm(pos-np.array(ref['positions']),axis=1).max()))
  row['joint_parity_max_m']=maximum
  if act.name=='Running':row['loop_joint_error_m']=float(np.linalg.norm(positions[-1]-positions[0],axis=1).max())
 rows[act.name]=row;print('EXPORT_CHECK',act.name,'samples',row['samples'],'crossings',len(row['crossings']),'head_depth_m',row['head_depth_m'],'joint_error',row.get('joint_parity_max_m'),flush=True)
(OUT/'export_checks.json').write_text(json.dumps({'sample_hz':192,'clips':rows},indent=2)+'\n')
assert set(rows)==set(manifest['clips'])
assert all(not row['crossings'] for row in rows.values()),'Shoulder crossings in preview'
assert all(row.get('joint_parity_max_m',0)<.00002 for row in rows.values()),'Export pose differs'
assert rows['Running']['loop_joint_error_m']<.00002
assert max(row['head_depth_m'] for row in rows.values())<.01,'Head touches shoulder'

assert all(row.get('floor_min_m',0)>-.002 for row in rows.values()),'Foot penetrates floor'
