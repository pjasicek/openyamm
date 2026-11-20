"""Attenuate demonstrated painted high-contrast markings, preserving generated geometry."""
import json
import numpy as np
from PIL import Image, ImageDraw
import lighting
from process import ROOT, queue, save, fix

def run():
    lighting.SIGMA = 5
    reg = json.loads((ROOT / 'registration.json').read_text())
    folder = ROOT / 'toned_2x'
    folder.mkdir(exist_ok=True)
    for name, record in reg.items():
        art = Image.open(ROOT / f'aligned_2x/{name}.png').convert('RGBA')
        pixels = np.array(art)
        alpha = pixels[:, :, 3] / 255
        rgb = pixels[:, :, :3].astype(float)
        native = Image.new('RGBA', art.size)
        native.paste(queue.native(ROOT, name).resize((512, 512), Image.Resampling.NEAREST),
                     tuple(-v for v in record['canvas_origin_px']))
        source = np.asarray(native)
        sourceField = lighting.field(source[:, :, :3].astype(float), source[:, :, 3] / 255)
        artField = lighting.field(rgb, alpha)
        # Only coarse native illumination is used. All contours and fine texture are generated.
        corrected = sourceField + .55 * (rgb - artField)
        pixels[:, :, :3] = np.round(corrected).clip(0, 255).astype(np.uint8)
        result = fix(Image.fromarray(pixels))
        assert np.array_equal(np.asarray(result)[:, :, 3], np.asarray(art)[:, :, 3])
        result.save(folder / (name + '.png'))
    save(ROOT / 'tone_refinement.json', {
        'reason': 'All-action review showed harsh cream veins and over-saturated plum after gain-only correction.',
        'operation': 'native coarse RGB + 0.55 * (generated RGB - generated coarse RGB), rounded/clamped RGB8',
        'coarse_filter': 'alpha-normalized Gaussian sigma 5 physical pixels, nearest supported extension',
        'fixed_across_all_frames': True, 'alpha_and_geometry_unchanged': True,
        'input': 'aligned_2x', 'output': 'toned_2x', 'frames': len(reg)
    })
    names = ['m636wa1', 'm636wh1', 'm636wa2', 'm636wa4', 'm636xa4']
    sheet = Image.new('RGB', (512 * len(names), 1650), (35, 35, 35))
    draw = ImageDraw.Draw(sheet)
    for i, name in enumerate(names):
        pics = [queue.native(ROOT, name).resize((512,512), Image.Resampling.NEAREST),
                Image.open(ROOT / f'final_2x/{name}.png'), Image.open(folder / (name + '.png'))]
        for row, pic in enumerate(pics):
            bg = Image.new('RGBA', pic.size, (35,35,35,255))
            bg.alpha_composite(pic)
            sheet.paste(bg.convert('RGB'), (512*i,550*row+25))
            draw.text((512*i+5,550*row+5), name+' '+['native','gain correction','tone refinement'][row], fill='white')
    sheet.save(ROOT / 'review/tone_refinement.png')
    print('Refined tone of', len(reg), 'generated frames; all alpha unchanged')

if __name__ == '__main__':
    run()
