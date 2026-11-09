"""Clean the full one-call image and make explicit row-normalized action previews without redrawing poses."""
from pathlib import Path
import importlib.util,json
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('goblin_edge_cleanup',ROOT.parent/'direct_ai_attack/clean_edges.py')
cleanup=importlib.util.module_from_spec(spec);spec.loader.exec_module(cleanup)
# Measured empty seams in this generated revision, not universal source-grid positions.
ROW_SEAMS=[0,217,390,574,770,960,1150,1237]
BASELINES=[205,382,573,758,952,1131,1220]
X_SEAMS=[0,212,424,636,840,1060,1272]
CELL=(240,240);BASELINE=224;XPAD=14

def build():
 source=json.loads((ROOT/'source_manifest.json').read_text())
 raw=Image.open(ROOT/'enhanced_front_all_actions_v1.png').convert('RGB')
 rgba,stats=cleanup.extract(raw)
 rgba.save(ROOT/'enhanced_front_all_actions_v1_rgba.png')
 for folder in ['frames_rgba','previews','action_sheets']:(ROOT/folder).mkdir(exist_ok=True)
 packed=Image.new('RGBA',(CELL[0]*6,CELL[1]*7));manifest={'raw_generated_size':raw.size,
  'requested_size':[2880,2800],'generated_alpha':False,'alpha_method':'Shared approved goblin deterministic cleanup',
  'cell_size':CELL,'common_baseline_y':BASELINE,'row_normalization':'Translation only per entire action row; no per-pose scaling or recentering.',
  'row_baselines_in_raw':BASELINES,'actions':[]}
 playback_columns=[]
 for row,action in enumerate(source['actions']):
  frames=[];record={'name':action['name'],'source_row':row,'held':action['held'],'loop':action['loop'],'frames':[]}
  row_atlas=Image.new('RGBA',(CELL[0]*len(action['frames']),CELL[1]))
  for info in action['frames']:
   col=info['column'];box=(X_SEAMS[col],ROW_SEAMS[row],X_SEAMS[col+1],ROW_SEAMS[row+1])
   tile=Image.new('RGBA',CELL)
   paste=(box[0]-col*212+XPAD,box[1]-BASELINES[row]+BASELINE)
   tile.paste(rgba.crop(box),paste)
   name=Path(info['source']).stem+'_ai.png';tile.save(ROOT/'frames_rgba'/name)
   bounds=tile.getchannel('A').getbbox();assert bounds and bounds[0]>0 and bounds[1]>0 and bounds[2]<CELL[0] and bounds[3]<CELL[1],(name,bounds)
   packed.paste(tile,(col*CELL[0],row*CELL[1]));row_atlas.paste(tile,(col*CELL[0],0));frames.append(tile)
   record['frames'].append({'file':'frames_rgba/'+name,'native_source':info['source'],'duration_seconds':info['duration_seconds'],
    'raw_extraction_box':box,'paste_in_cell':paste,'alpha_bounds':bounds})
  row_atlas.save(ROOT/'action_sheets'/(action['name'].lower()+'.png'))
  pics=[]
  for i,tile in enumerate(frames):
   pic=Image.new('RGB',(480,280),(42,45,44));d=ImageDraw.Draw(pic)
   native=Image.open(ROOT.parents[3]/action['frames'][i]['source'])
   mask=Image.frombytes('L',native.size,bytes(255 if x else 0 for x in native.tobytes()))
   original=native.convert('RGBA');original.putalpha(mask)
   original=original.convert('RGBa').resize((196,160),Image.Resampling.NEAREST).convert('RGBA')
   left=Image.new('RGBA',CELL);left.paste(original,(XPAD+8,BASELINE-160))
   pic.paste(cleanup.composite(left,(42,45,44)),(0,35));pic.paste(cleanup.composite(tile,(42,45,44)),(240,35))
   d.text((8,8),f"Native {action['name']} {i+1}",fill='white');d.text((248,8),'One-sheet AI / cleaned',fill='white');pics.append(pic)
  delays=[120 if i%2==0 else 130 for i in range(len(frames))]
  if len(frames)==5:delays=[120,130,120,130,130] # GIF 0.63 s vs exact native 0.625 s.
  if len(frames)==1:delays=[500] # Review hold only; source timing remains in manifest.
  pics[0].save(ROOT/'previews'/(action['name'].lower()+'.gif'),save_all=True,append_images=pics[1:],duration=delays,loop=0)
  contact=Image.new('RGB',(480,len(pics)*280),(42,45,44))
  for i,pic in enumerate(pics):contact.paste(pic,(0,i*280))
  contact.save(ROOT/'previews'/(action['name'].lower()+'_comparison.png'))
  record['gif_preview_ms']=delays;manifest['actions'].append(record)
 packed.save(ROOT/'all_actions_front_rgba.png')
 labeled=Image.new('RGB',(1440+105,1680),(40,43,42));labeled.paste(cleanup.composite(packed,(40,43,42)),(105,0))
 d=ImageDraw.Draw(labeled)
 for row,a in enumerate(source['actions']):d.text((6,row*240+12),a['name'],fill='white')
 labeled.save(ROOT/'previews/all_actions_labeled.png')
 manifest['matte_stats']=stats
 (ROOT/'output_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
 print('31 cleaned RGBA cells; all 7 action previews and row-normalized sheet saved.')

if __name__=='__main__':build()
