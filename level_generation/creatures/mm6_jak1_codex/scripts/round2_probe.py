import bpy,json,sys,numpy as np,math
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'))
G={s:json.loads((P/f'work/grip_pose{suffix}.json').read_text()) for s,suffix in [('R',''),('L','_left')]}
for file,clips in [('round2_sources',['Staff2','Cast1']),('runtime_master',['Attack','Cast','Standing','Death'])]:
 bpy.ops.wm.open_mainfile(filepath=str(P/f'work/{file}.blend'));rig=bpy.data.objects['Rig'];scene=bpy.context.scene
 for clip in clips:
  a=bpy.data.actions[clip];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];rows=[]
  for f in range(int(a.frame_range[1])+1):
   scene.frame_set(f);h={s:rig.matrix_world@rig.pose.bones[f'B_{s}_Hand'].matrix for s in 'LR'};c={s:h[s]@Vector(G[s]['handle_centre_hand_local'])for s in 'LR'};ax=(h['R'].to_3x3()@Vector(G['R']['handle_axis_hand_local'])).normalized();v=c['L']-c['R'];rows.append({'f':f,'axis':list(ax),'grip_span':v.dot(ax),'offaxis':(v-ax*v.dot(ax)).length,'R':list(c['R']),'L':list(c['L'])})
  print(file,clip,'span range',min(r['grip_span']for r in rows),max(r['grip_span']for r in rows),'offaxis',max(r['offaxis']for r in rows),flush=True)
  for i in np.linspace(0,len(rows)-1,7).astype(int):print(rows[i],flush=True)
  (P/f'review/round2/probe_{file}_{clip}.json').write_text(json.dumps(rows,indent=2))
