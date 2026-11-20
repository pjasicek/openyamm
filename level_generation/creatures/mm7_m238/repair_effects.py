"""Repair reviewed genie mist fringe and casting colors before the final premultiplied resize.

Run after shared process.py, before variants.py and package.py. The immutable input checkpoint
is the accepted extraction with tone 0.85, core tolerance 8 and material edge repair enabled.
"""
import json
import shutil
import sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'mm7_m514'))
from process import contour_score, repair_contour, repair_material_edge_hue


def run():
    registration = json.loads((HERE / 'registration.json').read_text())
    zones = json.loads((HERE / 'effect_repair_zones.json').read_text())
    checkpoint = HERE / 'checkpoints/cleaned_before_effect_repair'
    checkpoint.mkdir(parents=True, exist_ok=True)
    audit = {}
    for name, record in registration.items():
        source = checkpoint / f'{name}.png'
        if not source.exists():
            shutil.copy2(HERE / f'cleaned/{name}.png', source)
        rgba = np.array(Image.open(source))
        rgb = rgba[:, :, :3].astype(float)
        alpha = rgba[:, :, 3]
        r, g, b = rgb.transpose(2, 0, 1)
        edge = ndimage.distance_transform_edt(alpha >= 254) <= 8
        healthy = (alpha >= 254) & (g > r*1.25) & (b >= g) & (b < g*1.40)
        affected = (alpha > 0) & edge & (r > g*.80) & (b > g*1.20)
        if healthy.any():
            _, nearest = ndimage.distance_transform_edt(~healthy, return_indices=True)
            target = rgb[nearest[0], nearest[1]]
            luma = rgb @ np.array([.2126, .7152, .0722])
            target_luma = target @ np.array([.2126, .7152, .0722])
            corrected = target * (luma/np.maximum(target_luma, 1))[:, :, None]
            rgb[affected] = corrected[affected]
        spark = np.zeros(alpha.shape, bool)
        if name in zones:
            region = np.zeros(alpha.shape, bool)
            for x0, y0, x1, y1 in zones[name]['include']:
                region[y0:y1, x0:x1] = True
            for x0, y0, x1, y1 in zones[name]['exclude']:
                region[y0:y1, x0:x1] = False
            r, g, b = rgb.transpose(2, 0, 1)
            spark = region & (alpha > 0) & (r > 100) & (g > r*.40) & (r > b*1.15) & (r >= g)
            target = np.minimum(r/.85, 255)[:, :, None] * np.array([1.0, 1.0, .88])
            rgb[spark] = target[spark]
        if name in ['m238da0', 'm238db0', 'm238dc0', 'm238dd0']:
            r, g, b = rgb.transpose(2, 0, 1)
            luma = rgb @ np.array([.2126, .7152, .0722])
            weight = np.clip((luma-95)/45, 0, 1) * (b >= r*.98) * (g >= r*.98)
            rgb *= (1 + weight*(1/.85-1))[:, :, None]
        rgba[:, :, :3] = np.round(np.clip(rgb, 0, 255)).astype(np.uint8)
        clean = Image.fromarray(rgba)
        clean.save(HERE / f'cleaned/{name}.png')
        scale = record['scale']
        resized = clean.convert('RGBa').resize((round(clean.width*scale), round(clean.height*scale)),
            Image.Resampling.LANCZOS).convert('RGBA')
        resized = repair_material_edge_hue(repair_contour(resized, True, False), True)
        origin = record['canvas_origin_px']
        x, y = record['translate']
        size = Image.open(HERE / f'aligned_2x/{name}.png').size
        aligned = Image.new('RGBA', size)
        aligned.paste(resized, (x-origin[0], y-origin[1]))
        aligned.save(HERE / f'aligned_2x/{name}.png')
        audit[name] = dict(cleaned=contour_score(clean), aligned=contour_score(aligned),
                          repaired_mist_pixels=int(affected.sum()), repaired_spark_pixels=int(spark.sum()))
    (HERE / 'review/cleaned_edge_audit.json').write_text(json.dumps(audit, indent=2)+'\n')
    settings = json.loads((HERE / 'processing_settings.json').read_text())
    settings['effect_color_repair'] = dict(script='repair_effects.py', zones='effect_repair_zones.json',
        input_checkpoint=str(checkpoint.relative_to(HERE)),
        mist='Within 8px contour, purple-blue flecks take nearest healthy blue/cyan hue at unchanged luminance.',
        sparks='Authored enhanced-art rectangles with jewelry exclusions; warm spark RGB becomes [R,R,0.88R]/0.85.',
        clouds='Cool bright cloud RGB ramps from tone 0.85 to native pale tone 1.0 between luminance 95 and 140.',
        invariant='Alpha, native placement, geometry and common batch scale unchanged.')
    (HERE / 'processing_settings.json').write_text(json.dumps(settings, indent=2)+'\n')
    print('Repaired effect colors in', len(registration), 'frames; alpha and placement preserved')


if __name__ == '__main__':
    run()
