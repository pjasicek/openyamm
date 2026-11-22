import yaml, sys
L4 = sys.argv[1]
o = yaml.safe_load(open(L4 + '/objects.yml'))
def walk(node, path, out):
    if isinstance(node, dict):
        t = node.get('texture')
        if isinstance(t, str):
            out.append(('/'.join(path), t))
        for k, v in node.items():
            walk(v, path + [str(k)], out)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            walk(v, path + [str(i)], out)
for sect, items in o.items():
    if not isinstance(items, list): continue
    for it in items:
        out = []
        walk(it, [], out)
        if out:
            ident = it.get('id', '?') if isinstance(it, dict) else '?'
            room = it.get('room', '') if isinstance(it, dict) else ''
            print(sect, ident, room)
            for p, t in out:
                print(f'    {t:12s} {p}')
