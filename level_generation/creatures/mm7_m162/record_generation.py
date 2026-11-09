"""Copy a built-in image-generation checkpoint and record exact inputs/output hashes."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
from PIL import Image

ROOT = Path(__file__).resolve().parent

def record(batch, generated):
    assert batch in json.loads((ROOT / 'batches.json').read_text())
    (ROOT / 'prompts/submitted').mkdir(exist_ok=True)
    shutil.copy2(generated, ROOT / ('raw/' + batch + '.png'))
    shutil.copy2(ROOT / ('prompts/' + batch + '.txt'), ROOT / ('prompts/submitted/' + batch + '.txt'))
    def asset(relative):
        return {'path': relative, 'sha256': hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()}
    path = ROOT / 'generation.json'
    data = json.loads(path.read_text()) if path.exists() else {'tool': 'image_gen.imagegen (built-in)', 'batches': {}}
    references = [asset('references/' + batch + '.png')]
    if batch != 'standing':
        references.append(asset('raw/standing.png'))
    data['batches'][batch] = {'raw': asset('raw/' + batch + '.png'), 'original_output': str(generated),
                            'dimensions': Image.open(generated).size, 'references': references,
                            'prompt': asset('prompts/submitted/' + batch + '.txt')}
    path.write_text(json.dumps(data, indent=2) + '\n')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('batch')
    parser.add_argument('generated', type=Path)
    args = parser.parse_args()
    record(args.batch, args.generated)
