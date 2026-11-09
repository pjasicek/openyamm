import bpy,sys,runpy,os,json
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
import numpy as np
p=Path(__file__).resolve().parents[1];w=p/'work';s=p/'scripts';sys.path.insert(0,str(s));import common

def run(n,*args):
 sys.argv=[n,'--',*map(str,args)];runpy.run_path(str(s/n),run_name='__main__')
os.environ['R_HANDLE']='0.012';os.environ['GRIP_RENDER']=str(p/'review/grip_v2')
run('grip_solve.py',w/'rig_v4f.blend','Attack:0')
run('apply_grip.py',w/'pilot_equipped.blend',w/'pilot_grip.blend')
run('foot_level.py',w/'pilot_grip.blend',w/'pilot_feet.blend','Standing','Attack','Hit','Fidget','Walking:const','Running:const','Death:until=10')
bpy.ops.wm.open_mainfile(filepath=str(w/'pilot_feet.blend'));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];sc=bpy.context.scene
pc=np.array([v.value for v in body.data.attributes['piece'].data]);rest=np.array([v.co[:] for v in body.data.vertices]);feet=np.isin(pc,[0,2])&(rest[:,2]<.09);report={}
for name in ['Standing','Walking','Running','Attack','Hit','Fidget','Death']:
 a=bpy.data.actions[name];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];rows=[];ts=np.arange(0,float(a.frame_range[1])+.001,.25)
 for f in ts:
  sc.frame_set(int(f),subframe=float(f%1));ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();co=np.array([v.co[:] for v in me.vertices]);ev.to_mesh_clear();low=co[:,2].min() if name=='Death' else co[feet,2].min()
  dz=max(0,.002-low) if name=='Running' else .002-low;rows.append((rig.pose.bones['B_Pelvis'].location.copy(),dz,float(low)))
 inv=rig.data.bones['B_Pelvis'].matrix_local.to_3x3().inverted()
 for f,(loc,dz,low) in zip(ts,rows):
  b=rig.pose.bones['B_Pelvis'];b.location=loc+inv@Vector((0,0,dz));b.keyframe_insert('location',frame=float(f))
 report[name]={'ground_delta_m':[min(r[1] for r in rows),max(r[1] for r in rows)]}
 for layer in a.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    for fc in bag.fcurves:
     for k in fc.keyframe_points:k.interpolation='LINEAR'
rig.animation_data.action=None
for b in rig.pose.bones:b.matrix_basis=Matrix()
bpy.ops.wm.save_as_mainfile(filepath=str(w/'pilot_gated.blend'))
# Actual blade rays at its centre and both sides; ignore the grip and count only blade/body crossings.
for name in ['Standing','Walking','Running','Attack','Hit','Fidget','Death']:
 a=bpy.data.actions[name];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];hits=[]
 for f in np.arange(0,float(a.frame_range[1])+.001,.5):
  sc.frame_set(int(f),subframe=float(f%1));ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();tree=BVHTree.FromPolygons([v.co for v in me.vertices],[v.vertices for v in me.polygons]);ev.to_mesh_clear()
  M=rig.pose.bones['Sword'].matrix
  for dx in [-.022,0,.022]:
   start=M@Vector((dx,.15,0));d=(M.to_3x3()@Vector((0,1,0))).normalized();hit=tree.ray_cast(start,d,1.06)
   if hit[0] is not None:hits.append({'frame':float(f),'blade_side':dx,'distance':hit[3],'piece':int(pc[body.data.polygons[hit[2]].vertices[0]])})
 report[name]['blade_body_hits']=hits
 for f in [0,float(a.frame_range[1])*.33,float(a.frame_range[1])*.66]:
  sc.frame_set(int(f),subframe=f%1);common.workbench_clay(sc);common.render_views(str(p/f'review/equipped_{name}_{f:.1f}'),.85,2.65,views=('three_quarter',),resolution=(600,800))
(p/'review/pilot_contacts.json').write_text(json.dumps(report,indent=2));print('PILOT_CONTACTS',json.dumps(report))
run('g4_weights.py',w/'pilot_gated.blend','pilot','Attack:4','Attack:12','Attack:16','Running:6','Running:16','Fidget:30')
run('g5_hand_stretch.py',w/'pilot_gated.blend','Attack:0')
