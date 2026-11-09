"""Check real rendered water changes while land stays fixed; preserve timed preview evidence."""
import json
import numpy as np
from PIL import Image,ImageDraw
from common import *
def main():
 p=P/'captures';meta=json.loads((p/'mm7_water_animation_cycle_frames.json').read_text())
 frames=[np.asarray(Image.open(p/n).convert('RGB')) for n in meta['screenshots']]
 water=[a[340:420,850:1200] for a in frames];land=[a[750:850,300:800] for a in frames]
 hashes=[__import__('hashlib').sha256(a.tobytes()).hexdigest() for a in water]
 land_change=max(float(abs(a.astype(float)-land[0]).max()) for a in land)
 changes=[i for i in range(1,len(hashes)) if hashes[i]!=hashes[i-1]]
 recurrence=[dict(frame=i,previous=hashes[:i].index(hashes[i]),seconds=meta['captureElapsedSeconds'][i]-meta['captureElapsedSeconds'][hashes[:i].index(hashes[i])]) for i in range(1,len(hashes)) if hashes[i] in hashes[:i] and hashes[i]!=hashes[i-1]]
 unique=list(dict.fromkeys(hashes));selected=[]
 for i,a in enumerate(water):
  if not any(float(abs(a.astype(float)-water[j]).mean())<1 for j in selected):selected.append(i)
 period=14*15/128;times=meta['captureElapsedSeconds'];cycles=[]
 for i in range(len(water)):
  candidates=[j for j in range(i+1,len(water)) if abs(times[j]-times[i]-period)<.12]
  if candidates:
   j=min(candidates,key=lambda j:float(abs(water[i].astype(float)-water[j]).mean()))
   cycles.append(dict(a=i,b=j,seconds=times[j]-times[i],mae=float(abs(water[i].astype(float)-water[j]).mean())))
 cycle_mae=float(np.mean([r['mae'] for r in cycles]))
 contrast=float(np.mean([abs(water[0].astype(float)-a).mean() for a in water]))
 sheet=Image.new('RGB',(4*350,((len(selected)+3)//4)*112),'#202933');draw=ImageDraw.Draw(sheet)
 for j,i in enumerate(selected):
  x,y=j%4*350,j//4*112;sheet.paste(Image.fromarray(water[i]),(x,y+28));draw.text((x+4,y+6),'frame %d t=%.3f'%(i,meta['captureElapsedSeconds'][i]),fill='white')
 sheet.save(P/'water/native_animation_states.png')
 views=[Image.fromarray(a[300:735,420:1390]).resize((970,435)) for a in frames]
 durations=[max(1,round((b-a)*1000)) for a,b in zip(meta['captureElapsedSeconds'],meta['captureElapsedSeconds'][1:])]+[70]
 views[0].save(P/'water/native_animation.webp',save_all=True,append_images=views[1:],duration=durations,loop=0,lossless=True)
 report=dict(sample_count=len(frames),elapsed_seconds=meta['captureElapsedSeconds'][-1],distinct_water_states=len(unique),water_changes=len(changes),stationary_land_max_channel_difference=land_change,recurrences=recurrence,water_roi=[850,340,1200,420],land_roi=[300,750,800,850],capture_json_sha256=sha(p/'mm7_water_animation.json'),frame_hashes={n:sha(p/n) for n in meta['screenshots']},rendered_frame_clusters=len(selected),expected_period_seconds=period,cycle_matches=cycles,cycle_mean_error=cycle_mae,cycle_to_motion_ratio=cycle_mae/contrast,shader_note='Native frames are discrete; outdoor_textured_fog.sh adds time-dependent UV distortion with 6/8/10-second periods. Pixel hashes therefore do not repeat at the 1.640625-second frame cycle.',passed=len(selected)==14 and land_change==0 and cycle_mae/contrast<.2)
 (P/'water/native_animation.json').write_text(json.dumps(report,indent=2)+'\n');print({k:v for k,v in report.items() if k not in ('recurrences','frame_hashes','cycle_matches')})
if __name__=='__main__':main()
