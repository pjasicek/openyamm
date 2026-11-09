"""Freeze accepted masters and prepare corrected tropical imagegen artwork."""
import sys, json, shutil, importlib.util
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
P=Path(__file__).resolve().parent
sys.path.insert(0,str(P.parent/'v2'))
import build as previous
s=previous.seams

def main():
    records=[]
    for folder in ('materials','runtime_x2/worlds/mm6/terrain_x2','previews'): (P/folder).mkdir(parents=True,exist_ok=True)
    sheet=Image.new('RGB',(1024,1400),'#202933');draw=ImageDraw.Draw(sheet)
    for row,(name,tile) in enumerate(previous.MATERIALS.items()):
        master=P/'materials'/(name+'.png');runtime=P/'runtime_x2/worlds/mm6/terrain_x2'/(tile+'.png')
        if name=='tropical':
            a=np.asarray(Image.open(P/'raw/tropical.png').convert('RGB').resize((512,512),Image.Resampling.LANCZOS),float)
            a=s.periodic(a)
            Image.fromarray(s.byte(a)).save(master)
            Image.fromarray(s.reduce(s.pad(a,'wrap'))).save(runtime)
        else:
            for p in (master,runtime): shutil.copy2(P.parent/'v2'/p.relative_to(P),p)
        a=np.asarray(Image.open(runtime));repeat=np.tile(a,(3,3,1));offset=np.roll(a,(128,128),(0,1))
        Image.fromarray(repeat).save(P/'previews'/(name+'_repeat.png'))
        Image.fromarray(offset).resize((512,512)).save(P/'previews'/(name+'_offset.png'))
        old=Image.open(P.parents[1]/'references'/(tile+'.png')).convert('RGB').resize((256,256),Image.Resampling.NEAREST)
        for col,im in enumerate((old,Image.fromarray(a),Image.fromarray(repeat).resize((256,256)),Image.fromarray(offset))):
            sheet.paste(im,(col*256,row*280+24));draw.text((col*256+4,row*280+5),name+' '+['original','x2','repeat','offset'][col],fill='white')
        records.append(dict(material=name,tile=tile,master_sha256=previous.sha(master),runtime_sha256=previous.sha(runtime),edge_checks=previous.edge_check(a),unchanged_from_v2=name!='tropical'))
    sheet.save(P/'comparison.png')
    report=dict(materials=records,failures=[r['material'] for r in records if not all(e['pass'] for e in r['edge_checks'])])
    (P/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    (P/'index.html').write_text('<meta charset="utf-8"><title>MM6 masters v3</title><h1>Tropical correction; other four masters unchanged</h1><img src="comparison.png">'+''.join('<h2>'+n+'</h2><img src="previews/'+n+'_repeat.png">' for n in previous.MATERIALS))
    print(json.dumps(report))
if __name__=='__main__':main()
