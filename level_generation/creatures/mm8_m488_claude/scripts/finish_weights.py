"""Give hidden hips anatomical ownership and normalize the runtime's four influences."""
from pathlib import Path
import sys,bpy,numpy as np,json,runpy
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(p/'work/animated.blend'));body=bpy.data.objects['Body'];me=body.data
changed=0
def smooth(x):x=float(np.clip(x,0,1));return x*x*(3-2*x)
for v in me.vertices:
 if me.attributes['piece'].data[v.index].value!=0 or abs(v.co.x)>.35 or not .82<v.co.z<1.32:continue
 alpha=min(smooth((v.co.z-.82)/.08),smooth((1.32-v.co.z)/.14))
 wp=smooth((v.co.z-.92)/.23);left=smooth((v.co.x+.04)/.08)
 old={g.group:g.weight for g in v.groups};new={body.vertex_groups[n].index:w for n,w in [('B_Pelvis',wp),('B_L_Thigh',(1-wp)*left),('B_R_Thigh',(1-wp)*(1-left))]}
 weights={g:old.get(g,0)*(1-alpha)+new.get(g,0)*alpha for g in old.keys()|new.keys()}
 for g in list(v.groups):body.vertex_groups[g.group].remove([v.index])
 for g,w in weights.items():
  if w>1e-6:body.vertex_groups[g].add([v.index],w,'REPLACE')
 changed+=1
# Reduce only actual influence count; geometry and source animation keys remain intact.
dropped=0
for v in me.vertices:
 weights=sorted([(g.group,g.weight) for g in v.groups if g.weight>1e-7],key=lambda x:x[1],reverse=True)
 assert weights
 dropped+=max(0,len(weights)-4);weights=weights[:4];total=sum(w for _,w in weights)
 for g in list(v.groups):body.vertex_groups[g.group].remove([v.index])
 for g,w in weights:body.vertex_groups[g].add([v.index],w/total,'REPLACE')
 assert len(v.groups)<=4 and abs(sum(g.weight for g in v.groups)-1)<1e-5
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/animated_fixed.blend'))
path=p/'scripts/floor_clips.py';sys.argv=[str(path),'--',str(p/'work/animated_fixed.blend'),str(p/'work/animated_fixed.blend'),'Standing','Attack','Hit','Fidget','Death','Dead'];runpy.run_path(str(path),run_name='__main__')
# Changed weighting affects only the garment's hidden support; inspect its demanding states explicitly.
rig=bpy.data.objects['Rig'];common.workbench_clay(bpy.context.scene)
for action,frame in [('Fidget',21),('Running',9.5),('Death',45),('Standing',0)]:
 act=bpy.data.actions[action];rig.animation_data.action=act
 if act.slots:rig.animation_data.action_slot=act.slots[0]
 bpy.context.scene.frame_set(int(frame),subframe=frame%1);common.render_views(str(p/'review/animation'/('fixed_'+action)),1.05,2.5,views=('front','left','three_quarter'),resolution=(640,640))
(p/'review/weight_finish.json').write_text(json.dumps({'hip_vertices_refitted':changed,'influences_removed':dropped,'max_influences':4},indent=2)+'\n');print('WEIGHT_FINISH',changed,dropped)
