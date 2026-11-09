"""Flat water/shore pads using the existing native map writer."""
import json,subprocess,yaml
from pathlib import Path
P=Path(__file__).resolve().parent;ROOT=P.parents[2];L=P.parent/'mm6_new_sorpigal_transitions'
C=P.parent/'mm6_new_sorpigal';F=P/'fixture';F.mkdir(exist_ok=True)
cat=json.loads((C/'catalogue.json').read_text());ids={t['name']:t['raw_tile_ids'][0] for t in cat['tiles']}
grid=[['6dirttyl']*128 for _ in range(128)];pads=[]
for i,t in enumerate(t for t in cat['tiles'] if t['family']=='shoreline'):
 x=42+(i%4)*6;y=42+(i//4)*6
 for dy,row in enumerate(t['context_tiles']):
  for dx,n in enumerate(row):grid[y+dy][x+dx]=n
 pads.append({'name':t['name'],'column':x,'row':y,'width':3,'height':3})
# Large closed pool exercises straight shore, outer shore corners, and water/water joins.
lookup={}
from PIL import Image
import numpy as np
for t in cat['tiles']:
 if t['family']=='shoreline':
  a=np.array(Image.open(C/t['shore_alpha']));lookup[tuple(bool(v) for v in [a[0,0],a[0,-1],a[-1,-1],a[-1,0]])]=t['name']
lookup[(True,)*4]='6dirttyl';lookup[(False,)*4]='6wtrtyl'
for hole,x,y in [(True,42,65),(False,57,65)]:
 vertices=[[not(2<=xx<=8 and 2<=yy<=8) if hole else (2<=xx<=8 and 2<=yy<=8) for xx in range(12)] for yy in range(12)]
 for dy in range(11):
  for dx in range(11):grid[y+dy][x+dx]=lookup[vertices[dy][dx],vertices[dy][dx+1],vertices[dy+1][dx+1],vertices[dy+1][dx]]
 pads.append({'name':'pool' if hole else 'island','column':x,'row':y,'width':11,'height':11})
for kind in ['map','scene','terrain','geometry']:
 data=yaml.safe_load((L/'fixture'/f'oute3.{kind}.yml').read_text())
 if kind=='terrain':data['tile_map_hex']=bytes(ids[n] for row in grid for n in row).hex()
 if kind=='map':
  data.update(package_id='mm6:water_fixture',display_name='Water and shoreline fixture')
  data.pop('source_fingerprint',None);data.pop('built_source_fingerprint',None)
 (F/f'oute3.{kind}.yml').write_text(json.dumps(data,indent=2)+'\n')
(F/'pads.json').write_text(json.dumps(pads,indent=2)+'\n')
with (F/'build.log').open('w') as f:subprocess.run([str(ROOT/'build/editor/openyamm-editor'),'--asset-root',str(ROOT/'assets_dev'),'--headless-build-map',str(F/'oute3.map.yml')],stdout=f,stderr=subprocess.STDOUT,check=True)
print('Built14 flat shore/water pads.')
