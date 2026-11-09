import bpy,json,numpy as np
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/round1_sources.blend'));r=bpy.data.objects['Rig'];b=bpy.data.objects['Body'];sc=bpy.context.scene
r.animation_data.action=bpy.data.actions['Standing'];r.animation_data.action_slot=r.animation_data.action.slots[0];sc.frame_set(0)
report={}
for s,sign in [('R',-1),('L',1)]:
 rest=np.array([v.co[:] for v in b.data.vertices]);ids=np.where((rest[:,2]<.025)&(sign*rest[:,0]>0))[0];report[s]={'sole_count':len(ids),'rest_bounds':[rest[ids].min(0).tolist(),rest[ids].max(0).tolist()]}
 h=r.pose.bones['B_'+s+'_Hand'].matrix;f=r.pose.bones['B_'+s+'_Forearm'].matrix
 for label,m in [('hand',h),('forearm',f)]:report[s][label]=[list(x) for x in m]
 report[s]['grip']=json.loads((P/f'work/grip_pose_{s}.json').read_text())
 report[s]['knuckles_hand_local']=[list(h.inverted()@r.pose.bones[f'B_{s}_Finger{i}'].head) for i in range(1,5)]
print('PROBE',json.dumps(report));(P/'review/round1/probe.json').write_text(json.dumps(report,indent=2))
