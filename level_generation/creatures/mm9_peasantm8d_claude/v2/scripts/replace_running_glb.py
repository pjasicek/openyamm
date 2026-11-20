"""Copy only Running channels into an existing GLB, retaining every original byte of payload.
Arguments: animation GLB, baseline GLB, output GLB. Assertions verify untouched content.
"""
import copy
import hashlib
import json
from pathlib import Path
import struct
import sys


def read(path):
    raw = Path(path).read_bytes()
    size = struct.unpack_from('<I', raw, 12)[0]
    return json.loads(raw[20:20+size]), raw[28+size:]


def payload(doc, binary, index):
    acc = doc['accessors'][index]
    view = doc['bufferViews'][acc['bufferView']]
    assert 'sparse' not in acc and 'byteStride' not in view
    offset = view.get('byteOffset', 0) + acc.get('byteOffset', 0)
    width = {'SCALAR': 1, 'VEC3': 3, 'VEC4': 4}[acc['type']]
    assert acc['componentType'] == 5126
    return binary[offset:offset+acc['count']*width*4]


def fingerprints(doc, binary):
    out = {}
    for action in doc['animations']:
        h = hashlib.sha256()
        for channel in action['channels']:
            sampler = action['samplers'][channel['sampler']]
            target = channel['target']
            h.update(json.dumps([doc['nodes'][target['node']]['name'], target['path'],
                                 sampler.get('interpolation', 'LINEAR')]).encode())
            for kind in ('input', 'output'):
                h.update(payload(doc, binary, sampler[kind]))
        out[action['name']] = h.hexdigest()
    return out


def replace(source, baseline, output):
    src, sb = read(source)
    doc, binary = read(baseline)
    old = copy.deepcopy(doc)
    before = fingerprints(doc, binary)
    node_ids = {n['name']: i for i, n in enumerate(doc['nodes'])}
    action = copy.deepcopy(next(a for a in src['animations'] if a['name'] == 'Running'))
    # Animation transforms are local; matching encoded rest transforms is mandatory.
    for channel in action['channels']:
        sn = src['nodes'][channel['target']['node']]
        dn = doc['nodes'][node_ids[sn['name']]]
        for key, default in [('translation',[0,0,0]),('rotation',[0,0,0,1]),('scale',[1,1,1])]:
            assert max(abs(a-b) for a,b in zip(sn.get(key,default),dn.get(key,default))) < 1e-5, (sn['name'],key)
        channel['target']['node'] = node_ids[sn['name']]
    binary = bytearray(binary)
    remap = {}
    for sampler in action['samplers']:
        for kind in ('input','output'):
            index = sampler[kind]
            if index not in remap:
                data = payload(src, sb, index)
                binary += b'\0' * (-len(binary)%4)
                view = len(doc['bufferViews'])
                doc['bufferViews'].append({'buffer':0,'byteOffset':len(binary),'byteLength':len(data)})
                binary += data
                acc = copy.deepcopy(src['accessors'][index])
                acc['bufferView'] = view; acc.pop('byteOffset',None)
                remap[index] = len(doc['accessors']); doc['accessors'].append(acc)
            sampler[kind] = remap[index]
    slot = next(i for i,a in enumerate(doc['animations']) if a['name']=='Running')
    doc['animations'][slot] = action
    after = fingerprints(doc,binary)
    assert before.keys()==after.keys()
    assert all(before[n]==after[n] for n in before if n!='Running')
    assert before['Running']!=after['Running']
    for key in old:
        if key not in ('animations','accessors','bufferViews','buffers'):
            assert old[key]==doc[key],key
    assert doc['accessors'][:len(old['accessors'])]==old['accessors']
    assert doc['bufferViews'][:len(old['bufferViews'])]==old['bufferViews']
    assert bytes(binary[:len(read(baseline)[1])])==read(baseline)[1]
    binary += b'\0' * (-len(binary)%4)
    doc['buffers'][0]['byteLength']=len(binary)
    enc=json.dumps(doc,separators=(',',':')).encode(); enc+=b' '*(-len(enc)%4)
    raw=struct.pack('<III',0x46546c67,2,28+len(enc)+len(binary))+struct.pack('<II',len(enc),0x4e4f534a)+enc
    raw+=struct.pack('<II',len(binary),0x004e4942)+binary
    Path(output).write_bytes(raw)
    assert fingerprints(*read(output))==after
    return {'output':str(output),'sha256':hashlib.sha256(raw).hexdigest(),
            'before':before,'after':after,'original_payload_bytes_preserved':len(read(baseline)[1])}

if __name__=='__main__':
    print(json.dumps(replace(*sys.argv[1:]),indent=2))
