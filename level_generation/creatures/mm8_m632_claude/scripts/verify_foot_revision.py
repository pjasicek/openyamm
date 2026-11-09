"""Regression for sole planes, planted attack travel, and preserved geometry/UVs/other clips."""
import bpy,numpy as np,sys,math,json,hashlib
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1]
def fingerprints():
 out={}
 for o in bpy.data.objects:
  if o.type!='MESH':continue
  data={'co':[tuple(v.co) for v in o.data.vertices],'faces':[tuple(f.vertices) for f in o.data.polygons],'uv':{l.name:[tuple(d.uv) for d in l.data] for l in o.data.uv_layers},'weights':[[(o.vertex_groups[g.group].name,g.weight) for g in v.groups] for v in o.data.vertices]}
  out[o.name]=hashlib.sha256(json.dumps(data,sort_keys=True).encode()).hexdigest()
 for a in bpy.data.actions:
  if a.name in ('Walking','Running','Attack'):continue
  data=[(fc.data_path,fc.array_index,[tuple(k.co) for k in fc.keyframe_points]) for l in a.layers for s in l.strips for b in s.channelbags for fc in b.fcurves]
  out[a.name]=hashlib.sha256(json.dumps(data).encode()).hexdigest()
 return out
bpy.ops.wm.open_mainfile(filepath=str(P/'work/before_foot_attack_revision/textured_uv.blend'));before=fingerprints()
bpy.ops.wm.open_mainfile(filepath=str(P/'work/textured_uv.blend'));assert fingerprints()==before,'Geometry, UVs, weights or unrelated action changed'
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];sc=bpy.context.scene
co=np.array([v.co[:] for v in body.data.vertices]);pv=np.array([d.value for d in body.data.attributes['piece'].data]);refs={};out={'unchanged':before,'clips':{}}
for s,p in [('R',12),('L',14)]:
 ids=np.where((pv==p)&(co[:,2]<.025))[0];forward=np.array(rig.data.bones[f'B_{s}_Toe0'].head_local-rig.data.bones[f'B_{s}_Foot'].head_local);forward[2]=0;forward/=np.linalg.norm(forward);right=np.cross(forward,[0,0,1]);refs[s]=(ids,forward,right)
for name in ['Standing','Walking','Running','Attack']:
 a=bpy.data.actions[name];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];rows=[]
 for f in np.arange(a.frame_range[1]+1):
  sc.frame_set(int(f));ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();xyz=np.array([v.co[:] for v in me.vertices]);ev.to_mesh_clear()
  info={'frame':float(f),'pelvis':list(rig.pose.bones['B_Pelvis'].matrix.translation),'feet':{}}
  for s,(ids,forward,right) in refs.items():
   x=co[ids]-co[ids].mean(0);y=xyz[ids]-xyz[ids].mean(0);u,_,vt=np.linalg.svd(x.T@y);R=vt.T@u.T
   info['feet'][s]={'roll_deg':math.degrees(math.asin(np.clip((R@right)[2],-1,1))),'pitch_deg':math.degrees(math.asin(np.clip((R@forward)[2],-1,1))),'z_m':float(xyz[ids,2].min())}
  rows.append(info)
 maxroll=max(abs(v['roll_deg']) for r in rows for v in r['feet'].values());floors=[min(v['z_m'] for v in r['feet'].values()) for r in rows]
 movement=np.ptp([r['pelvis'] for r in rows],axis=0).tolist()
 out['clips'][name]={'max_lateral_roll_deg':maxroll,'floor_range_m':[min(floors),max(floors)],'pelvis_travel_m':movement,'samples':rows}
 print(name, 'roll',maxroll,'floor',min(floors),max(floors),'pelvis',movement,flush=True)
 assert maxroll<1,(name,'rolled sole',maxroll)
 assert min(floors)>-.01,(name,'floor penetration',min(floors))
 if name!='Running':assert max(floors)<.01,(name,'floating',max(floors))
 if name=='Attack':assert movement[2]>.025 and movement[0]>.02
(P/'review/foot_revision/measurements.json').write_text(json.dumps(out,indent=2))
