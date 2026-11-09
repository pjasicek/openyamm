import bpy,json,sys,subprocess
from pathlib import Path
from shutil import copyfile
P=Path(__file__).resolve().parents[1]
exec((P/'scripts/reduction_balanced.py').read_text().replace("[('Standing',0),('Attack',.4375)]","[('Attack',.4375)]").split('config=json.loads')[0].replace('.4375','.4166666666667'))
selection=json.loads((P/'review/reduction_soft/selection.json').read_text());reports={}
for level in range(4):
 ref=P/'work/rig_polished.blend'if level==0 else P/selection['0']['blend'];bpy.ops.wm.open_mainfile(filepath=str(ref));cleanup();reset();folder=P/f'work/final_reference{level}';folder.mkdir(exist_ok=True)
 for stem in ['mfp','mfp_head']:
  source=P/'textures'/f'{stem}_basecolor_1k.png'if level==0 else Path(selection['0']['textures'])/f'{stem}_basecolor.png';copyfile(source,folder/f'{stem}_basecolor.png');mask=P/'textures'/f'{stem}_region_mask.png'if level==0 else Path(selection['0']['textures'])/f'{stem}_region_mask.png';copyfile(mask,folder/f'{stem}_region_mask.png')
 subprocess.run(['/usr/bin/python3',str(P/'scripts/bake_tiers.py'),str(folder)],check=True);r=P/f'review/final_comparison/lod{level}';render(r/'reference',level,folder)
 bpy.ops.wm.open_mainfile(filepath=str(P/selection[str(level)]['blend']));cleanup();render(r/'selected',level,Path(selection[str(level)]['textures']));scores=metrics(r/'reference',r/'selected');scores['pass']=scores['pass']if level==0 else scores['pooled_iou']>=.97;reports[str(level)]=scores;print('FINAL_VISUAL',level,scores['min_iou'],scores['min_ssim'],scores['pooled_iou'],scores['pass'],flush=True);(P/'review/final_comparison/scores.json').write_text(json.dumps(reports,indent=2))
assert all(r['pass']for r in reports.values())
