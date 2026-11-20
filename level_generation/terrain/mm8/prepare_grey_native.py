"""Add a native grey-fringe review pose without regenerating other frozen poses."""
import json
from prepare_native import parse_odm_file
from common import *

grid=json.loads((P/'grids.json').read_text())['out06']
source=ROOT/'assets_dev/worlds/mm8/maps/out06.odm'
data=parse_odm_file(source)['payload']
candidates=[(y,x) for y in range(8,118) for x in range(8,118) if grid[y][x]=='gsn']
def score(pos):
    y,x=pos
    h=[data['height_map'][yy*128+xx] for yy in range(y-1,y+3) for xx in range(x-1,x+2)]
    return max(h)-min(h),abs(y-64)+abs(x-64)
y,x=min(candidates,key=score)
height=max(data['height_map'][yy*128+xx] for yy in (y,y+1,y+2) for xx in (x,x+1))*32
report=json.loads((P/'reports/native_stage.json').read_text())
report['poses']['grey_fringe_overhead']=dict(map='out06',tile='gsn',row=y,column=x,
    pose=[(x+.5-64)*512,(64-y-.5)*512,height+850,1.5707963268,-1.50],
    diagnostic_flying=True,source_sha256=sha(source))
(P/'reports/native_stage.json').write_text(json.dumps(report,indent=2)+'\n')
print(report['poses']['grey_fringe_overhead'])
