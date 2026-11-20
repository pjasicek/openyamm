"""Verify the final three sampling replacements against their immediate checkpoint."""
import hashlib
import importlib.util
import json
from pathlib import Path
from PIL import Image, ImageDraw

P = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('sprite_process', P.parent/'mm7_m514/process.py')
pipeline = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pipeline)
reg = json.loads((P/'registration.json').read_text())
checkpoint = P/'checkpoints/before_final_sampling_retry_v3'
before = json.loads((checkpoint/'registration.json').read_text())
changed = ['m198aa0', 'm198ab0', 'm198ac0']
assert set(reg) == set(before)
unchanged = set(reg)-set(changed)
assert all(reg[n] == before[n] for n in unchanged)
hashes = json.loads((checkpoint/'pixel_hashes.json').read_text())
assert all(hashlib.sha256((P/n).read_bytes()).hexdigest() == sha
           for n,sha in hashes.items() if Path(n).stem in unchanged)
assert all(reg[n]['batch'] == 'a_0_detail_0' and 2/reg[n]['scale'] >= 2 for n in changed)
audit = json.loads((P/'review/sampling_repair_edge_audit.json').read_text())
out = Image.new('RGB', (1184,600*len(changed)), 'white')
draw = ImageDraw.Draw(out)
for i,n in enumerate(changed):
    audit[n] = {stage: pipeline.contour_score(Image.open(P/f'{folder}/{n}.png'))
                for stage,folder in [('cleaned','cleaned'),('aligned','aligned_2x')]}
    origin = reg[n]['canvas_origin_px']
    im = Image.open(P/f'aligned_2x/{n}.png').crop([-32-origin[0],-32-origin[1],560-origin[0],544-origin[1]])
    for col,bg in enumerate(['#e8e8e8','#303030']):
        tile = Image.new('RGB', im.size, bg)
        tile.paste(im,mask=im.getchannel('A'))
        out.paste(tile,(col*592,i*600+24))
    draw.text((8,i*600+5),n+' actual 2x; master '+format(2/reg[n]['scale'],'.6f')+'x',fill='black')
out.save(P/'review/final_sampling_retry_v3_edges.png')
(P/'review/sampling_repair_edge_audit.json').write_text(json.dumps(audit,indent=2)+'\n')
result = dict(new_frames=changed,previous_pixels_exact=True,previous_registration_exact=True,
              minimum_sampling=min(2/reg[n]['scale'] for n in changed),
              maximum_sampling=max(2/reg[n]['scale'] for n in changed),
              edge_spill_above32=sum(audit[n]['aligned']['above_32'] for n in changed),
              remaining_undersized_frames=sorted(n for n in reg if 2/reg[n]['scale']<2-1e-6),
              visual_review='pending',family_complete=False)
(P/'review/final_sampling_retry_v3_checks.json').write_text(json.dumps(result,indent=2)+'\n')
print(result)
