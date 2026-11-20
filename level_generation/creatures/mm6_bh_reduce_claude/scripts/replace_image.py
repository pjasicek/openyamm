#!/usr/bin/env python3
"""Replace named images of a GLB (everything else byte-for-byte): replace_image.py <in.glb> <out.glb> name=file.png ..."""
import io, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
from build_actor_lods import read_glb, write_glb  # noqa: E402
doc, binary = read_glb(Path(sys.argv[1])); repl = dict(a.split('=', 1) for a in sys.argv[3:])
new = {}
for im in doc['images']:
    if im.get('name') in repl:
        new[im['bufferView']] = Path(repl[im['name']]).read_bytes()
assert len(new) == len(repl), (list(repl), [im.get('name') for im in doc['images']])
nb = bytearray()
for k, bv in enumerate(doc['bufferViews']):
    data = new.get(k, bytes(binary[bv.get('byteOffset', 0):bv.get('byteOffset', 0) + bv['byteLength']]))
    nb += b'\0' * (-len(nb) % 4); bv['byteOffset'] = len(nb); bv['byteLength'] = len(data); nb += data
write_glb(Path(sys.argv[2]), doc, bytes(nb)); print('REPLACED', list(repl))
