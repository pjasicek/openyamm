from pathlib import Path
import subprocess,json
O=Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm6_goblin/full_20261006');f=O/'review/final_playback';w=O/'review/reel_work';w.mkdir(exist_ok=True);manifest=[]
for mode in ['normal','quarter_speed']:
 for c in ['Standing','Walk','Attack','Hit','Death','Corpse','Fidget']:
  suffix='' if mode=='normal' else '_quarter_speed';t=.125 if c in ['Standing','Corpse'] else .625 if c=='Death' else .75
  target=1. if c in ['Standing','Corpse'] else t*(4 if mode=='quarter_speed' else 1)*(2 if mode=='quarter_speed' else 4)
  a=f/(c+'_front'+suffix+'.mp4');b=f/(c+'_right'+suffix+'.mp4');out=w/(c+'_'+mode+'.mp4');label=c+' | '+('normal speed' if mode=='normal' else 'quarter speed')+' | front and profile | preview repeats / resets'
  subprocess.run(['ffmpeg','-y','-loglevel','error','-stream_loop','-1','-i',str(a),'-stream_loop','-1','-i',str(b),'-filter_complex',"[0:v][1:v]hstack,drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf:text='"+label+"':x=12:y=12:fontsize=18:fontcolor=white:box=1:boxcolor=black@0.7",'-t',str(target),'-r','48','-c:v','libx264','-crf','20','-pix_fmt','yuv420p','-an',str(out)],check=True)
  manifest.append({'file':str(out),'clip':c,'mode':mode,'preview_duration_seconds':target,'note':'Repetition/reset is only for review; native exports retain original duration'})
listing=w/'concat.txt';listing.write_text(''.join("file '"+r['file']+"'\n" for r in manifest));out=O/'review/review_reel.mp4'
subprocess.run(['ffmpeg','-y','-loglevel','error','-f','concat','-safe','0','-i',str(listing),'-c','copy','-movflags','+faststart',str(out)],check=True)
info=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_format','-of','json',str(out)]));assert abs(float(info['format']['duration'])-sum(r['preview_duration_seconds'] for r in manifest))<.05
(O/'review/review_reel.json').write_text(json.dumps({'file':'review_reel.mp4','duration_seconds':float(info['format']['duration']),'segments':[{k:v for k,v in r.items() if k!='file'} for r in manifest]},indent=2)+'\n');print('Review reel:',info['format']['duration'],'seconds')
