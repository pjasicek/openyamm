import bpy,sys,runpy,json,numpy as np
from pathlib import Path
p=Path(__file__).resolve().parents[1]
sys.argv=['g4_weights.py','--',str(p/'work/pilots_twist.blend'),'pilots','Standing:0','Walking:0','Walking:6','Walking:12','Walking:18','Death:15','Death:30','Death:45','Death:60']
runpy.run_path(str(p/'scripts/g4_weights.py'),run_name='__main__')
bpy.ops.wm.open_mainfile(filepath=str(p/'work/pilots_raw.blend'))
r=bpy.data.objects['Rig'];o=bpy.data.objects['Body'];me=o.data;pv=np.array([v.value for v in me.attributes['piece'].data])
data={}
for name in ['Standing','Walking','Death']:
 a=bpy.data.actions[name];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];N=int(a.frame_range[1]);rows=[]
 for f in range(N+1):
  bpy.context.scene.frame_set(f);ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();co=np.array([tuple(v.co) for v in m.vertices]);ev.to_mesh_clear()
  row={'f':f,'pelvis':list(r.pose.bones['B_Pelvis'].head)}
  for s,parts in [('R',[5,15]),('L',[6,14])]:
   P=co[np.isin(pv,parts)];row[s]={'ankle':list(r.pose.bones[f'B_{s}_Foot'].head),'floor_min':float(P[:,2].min()),'floor_max':float(P[:,2].max())}
  row['head_min_z']=float(co[np.isin(pv,[1,2,7])][:,2].min());rows.append(row)
 data[name]=rows
 print('POSE',name,'frames',N,'R floor extrema',min(x['R']['floor_min'] for x in rows),max(x['R']['floor_min'] for x in rows),'pelvis0',rows[0]['pelvis'],'end',rows[-1]['pelvis'],'head_end',rows[-1]['head_min_z'])
 if name=='Walking':
  for s in 'RL':print('HEEL',s,min(rows,key=lambda x:x[s]['ankle'][1])['f'],'range',np.ptp([x[s]['ankle'][1] for x in rows]))
(p/'work/pilot_motion_measurements.json').write_text(json.dumps(data,indent=1))
