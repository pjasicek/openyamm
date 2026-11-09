"""Extract reviewed AI cells and apply the accepted goblin matte/decontamination algorithm."""
from pathlib import Path
import importlib.util
import json
import shutil

from PIL import Image

ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('goblin_matte', ROOT.parent / 'direct_ai_attack/clean_edges.py')
matte = importlib.util.module_from_spec(spec)
spec.loader.exec_module(matte)


def build():
    out = ROOT / 'cleaned_source'
    out.mkdir(exist_ok=True)
    groups = json.loads((ROOT / 'groups.json').read_text())
    records = []
    for action, names in groups.items():
        if action == 'attack':
            source = ROOT.parent / 'direct_ai_attack'
            shutil.copy2(source / 'attack_restored_v1.png', ROOT / 'raw/attack_accepted_v1.png')
            shutil.copy2(source / 'prompt_v1.txt', ROOT / 'prompts/attack_accepted_v1.txt')
            shutil.copy2(source / 'original_attack_3x2_magenta.png', ROOT / 'references/attack.png')
            for name in names:
                original = source / 'edge_cleanup/frames_rgba' / (name + '_ai.png')
                shutil.copy2(original, out / (name + '.png'))
                records.append({'name': name, 'action': action, 'provenance': str(original.relative_to(ROOT.parent)),
                                'note': 'Accepted attack cleanup preserved byte-for-byte before registration.'})
            continue
        raw = ROOT / 'raw' / (action + '_v1.png')
        image = Image.open(raw).convert('RGB')
        xs = [round(i * image.width / 3) for i in range(4)]
        # Death generator changed the vertical spacing; measured gap safely contains this seam.
        ys = [0, 630 if action == 'death_corpse' else round(image.height / 2), image.height]
        for i, name in enumerate(names):
            box = (xs[i % 3], ys[i // 3], xs[i % 3 + 1], ys[i // 3 + 1])
            if action == 'standing':
                box = (0, 0, image.width, image.height)
            if name == 'gobwad0':
                raw = ROOT / 'raw/walk_d_v2.png'
                rgb = Image.open(raw).convert('RGB')
                box = (0, 0, rgb.width, rgb.height)
            else:
                raw = ROOT / 'raw' / (action + '_v1.png')
                rgb = image.crop(box)
            cleaned, stats = matte.extract(rgb)
            cleaned.save(out / (name + '.png'))
            bounds = cleaned.getchannel('A').getbbox()
            assert bounds and bounds[0] > 0 and bounds[1] > 0
            assert bounds[2] < cleaned.width and bounds[3] < cleaned.height
            records.append({'name': name, 'action': action, 'raw': str(raw.relative_to(ROOT)),
                            'extraction_box': box, 'cleaned_size': cleaned.size, 'alpha_bounds': bounds,
                            'cleanup': stats})
    (ROOT / 'extraction_manifest.json').write_text(json.dumps(records, indent=2) + '\n')
    print(f'Extracted {len(records)} front frames, no clipped source silhouettes.')


if __name__ == '__main__':
    build()
