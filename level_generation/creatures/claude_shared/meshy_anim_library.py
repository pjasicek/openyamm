"""Store paid Meshy animation-library results in anim_library/meshy/ so no action is bought twice.

Usage (repo root or anywhere; plain python3, no Blender):
  meshy_anim_library.py check ID [ID ...]            which action IDs are already stored (exit 1 if any missing)
  meshy_anim_library.py ingest REQUEST.json RESULT.glb [--project NAME] [--names]
      split a result GLB (one clip per action, in action_ids order) into anim_library/meshy/<id>_<slug>/animation.glb
      --names: match clips to actions by catalogue name instead of order (web-app exports, any clip order)
  meshy_anim_library.py list                          stored actions

Each action folder holds animation.glb (that clip only, compacted), info.json (action, clip, duration, rig task,
every source it was seen in). anim_library/meshy/index.json lists all stored actions. An action already stored keeps
its first animation.glb; later sources are only added to its info.json.
"""
import json, os, re, struct, sys

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))
LIB = os.path.join(REPO, 'anim_library', 'meshy')
CATALOGUE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'catalogues', 'meshy_library.json')


def norm(name):
    name = re.sub(r'^Armature\|', '', name)
    name = re.sub(r'\|baselayer$', '', name)
    return re.sub(r'[^a-z0-9]', '', name.lower())


def slug(name):
    return re.sub(r'[^a-z0-9]+', '_', name.lower()).strip('_')


def catalogue():
    return {c['action_id']: c for c in json.load(open(CATALOGUE))}


def read_glb(path):
    data = open(path, 'rb').read()
    length = struct.unpack('<I', data[12:16])[0]
    gltf = json.loads(data[20:20 + length])
    rest = data[20 + length:]
    blob = b''
    if len(rest) >= 8:
        blob_len = struct.unpack('<I', rest[:4])[0]
        blob = rest[8:8 + blob_len]
    return gltf, blob


def write_glb(path, gltf, blob):
    js = json.dumps(gltf, separators=(',', ':')).encode()
    js += b' ' * (-len(js) % 4)
    blob += b'\0' * (-len(blob) % 4)
    total = 12 + 8 + len(js) + (8 + len(blob) if blob else 0)
    out = struct.pack('<III', 0x46546C67, 2, total) + struct.pack('<II', len(js), 0x4E4F534A) + js
    if blob:
        out += struct.pack('<II', len(blob), 0x004E4942) + blob
    open(path, 'wb').write(out)


def single_clip(gltf, blob, index):
    """A copy of the GLB with only animation `index`; unused accessors, buffer views and bytes are dropped."""
    g = json.loads(json.dumps(gltf))
    g['animations'] = [g['animations'][index]]
    used = set()

    def walk(obj, key=None):
        if isinstance(obj, dict):
            for k, v in obj.items():
                if k in ('input', 'output', 'indices', 'inverseBindMatrices') and isinstance(v, int):
                    used.add(v)
                elif k == 'attributes' or k == 'targets':
                    walk_refs(v)
                else:
                    walk(v, k)
        elif isinstance(obj, list):
            for v in obj:
                walk(v, key)

    def walk_refs(v):
        if isinstance(v, dict):
            used.update(x for x in v.values() if isinstance(x, int))
        elif isinstance(v, list):
            for t in v:
                walk_refs(t)

    for k in ('meshes', 'skins', 'animations'):
        walk(g.get(k, []))
    acc_map, views_used = {}, set()
    new_acc = []
    for i, a in enumerate(g.get('accessors', [])):
        if i in used:
            acc_map[i] = len(new_acc); new_acc.append(a)
            if 'bufferView' in a: views_used.add(a['bufferView'])
            for sp in ('indices', 'values'):
                if 'sparse' in a: views_used.add(a['sparse'][sp]['bufferView'])
    for im in g.get('images', []):
        if 'bufferView' in im: views_used.add(im['bufferView'])
    view_map, new_views, new_blob = {}, [], b''
    for i, v in enumerate(g.get('bufferViews', [])):
        if i not in views_used: continue
        start = v.get('byteOffset', 0); chunk = blob[start:start + v['byteLength']]
        new_blob += b'\0' * (-len(new_blob) % 4)
        nv = dict(v); nv['byteOffset'] = len(new_blob); nv['buffer'] = 0
        view_map[i] = len(new_views); new_views.append(nv); new_blob += chunk
    for a in new_acc:
        if 'bufferView' in a: a['bufferView'] = view_map[a['bufferView']]
        if 'sparse' in a:
            for sp in ('indices', 'values'): a['sparse'][sp]['bufferView'] = view_map[a['sparse'][sp]['bufferView']]
    for im in g.get('images', []):
        if 'bufferView' in im: im['bufferView'] = view_map[im['bufferView']]

    def remap(obj):
        if isinstance(obj, dict):
            for k, v in list(obj.items()):
                if k in ('input', 'output', 'indices', 'inverseBindMatrices') and isinstance(v, int):
                    obj[k] = acc_map[v]
                elif k == 'attributes':
                    obj[k] = {n: acc_map[x] for n, x in v.items()}
                elif k == 'targets':
                    obj[k] = [{n: acc_map[x] for n, x in t.items()} for t in v]
                else:
                    remap(v)
        elif isinstance(obj, list):
            for v in obj: remap(v)

    for k in ('meshes', 'skins', 'animations'):
        remap(g.get(k, []))
    g['accessors'], g['bufferViews'] = new_acc, new_views
    g['buffers'] = [{'byteLength': len(new_blob)}]
    return g, new_blob


def duration(gltf, anim):
    return max(gltf['accessors'][s['input']]['max'][0] for s in anim['samplers'])


def load_index():
    p = os.path.join(LIB, 'index.json')
    return json.load(open(p)) if os.path.exists(p) else {}


def save_index(index):
    os.makedirs(LIB, exist_ok=True)
    json.dump(dict(sorted(index.items(), key=lambda kv: int(kv[0]))), open(os.path.join(LIB, 'index.json'), 'w'),
              indent=1)


def ingest(request_path, result_path, project, by_name):
    cat = catalogue()
    req = json.load(open(request_path))
    ids = req.get('action_ids') or ([req['action_id']] if 'action_id' in req else [])
    gltf, blob = read_glb(result_path)
    anims = gltf.get('animations', [])
    pairs = []
    if by_name:
        by = {}
        for aid, c in cat.items():
            by.setdefault(norm(c['name']), []).append(aid)     # several actions can share a name (Spear Walk)
        for i, a in enumerate(anims):
            cands = [x for x in by.get(norm(a['name']), []) if not ids or x in ids]
            if cands:
                pairs.append((cands[0], i))
            else:
                print(f'  skip clip {a["name"]!r}: no catalogue action' + (' in request' if ids else ''))
    else:
        if len(anims) != len(ids):
            sys.exit(f'{result_path}: {len(anims)} clips for {len(ids)} actions; use --names')
        pairs = list(zip(ids, range(len(anims))))
    index = load_index()
    for aid, i in pairs:
        c = cat.get(aid, {'name': anims[i]['name']})
        if norm(c['name']) != norm(anims[i]['name']):
            print(f'  note: action {aid} {c["name"]!r} has clip name {anims[i]["name"]!r}')
        folder = f'{aid}_{slug(c["name"])}'
        d = os.path.join(LIB, folder)
        source = {'project': project, 'request': os.path.relpath(os.path.abspath(request_path), REPO),
                  'result': os.path.relpath(os.path.abspath(result_path), REPO), 'clip': anims[i]['name'],
                  'rig_task_id': req.get('rig_task_id'), 'fps_post_process': req.get('post_process', {}).get('fps')}
        info_path = os.path.join(d, 'info.json')
        if os.path.exists(info_path):
            info = json.load(open(info_path))
            if not any(s['result'] == source['result'] and s['clip'] == source['clip'] for s in info['sources']):
                info['sources'].append(source)
            print(f'  {aid:4d} {c["name"]}: already stored, source added')
        else:
            os.makedirs(d, exist_ok=True)
            g, b = single_clip(gltf, blob, i)
            write_glb(os.path.join(d, 'animation.glb'), g, b)
            info = {'action_id': aid, 'name': c['name'], 'category': c.get('category'),
                    'sub_category': c.get('sub_category'), 'roles': c.get('roles', []),
                    'clip': anims[i]['name'], 'duration_s': round(duration(gltf, anims[i]), 4),
                    'joints': len(gltf['skins'][0]['joints']) if gltf.get('skins') else 0, 'sources': [source]}
            print(f'  {aid:4d} {c["name"]}: stored ({info["duration_s"]} s)')
        json.dump(info, open(info_path, 'w'), indent=1)
        index[str(aid)] = {'folder': folder, 'name': info['name'], 'duration_s': info['duration_s'],
                           'roles': info['roles'], 'sources': len(info['sources'])}
    save_index(index)


def main():
    args = sys.argv[1:]
    if not args:
        sys.exit(__doc__)
    cmd = args[0]
    if cmd == 'check':
        index, cat = load_index(), catalogue()
        missing = []
        for a in args[1:]:
            aid = int(a); name = cat.get(aid, {}).get('name', '?')
            if str(aid) in index:
                print(f'HAVE {aid:4d} {name} -> anim_library/meshy/{index[str(aid)]["folder"]}')
            else:
                print(f'BUY  {aid:4d} {name}'); missing.append(aid)
        sys.exit(1 if missing else 0)
    if cmd == 'list':
        for aid, e in load_index().items():
            print(f'{int(aid):4d} {e["name"]:40s} {e["duration_s"]:6.2f}s {",".join(e["roles"])}  {e["folder"]}')
        return
    if cmd == 'ingest':
        project = args[args.index('--project') + 1] if '--project' in args else ''
        ingest(args[1], args[2], project, '--names' in args)
        return
    sys.exit(__doc__)


if __name__ == '__main__':
    main()
