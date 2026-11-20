"""Assemble connected bank islands and holes from their corner contracts."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
import json
from PIL import ImageDraw
from common import *
F=Path(__file__).resolve().parent
report=json.loads((F/'build.json').read_text());outputs={}
for family in ('shore_dirt','lava_dirt','tar_grey'):
    records=[r for r in report['tiles'] if r['family']==family];binding=records[0]['binding']
    names={tuple(int(v) for v in r['topology']['N']+r['topology']['S']):r['name'] for r in records}
    land=read(M/'runtime'/(binding['land']+'.png'))
    liquid=read(P/'liquids/v1/runtime'/({'water':'hdwtr000','lava':'hdlav000','tar':'hwoil000'}[binding['liquid']]+'.png'))
    for hole in (False,True):
        vertex=np.zeros((6,6),int);vertex[1:5,1:5]=1
        if hole:vertex=1-vertex
        sheet=Image.new('RGB',(2560,1304),'#202933');draw=ImageDraw.Draw(sheet);grid=[]
        for col,folder in enumerate((OUT,F/'runtime')):
            draw.text((col*1280+4,4),family+(' liquid hole' if hole else ' land island')+(' previous' if col==0 else ' candidate'),fill='white')
            for y in range(5):
                row=[]
                for x in range(5):
                    key=(vertex[y,x],vertex[y,x+1],vertex[y+1,x],vertex[y+1,x+1])
                    if key==(0,0,0,0):a=liquid;n=binding['liquid']
                    elif key==(1,1,1,1):a=land;n=binding['land']
                    else:
                        n=names[key];rgba=np.asarray(Image.open(folder/(n+'.png')).convert('RGBA'),float);alpha=rgba[:,:,3:4]/255
                        a=rgba[:,:,:3]*alpha+liquid*(1-alpha)
                    row.append(n);sheet.paste(Image.fromarray(seams.byte(a)),(col*1280+x*256,24+y*256))
                if col==0:grid.append(row)
        name=family+('_hole' if hole else '_island')+'.png';sheet.save(F/name);outputs[name]=dict(grid=grid,sha256=sha(F/name))
(F/'contexts.json').write_text(json.dumps(dict(build_sha256=sha(F/'build.json'),layouts=outputs),indent=2)+'\n')
