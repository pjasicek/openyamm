import bpy,json,sys,math,runpy
from pathlib import Path
from mathutils import Quaternion
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import armik
bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_motion.blend'));rig=bpy.data.objects['Rig'];sc=bpy.context.scene;out={}
for a in [x for x in bpy.data.actions if x.use_fake_user]:
 rig.animation_data.action=a
 if len(a.slots):rig.animation_data.action_slot=a.slots[0]
 maxima={s:{'swing':(0,0),'twist':(0,0)} for s in 'RL'}
 for f in range(int(a.frame_range[1])*2+1):
  sc.frame_set(f//2,subframe=(f%2)*.5)
  for s in 'RL':
   sw,tw=armik.wrist_cost(rig,s,armik.W(rig,'B_'+s+'_Hand').to_3x3().normalized())
   if sw>maxima[s]['swing'][0]:maxima[s]['swing']=(sw,f/2)
   if abs(tw)>maxima[s]['twist'][0]:maxima[s]['twist']=(abs(tw),f/2)
 out[a.name]=maxima;print('WRIST',a.name,maxima)
json.dump(out,open(p/'work/wrist_audit.json','w'),indent=2)
def run(n,*a):
 sys.argv=[n,'--',*map(str,a)];runpy.run_path(str(p/'scripts'/n),run_name='__main__')
run('g4_weights.py',p/'work/rig_motion.blend','pilot','Standing:0','Walking:6','Attack:10','Attack:14','Attack:18','Hit:5','Fidget:40','Death:28')
for v in ('front','left','three_quarter'):
 run('clip_sheet.py',p/'work/rig_motion.blend',p/('review/motion/'+v),v,7,'Standing','Walking','Attack','Hit','Fidget','Death')
