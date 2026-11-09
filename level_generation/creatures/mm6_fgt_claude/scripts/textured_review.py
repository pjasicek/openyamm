from pathlib import Path
import runpy,sys,bpy,numpy as np
p=Path(__file__).resolve().parents[1];s=p/'scripts'
sys.argv=[str(s/'glb_hand_closeups.py'),'--',str(p/'review/viewer/mm6_fgt_a.glb'),str(p/'review/hands'),'Standing:0','Walking:0.4','Attack:0.7','Death:0.2']
runpy.run_path(sys.argv[0],run_name='__main__')
# Grounded walk stride = total rearward foot travel over one planted phase on each foot.
bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_v7.blend'))
r=bpy.data.objects['Rig'];r.animation_data.action=bpy.data.actions['Walking'];r.animation_data.action_slot=r.animation_data.action.slots[0]
strides=[]
for side in 'LR':
 rows=[]
 for frame in np.arange(0,24.001,.5):
  bpy.context.scene.frame_set(int(frame),subframe=float(frame%1));rows.append(tuple(r.pose.bones[f'B_{side}_Foot'].head))
 co=np.array(rows);dy=np.diff(co[:,1]);ground=(co[:-1,2]<np.percentile(co[:,2],50))
 strides.append(float(dy[(dy>0)&ground].sum()*2))
print('MEASURED walk stride per side',strides)
