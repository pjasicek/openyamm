"""Record two native Alvar path poses without replacing other frozen review poses."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from common import *
sys.path.insert(0,str(ROOT/'util'))
from map_export import parse_odm_file
import json

report_path=P/'reports/native_stage.json'
report=json.loads(report_path.read_text())
grid=json.loads((P/'effective_grids.json').read_text())['out04']
source=ROOT/'assets_dev/worlds/mm8/maps/out04.odm'
data=parse_odm_file(source)['payload']
for name,tile,yaw in [('stepping_ew','plrdew',0),('stepping_ns','plrdns',1.5707963268),
                      ('stepping_ns_south','plrdns',1.5707963268)]:
    candidates=[(y,x) for y in range(8,119) for x in range(8,119) if grid[y][x]==tile]
    if name=='stepping_ns_south':
        # The central village view is occluded by a Troll Warrior. Use the
        # southern path for the second orientation, retaining the rejected pose.
        candidates=[(y,x) for y,x in candidates if y>=90]
    def score(pos):
        y,x=pos
        heights=[data['height_map'][yy*128+xx] for yy in range(y-2,y+3) for xx in range(x-2,x+3)]
        count=sum(n==tile for row in grid[y-2:y+3] for n in row[x-2:x+3])
        return max(heights)-min(heights),-count,abs(y-64)+abs(x-64)
    y,x=min(candidates,key=score)
    height=max(data['height_map'][yy*128+xx] for yy in (y,y+1) for xx in (x,x+1))*32
    report['poses'][name]=dict(map='out04',tile=tile,row=y,column=x,
        pose=[(x+.5-64)*512,(64-y-.5)*512,height+161,yaw,-.6],source_sha256=sha(source))
report_path.write_text(json.dumps(report,indent=2)+'\n')
