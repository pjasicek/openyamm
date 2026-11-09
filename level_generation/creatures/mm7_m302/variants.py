"""Author enhanced cloth/hair masks and deterministic native palette transforms."""
import json
from pathlib import Path
import sys
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
sys.path.insert(0,str(HERE.parent/'mm7_m514'))
from process import apply_variant, green_material_mask


def run():
    sources = json.loads((HERE/'sources.json').read_text())
    registration = json.loads((HERE/'registration.json').read_text())
    palettes = {int(p):np.frombuffer((REPO/r['path']).read_bytes()[:768],np.uint8).reshape(256,3).astype(float)
                for p,r in sources['palette_sources'].items()}
    variants = []
    for palette, colors in palettes.items():
        regions = []
        for channel, interval in enumerate([(157,250),(97,138)]):
            a,b = interval
            base = palettes[58][a:b]
            target = colors[a:b]
            matrix = np.linalg.lstsq(base,target,rcond=None)[0]
            regions.append(dict(channel=channel,rgb_matrix=matrix.tolist(),native_indices=[a,b-1],
                                mean_fit_error=float(abs(base@matrix-target).mean())))
        descriptors = []
        for descriptor, binding in sources['descriptor_bindings'].items():
            group = sources['groups'][binding['standing']]
            if group['frames'][0]['palette_id'] == palette:
                descriptors.append(int(descriptor))
        variants.append(dict(id=f'mm7:palette{palette}',palette_id=palette,default=palette==58,
                             exact_bypass=palette==58,descriptors=descriptors,regions=regions))
    corrections = json.loads((HERE/'hair_mask_corrections.json').read_text())['frames']
    masks = {}
    for name, record in registration.items():
        image = Image.open(HERE/f'aligned_2x/{name}.png')
        rgba = np.array(image)
        rgb = rgba[:,:,:3].astype(float)
        red,green,blue = rgb.transpose(2,0,1)
        cloth = np.array(green_material_mask(image))
        # Enhanced green cap and nearby disconnected brown material identify hair.
        green_labels, count = ndimage.label(cloth>128)
        components = ndimage.find_objects(green_labels)
        viable = [(i+1,box) for i,box in enumerate(components)
                  if box and np.count_nonzero(green_labels[box]==i+1)>30]
        compact = [(i,box) for i,box in viable
                   if (box[1].stop-box[1].start)/(box[0].stop-box[0].start) >= .8]
        cap_label, cap_box = min(compact or viable,key=lambda entry:entry[1][0].start)
        cap = green_labels == cap_label
        cap_width = cap_box[1].stop-cap_box[1].start
        cap_height = cap_box[0].stop-cap_box[0].start
        cap_x = (cap_box[1].start+cap_box[1].stop)/2
        yy,xx = np.indices(rgba.shape[:2])
        candidate = (red>green*1.35)&(green>blue*1.4)&(blue<red*.4)&(red<122)&(rgba[:,:,3]>0)
        # Keep the short rear nape above the fleece collar. Side beards lie forward of the cap.
        view = int(name[-1])
        if view == 4:
            candidate &= yy < cap_box[0].stop+cap_height*.35
        elif view == 3:
            candidate &= (yy < cap_box[0].stop+cap_height*.35)|(xx>cap_x+cap_width*.25)
        elif view == 2:
            candidate &= (yy < cap_box[0].stop+cap_height*.35)|(xx>cap_x)
        labels, count = ndimage.label(ndimage.binary_opening(candidate,iterations=2))
        cap_distance = ndimage.distance_transform_edt(~cap)
        hair = np.zeros(rgba.shape[:2],np.uint8)
        eligible = []
        for component in range(1,count+1):
            selection = labels==component
            area = np.count_nonzero(selection)
            if area>15 and cap_distance[selection].min()<cap_width*.65:
                eligible.append((area,component))
        if eligible:
            largest = max(eligible)[1]
            hair[(ndimage.distance_transform_edt(labels!=largest)<=2)&candidate] = 255
            nape = (yy<cap_box[0].stop+cap_height*.35)&(abs(xx-cap_x)<cap_width*.6)
            hair[candidate&nape] = 255
        if name in corrections:
            selected = Image.new('L',image.size)
            painter = ImageDraw.Draw(selected)
            for points in corrections[name]['include']:
                painter.polygon([tuple(point) for point in points],fill=255)
            for points in corrections[name]['exclude']:
                painter.polygon([tuple(point) for point in points],fill=0)
            material = (red>green*1.30)&(green>blue*1.3)&(blue<red*.44)&(rgba[:,:,3]>0)
            hair = np.where(material&(np.array(selected)>0),255,0).astype(np.uint8)
        hair[cloth>0] = 0
        mask = Image.fromarray(np.dstack((cloth,hair,np.zeros_like(hair))))
        mask.save(HERE/f'masks_2x/{name}.png')
        masks[name] = mask
    data = dict(variants=variants,regions=[dict(id='cloth',channel='R',construction='Enhanced RGB green dominance coverage.'),
        dict(id='hair',channel='G',construction='Enhanced warm brown components adjoining the enhanced green cap, with view-specific nape constraints and 24 traced pose corrections in hair_mask_corrections.json.')],
        recolor=dict(operation='independent_masked_rgb_matrices',color_space='encoded sRGB 0..255',
                     rule='base + sum(mask[channel] * (base @ region_matrix - base)); exact base bypass; alpha unchanged',
                     mask_format='RGB8 linear; R cloth, G hair, B reserved zero',
                     calibration='Native palette entries 157..249 cloth and 97..137 hair. Masks are selected on enhanced pixels.'))
    (HERE/'variants.json').write_text(json.dumps(data,indent=2)+'\n')
    settings = json.loads((HERE/'processing_settings.json').read_text())
    settings['masks'] = data['recolor']['mask_format']
    settings['mask_regions'] = data['regions']
    settings['recolor'] = data['recolor']
    (HERE/'processing_settings.json').write_text(json.dumps(settings,indent=2)+'\n')
    names = list(registration)
    contact = Image.new('RGB',(4*270,((len(names)+3)//4)*350),(45,45,45));draw=ImageDraw.Draw(contact)
    for i,name in enumerate(names):
        im = Image.open(HERE/f'aligned_2x/{name}.png');mask=masks[name]
        color = np.array(im);w = np.array(mask)/255
        color[:,:,:3] = np.round(color[:,:,:3]*(1-w.sum(axis=2)[:,:,None]*.7)+
                              (w[:,:,0,None]*np.array([0,200,255])+w[:,:,1,None]*np.array([255,180,0]))*.7).astype(np.uint8)
        preview = Image.fromarray(color).resize((256,256),Image.Resampling.LANCZOS)
        x=i%4*270;y=i//4*350;contact.paste(preview,(x,y+24),preview);draw.text((x,y+3),name,fill='white')
    for i,y in enumerate(range(0,contact.height,350*4)):
        contact.crop((0,y,contact.width,min(y+350*4,contact.height))).save(HERE/f'review/material_masks_{i}.png')
    contact = Image.new('RGB',(9*180,5*225),(45,45,45));draw=ImageDraw.Draw(contact)
    for row,name in enumerate(json.loads((HERE/'batches.json').read_text())['standing']['frames']):
        im=Image.open(HERE/f'aligned_2x/{name}.png')
        for col,v in enumerate(variants):
            out=apply_variant(im,masks[name],v)
            assert np.array_equal(np.array(out)[:,:,3],np.array(im)[:,:,3])
            tile=out.resize((200,200),Image.Resampling.LANCZOS)
            contact.paste(tile,(col*180,row*225+20),tile);draw.text((col*180,row*225),str(v['palette_id'])+' '+name,fill='white')
    contact.save(HERE/'review/identity_variants.png')
    print('Authored cloth/hair masks and nine native appearance transforms for',len(names),'frames')


if __name__ == '__main__':
    run()
