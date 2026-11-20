"""Fit x2 comparison files, add deterministic terrain styling, and measure alignment."""
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy.ndimage import gaussian_filter

HERE = Path(__file__).resolve().parent
OUT = HERE / 'new_sorpigal'
ROOT = HERE.parents[3]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def bilateral(image):
    source = np.array(image, dtype=np.float32)
    padded = np.pad(source, ((2,2),(2,2),(0,0)), mode='edge')
    total = np.zeros_like(source)
    norm = np.zeros(source.shape[:2], np.float32)
    for dy in range(-2,3):
        for dx in range(-2,3):
            other = padded[2+dy:2+dy+1024,2+dx:2+dx+1024]
            distance = np.sum((other-source)**2, axis=2)
            weight = np.exp(-distance/(2*26**2)-(dx*dx+dy*dy)/(2*1.4**2))
            total += other*weight[:,:,None]
            norm += weight
    return total/norm[:,:,None]


def main():
    outputs = {}
    for name in ['faithful','light_denoise']:
        raw = OUT / 'esrgan_raw' / (name+'.png')
        image = Image.open(raw).convert('RGB')
        assert image.size == (2176,2176)
        master = image.crop((64,64,2112,2112))
        master.save(OUT / ('esrgan_'+name+'_master.png'))
        master.resize((1024,1024),Image.Resampling.LANCZOS).save(OUT/('esrgan_'+name+'_x2.png'))
    for name in ['blender','blender_smooth']:
        Image.open(OUT/(name+'_master.png')).resize((1024,1024),Image.Resampling.LANCZOS).save(OUT/(name+'_x2.png'))
    for name in ['faithful','light_denoise']:
        with Image.open(OUT/'esrgan_anime_raw'/(name+'.png')) as image:
            assert image.size==(1088,1088)
            image.crop((32,32,1056,1056)).save(OUT/('anime_'+name+'_x2.png'))
    data = json.loads((OUT/'scene_data.json').read_text())
    styled = bilateral(Image.open(OUT/'blender_smooth_x2.png').convert('RGB'))
    # Heights are sampled in world UV coordinates; this changes shading, never XY positions.
    heights = np.array(data['height_map'],np.float32).reshape(128,128)*32
    # Extend only the final sample to the map's unsampled boundary margin.
    expanded = Image.fromarray(np.pad(heights,((0,1),(0,1)),mode='edge'))
    grid = np.arange(1024,dtype=np.float32)/8
    left = grid.astype(int); frac = grid-left
    field = np.array(expanded)
    interp_x = field[:,left]*(1-frac) + field[:,left+1]*frac
    field = interp_x[left]*(1-frac[:,None]) + interp_x[left+1]*frac[:,None]
    dy,dx = np.gradient(gaussian_filter(field/64, sigma=4))
    dx*=2;dy*=2
    illumination = (.5*dx+.5*dy+.70710678)/np.sqrt(1+dx*dx+dy*dy)
    shade = np.clip(1+1.25*(illumination-.70710678),.5,1.3)
    styled = 255*np.power(np.clip(styled/255,0,1),.88)*shade[:,:,None]
    Image.fromarray(np.clip(styled,0,255).astype('uint8')).save(OUT/'blender_styled_x2.png')

    selected_models = {13:'Temple',19:'West bridge',46:'Pier',75:'Dungeon entrance',
                       78:'Obelisk',79:'Tavern',82:'Keep'}
    controls = []
    for model in data['bmodels']:
        if model['index'] not in selected_models:
            continue
        vertices = np.array([[v[a] for a in 'xyz'] for v in model['vertices']])
        position = (vertices.min(axis=0)+vertices.max(axis=0))/2
        controls.append(dict(label=selected_models[model['index']],world=position.tolist(),
            pixel=[(position[0]+32768)/64,(32768-position[1])/64]))
    overlay = Image.new('RGBA',(1024,1024));draw=ImageDraw.Draw(overlay)
    for polygon in data['roof_polygons']:
        coords=[((x+32768)/64,(32768-y)/64) for x,y in polygon['points']]
        draw.line(coords+[coords[0]],fill=(255,220,70,180),width=1)
    overlay.save(OUT/'geometry_overlay.png')

    # Whole-frame translation test is a signal, not a guarantee against local neural changes.
    original = Image.open(OUT/'original.png').convert('L')
    base = np.array(original.filter(ImageFilter.GaussianBlur(1)),float)
    base -= base.mean()
    shifts = {}
    for name in ['esrgan_faithful','esrgan_light_denoise','anime_faithful','anime_light_denoise']:
        image=Image.open(OUT/(name+'_x2.png')).resize((512,512),Image.Resampling.LANCZOS).convert('L')
        other=np.array(image.filter(ImageFilter.GaussianBlur(1)),float);other-=other.mean()
        cross=np.fft.fft2(base)*np.conj(np.fft.fft2(other));cross/=np.maximum(abs(cross),1e-9)
        peak=np.unravel_index(np.argmax(np.fft.ifft2(cross).real),base.shape)
        shifts[name]=[int(p if p<=256 else p-512)*2 for p in peak[::-1]]
    names=['original_x2','installed','lanczos_x2','esrgan_faithful_x2','esrgan_light_denoise_x2',
           'anime_faithful_x2','anime_light_denoise_x2','blender_x2','blender_smooth_x2','blender_styled_x2']
    for name in names:
        path=OUT/(name+'.png')
        with Image.open(path) as im:
            assert im.size==(1024,1024)
        outputs[name]=dict(file=name+'.png',sha256=sha(path))
    source=json.loads((OUT/'sources.json').read_text())
    assert all(sha(ROOT/path)==value for path,value in source['sources'].items())
    # Other active work may publish unrelated icons. Validate this study's target,
    # without requiring the entire shared ledger to remain frozen.
    current_index=json.loads((HERE.parent/'accepted_icons.json').read_text())
    current_ledger=json.loads((HERE.parent/'checkpoint/state.json').read_text())
    expected=source['sources']['assets_dev/worlds/mm6/icons_x2/oute3.bmp']
    target='worlds-mm6--icons--oute3.bmp'
    assert current_index['records'][target]['sha256']==expected
    assert current_ledger['staged_targets'][target]['sha256']==expected
    capture=json.loads((OUT/'blender_capture.json').read_text())
    report=dict(status='comparison_only_not_accepted',outputs=outputs,controls=controls,
        esrgan_global_translation_x2_pixels=shifts,blender_projection=capture,
        minimap_runtime_and_acceptance_unchanged=True,
        shared_index_changed_during_study=sha(HERE.parent/'accepted_icons.json')!=source['index_sha256'],
        model=dict(name='realesrgan-x4plus',scale=4,output_scale=2,reflect_padding_native_pixels=16,
                   param_sha256=sha(ROOT/'tools/upscaling/models/realesrgan-x4plus.param'),
                   weights_sha256=sha(ROOT/'tools/upscaling/models/realesrgan-x4plus.bin')),
        second_model=dict(name='realesr-animevideov3',scale=2,
            param_sha256=sha(ROOT/'tools/upscaling/models/realesr-animevideov3-x2.param'),
            weights_sha256=sha(ROOT/'tools/upscaling/models/realesr-animevideov3-x2.bin')),
        blender_styling=dict(bilateral_radius=2,bilateral_sigma_color=26,bilateral_sigma_space=1.4,
            gamma=.88,height_shade_gaussian_pixels=4,height_normal_exaggeration=2,xy_warp=False),
        warning='Exact camera alignment does not prove the original painted map is perfectly registered. '
                'Neural upscaling can change small details; inspect landmarks and compare against geometry.')
    # Preserve the separately rendered layered-process trial when refreshing the original study.
    if (OUT/'vinevi_comparison.json').exists():
        process = json.loads((OUT/'vinevi_comparison.json').read_text())
        assert process['recipe'] == json.loads((HERE/'vinevi_recipe.json').read_text()), \
            'Run finish_vinevi.py after changing its recipe'
        for row in process['outputs'].values():
            assert sha(OUT/row['file']) == row['sha256']
        report['outputs'].update(process['outputs'])
        report['vinevi_process'] = process
    if (OUT/'noise_trial.json').exists():
        noise = json.loads((OUT/'noise_trial.json').read_text())
        for name, expected in noise['inputs'].items():
            assert sha(OUT/name) == expected, 'Rerun noise_trial.py after changing its base layers'
        for row in noise['outputs'].values():
            assert sha(OUT/row['file']) == row['sha256']
        report['outputs'].update(noise['outputs'])
        report['noise_trial'] = noise
    (OUT/'comparison.json').write_text(json.dumps(report,indent=2)+'\n')
    (OUT/'data.js').write_text('window.MINIMAP_STUDY = '+json.dumps(report)+';\n')
    print(json.dumps(dict(outputs=len(outputs),global_shifts=shifts,projection_error=capture['max_projection_error_x2_pixels'])))


if __name__=='__main__':
    main()
