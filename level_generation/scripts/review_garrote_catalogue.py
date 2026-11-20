"""Compose review sheets and verify Garrote source bindings and rendered coverage."""
import hashlib
import json
import re
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
from catalogue_garrote import ROOT,OUT


def build():
    c=json.loads((OUT/'catalogue.json').read_text());textures=c['textures']
    font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',15)
    groups=[('houses',list(range(24,26))+list(range(27,30))+[31,32]+list(range(35,48))),
            ('services',list(range(16,24))+[54,55]),('walls_keep',list(range(9,16))),
            ('other',list(range(0,9))+[26,30,33,34,48]+list(range(49,54)))]
    assert sorted(i for _,ids in groups for i in ids)==list(range(56))
    for title,ids in groups:
        sheet=Image.new('RGB',(1280,((len(ids)+3)//4)*310+45),'#20272a');draw=ImageDraw.Draw(sheet)
        draw.text((12,12),'Garrote reference — '+title.replace('_',' ')+' (individually framed; use dimensions for scale)',font=font,fill='white')
        for j,i in enumerate(ids):
            r=c['models'][i];a=next(a for a in c['assemblies'] if a['id']==r['assembly'])
            im=Image.open(OUT/f'images/{i:03d}.png').convert('RGB');im.thumbnail((320,260))
            x=j%4*320;y=45+j//4*310;sheet.paste(im,(x,y))
            draw.text((x+5,y+261),f'{i:03d} '+a['title'][:32],font=font,fill='white')
            draw.text((x+5,y+281),' × '.join(str(round(v)) for v in r['bounds']['size']),font=font,fill='#dec799')
        sheet.save(OUT/f'images/contact_{title}.jpg',quality=92)
    # Human-readable roles were checked against both original textures and native rendered facades.
    palette=[('t18a01a','Regular wall'),('t18a02a','Continuous stone'),('t18b01','Dressed base'),('t18a05','Rounded roof tiles'),
      ('t18a03c','Domestic timber door'),('t18b03c','Dressed door'),('t18a04d','Shuttered cottage window'),('t18b04a','Formal lit window'),
      ('t18a06','Stone corner strip'),('t18b06','Dressed corner strip'),('t18a11a','Horizontal trim'),('t68a13mm','Timber canopy / fence')]
    sheet=Image.new('RGB',(1200,3*350+50),'#20272a');draw=ImageDraw.Draw(sheet)
    draw.text((12,12),'Garrote architectural palette — observed role and source bitmap size',font=font,fill='white')
    for j,(key,role) in enumerate(palette):
        t=textures[key];im=Image.open(ROOT/t['path']).convert('RGB');fac=min(256/im.width,256/im.height)
        im=im.resize((round(im.width*fac),round(im.height*fac)),Image.Resampling.NEAREST)
        x=j%4*300;y=50+j//4*350;sheet.paste(im,(x+(300-im.width)//2,y))
        draw.text((x+8,y+265),key+' — '+'×'.join(map(str,t['size'])),font=font,fill='#dec799')
        draw.text((x+8,y+291),role,font=font,fill='white')
    sheet.save(OUT/'images/texture_roles.png')
    assert sorted(i for a in c['assemblies'] for i in a['models'])==list(range(56))
    houses={h['id']:h for a in c['assemblies'] for h in a['houses']}
    assert len(houses)==24
    assert sum(len(h['resident_candidates']) for h in houses.values())==21
    assert sum(bool(h['proprietor']) for h in houses.values())==7
    expected=[(f'{m["index"]:03d}',[m['index']]) for m in c['models']]
    expected += [('assembly_'+a['id'],a['models']) for a in c['assembly_views']]
    for name,ids in expected:
        report=json.loads((OUT/f'images/{name}.json').read_text());assert report['models']==ids
        with Image.open(OUT/f'images/{name}.png') as im:assert im.size==(800,650);im.verify()
    for source in c['sources']+list(textures.values()):
        assert hashlib.sha256((ROOT/source['path']).read_bytes()).hexdigest()==source['sha256'],source['path']
    for m in c['models']:
        assert len(m['face_records'])==m['faces']
        for s in m['services']:
            for f in s['active_faces']:assert m['face_records'][f]['event']==s['event']
    links=0
    for doc in list(OUT.rglob('*.md'))+list((ROOT/'level_generation/projects/mm5_castleview_kalindra').glob('*.md')):
        for target in re.findall(r'\]\(([^)]+)\)',doc.read_text()):
            if target.startswith(('https:','http:','#')):continue
            assert (doc.parent/target.split('#')[0]).exists(),(doc,target)
            links+=1
    result=dict(passed=True,parts=56,physicalAssemblies=len(c['assemblies']),renderedViews=len(expected),
        houses=24,npcRows=21,serviceProprietors=7,textures=len(textures),localLinks=links,
        limitations=['Static initial merged-base assignments; no quest-state simulation.',
          'Reference images use original meshes and UVs, independent framing and neutral lighting.',
          'New MM5 architecture mapping is a proposal; geometry and runtime behavior are not generated.'])
    (OUT/'validation.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))

if __name__=='__main__':build()
