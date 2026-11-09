"""Compare original / v1 / v2 scale and inspect sand border and internal joins."""
import json
import zipfile
from pathlib import Path
from PIL import Image, ImageDraw
import numpy as np
from scipy.ndimage import gaussian_filter
from build import P, T, MATERIALS, sha


def main():
    report=json.loads((P/'report.json').read_text())
    sheet=Image.new('RGB',(1024,3*368),'#202933');draw=ImageDraw.Draw(sheet)
    for row,name in enumerate(('cracked','tropical','sand')):
        tile=MATERIALS[name]
        paths=[T/'mm6_remaining/references'/(tile+'.png'),P.parent/'v1/runtime_x2/worlds/mm6/terrain_x2'/(tile+'.png'),P/'runtime_x2/worlds/mm6/terrain_x2'/(tile+'.png')]
        for col,path in enumerate(paths):
            image=Image.open(path).convert('RGB').resize((336,336),Image.Resampling.NEAREST)
            sheet.paste(image,(col*342,row*368+24))
            draw.text((col*342+4,row*368+5),name+' '+['original','v1','v2'][col],fill='white')
    sheet.save(P/'revision_comparison.png')
    # Separate broad dune shape from fine grain: inspect both at true wraps AND
    # internal offsets, where v1's cut-and-paste strips escaped the old edge test.
    diagnostics=[]
    for version in ('v1','v2'):
        a=np.asarray(Image.open(P.parent/version/'runtime_x2/worlds/mm6/terrain_x2/6sandtyl.png'),float)
        for scale in (0,3,8):
            b=a if scale==0 else gaussian_filter(a,(scale,scale,0),mode='wrap')
            for axis in (0,1):
                c=b if axis==1 else b.transpose(1,0,2)
                gradient=np.sqrt(np.mean((c-np.roll(c,1,axis=1))**2,axis=2))
                diagnostics.append(dict(version=version,sigma=scale,axis=axis,column_rms=np.sqrt(np.mean(gradient**2,axis=0)).tolist()))
    (P/'sand_multiscale.json').write_text(json.dumps({'method':'Diagnostic profiles, not an artistic pass guarantee. Includes internal columns and low-frequency dune contours.', 'profiles':diagnostics},indent=2)+'\n')
    for name in ('snow','swamp'):
        for relative in (f'materials/{name}.png',f'runtime_x2/worlds/mm6/terrain_x2/{MATERIALS[name]}.png'):
            assert sha(P/relative)==sha(P.parent/'v1'/relative)
    for r in report['materials']:
        r['prompt']='prompts/'+('sand_repair' if r['material']=='sand' else r['material'])+'.txt' if r['material'] in ('sand','cracked','tropical') else '../v1/prompts/'+r['material']+'.txt'
    report['sand_repair']={'guide':'raw/sand_repair.png','guide_sha256':sha(P/'raw/sand_repair.png'),
                           'offset_input':'raw/sand_offset_input.png','offset_input_sha256':sha(P/'raw/sand_offset_input.png'),
                           'method':'Periodic Poisson gradient insertion in an 80px outer band; central 352px source unchanged'}
    report['visual_review']={'passed':True,'findings':'Cracked and tropical main segments visibly larger; sand border patches in 1281 removed in single, offset and repeated views. Repeating ridge motif remains intentional.'}
    report['preserved_previous_materials']=['snow','swamp']
    report['review_scope']='Texture-space review only: original/v1/v2 comparisons, 3x3 repeats, half-tile shifts, fine and broad sand gradient profiles. No game integration or transitions.'
    (P/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    with zipfile.ZipFile(P/'mm6_material_masters_v2.zip','w',zipfile.ZIP_DEFLATED) as z:
        for folder in ('materials','runtime_x2','prompts'):
            for f in sorted((P/folder).rglob('*')):
                if f.is_file():z.write(f,f.relative_to(P))
        for name in ('README.md','report.json'):z.write(P/name,name)
    page=P/'index.html';s=page.read_text().replace('<h1>','<p><a href="mm6_material_masters_v2.zip">Download v2 masters and runtime exports</a></p><h1>',1)
    s=s.replace('href="prompts/sand.txt"','href="prompts/sand_repair.txt"')
    for name in ('snow','swamp'):s=s.replace(f'href="prompts/{name}.txt"',f'href="../v1/prompts/{name}.txt"')
    page.write_text(s)
    print('Review and export archive saved. Snow and swamp byte-identical to v1.')

if __name__=='__main__':main()
