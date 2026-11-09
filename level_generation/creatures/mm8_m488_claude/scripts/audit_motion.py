from pathlib import Path
import bpy,sys,numpy as np,json
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import common
src=sys.argv[sys.argv.index('--')+1];bpy.ops.wm.open_mainfile(filepath=str(Path(src).resolve()))
body=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];me=body.data
# Dense edge screens and representative actual-mesh poses, independent of bone naming.
rest=np.array([v.co[:] for v in me.vertices]);edges=np.array([e.vertices[:] for e in me.edges]);rl=np.linalg.norm(rest[edges[:,0]]-rest[edges[:,1]],axis=1)
pieces=np.array([x.value for x in me.attributes['piece'].data]);skin=(pieces[edges[:,0]]==0)&(pieces[edges[:,1]]==0)
hand=(np.abs(rest[:,0])>.73);arm=(np.abs(rest[:,0])>.23)&(rest[:,2]>1.25)&(rest[:,2]<1.73)
regions={'hands':skin&hand[edges[:,0]]&hand[edges[:,1]],'arms':skin&arm[edges[:,0]]&arm[edges[:,1]],'wrap':pieces[edges[:,0]]==1}
report={};out=p/'review/cage';out.mkdir(parents=True,exist_ok=True)
common.workbench_clay(bpy.context.scene)
for name in ('Standing','Walking','Running','Attack','Hit','Fidget','Death','Dead'):
 act=bpy.data.actions[name];rig.animation_data.action=act
 if act.slots:rig.animation_data.action_slot=act.slots[0]
 f0,f1=act.frame_range;record={r:{'p99':0,'max':0} for r in regions};record['floor_min']=99
 for f in np.arange(f0,f1+.01,.5):
  bpy.context.scene.frame_set(int(f),subframe=float(f%1));ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh();co=np.array([v.co[:] for v in mesh.vertices]);ev.to_mesh_clear()
  st=np.linalg.norm(co[edges[:,0]]-co[edges[:,1]],axis=1)/np.maximum(rl,1e-7)
  for r,mask in regions.items():
   mx=float(st[mask].max());p99=float(np.percentile(st[mask],99))
   if mx>record[r]['max']:record[r].update(max=mx,frame=float(f),edge=[int(v) for v in edges[mask][np.argmax(st[mask])]])
   record[r]['p99']=max(p99,record[r]['p99'])
  record['floor_min']=min(record['floor_min'],float(co[:,2].min()))
 for i,f in enumerate([f0,(f0+f1)/2,f1]):
  bpy.context.scene.frame_set(int(f),subframe=float(f%1));common.render_views(str(out/f'{name}_{i:02d}'),1.05,2.5,views=('front','left','three_quarter'),resolution=(640,640))
 report[name]=record
(p/'review/animation/measurements.json').write_text(json.dumps(report,indent=2)+'\n');print('PILOT',json.dumps(report))
