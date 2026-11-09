#!/usr/bin/env python3
"""Play GLB clips faster by dividing their key times (user, 2026-10-14: Minotaur Attack and Death 2x faster).
Every sampler input of a named animation is scaled by 1/speed (accessor min/max too); an input shared with another
animation is refused. Prints each clip's new length; event times in actors.yml must be divided by the same speed.
Usage: retime_glb.py <in.glb> <out.glb> Attack:2 Death:2"""
import struct, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
from build_actor_lods import read_glb, write_glb, accessor_bytes  # noqa: E402

src, out, specs = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3:]
doc, binary = read_glb(src); binary = bytearray(binary)
users = {}
for a in doc['animations']:
    for s in a['samplers']:
        users.setdefault(s['input'], set()).add(a['name'])
for spec in specs:
    name, speed = spec.split(':'); speed = float(speed)
    anim = next(a for a in doc['animations'] if a['name'] == name)
    inputs = sorted({s['input'] for s in anim['samplers']})
    for i in inputs:
        assert users[i] == {name}, f'{name}: input {i} shared with {users[i]}'
        acc = doc['accessors'][i]; view = doc['bufferViews'][acc['bufferView']]
        start = view.get('byteOffset', 0) + acc.get('byteOffset', 0); n = acc['count']
        assert acc['componentType'] == 5126 and acc['type'] == 'SCALAR' and view.get('byteStride', 4) == 4
        times = [t / speed for t in struct.unpack_from(f'<{n}f', binary, start)]
        struct.pack_into(f'<{n}f', binary, start, *times)
        acc['min'] = [min(times)]; acc['max'] = [max(times)]
    end = max(doc['accessors'][i]['max'][0] for i in inputs)
    print('RETIMED', name, 'x', speed, '->', round(end, 6), 's')
write_glb(out, doc, bytes(binary))
