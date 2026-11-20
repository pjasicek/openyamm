"""Propose enhanced-art sash/peg rectangles; never accept proposals without visual review."""
import json
import numpy as np
from scipy import ndimage as ndi
from PIL import Image, ImageDraw
from process import ROOT, save

def components(mask):
    labels, count = ndi.label(ndi.binary_closing(mask, iterations=2))
    result = []
    for i, bounds in enumerate(ndi.find_objects(labels), 1):
        if bounds is None:
            continue
        yy, xx = bounds
        area = int((labels[bounds] == i).sum())
        if area >= 25:
            result.append(([xx.start, yy.start, xx.stop, yy.stop], area))
    return result

def contacts(exclusions, folder):
    folder.mkdir(exist_ok=True, parents=True)
    batches = json.loads((ROOT/'batches.json').read_text())
    for key, batch in batches.items():
        cols = min(4, len(batch['frames']))
        sheet = Image.new('RGB', (cols*300, ((len(batch['frames'])+cols-1)//cols)*320), '#222222')
        for i, name in enumerate(batch['frames']):
            im = Image.open(ROOT/f'toned_2x/{name}.png').convert('RGBA')
            bg = Image.new('RGBA', im.size, (35,35,35,255)); bg.alpha_composite(im)
            draw = ImageDraw.Draw(bg)
            for j, box in enumerate(exclusions.get(name, [])):
                draw.rectangle(box, outline=(255,80,220,255), width=2)
                draw.text((box[0],box[1]-12), str(j), fill='white')
            for y in range(128,576,64):
                draw.text((2,y), str(y), fill='#aaaaaa')
            for x in range(128,576,64):
                draw.text((x,2), str(x), fill='#aaaaaa')
            x,y = (i%cols)*300,(i//cols)*320
            sheet.paste(bg.convert('RGB').resize((288,288)),(x,y+25))
            ImageDraw.Draw(sheet).text((x+3,y+5),name,fill='white')
        sheet.save(folder/f'{key}.png')

if __name__ == '__main__':
    identity = json.loads((ROOT/'checkpoints/identity_material_exclusions.json').read_text())
    proposals = dict(identity)
    reg = json.loads((ROOT/'calibration_registration.json').read_text())
    for name, record in reg.items():
        if name in proposals:
            continue
        if record['batch'].startswith('native_d_'):
            proposals[name] = []
            continue
        a = np.asarray(Image.open(ROOT/f'toned_2x/{name}.png')).astype(int)
        r,g,b = np.moveaxis(a[:,:,:3],-1,0); y,x = np.indices(r.shape)
        sash = (r-g>12)&(b>=g-8)&(a[:,:,3]>128)&(y>260)&(y<350)&(x>200)&(x<380)
        candidates = components(sash)
        boxes = []
        if candidates:
            box, area = max(candidates, key=lambda v: v[1])
            boxes.append([box[0]-2,box[1]-2,box[2]+2,box[3]+2])
        wood = (r-g>8)&(g-b>8)&(a[:,:,3]>128)&(y>365)
        for box, area in components(wood):
            if box[3]-box[1]>25:
                boxes.append([box[0]-2,box[1]-3,box[2]+2,box[3]+3])
        proposals[name] = boxes
    save(ROOT/'review/material_exclusion_proposals.json',proposals)
    contacts(proposals, ROOT/'review/exclusion_proposals')
    print('Proposed enhanced-art exclusions; all rectangles require visual review, death poses require manual annotation.')
