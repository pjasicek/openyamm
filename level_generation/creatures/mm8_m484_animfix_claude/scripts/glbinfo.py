import json, struct, sys
def load(p):
    b = open(p, 'rb').read()
    n = struct.unpack_from('<I', b, 12)[0]
    return json.loads(b[20:20 + n])
for p in sys.argv[1:]:
    g = load(p)
    print(p)
    acc = g['accessors']
    for a in g.get('animations', []):
        t = max(acc[s['input']]['max'][0] for s in a['samplers'])
        print('  anim %-12s %.3f s  channels %d' % (a['name'], t, len(a['channels'])))
    names = [n.get('name', '') for n in g['nodes']]
    print('  nodes:', ' '.join(names))
