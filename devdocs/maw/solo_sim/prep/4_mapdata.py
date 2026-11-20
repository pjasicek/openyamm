"""Step 4. inv/mapdata.json: every map's chests as the scene file places them (type, flags, raw item records, grid
size; the harness materialises them with the game's ChestRuntime) and the experience its map script awards
(AddValue(Experience, n)), per map."""
import json, re, struct, collections, os
from _common import REPO, INV

os.chdir(REPO)
maps = json.load(open(INV + '/maps.json'))
chests = {}; qx = {}; stats = collections.Counter()
for f, m in maps.items():
    p = f'assets_dev/worlds/{m["world"]}/maps/{f.rsplit(".", 1)[0]}.scene.yml'
    try:
        txt = open(p, errors='replace').read()
    except FileNotFoundError:
        continue
    i = txt.find('\n  chests:'); cl = []
    if i >= 0:
        seg = txt[i:]
        j = seg.find('\n  variables:'); seg = seg[:j] if j > 0 else seg
        for block in seg.split('    - chest_index:')[1:]:
            t = int(re.search(r'chest_type_id: (\d+)', block).group(1))
            fl = int(re.search(r'flags: (\d+)', block).group(1))
            h = re.search(r'raw_items_hex: "([0-9A-F]*)"', block).group(1)
            mat = re.search(r'inventory_matrix: \[([^\]]*)\]', block)
            n = len(mat.group(1).split(',')) if mat else 140
            raw = bytes.fromhex(h); ids = [struct.unpack('<i', raw[k:k + 4])[0] for k in range(0, len(raw), 36)]
            if any(x != 0 for x in ids):
                cl.append(dict(type=t, flags=fl, hex=h, matrix=n))
                for x in ids:
                    if x < 0: stats['rand%d' % (-x)] += 1
                    elif x > 0: stats['placed'] += 1
    chests[f] = cl
    lua = f'assets_dev/worlds/{m["world"]}/events/maps/{f.rsplit(".", 1)[0]}.lua'
    try:
        q = [int(v) for v in re.findall(r'AddValue\(Experience, *(\d+)', open(lua, errors='replace').read())]
    except FileNotFoundError:
        q = []
    qx[f] = [len(q), sum(q)]
json.dump(dict(chests=chests, quests=qx), open(INV + '/mapdata.json', 'w'))
print('maps with chests', sum(1 for v in chests.values() if v), 'chests', sum(len(v) for v in chests.values()), dict(stats))
