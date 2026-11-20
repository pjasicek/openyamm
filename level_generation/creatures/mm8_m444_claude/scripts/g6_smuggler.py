"""Half-frame surface contacts, using the shared gate's open-surface parity check."""
from pathlib import Path
import bpy,sys,json,os
import numpy as np
from mathutils import Vector
from types import SimpleNamespace
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p.parent/'claude_shared/gates'));from run_gates import Surface,penetration
bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_v6.blend'));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];me=body.data;nv=len(me.vertices);me.calc_loop_triangles()
faces=np.array([tuple(t.vertices) for t in me.loop_triangles]);rest=np.array([tuple(v.co) for v in me.vertices]);pv=np.zeros(nv,np.int32);me.attributes['piece'].data.foreach_get('value',pv)
names=[g.name for g in body.vertex_groups];W=np.zeros((nv,len(names)))
for v in me.vertices:
 for g in v.groups:W[v.index,g.group]=g.weight
mesh=SimpleNamespace(weld=np.arange(nv),weld_first=np.arange(nv),faces=faces,rest=rest,label='Smuggler',components=pv,find_components=lambda:None)
parts={};surfaces={}
for side in 'LR':
 arm=W[:,[i for i,n in enumerate(names) if n.startswith('B_'+side+'_') and any(k in n for k in ['Clavicle','UpperArm','Forearm','Hand','Finger'])]].sum(1)>.2
 parts[side]=W[:,[i for i,n in enumerate(names) if n.startswith('B_'+side+'_') and any(k in n for k in ['Forearm','Hand','Finger'])]].sum(1)>.5
 surfaces[side]=Surface(mesh,~arm)
G=json.loads((p/'work/grip_pose.json').read_text());report={}
report=json.loads((p/'work/g6_contacts.json').read_text()) if os.environ.get('CHECK_CLIPS') else {}
for name in os.environ.get('CHECK_CLIPS','Standing Walking Running Attack Hit Cast Fidget Death Dead').split():
 a=bpy.data.actions[name];rig.animation_data.action=a
 if len(a.slots):rig.animation_data.action_slot=a.slots[0]
 worst={}
 for frame in np.arange(0,float(a.frame_range[1])+.001,.5):
  bpy.context.scene.frame_set(int(frame),subframe=float(frame-int(frame)));ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();P=np.array([tuple(body.matrix_world@v.co) for v in m.vertices]);ev.to_mesh_clear()
  for side in 'LR':
   surf=surfaces[side].build(P);queries={side+'_arm':P[parts[side]]}
   if side=='R':
    M=rig.matrix_world@rig.pose.bones['B_R_Hand'].matrix;c=M@Vector(G['handle_centre_hand_local']);ax=(M.to_3x3()@Vector(G['handle_axis_hand_local'])).normalized();flat=ax.orthogonal().normalized()
    queries['sword']=np.array([tuple(c+ax*t+flat*off) for t in np.linspace(-.06,.68,48) for off in [-.027,0,.027]])
   for label,points in queries.items():
    depth,idx=penetration(surf,points)
    if depth>worst.get(label,{}).get('mm',0):worst[label]={'mm':round(depth,2),'frame':float(frame),'sample':idx}
 report[name]=worst;print('G6',name,worst,flush=True)
(p/'work/g6_contacts.json').write_text(json.dumps(report,indent=2))
