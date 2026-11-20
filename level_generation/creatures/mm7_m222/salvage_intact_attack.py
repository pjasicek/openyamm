"""Recover three intact poses from an otherwise rejected sheet, without resampling."""
from pathlib import Path
import hashlib
import json
import numpy as np
from PIL import Image

P = Path(__file__).resolve().parent
raw = P/'raw/a_2_detail_2_v1.png'
im = Image.open(raw)
assert im.size == (1254, 1254) and im.mode == 'RGBA'
out = Image.new('RGBA', (1881, 627))
records = []
for destination, (index, name) in enumerate([(1,'m222af2'), (2,'m222ag2'), (3,'m222ah2')]):
    box = [index%2*627, index//2*627, (index%2+1)*627, (index//2+1)*627]
    pixels = np.array(im.crop(box))
    gutter = np.zeros((627,627), dtype=bool)
    gutter[:8] = gutter[-8:] = True
    gutter[:,:8] = gutter[:,-8:] = True
    assert pixels[:,:,3][gutter].max() <= 3, 'A visible pose reaches this crop gutter.'
    before = pixels.copy()
    # Inspected native-scale composites: these are empty gutters, opacity <=3/255.
    pixels[gutter] = 0
    assert np.array_equal(before[~gutter], pixels[~gutter])
    out.paste(Image.fromarray(pixels), (destination*627,0))
    records.append(dict(frame=name, original_raw_rect=box, derived_rect=[destination*627,0,(destination+1)*627,627],
                        interior_pixels_exact=True, discarded_gutter_maximum_alpha=int(before[:,:,3][gutter].max())))
(P/'derived').mkdir(exist_ok=True)
destination = P/'derived/a_2_detail_2_v1_intact.png'
out.save(destination)
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
provenance = dict(original=str(raw.relative_to(P)), original_sha256=sha(raw),
                  output=str(destination.relative_to(P)), output_sha256=sha(destination),
                  resampling=False, transforms='Integer crop and translation only; reviewed empty 8px crop gutters cleared (alpha <=3/255).',
                  excluded_frame='m222ae2: sword tip clipped in original raw; never exported from this sheet.', frames=records)
(P/'derived/a_2_detail_2_v1_intact.json').write_text(json.dumps(provenance,indent=2)+'\n')
p=P/'batches.json';b=json.loads(p.read_text());key='a_2_detail_2_intact'
v=dict(b['a_2_detail_2']);v.update(columns=3, rows=1, frames=[r['frame'] for r in records], reference_only_frames=[],
                                derivation='derived/a_2_detail_2_v1_intact.json')
b[key]=v
# The original batch is retired once every pose has a reviewed replacement.
if 'a_2' in b:
    b['a_2']['reference_only_frames']=sorted(set(b['a_2'].get('reference_only_frames',[]))|set(v['frames']))
p.write_text(json.dumps(b,indent=2)+'\n')
p=P/'generation.json';g=json.loads(p.read_text());g['batches'][key]=dict(selected=str(destination.relative_to(P)),
    derived_from_batch='a_2_detail_2', derived_from_version='v1', provenance='derived/a_2_detail_2_v1_intact.json',
    note='No new generation: reuse only the three intact native poses. Clipped ae2 remains rejected.')
p.write_text(json.dumps(g,indent=2)+'\n')
print('Recovered three poses without resizing; clipped ae2 excluded.')
