from pathlib import Path
import bpy,json,sys,math,numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import armik
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_run_source_twist.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];me=body.data;dag=bpy.data.objects['DaggerMesh']
pv=np.zeros(len(me.vertices),np.int32);me.attributes['piece'].data.foreach_get('value',pv)
faces=[tuple(p.vertices) for p in me.polygons if pv[p.vertices[0]] in (0,1,2,3,5,6,7,8,9,10,11,12,13,14,15,16)]
a=bpy.data.actions['Running'];rig.animation_data.action=a
if len(a.slots):rig.animation_data.action_slot=a.slots[0]
report=[]
for f in np.arange(0,float(a.frame_range[1])+.01,.5):
 bpy.context.scene.frame_set(int(f),subframe=float(f-int(f)))
 ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());em=ev.to_mesh();co=[tuple(body.matrix_world@v.co) for v in em.vertices];ev.to_mesh_clear()
 tree=BVHTree.FromPolygons(co,faces)
 m=rig.matrix_world@rig.pose.bones['Dagger'].matrix
 samples=[m@Vector((0,t,0)) for t in np.linspace(.02,.325,40)]
 pen=[]
 for pos in samples:
  hit,norm,_,dist=tree.find_nearest(pos,.06)
  if hit is not None and (pos-hit).dot(norm)<-.7*dist and dist>.002:pen.append(float(dist))
 sw,tw=armik.wrist_cost(rig,'R',armik.W(rig,'B_R_Hand').to_3x3().normalized())
 report.append({'frame':float(f),'wrist_swing':sw,'wrist_twist':tw,'dagger_inside_body_m':max(pen,default=0)})
(P/'review/arm_20261016/source_candidate_gate.json').write_text(json.dumps(report,indent=2)+'\n')
print('SOURCE ARM', 'swing',max(r['wrist_swing'] for r in report),'twist',min(r['wrist_twist'] for r in report),max(r['wrist_twist'] for r in report),'blade penetration',max(r['dagger_inside_body_m'] for r in report))
