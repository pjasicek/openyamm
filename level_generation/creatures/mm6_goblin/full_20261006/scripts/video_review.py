"""Encode genuine timed previews and extract their decoded frames for explicit sequential review."""
import sys,json,subprocess
from pathlib import Path
folder=Path(sys.argv[1]).resolve()
records=json.loads((folder/'clips.json').read_text())
for c in records:
 name=c['name'];normal=folder/c['video'];slow=folder/(name+'_quarter_speed.mp4')
 subprocess.run(['ffmpeg','-y','-loglevel','error','-i',str(normal),'-vf','setpts=4*PTS,fps=48,tpad=stop_mode=clone:stop_duration=0.1','-t',str(c['duration_seconds']*4),'-r','48','-c:v','libx264','-crf','20','-pix_fmt','yuv420p','-movflags','+faststart',str(slow)],check=True)
 timings={}
 for label,video,fps in [('normal',normal,48),('quarter_speed',slow,12)]:
  output=folder/'decoded'/name/label;output.mkdir(parents=True,exist_ok=True)
  subprocess.run(['ffmpeg','-y','-loglevel','error','-i',str(video),'-vf',f'fps={fps}',str(output/'%03d.png')],check=True)
  info=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(video)]))
  duration=float(info['format']['duration']);expected=c['duration_seconds']*(4 if label=='quarter_speed' else 1)
  assert abs(duration-expected)<.002,(name,label,duration,expected)
  timings[label]={'file':video.name,'duration_seconds':duration,'decoded_fps':fps,'decoded_frame_count':len(list(output.glob('*.png')))}
 c['timed_preview_checks']=timings
(folder/'playback_timing.json').write_text(json.dumps(records,indent=2)+'\n')
print('Encoded normal and quarter-speed previews with decoded sequential frames:',len(records))
