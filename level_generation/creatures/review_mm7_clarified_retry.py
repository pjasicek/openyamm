"""Inspect new clarified-request pixels and audit every accepted sampling replacement."""
import hashlib
import importlib.util
import json
import math
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('sprite_process', ROOT/'mm7_m514/process.py')
pipeline = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pipeline)
for family in ['mm7_m198','mm7_m222']:
    p = ROOT/family
    reg = json.loads((p/'registration.json').read_text())
    before = json.loads((p/'checkpoints/before_clarified_retry/registration.json').read_text())
    changed = sorted(n for n in reg if reg[n]['batch'] != before[n]['batch'])
    unchanged = sorted(set(reg)-set(changed))
    assert set(reg) == set(before)
    assert all(reg[n] == before[n] for n in unchanged)
    hashes = json.loads((p/'checkpoints/before_clarified_retry/pixel_hashes.json').read_text())
    assert all(hashlib.sha256((p/n).read_bytes()).hexdigest()==sha for n,sha in hashes.items() if Path(n).stem in unchanged)
    assert all(2/reg[n]['scale'] >= 2 for n in changed)
    audit = {n: {stage: pipeline.contour_score(Image.open(p/f'{folder}/{n}.png'))
                 for stage,folder in [('cleaned','cleaned'),('aligned','aligned_2x')]}
             for n in reg if '_detail_' in reg[n]['batch']}
    (p/'review/sampling_repair_edge_audit.json').write_text(json.dumps(audit,indent=2)+'\n')
    worst = sorted(changed, key=lambda n: audit[n]['aligned']['maximum'], reverse=True)[:3]
    edges = Image.new('RGB', (1152,600*len(worst)), 'white')
    edge_draw = ImageDraw.Draw(edges)
    for i,n in enumerate(worst):
        im = Image.open(p/f'aligned_2x/{n}.png')
        im = im.crop(im.getbbox())
        im.thumbnail((560,560))
        for col,bg in enumerate(['#e8e8e8','#303030']):
            tile = Image.new('RGB',(576,576),bg)
            tile.paste(im,((576-im.width)//2,(576-im.height)//2),im.getchannel('A'))
            edges.paste(tile,(col*576,i*600+24))
        edge_draw.text((8,i*600+5),n+' light/dark contour review',fill='black')
    edges.save(p/'review/clarified_edges.png')
    for first in range(0,len(changed),4):
        names = changed[first:first+4]
        out = Image.new('RGB',(1152,600*math.ceil(len(names)/2)),'#e8e8e8')
        draw = ImageDraw.Draw(out)
        for i,n in enumerate(names):
            origin = reg[n]['canvas_origin_px']
            im = Image.open(p/f'aligned_2x/{n}.png').crop([-32-origin[0],-32-origin[1],544-origin[0],544-origin[1]])
            tile = Image.new('RGB',im.size,'#303030' if i%2 else '#e8e8e8');tile.paste(im,mask=im.getchannel('A'))
            x,y = i%2*576,i//2*600
            out.paste(tile,(x,y+24));draw.text((x+4,y+4),n+' actual2x; master '+format(2/reg[n]['scale'],'.3f')+'x',fill='black')
        out.save(p/f'review/clarified_actual_2x_{first//4}.png')
    result = dict(new_frames=changed,previous_pixels_exact=True,previous_registration_exact=True,
                  minimum_sampling=min(2/reg[n]['scale'] for n in changed),maximum_sampling=max(2/reg[n]['scale'] for n in changed),
                  edge_spill_above32=sum(audit[n]['aligned']['above_32'] for n in changed),
                  remaining_undersized_frames=sorted(n for n in reg if 2/reg[n]['scale']<2-1e-6),visual_review='pending')
    (p/'review/clarified_retry_checks.json').write_text(json.dumps(result,indent=2)+'\n')
    print(family,result)
