"""Keep presentation visibility explicit in every exported clip, including constant states.

Blender's NLA exporter drops constant object scales, samples CONSTANT curves as LINEAR,
and caches this shared KEY-slot death morph at one frame. Write the actual evaluated
source samples and visibility channels explicitly; skeletal data stay as exported.
"""
import json
import struct
from pathlib import Path


def normalize(path, death_weights):
    raw = Path(path).read_bytes()
    size = struct.unpack_from('<I', raw, 12)[0]
    document = json.loads(raw[20:20+size])
    binary = bytearray(raw[28+size:])
    nodes = {n['name']: i for i, n in enumerate(document['nodes'])}
    ends = {'Attack': 36, 'Walking': 50, 'Running': 32, 'Standing': 6, 'Walk_Native': 54,
            'Hit': 36, 'Fidget': 30, 'Death': 60, 'Ash_Remains': 6}

    def accessor(values, kind):
        binary.extend(b'\x00' * (-len(binary) % 4))
        offset = len(binary)
        binary.extend(struct.pack('<' + 'f'*len(values), *values))
        view = len(document['bufferViews'])
        document['bufferViews'].append({'buffer': 0, 'byteOffset': offset, 'byteLength': len(values)*4})
        result = {'bufferView': view, 'componentType': 5126, 'count': len(values)//(3 if kind == 'VEC3' else 1),
                  'type': kind}
        if kind == 'SCALAR':
            result.update(min=[min(values)], max=[max(values)])
        document['accessors'].append(result)
        return len(document['accessors'])-1

    for animation in document['animations']:
        clip = animation['name']
        if clip == 'Death':
            assert len(death_weights) == 61 and all(len(w) == 9 for w in death_weights)
            animation['channels'] = [c for c in animation['channels'] if c['target']['path'] != 'weights']
            sampler = len(animation['samplers'])
            animation['samplers'].append({'input': accessor([f/48 for f in range(61)], 'SCALAR'),
                                         'output': accessor([v for row in death_weights for v in row], 'SCALAR'),
                                         'interpolation': 'LINEAR'})
            animation['channels'].append({'sampler': sampler, 'target': {'node': nodes['Demon_Death_Plume'], 'path': 'weights'}})
        for name in ('Demon_Body_Visibility', 'Demon_Ash_Remains'):
            node = nodes[name]
            animation['channels'] = [c for c in animation['channels']
                                     if not (c['target']['node'] == node and c['target']['path'] == 'scale')]
            times = [0, ends[clip]/48]
            if name == 'Demon_Body_Visibility':
                values = [0, 0] if clip == 'Ash_Remains' else [1, 1]
                if clip == 'Death':
                    times, values = [0, 18/48, ends[clip]/48], [1, 0, 0]
            else:
                values = [int(clip == 'Ash_Remains')]*2
            sampler = len(animation['samplers'])
            animation['samplers'].append({'input': accessor(times, 'SCALAR'),
                                         'output': accessor([v for v in values for _ in range(3)], 'VEC3'),
                                         'interpolation': 'STEP'})
            animation['channels'].append({'sampler': sampler, 'target': {'node': node, 'path': 'scale'}})
    document['buffers'][0]['byteLength'] = len(binary)
    encoded = json.dumps(document, separators=(',', ':')).encode()
    encoded += b' ' * (-len(encoded) % 4)
    binary.extend(b'\x00' * (-len(binary) % 4))
    length = 12+8+len(encoded)+8+len(binary)
    Path(path).write_bytes(struct.pack('<III', 0x46546C67, 2, length) +
                           struct.pack('<II', len(encoded), 0x4E4F534A)+encoded +
                           struct.pack('<II', len(binary), 0x004E4942)+binary)

