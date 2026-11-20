import bpy,sys,runpy,json,shutil,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import reduce_round2 as red
R=P/'review/round2';W=P/'work/round2';roles=['Standing','Walking','Running','Attack','Hit','Death','Dead','Fidget']
def run(name,args):
 sys.argv=[name,'--',*map(str,args)];runpy.run_path(str(P/'scripts'/name),run_name='__main__')
for level in range(4):
 body,rig=red.reset(level);bpy.ops.wm.save_as_mainfile(filepath=str(W/f'audit_baseline_l{level}.blend'))
for tag in ['baseline_l0','baseline_l1','baseline_l3','selected_l0','selected_l1','selected_l2','selected_l3']:
 level=int(tag[-1]);src=W/(f'audit_baseline_l{level}.blend'if tag.startswith('baseline')else f'selected_body_l{level}.blend')
 run('g6_contacts_round2.py',[src,*roles]);shutil.copyfile(P/'work/g6_contacts.json',R/f'g6_confirmed_{tag}.json')
 if level==1:
  run('cloth_probe_round2.py',[src,'Walking','Death']);shutil.copyfile(P/'work/g6_fauld.json',R/f'cloth_probe_{tag}.json')
 if tag=='baseline_l3':
  bpy.ops.wm.open_mainfile(filepath=str(src));fps=bpy.context.scene.render.fps;picks=[f'Attack:{f}'for f in np.arange(0,float(bpy.data.actions['Attack'].frame_range[1])+.001,fps/48)];run('g4_round2.py',[src,'round2_baseline_l3',*picks]);shutil.copyfile(P/'work/g4_round2_baseline_l3.json',R/'g4_baseline_l3.json')
 print('DIAGNOSTIC',tag,flush=True)
run('anatomy_round2.py',[])
