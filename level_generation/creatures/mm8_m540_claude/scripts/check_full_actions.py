"""Measure the actual Mage head against its high collar and shoulders, plus action deformation."""
from pathlib import Path
import bpy,sys,runpy,os,json,numpy as np
from mathutils.bvhtree import BVHTree
p=Path(__file__).resolve().parents[1]
blend=Path(os.environ.get('MAGE_BLEND',str(p/'work/full_actions.blend')));stage=os.environ.get('MAGE_CHECK_STAGE','full')
def run(name,args):
 s=p/'scripts'/name;sys.argv=[str(s),'--']+[str(x) for x in args];runpy.run_path(str(s),run_name='__main__')
run('full_contacts.py',[])
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];me=body.data
pv=np.array([x.value for x in me.attributes['piece'].data]);P=np.array([tuple(v.co) for v in me.vertices]);q=P[:,2]-.2*P[:,1]
head=[tuple(f.vertices) for f in me.polygons if me.attributes['head'].data[f.index].value and all(q[i]>1.395 for i in f.vertices)]
collar=[tuple(f.vertices) for f in me.polygons if not me.attributes['head'].data[f.index].value and all((pv[i]==1 and P[i,2]>1.29) or (pv[i]==0 and abs(P[i,0])>.12 and 1.1<P[i,2]<1.40) or 13<=pv[i]<=24 for i in f.vertices)]
assert len(head)>100 and len(collar)>100
report={}
for name in ['Standing','Walking','Running','Attack','Hit','Death','Dead','Fidget']:
 a=bpy.data.actions[name];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];bad=[];worst=0
 for f in np.arange(0,a.frame_range[1]+.001,.5):
  bpy.context.scene.frame_set(int(f),subframe=f-int(f));ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh();verts=[v.co.copy() for v in mesh.vertices];ev.to_mesh_clear()
  pairs=BVHTree.FromPolygons(verts,head).overlap(BVHTree.FromPolygons(verts,collar))
  if pairs:bad.append({'frame':float(f),'triangle_pairs':len(pairs)})
  worst=max(worst,len(pairs))
 report[name]={'intersecting_samples':bad,'max_triangle_pairs':worst}
 print('HEAD_COLLAR_INTERSECTIONS',name,worst,bad[:3],flush=True)
(p/f"review/{stage}_head_collar.json").write_text(json.dumps(report,indent=2)+'\n')
run('g5_hand_stretch.py',[blend,'Standing','Walking','Running','Attack','Hit','Death','Dead','Fidget'])
run('g4_weights.py',[blend,stage,'Standing:0','Walking:12','Running:12','Attack:12','Attack:23','Attack:33','Hit:5','Death:10','Death:20','Death:39','Fidget:22'])
run('jerk_probe.py',[blend,'Standing','Walking','Running','Attack','Hit','Death','Dead','Fidget'])

os.environ['STEP']='0.5'
run('sole_probe.py',[blend,'Standing','Walking','Running','Attack','Hit','Fidget'])
