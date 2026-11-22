import yaml, sys, collections
L4 = sys.argv[1]
rooms = yaml.safe_load(open(L4 + '/rooms.yml'))
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
for r in rooms['rooms']:
    out = []
    walk(r, [], out)
    c = collections.Counter()
    for p, t in out:
        role = '/'.join(x for x in p.split('/') if not x.isdigit())
        c[(t, role.replace('/surface','').replace('surface',''))] += 1
    print(r['id'], r.get('theme', '(default)'))
    for (t, role), n in sorted(c.items()):
        print(f'    {t:12s} {role} x{n}')
