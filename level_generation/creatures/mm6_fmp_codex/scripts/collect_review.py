"""Retain the selected browser and native-game review evidence with reproducible run records."""
from pathlib import Path
import json,shutil
from PIL import Image,ImageDraw
P=Path(__file__).resolve().parents[1];R=P/'review';G=R/'game';G.mkdir(exist_ok=True)
runs={'outdoor_model':'/tmp/openyamm-desktop-fmp-outdoor-model-c2rlbnug','indoor_model':'/tmp/openyamm-desktop-fmp-indoor-model-pmgiai88','outdoor_sprite':'/tmp/openyamm-desktop-fmp-outdoor-sprite-_i8b8047','indoor_sprite':'/tmp/openyamm-desktop-fmp-indoor-sprite-_q0sb9mk'}
for name,run in runs.items():
 dest=G/name;dest.mkdir(exist_ok=True);record=json.loads((Path(run)/'run.json').read_text());assert record['status']=='completed' and record['exit_code']==0
 images=list(Path('/tmp/fmp-game-'+name).glob('*.png'));assert len(images)==16,(name,len(images))
 for source in [*images,Path(run)/'game.log',Path(run)/'run.json']:shutil.copy2(source,dest/source.name)
for area in ['indoor','outdoor']:
 a=json.loads((G/(area+'_model')/'run.json').read_text());b=json.loads((G/(area+'_sprite')/'run.json').read_text());assert a['loaded_camera']==b['loaded_camera'] and a['binary_sha256']==b['binary_sha256']
 sheet=Image.new('RGB',(1600,478),(27,30,35));draw=ImageDraw.Draw(sheet)
 for i,mode in enumerate(['sprite','model']):
  im=Image.open(G/(area+'_'+mode)/'tiers.png').convert('RGB');im.thumbnail((800,450));sheet.paste(im,(i*800,28));draw.text((i*800+10,8),area+' / '+mode,fill='white')
 sheet.save(G/(area+'_comparison.jpg'),quality=93)
for src,dst in [('fmp-build.log','game/build.log'),('fmp-regression.log','game/peasant_regression.log'),('fmp-mm6-actors.log','game/mm6_actor_regressions.log'),('fmp-viewer-check.json','viewer_check.json'),('fmp-loop-check.json','loop_playback.json'),('fmp-playback-check.json','final_playback.json')]:shutil.copy2(Path('/tmp')/src,R/dst)
play=json.loads((R/'final_playback.json').read_text());assert play['revision']=='fmp_v2' and len(play['rows'])==14
out=R/'playback';out.mkdir(exist_ok=True)
for f in Path('/tmp').glob('fmp-final-play-*.png'):shutil.copy2(f,out/f.name)
for f in Path('/tmp').glob('fmp-final-fmp_*.png'):shutil.copy2(f,R/f.name)
shutil.copy2('/tmp/fmp-final-corpse-left.png',R/'corpse_left.png')
sheet=Image.new('RGB',(1080,703),(27,30,35));draw=ImageDraw.Draw(sheet)
for i,tier in enumerate('abc'):
 im=Image.open(R/f'fmp-final-fmp_{tier}-body.png').crop((16,127,710,778)).resize((360,338));sheet.paste(im,(i*360,30));draw.text((i*360+10,10),'Peasant '+tier.upper(),fill='white')
 im=Image.open(R/f'fmp-final-fmp_{tier}-head.png').crop((16,127,710,778)).resize((360,338));sheet.paste(im,(i*360,365))
sheet.save(R/'selected_variants.jpg',quality=94)
print('Collected 64 native screenshots, matching cameras, seven clips at two speeds, loops and selected tier close-ups.')
