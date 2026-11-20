"""Build native-order contacts from selected poses, recording incomplete sequences."""
import json
from PIL import Image, ImageDraw
from process import ROOT, queue, save


def run():
    source = json.loads((ROOT / 'sources.json').read_text())
    registration = json.loads((ROOT / 'registration.json').read_text())
    evidence = {}
    for action in ['a', 'w', 'n', 'f', 'd', 's']:
        for view in range(5):
            names = sorted(n for n in source['sources'] if n[4] == action and n[-1] == str(view))
            if action == 'd':
                names += [f'm460xa{view}']
            missing = sorted(set(names) - set(registration))
            key = f'{action}_v{view}'
            evidence[key] = {'frames': names, 'missing': missing, 'visually_reviewed': False}
            if missing:
                continue
            sheet = Image.new('RGB', (192 * len(names), 832), (35, 35, 35))
            draw = ImageDraw.Draw(sheet)
            for col, name in enumerate(names):
                native = Image.new('RGBA', (576, 576))
                native.paste(queue.native(ROOT, name).resize((512, 512), Image.Resampling.NEAREST), (32, 32))
                images = [native] + [Image.open(ROOT / f'previews/{name}_{p}.png') for p in [461, 462, 463]]
                for row, im in enumerate(images):
                    thumb = im.convert('RGBa').resize((192, 192), Image.Resampling.LANCZOS).convert('RGBA')
                    bg = Image.new('RGBA', thumb.size, (35, 35, 35, 255))
                    bg.alpha_composite(thumb)
                    sheet.paste(bg.convert('RGB'), (col * 192, row * 208 + 16))
                    draw.text((col * 192 + 3, row * 208 + 2), name + [' native', ' 461', ' 462', ' 463'][row], fill='white')
            path = ROOT / f'review/sequence_{key}.png'
            sheet.save(path)
            evidence[key]['contact'] = {'path': str(path.relative_to(ROOT)), 'sha256': queue.sha(path)}
    save(ROOT / 'review/sequence_coverage.json', evidence)
    print(sum(not e['missing'] for e in evidence.values()), '/', len(evidence), 'complete sequences')


if __name__ == '__main__':
    run()
