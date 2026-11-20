"""Record already selected built-in generations and immutable exact prompt checkpoints."""
import json
import hashlib
import shutil
from PIL import Image
from prepare import ROOT

def run():
    outputs=json.loads((ROOT/'selected_outputs.json').read_text());records={}
    (ROOT/'prompts/submitted').mkdir(exist_ok=True)
    def asset(path):
        return {'path':str(path.relative_to(ROOT)),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
    for batch,original in outputs.items():
        submitted=ROOT/f'prompts/submitted/{batch}.txt'
        if not submitted.exists():shutil.copy2(ROOT/f'prompts/{batch}.txt',submitted)
        refs=[ROOT/f'references/{batch}.png',ROOT/'references/accepted_front.png']
        if batch!='standing_sides':refs.append(ROOT/'raw/standing_sides.png')
        records[batch]={'original_output':original,'raw':asset(ROOT/f'raw/{batch}.png'),
            'dimensions':Image.open(ROOT/f'raw/{batch}.png').size,'prompt':asset(submitted),
            'references':[asset(p) for p in refs]}
    (ROOT/'generation.json').write_text(json.dumps({'tool':'image_gen.imagegen (built-in)',
        'batches':records,'reused_front_provenance':'../direct_front_final/README.md; sources.json reused hashes'},indent=2)+'\n')

if __name__=='__main__':run()
