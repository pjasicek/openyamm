"""Check all liquid phases and compatible shaded-bank joins against matching masters."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
import json
import argparse
from PIL import ImageDraw
from common import *
from check_land import checks

F=Path(__file__).resolve().parent
BASES=dict(water=('wtrtyl','hdwtr'),lava=('lavtyl','hdlav'),tar=('tartyl','hwoil'))
LANDS=dict(dirt='dirttyl',plains='plntyl',grey_dirt='gdtyl')


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--banks',type=Path,help='Explicit alternative bank candidate folder')
    args=parser.parse_args()
    banks=args.banks.resolve() if args.banks else None
    destination=banks if banks else F
    build=json.loads((F/'build.json').read_text())
    transition_path=banks/'build.json' if banks else P/'transitions/build.json'
    transitions=json.loads(transition_path.read_text())
    overlays=[r for r in transitions['tiles'] if r['overlay']]
    assert len(overlays)==57
    labels={};rgba={};files={};shape_checks=[]
    for r in overlays:
        name=r['name'];path=(banks/'runtime' if banks else OUT)/(name+'.png')
        assert sha(path)==r['runtime_sha256'],name
        assert sha((banks/'fields' if banks else P/'transitions/fields')/(name+'.npz'))==r['field_sha256'],name
        im=Image.open(path);assert im.mode=='RGBA' and im.size==(256,256),name
        rgba[name]=np.asarray(im,float)
        a=rgba[name][:,:,3]/255
        assert np.any(a==0) and np.any(a==1),name
        labels[name]={s:r['binding']['liquid'] if t=='00' else r['binding']['land'] if t=='11'
                      else r['family']+':'+t for s,t in r['topology'].items()}
        files[str(path.relative_to(P))]=sha(path)
        shape_checks.append(dict(name=name,opaque_pixels=int(np.count_nonzero(a==1)),
                                 transparent_pixels=int(np.count_nonzero(a==0))))
    lands={}
    for family,name in LANDS.items():
        path=M/'runtime'/(family+'.png');lands[name]=read(path)
        labels[name]=dict.fromkeys('NSEW',family);files[str(path.relative_to(P))]=sha(path)
    for family,(base,prefix) in BASES.items():
        labels[base]=dict.fromkeys('NSEW',family)
        for record in build['families'][family]['files']:
            path=F/'runtime'/record['name'];assert sha(path)==record['sha256'],path
            files[str(path.relative_to(P))]=sha(path)
    pairs=[(a,s,b) for a in sorted(labels) for b in sorted(labels) for s,o in [('E','W'),('S','N')]
           if labels[a][s]==labels[b][o]]
    results=[];worst=[];bank_change=0
    frozen={};family_loops={g:[] for g in {r['family'] for r in overlays}}
    for phase in range(14):
        liquid={g:read(F/'runtime'/('%s%03d.png'%(prefix,phase))) for g,(_,prefix) in BASES.items()}
        tiles=dict(lands)
        for g,(base,_) in BASES.items():tiles[base]=liquid[g]
        for r in overlays:
            n=r['name'];a=rgba[n][:,:,3:4]/255
            tiles[n]=rgba[n][:,:,:3]*a+liquid[r['binding']['liquid']]*(1-a)
            opaque=a[:,:,0]==1
            if phase==0:frozen[n]=tiles[n][opaque]
            bank_change=max(bank_change,float(abs(tiles[n][opaque]-frozen[n]).max()))
        for a,s,b in pairs:
            m,joined,start=checks.metrics(tiles[a],tiles[b],s)
            score=max(m['boundary_p95']/max(m['interior_p95'],1e-6),m['boundary_max']/max(m['interior_p999'],1e-6))
            results.append(dict(phase=phase,a=a,side=s,b=b,score=score,**m))
            worst.append((score,phase,a,s,b,joined,start));worst=sorted(worst,key=lambda x:-x[0])[:16]
        for family in family_loops:
            records=[r for r in overlays if r['family']==family]
            sheet=Image.new('RGB',(4*256,3*280),'#202933');draw=ImageDraw.Draw(sheet)
            for i,r in enumerate(records):
                draw.text((i%4*256+4,i//4*280+4),r['name']+' frame'+str(phase),fill='white')
                sheet.paste(Image.fromarray(seams.byte(tiles[r['name']])),(i%4*256,i//4*280+24))
            family_loops[family].append(sheet)
        print('Liquid phase',phase,':',len(pairs),'compatible joins',flush=True)
    assert bank_change==0
    for family,views in family_loops.items():
        views[0].save(destination/(family+'_banks.png'))
        views[0].save(destination/(family+'_banks.webp'),save_all=True,append_images=views[1:],duration=117,loop=0,lossless=True)
    sheet=Image.new('RGB',(1024,4*160),'#202933');draw=ImageDraw.Draw(sheet)
    for i,(score,phase,a,s,b,joined,start) in enumerate(worst):
        x,y=i%4*256,i//4*160
        draw.text((x+2,y+2),'%s %s %s f%d'%(a,s,b,phase),fill='white')
        draw.text((x+2,y+16),'relative %.2f'%score,fill='white')
        start=max(0,min(start-8,224))
        crop=Image.fromarray(seams.byte(joined[start:start+32,224:288]))
        sheet.paste(crop.resize((256,128)),(x,y+32))
    sheet.save(destination/'worst_bank_joins.png')
    report=dict(scope='57 shaded RGBA overlays,3 land masters,3 liquid families; all14 phases and cross-family shared pure edges',
        compatible_pairs=len(pairs),checks=results,failures=[r for r in results if not r['passed']],
        alpha_checks=shape_checks,opaque_bank_max_phase_change=bank_change,files=files,
        build_sha256=sha(F/'build.json'),transition_build_sha256=sha(transition_path),
        script_sha256=sha(Path(__file__)),metric_source_sha256=sha(T/'mm7/check.py'))
    (destination/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
    print('Total',len(results),'checks;',len(report['failures']),'failures; opaque banks stable')


if __name__=='__main__':main()
