import json,subprocess,runpy,shutil
from pathlib import Path
P=Path(__file__).resolve().parents[1];url='http://127.0.0.1:8919/level_generation/creatures/mm6_lzd_codex/review/viewer/'
r=subprocess.run(['node',str(P.parent/'claude_shared/check_viewer.mjs'),url,'60'],text=True,capture_output=True,check=True);d=json.loads(r.stdout);assert d['ready']=='true' and d['switched']==27 and not d['failed'] and not d['consoleErrors'];(P/'review/viewer_check.json').write_text(json.dumps(d,indent=2));print(r.stdout)
shots=[f'walk{f}:Walking:{f/48}:quarter:body'for f in [0,5,10,13,14,15,19,24,28,29,34,38]]
shots+=['walk10_side:Walking:0.208333333:left:body','walk35_side:Walking:0.729166667:left:body','hand_back:Walking:0.2:front:arms','hand_forward:Walking:0.6:front:arms']
subprocess.run(['node',str(P/'scripts/viewer_shots.mjs'),url,str(P/'review/round6'),*shots],check=True)
for name,args in [('check_weights',[P/'export/mm6_lzd.glb',P/'export/mm6_lzd_bow.glb']),('check_bindings',[P/'integration/actors.yml'])]:
 r=subprocess.run(['python3',str(P.parents[2]/'output/codex_batch'/f'{name}.py'),*map(str,args)],capture_output=True,text=True,check=True);out=r.stdout+r.stderr;assert 'BAD' not in out;(P/f'review/round6/{name}.txt').write_text(out);print(out)
runpy.run_path(str(P/'scripts/round5_make_sheets.py'),run_name='__main__')
from PIL import Image,ImageDraw,ImageFont
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',20)
sheet=Image.new('RGB',(1920,1788),(35,38,41));draw=ImageDraw.Draw(sheet)
for i,f in enumerate([0,5,10,13,14,15,19,24,29,34,38]):
 x=i%4*480;y=i//4*596;draw.text((x+8,y+6),f'Walking {f}/48 s ({f/48:.3f} s)',font=font,fill='white')
 im=Image.open(P/f'review/round6/walk_{f:02}_left.png').convert('RGBA');sheet.paste(im,(x,y+36),im)
sheet.save(P/'review/round6/walking_sequence.jpg',quality=93)
import sys,os
sys.dont_write_bytecode=True
sys.path.insert(0,str(P/'work/round6/plot_packages'));os.environ['MPLCONFIGDIR']=str(P/'work/round6/matplotlib')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
motion=json.loads((P/'review/round6/motion_diagnostics.json').read_text())
fig,axes=plt.subplots(3,1,figsize=(9,9),sharex=True)
for label in ['before','after']:
 d=motion['versions'][label]['B_Pelvis'];times=[r['time_s']for r in d['samples']]
 axes[0].plot(times,[r['height_m']for r in d['samples']],label=label)
 axes[1].plot(times[1:],d['velocity_m_s'],label=label)
 axes[2].plot(times[1:-1],d['acceleration_m_s2'],label=label)
for ax,title in zip(axes,['Pelvis height (m)','Vertical velocity (m/s)','Vertical acceleration (m/s²)']):
 ax.set_ylabel(title);ax.grid(alpha=.25);ax.axvspan(13/48,15/48,color='grey',alpha=.12)
axes[0].legend();axes[2].set_xlabel('Walking time (seconds)');fig.suptitle('Round 6: shared GLB evaluator at 48 Hz; shaded frames 13–15')
fig.tight_layout();fig.savefig(P/'review/round6/height_trace.png',dpi=150);plt.close(fig)
for name in ['work/master.blend','work/master_export.blend']:shutil.copyfile(P/'work/round6/master.blend',P/name)
print('ROUND6 REVIEW COMPLETE')
