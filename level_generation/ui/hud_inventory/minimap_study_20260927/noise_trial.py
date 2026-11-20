"""Add seeded land-only tonal texture to the gentler minimap; never change coordinates or deploy."""
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import gaussian_filter

HERE = Path(__file__).resolve().parent
OUT = HERE/'new_sorpigal'
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT))
from level_generation.minimaps.processing import composite, rgba


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    terrain_path = OUT/'vinevi_terrain_processed_master.png'
    objects_path = OUT/'vinevi_objects_processed_master.png'
    terrain = np.array(Image.open(terrain_path).convert('RGBA'), dtype=np.float32)/255
    objects = np.array(Image.open(objects_path).convert('RGBA'), dtype=np.float32)/255
    size = terrain.shape[0]
    assert terrain.shape == objects.shape == (2048, 2048, 4)
    # Select land from unlit material color, so blue fill on shadowed slopes is not mistaken for water.
    atlas = np.array(Image.open(OUT/'materials/terrain.png').convert('RGB'), dtype=np.float32)
    water = (atlas[:, :, 2] > atlas[:, :, 0]*1.25) & (atlas[:, :, 1] > atlas[:, :, 0]*1.2)
    land = np.array(Image.fromarray((~water).astype('uint8')*255).resize((size, size), Image.Resampling.BOX),
                    dtype=np.float32)/255
    rng = np.random.default_rng(20260928)
    bands = [(0, .25), (1, .50), (3, .35), (9, .15)]
    field = np.zeros((size, size), dtype=np.float32)
    for sigma, weight in bands:
        layer = rng.standard_normal((size, size), dtype=np.float32)
        if sigma:
            layer = gaussian_filter(layer, sigma)
        layer = (layer-layer.mean())/layer.std()
        field += layer*weight
    field = np.clip(field/field.std(), -2.5, 2.5)
    field -= field[land > .99].mean()
    outputs = {}
    stats = {}
    for key, strength in [('vinevi_noise_light', .06), ('vinevi_noise_medium', .11)]:
        adjusted = terrain.copy()
        adjusted[:, :, :3] = np.clip(terrain[:, :, :3]*(1+field[:, :, None]*land[:, :, None]*strength), 0, 1)
        assert np.array_equal(adjusted[:, :, 3], terrain[:, :, 3])
        assert np.array_equal(adjusted[land == 0], terrain[land == 0])
        image = composite(adjusted, objects)
        image.save(OUT/(key+'_master.png'))
        rgba(adjusted).save(OUT/(key+'_terrain_master.png'))
        path = OUT/(key+'_x2.png')
        image.resize((1024, 1024), Image.Resampling.LANCZOS).save(path)
        outputs[key+'_x2'] = dict(file=path.name, sha256=sha(path))
        delta = (adjusted[:, :, :3]-terrain[:, :, :3]) @ np.array([.2126,.7152,.0722])
        stats[key] = dict(strength=strength, land_luma_rms_255=float(np.sqrt(np.mean(delta[land>.99]**2))*255))
    rgba(np.dstack([land]*3+[np.ones_like(land)])).save(OUT/'noise_land_mask.png')
    original = np.array(Image.open(OUT/'vinevi_master.png').convert('RGB'))
    assert np.array_equal(np.array(composite(terrain, objects)), original), 'Layer base differs from the reviewed image'
    opaque = objects[:, :, 3] == 1
    for key in ['vinevi_noise_light', 'vinevi_noise_medium']:
        candidate = np.array(Image.open(OUT/(key+'_master.png')))
        assert np.array_equal(candidate[opaque], original[opaque]), 'Building colors changed'
    # Retain the base and its approval records. These are additional, unaccepted comparisons only.
    sources = json.loads((OUT/'sources.json').read_text())
    for path, expected in sources['sources'].items():
        assert sha(ROOT/path) == expected
    receipt = dict(status='new_sorpigal_trial_only_not_accepted', outputs=outputs,
        inputs={str(p.relative_to(OUT)):sha(p) for p in [terrain_path, objects_path, OUT/'materials/terrain.png']},
        seed=20260928, bands_master_pixels=bands, stats=stats, chromatic_noise=False,
        geometry_or_image_warp=False, building_layer_unchanged=True, pure_water_master_pixels_unchanged=True,
        caveat='Land mask is color-derived from the unlit atlas; a narrow antialiased shoreline can receive partial texture.',
        bulk_generation_and_deployment='Stopped at user request; this trial does not authorize resuming it.')
    (OUT/'noise_trial.json').write_text(json.dumps(receipt,indent=2)+'\n')
    report = json.loads((OUT/'comparison.json').read_text())
    report['outputs'].update(outputs)
    report['noise_trial'] = receipt
    (OUT/'comparison.json').write_text(json.dumps(report,indent=2)+'\n')
    (OUT/'data.js').write_text('window.MINIMAP_STUDY = '+json.dumps(report)+';\n')
    sheet = Image.new('RGB',(1440,514),'#1a2026')
    draw = ImageDraw.Draw(sheet)
    for i,(key,label) in enumerate([('vinevi_x2','Gentler base'), ('vinevi_noise_light_x2','Light terrain texture'),
                                    ('vinevi_noise_medium_x2','Medium terrain texture')]):
        image = Image.open(OUT/(key+'.png')).crop((140,390,640,890)).resize((480,480),Image.Resampling.LANCZOS)
        sheet.paste(image,(i*480,34))
        draw.text((i*480+12,10),label,fill='white')
    sheet.save(HERE/'noise_comparison.png')
    print(json.dumps(dict(outputs=list(outputs),checks='PASS',stats=stats),indent=2))


if __name__ == '__main__':
    main()
