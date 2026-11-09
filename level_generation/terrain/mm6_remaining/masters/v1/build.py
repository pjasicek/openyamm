"""Prepare imagegen masters using accepted quilting and wrapped-gutter 2x export."""
import hashlib
import importlib.util
import json
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
P = Path(__file__).resolve().parent
T = P.parents[2]
spec = importlib.util.spec_from_file_location('terrain_seams', T / 'seam_repair/build.py')
seams = importlib.util.module_from_spec(spec)
spec.loader.exec_module(seams)
MATERIALS = {'sand':'6sandtyl','snow':'snotyl','cracked':'crktyl','tropical':'troptyl','swamp':'swmtyl'}
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def edge_check(a):
    records=[]
    for axis in (0,1):
        b=a.astype(float) if axis==1 else a.transpose(1,0,2).astype(float)
        energy=np.mean(np.diff(np.tile(b,(1,2,1)),axis=1)**2,axis=2)
        def windows(columns):
            edge=energy[:,np.asarray(columns)-1]
            neighbour=np.stack([np.mean(np.concatenate([energy[:,c-5:c-1],energy[:,c:c+4]],axis=1),axis=1) for c in columns],axis=1)
            values=[]
            for y in range(0,241,4):
                values.extend((np.sqrt(edge[y:y+16].mean(0))/np.maximum(1,np.sqrt(neighbour[y:y+16].mean(0)))).tolist())
            return np.asarray(values)
        e=windows([256]);i=windows([c for c in range(16,497,16) if c!=256])
        r=dict(axis=axis,edge_p95=float(np.percentile(e,95)),edge_max=float(e.max()),interior_p95=float(np.percentile(i,95)),interior_p999=float(np.percentile(i,99.9)))
        r['pass']=r['edge_p95']<1.25*r['interior_p95'] and r['edge_max']<1.25*r['interior_p999']
        records.append(r)
    return records

def main():
    for n in ('materials','runtime_x2/worlds/mm6/terrain_x2','previews'): (P/n).mkdir(parents=True,exist_ok=True)
    records=[];overview=Image.new('RGB',(1024,1400),'#202933');draw=ImageDraw.Draw(overview)
    for row,(name,tile) in enumerate(MATERIALS.items()):
        source=P/'raw'/(name+'.png');original=T/'mm6_remaining/references'/(tile+'.png')
        a=np.asarray(Image.open(source).convert('RGB').resize((512,512),Image.Resampling.LANCZOS),float)
        repaired=seams.periodic(a.copy())
        assert np.array_equal(repaired[64:-64,64:-64],a[64:-64,64:-64])
        master=P/'materials'/(name+'.png');Image.fromarray(seams.byte(repaired)).save(master)
        runtime=seams.reduce(seams.pad(repaired,'wrap'))
        export=P/'runtime_x2/worlds/mm6/terrain_x2'/(tile+'.png');Image.fromarray(runtime).save(export)
        repeated=np.tile(runtime,(3,3,1));offset=np.roll(runtime,(128,128),axis=(0,1))
        Image.fromarray(repeated).save(P/'previews'/(name+'_repeat.png'))
        Image.fromarray(offset).resize((512,512),Image.Resampling.NEAREST).save(P/'previews'/(name+'_offset.png'))
        old=Image.open(original).convert('RGB')
        for col,preview in enumerate([old.resize((256,256),Image.Resampling.NEAREST),Image.fromarray(runtime),Image.fromarray(repeated).resize((256,256)),Image.fromarray(offset)]):
            overview.paste(preview,(col*256,row*280+24));draw.text((col*256+4,row*280+5),name+' '+['original','restored x2','3x3','offset seam'][col],fill='white')
        records.append(dict(material=name,tile=tile,source=str(source.relative_to(P)),source_sha256=sha(source),original=str(original.relative_to(T)),original_sha256=sha(original),prompt='prompts/'+name+'.txt',master='materials/'+name+'.png',master_sha256=sha(master),runtime=str(export.relative_to(P)),runtime_sha256=sha(export),central_384_square_unchanged=True,edge_checks=edge_check(runtime),border_detail=seams.detail(runtime),original_mean_rgb=np.asarray(old).mean((0,1)).tolist(),runtime_mean_rgb=runtime.mean((0,1)).tolist()))
    overview.save(P/'comparison.png')
    report=dict(method='Built-in imagegen; original material and accepted grass fidelity reference. 512px authors, cyclic minimum-error quilting, wrapped-gutter Lanczos to 256px runtime.',status='Prepared masters for visual review; transitions not generated and enhanced not modified.',materials=records,failures=[r['material'] for r in records if not all(c['pass'] for c in r['edge_checks'])])
    (P/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    (P/'runtime_x2/manifest.json').write_text(json.dumps(dict(iteration='mm6_remaining_masters_v1',size=[256,256],files={r['runtime'][len('runtime_x2/') :]:r['runtime_sha256'] for r in records}),indent=2)+'\n')
    page='''<!doctype html><meta charset="utf-8"><title>MM6 material masters</title><style>body{background:#202933;color:#eee;font:16px/1.5 system-ui;max-width:1200px;margin:24px auto}img{max-width:100%}a{color:#9cf}.pair{display:flex}.pair img{width:50%}details{margin:20px 0}</style><h1>MM6 material masters — v1</h1><p>Five masters, 512px authoring and 256px runtime. Original broad forms and palettes guide the restoration. Grass provides the fidelity reference; sand and snow keep their wind-shaped ridges.</p><p>Master review only; transitions and native-map integration remain separate work. <a href="report.json">Checks and provenance</a> · <a href="runtime_x2/manifest.json">Runtime manifest</a></p><img src="comparison.png">'''
    for name,tile in MATERIALS.items():
        page+=f'<h2>{name}</h2><p><a href="materials/{name}.png">512px master</a> · <a href="runtime_x2/worlds/mm6/terrain_x2/{tile}.png">256px runtime</a> · <a href="prompts/{name}.txt">Imagegen prompt</a></p><div class="pair"><img src="../../references/{tile}.png" alt="Original"><img src="materials/{name}.png" alt="Restored"></div><details open><summary>3×3 repetition</summary><img src="previews/{name}_repeat.png"></details><details><summary>Boundary shifted to centre</summary><img src="previews/{name}_offset.png"></details>'
    (P/'index.html').write_text(page)
    print(json.dumps({'materials':len(records),'seam_screening_failures':report['failures']},indent=2))
if __name__ == '__main__': main()
