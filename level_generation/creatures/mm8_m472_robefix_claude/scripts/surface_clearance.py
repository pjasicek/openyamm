"""Small garment-only translation correctives from evaluated surface contacts, after the chain simulation.
Body limbs retain fixed-length source-frame motion. Waist attachment vertices retain their body weights.
"""
from pathlib import Path
import bpy,json
import numpy as np
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
p=Path(__file__).resolve().parents[1]
# gait2 (2026-10-21): INPUT_BLEND/OUTPUT_BLEND/CLIPS/LOOPS may be given as runpy init_globals (defaults: production run).
bpy.ops.wm.open_mainfile(filepath=str(p/'work'/globals().get('INPUT_BLEND','rig_polished.blend')))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];me=body.data;sc=bpy.context.scene
pv=np.array([x.value for x in me.attributes['piece'].data]);cr=np.array([x.value for x in me.attributes['cloth_region'].data]);CH=json.loads(sc['garment_chains']);bones=[n for c in CH for n in c['bones']];column={n:i for i,n in enumerate(bones)};W=np.zeros((len(me.vertices),len(bones)))
for v in me.vertices:
 for g in v.groups:
  n=body.vertex_groups[g.group].name
  if n in column:W[v.index,column[n]]=g.weight
faces=[tuple(f.vertices) for f in me.polygons if all(pv[i]==12 for i in f.vertices)]
cloth=np.where(cr>0)[0];robe=np.where(cr==1)[0];reg=np.eye(len(bones))*.025
for c in CH:
 for a,b in zip(c['bones'][:-1],c['bones'][1:]):
  d=np.zeros(len(bones));d[column[a]]=1;d[column[b]]=-1;reg+=np.outer(d,d)*.02

def setact(a):
 rig.animation_data.action=a
 if a is not None and a.slots:rig.animation_data.action_slot=a.slots[0]
def posed():
 ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();co=np.array([tuple(v.co) for v in m.vertices]);ev.to_mesh_clear();return co

def corrections(co,tree):
 out={}
 for i in cloth:
  if co[i,2]<.003:out[i]=np.array([0.,0.,.003-co[i,2]])
 direction=Vector((1,.371,.237)).normalized()
 for i in robe:
  pt=Vector(co[i]);loc,n,_,dist=tree.find_nearest(pt)
  if loc is None or (pt-loc).dot(n)>=0:continue
  origin=pt;crossings=0
  for _ in range(20):
   q,_,_,_=tree.ray_cast(origin,direction)
   if q is None:break
   crossings+=1;origin=q+direction*.00001
  if crossings%2:
   d=np.array(loc+n*.006)-co[i]
   if i in out:d[2]=max(d[2],out[i][2])
   out[i]=d
 return out
report={}
for act in [a for a in bpy.data.actions if a.use_fake_user]:
 if act.name not in globals().get('CLIPS',['Standing','Walking','Running','Attack','Cast','Hit','Death','Fidget']):continue
 rows=[];worst=0.;remaining=0;max_shift=0.;previous=np.zeros((len(bones),3));frames=range(int(act.frame_range[1])+1)
 for f in frames:
  setact(act);sc.frame_set(f);snap={b.name:b.matrix_basis.copy() for b in rig.pose.bones};base={n:rig.pose.bones[n].matrix.copy() for n in bones}
  setact(None)
  for b in rig.pose.bones:b.matrix_basis=snap[b.name]
  bpy.context.view_layer.update();co=posed();tree=BVHTree.FromPolygons(co.tolist(),faces);delta=np.zeros_like(previous)
  for iteration in range(5):
   fix=corrections(co,tree)
   if not fix:break
   ids=np.array(list(fix));A=W[ids];target=np.array([fix[i] for i in ids]);valid=A.sum(1)>.03;A=A[valid];target=target[valid]
   if not len(A):break
   step=np.linalg.solve(A.T@A+reg,A.T@target-reg@delta*.15)
   delta+=step;length=np.linalg.norm(delta,axis=1);delta*=np.minimum(1,.09/np.maximum(length,1e-9))[:,None]
   for n in bones:
    m=base[n].copy();m.translation+=Vector(delta[column[n]]);rig.pose.bones[n].matrix=m;bpy.context.view_layer.update()
   co=posed()
  fix=corrections(co,tree);remaining=max(remaining,len(fix));worst=max(worst,max((float(np.linalg.norm(d)) for d in fix.values()),default=0));max_shift=max(max_shift,float(np.linalg.norm(delta,axis=1).max()));previous=delta
  rows.append({n:rig.pose.bones[n].location.copy() for n in bones})
 if act.name in globals().get('LOOPS',['Standing','Walking','Running','Fidget']):rows[-1]=rows[0]
 setact(act)
 for f,row in enumerate(rows):
  for n,l in row.items():rig.pose.bones[n].location=l;rig.pose.bones[n].keyframe_insert('location',frame=f)
 report[act.name]={'max_control_shift_m':max_shift,'remaining_contact_count':remaining,'remaining_correction_m':worst}
 print('SURFACE_CLEARANCE',act.name,report[act.name],flush=True)
setact(None)
for b in rig.pose.bones:b.matrix_basis.identity()
old=json.loads((p/'work/surface_clearance.json').read_text()) if globals().get('CLIPS') and (p/'work/surface_clearance.json').exists() else {}
old.update(report);(p/'work/surface_clearance.json').write_text(json.dumps(old,indent=2)+'\n')
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work'/globals().get('OUTPUT_BLEND','rig_gated.blend')))
