"""Dense authored animation checks before UV freeze and export."""
import bpy,json,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/reduced.blend'))
o=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];sc=bpy.context.scene
rest=np.array([v.co[:] for v in o.data.vertices]);edges=np.array([e.vertices[:] for e in o.data.edges]);length=np.linalg.norm(rest[edges[:,0]]-rest[edges[:,1]],axis=1)
for v in o.data.vertices:
 w=[g.weight for g in v.groups if g.weight>1e-7];assert 1<=len(w)<=4 and abs(sum(w)-1)<1e-5
report={};surfaces={}
for act in bpy.data.actions:
 rig.animation_data.action=act;start,end=act.frame_range;minimum=1e6;maximum=0;stretch=[];ends=[]
 for f in np.arange(start,end+.25,.5):
  sc.frame_set(int(f),subframe=f%1);ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
  co=np.array([v.co[:] for v in me.vertices]);ev.to_mesh_clear();assert np.isfinite(co).all()
  minimum=min(minimum,float(co[:,2].min()));maximum=max(maximum,float(co[:,2].max()))
  el=np.linalg.norm(co[edges[:,0]]-co[edges[:,1]],axis=1);stretch.append(float(np.quantile(el/np.maximum(length,1e-9),.999)))
  if f in (start,end):ends.append(co.copy())
 delta=float(np.max(np.linalg.norm(ends[0]-ends[1],axis=1)))
 assert minimum>-.0002,(act.name,minimum)
 if act.name in ('Standing','Walking','Running','Fidget','Dead'):assert delta<1e-5,(act.name,delta)
 report[act.name]={'sample_rate':48,'minimum_z':minimum,'maximum_z':maximum,'end_difference':delta,'p999_edge_stretch':max(stretch)}
 surfaces[act.name]=ends
assert np.max(abs(surfaces['Death'][-1]-surfaces['Dead'][0]))<1e-6
assert np.max(abs(surfaces['Attack'][0]-surfaces['Cast'][0]))<1e-6
(P/'review/animation_gate_reduced.json').write_text(json.dumps(report,indent=2)+'\n');print('ANIMATION_GATE',report)
