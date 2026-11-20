from pathlib import Path
import bpy,sys,numpy as np,json
p=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(p/'work/reduced.blend'));body=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];me=body.data;fixed=0;max_old=0
for v in me.vertices:
 if me.attributes['piece'].data[v.index].value!=0:continue
 side='L' if v.co.x>0 else 'R';wr=rig.data.bones['B_'+side+'_Hand'].head_local;el=rig.data.bones['B_'+side+'_Forearm'].head_local;axis=(wr-el).normalized();depth=(v.co-wr).dot(axis)
 if (v.co-wr).length>.30:continue
 finger_share=sum(g.weight for g in v.groups if body.vertex_groups[g.group].name.startswith('B_'+side+'_Finger'))
 factor=1 if me.attributes['finger'].data[v.index].value>0 or finger_share>.05 else float(np.clip(depth/.06,0,1));factor=factor*factor*(3-2*factor)
 if factor==0:continue
 old={g.group:g.weight for g in v.groups};allowed={g:w for g,w in old.items() if body.vertex_groups[g].name=='B_'+side+'_Hand' or body.vertex_groups[g].name.startswith('B_'+side+'_Finger')};total=sum(allowed.values())
 if total<=1e-6:continue
 max_old=max(max_old,1-total);new={g:w*(1-factor)+factor*allowed.get(g,0)/total for g,w in old.items()}
 for g in list(v.groups):body.vertex_groups[g.group].remove([v.index])
 for g,w in new.items():
  if w>1e-7:body.vertex_groups[g].add([v.index],w,'REPLACE')
 assert abs(sum(g.weight for g in v.groups)-1)<1e-5
 if me.attributes['finger'].data[v.index].value>0:assert all(body.vertex_groups[g.group].name=='B_'+side+'_Hand' or body.vertex_groups[g.group].name.startswith('B_'+side+'_Finger') for g in v.groups)
 fixed+=1
(p/'review/hand_weight_finish.json').write_text(json.dumps({'vertices':fixed,'largest_removed_forearm_share':max_old},indent=2)+'\n');print('HAND_OWNERSHIP',fixed,max_old)
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/weighted_hands.blend'))
