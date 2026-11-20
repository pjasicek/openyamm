"""Preserve imagegen output and normalize an opaque coverage mask without interpreting source colours."""
import hashlib
import json
from pathlib import Path
import shutil
import sys
from PIL import Image

P = Path(__file__).resolve().parent
name, source = sys.argv[1], Path(sys.argv[2])
raw = P / 'raw/v1' / (name + '.png')
assert not raw.exists(), raw
shutil.copy2(source, raw)
with Image.open(raw) as image:
    image.convert('L').resize((512,512), Image.Resampling.LANCZOS).save(P/'masks/v1'/(name+'.png'))
record = {'tile': name, 'tool': 'built-in imagegen', 'backend_model': 'not exposed',
          'raw': str(raw.relative_to(P)), 'raw_sha256': hashlib.sha256(raw.read_bytes()).hexdigest(),
          'tool_output_path': str(source), 'prompt': 'prompts/v1/'+name+'.txt',
          'reference': '../mm6_new_sorpigal/source_rgb/'+name+'.png',
          'reference_sha256': hashlib.sha256((P.parent/'mm6_new_sorpigal/source_rgb'/(name+'.png')).read_bytes()).hexdigest(),
          'normalization': 'grayscale conversion and Lanczos reduction to 512; no source-colour segmentation'}
(P/'raw/v1'/(name+'.json')).write_text(json.dumps(record,indent=2)+'\n')
print('Preserved and normalized',name)
