from pathlib import Path
import json,runpy,sys,bpy,numpy as np
p=Path(__file__).resolve().parents[1]
rom=json.loads((p/'work/rom.json').read_text());picks=set()
for pose in rom['stress_poses']:
 role=pose['role']
 if role not in ('Walking','Running','Attack','Hit'):continue
 f=round((pose['frame']-1)*30/24)+(12 if role=='Attack' else 0);picks.add(f'{role}:{f}')
picks.update(['Standing:0','Fidget:11','Death:5','Death:13','Death:20','Death:28','Dead:0'])
s=p/'scripts/g4_weights.py';sys.argv=[str(s),'--',str(p/'work/rig_v5t.blend'),'rom',*sorted(picks)];runpy.run_path(str(s),run_name='__main__')
r=json.loads((p/'work/g4_rom.json').read_text());worst=max((v['stretch_p99'],k,s) for k,a in r.items() for s,v in a.items());print('ROM_P99_WORST',worst);assert worst[0]<2.05
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];sc=bpy.context.scene;result={}
for role in ('Standing','Walking','Running'):
 a=bpy.data.actions[role];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0]
 rows=[]
 for f in range(int(a.frame_range[1])+1):
  sc.frame_set(f);ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();co=np.array([tuple(v.co) for v in m.vertices]);ev.to_mesh_clear()
  feet={s:tuple(rig.pose.bones[f'B_{s}_Foot'].head) for s in 'LR'};rows.append({'frame':f,'height':float(co[:,2].max()-co[:,2].min()),'feet':feet})
 result[role]={'height_min':min(x['height'] for x in rows),'height_max':max(x['height'] for x in rows),'foot_stride':{s:2*(max(x['feet'][s][1] for x in rows)-min(x['feet'][s][1] for x in rows)) for s in 'LR'},'frames':rows}
print('CALIBRATION',json.dumps({k:{n:v for n,v in d.items() if n!='frames'} for k,d in result.items()}));(p/'work/calibration.json').write_text(json.dumps(result,indent=2)+'\n')
