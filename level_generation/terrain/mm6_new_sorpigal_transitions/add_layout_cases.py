"""Add legal larger layouts to complement exhaustive native pairs and four-way corners."""
import json
from pathlib import Path
P=Path(__file__).resolve().parent
records=json.loads((P/'mask_inventory.json').read_text())['masks']
extra=[]
for family,foreground,base in [('grass_dirt','grass','6grastyl'),('rock_dirt','volcano','6voltyl')]:
 lookup={tuple(r['corners_NW_NE_SE_SW']):r['tile'] for r in records if r['family']==family}
 lookup[('dirt',)*4]='6dirttyl';lookup[(foreground,)*4]=base
 for hole in [False,True]:
  vertices=[[foreground if ((2<=x<=7 and 2<=y<=7)!=hole) else 'dirt' for x in range(11)] for y in range(11)]
  grid=[[lookup[(vertices[y][x],vertices[y][x+1],vertices[y+1][x+1],vertices[y+1][x])] for x in range(10)] for y in range(10)]
  label=family+('_hole' if hole else '_island')
  extra.append({'id':'layout:'+label,'group':'Large legal layouts','label':label,'tiles':grid})
grid=[['6dirttyl']*10 for _ in range(10)]
for x in range(2,8):grid[1][x]=grid[8][x]='6drsrew'
for y in range(2,8):grid[y][1]=grid[y][8]='6drsrns'
grid[1][1]='6drsrs_e';grid[1][8]='6drsrs_w';grid[8][1]='6drsrn_e';grid[8][8]='6drsrn_w'
extra.append({'id':'layout:road_loop','group':'Large legal layouts','label':'Road loop: four turns and long straights','tiles':grid})
grid=[['6dirttyl']*10 for _ in range(10)]
grid[1][1]='6drsrwcap';grid[1][8]='6drsrecap'
for x in range(2,8):grid[1][x]='6drsrew'
grid[1][4]='6drsrew_s'
for y in range(2,7):grid[y][4]='6drsrns'
grid[7][4]='6drsrn_e'
for x in range(5,8):grid[7][x]='6drsrew'
grid[7][8]='6drsrecap'
extra.append({'id':'layout:road_branch','group':'Large legal layouts','label':'T-junction, both caps and bent branch','tiles':grid})
(P/'extra_cases.json').write_text(json.dumps(extra,indent=2)+'\n')
print('Prepared six legal large layouts.')
