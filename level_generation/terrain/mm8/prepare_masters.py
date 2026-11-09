"""Prepare candidate masters and repeat evidence; visual acceptance remains a separate gate."""
import argparse
import importlib.util
import json

from PIL import ImageDraw
from common import *
from inventory import GROUPS

spec = importlib.util.spec_from_file_location('reviewed_join_metrics', T / 'mm7/check.py')
checks = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checks)
spec = importlib.util.spec_from_file_location('reviewed_poisson_repair', T / 'mm6_remaining/masters/v2/repair_sand.py')
poisson = importlib.util.module_from_spec(spec)
spec.loader.exec_module(poisson)
spec = importlib.util.spec_from_file_location('reviewed_periodic_component', T / 'mm6_new_sorpigal_water/restoration_v2/build.py')
periodic_component = importlib.util.module_from_spec(spec)
spec.loader.exec_module(periodic_component)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('families', nargs='+')
    args = parser.parse_args()
    for name in args.families:
        native = read(P / 'references' / (GROUPS[name][0] + '.png'), 512)
        raw = M / 'raw' / (name + '.png')
        pixels = read(raw, 512)
        if name in ('rock', 'sandstone'):
            # Native-template correlation confirms the generated image contains 1.5 source repeats.
            # Select one native-sized repeat rather than shrinking the original rock features.
            pixels = read(raw, 768)[:512, :512].copy()
        center_repair = M / 'raw' / (name + '_center_repair.png')
        if center_repair.exists():
            assert name == 'plains', 'A new local repair needs its own reviewed region'
            yy, xx = np.mgrid[:512, :512]
            weight = np.clip(np.minimum.reduce([xx - 165, 365 - xx, yy - 160, 300 - yy]) / 24, 0, 1)
            pixels += weight[:, :, None] * (read(center_repair, 512) - pixels)
        pixels = np.clip((pixels - pixels.mean((0, 1))) * np.clip(
            native.std((0, 1)) / np.maximum(pixels.std((0, 1)), 1), .65, 1.35) + native.mean((0, 1)), 0, 255)
        input_name = name + ('_offset_scale_v2.png' if name in ('rock', 'sandstone') else '_offset.png')
        save(M / 'inputs' / input_name, np.roll(pixels, (256, 256), (0, 1)))
        repair_path = M / 'raw' / (name + '_repair.png')
        if name in ('rock', 'sandstone'):
            repair_path = M / 'raw' / (name + '_repair_scale_v2.png')
        if name in ('rock', 'sandstone'):
            pixels = periodic_component.periodic_residual(pixels)
            method = 'Native-scale crop plus smooth periodic boundary-component removal; no detail-strip averaging'
        elif repair_path.exists():
            pixels = poisson.repair(pixels, read(repair_path, 512), width=80)
            method = 'Local AI half-offset repair with periodic Poisson insertion; central352 square protected'
        elif name in ('plains_sand', 'rock', 'sandstone', 'grey_stone'):
            # Structured relief needs a connected guide, not a quilting cut across ridges.
            method = 'Unrepaired candidate; periodic repair pending'
        else:
            pixels = seams.periodic(pixels)
            method = 'Periodic donor quilting; central384 square protected'
        save(M / 'materials' / (name + '.png'), pixels)
        runtime = seams.reduce(seams.pad(pixels, 'wrap'))
        save(M / 'runtime' / (name + '.png'), runtime)
        save(M / 'reviews' / (name + '_repeat.png'), np.tile(runtime, (3, 3, 1)))
        save(M / 'reviews' / (name + '_offset.png'), np.roll(runtime, (128, 128), (0, 1)))
        sheet = Image.new('RGB', (768, 280), '#202933')
        draw = ImageDraw.Draw(sheet)
        for i, (label, image) in enumerate([
                ('native', Image.open(P / 'references' / (GROUPS[name][0] + '.png')).resize((256, 256))),
                ('candidate x2', Image.fromarray(runtime)),
                ('half offset', Image.open(M / 'reviews' / (name + '_offset.png'))) ]):
            sheet.paste(image, (i * 256, 24))
            draw.text((i * 256 + 5, 5), name + ' ' + label, fill='white')
        sheet.save(M / 'reviews' / (name + '_comparison.png'))
        report = dict(material=name, status='candidate_visual_review_required', method=method,
                      raw_sha256=sha(raw), prompt_sha256=sha(M / 'prompts' / (name + '.txt')),
                      native_sha256=sha(P / 'references' / (GROUPS[name][0] + '.png')),
                      authoring_sha256=sha(M / 'materials' / (name + '.png')),
                      runtime_sha256=sha(M / 'runtime' / (name + '.png')),
                      native_mean_rgb=native.mean((0, 1)).tolist(),
                      runtime_mean_rgb=runtime.mean((0, 1)).tolist(),
                      seams={side: checks.metrics(runtime.astype(float), runtime.astype(float), side)[0]
                             for side in ('E', 'S')})
        if repair_path.exists():
            report['repair_sha256'] = sha(repair_path)
        if name in ('rock', 'sandstone'):
            report['source_framing'] = 'Resize raw768, retain top-left512; restores native feature scale'
        if center_repair.exists():
            report['center_repair_sha256'] = sha(center_repair)
            report['center_repair_region'] = [165, 160, 365, 300]
        (M / 'reviews' / (name + '.json')).write_text(json.dumps(report, indent=2) + '\n')
        print(name, method, {s: v['passed'] for s, v in report['seams'].items()}, flush=True)


if __name__ == '__main__':
    main()
