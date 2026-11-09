import bpy,sys,runpy,json
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];sys.argv=['hands','--',str(P/'export/mm6_jak1_runtime_lod0.glb'),str(P/'review/diagnostic'),'Attack:0.791667','Cast:0.75'];runpy.run_path(str(P/'scripts/glb_hand_closeups.py'),run_name='__main__')
rig=next(o for o in bpy.data.objects if o.type=='ARMATURE')
for clip,t in [('Attack',.791667),('Cast',.75)]:
 rig.animation_data.action=bpy.data.actions[clip];rig.animation_data.action_slot=rig.animation_data.action.slots[0];f=t*bpy.context.scene.render.fps;bpy.context.scene.frame_set(int(f),subframe=f-int(f));M=rig.pose.bones['Staff'].matrix;G=M.translation;a=(M.to_3x3()@Vector((0,0,1))).normalized();E=rig.pose.bones['B_R_Forearm'].head;W=rig.pose.bones['B_R_Hand'].head
 print('SEGMENT',clip,'elbow',list(E),'wrist',list(W),'grip',list(G),'axis',list(a),'distance samples',[(round(u,1),round(((E.lerp(W,u)-G)-a*(E.lerp(W,u)-G).dot(a)).length,4))for u in [0,.2,.4,.6,.8,1]],flush=True)
