#!/usr/bin/env python3
"""Replace named images of a GLB with PNG files (preview only). Usage: patch_image.py <in.glb> <out.glb> name=file.png ..."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
from build_actor_lods import read_glb, write_glb
doc, binary = read_glb(Path(sys.argv[1])); binary = bytearray(binary)
for arg in sys.argv[3:]:
    name, f = arg.split('=', 1); data = Path(f).read_bytes()
    im = next(i for i in doc['images'] if i.get('name') == name)
    binary.extend(b'\0' * (-len(binary) % 4))
    doc['bufferViews'].append({'buffer': 0, 'byteOffset': len(binary), 'byteLength': len(data)}); binary.extend(data)
    im['bufferView'] = len(doc['bufferViews']) - 1
write_glb(Path(sys.argv[2]), doc, bytes(binary)); print('PATCHED', sys.argv[2])
