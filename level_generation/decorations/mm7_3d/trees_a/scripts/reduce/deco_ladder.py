"""Texture-aware reduction of the opaque faces of static decorations (alpha cards and water untouched), with the
two-way surface distance in % of the model height (pymeshlab Hausdorff, both directions, opaque surfaces only).
Pass: max <= 1.5 % and mean <= 0.15 % of the height (the creature limits per metre). Usage (venv with pymeshlab):
deco_ladder.py name [name ...] -> work/<name>_r<NN>.npz, work/ladder_<name>.json, printed table."""
import json, os, struct, sys, zlib, numpy as np, pymeshlab as ml
# MM7 trees_a copy of ../../../mm6_reduce_pilot/scripts/deco_ladder.py
W = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'work', 'reduce')
RATIOS = [float(r) for r in os.environ.get('DECO_RATIOS', '0.7,0.55,0.45,0.35,0.25').split(',')]   # MM7 trees_a: DECO_RATIOS overrides


def write_obj(path, verts, faces, uv):
    """OBJ with one textured material: MeshLab's texture-aware collapse needs a texture per face."""
    folder = os.path.dirname(path)
    chunk = lambda t, b: struct.pack('>I', len(b)) + t + b + struct.pack('>I', zlib.crc32(t + b))
    open(os.path.join(folder, 'tex.png'), 'wb').write(b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', 1, 1, 8, 2, 0, 0, 0))
        + chunk(b'IDAT', zlib.compress(b'\x00\xff\xff\xff')) + chunk(b'IEND', b''))
    open(os.path.join(folder, 'in.mtl'), 'w').write('newmtl m\nmap_Kd tex.png\n')
    with open(path, 'w') as f:
        f.write('mtllib in.mtl\n')
        f.writelines(f'v {x} {y} {z}\n' for x, y, z in verts)
        f.writelines(f'vt {u} {v}\n' for u, v in uv)
        f.write('usemtl m\n')
        f.writelines(f'f {a+1}/{3*i+1} {b+1}/{3*i+2} {c+1}/{3*i+3}\n' for i, (a, b, c) in enumerate(faces))


def read_obj(path):
    vs, vts, fs, fts = [], [], [], []
    for line in open(path):
        p = line.split()
        if not p:
            continue
        if p[0] == 'v':
            vs.append([float(x) for x in p[1:4]])
        elif p[0] == 'vt':
            vts.append([float(x) for x in p[1:3]])
        elif p[0] == 'f':
            idx = [q.split('/') for q in p[1:4]]
            fs.append([int(q[0]) - 1 for q in idx]); fts.append([int(q[1]) - 1 for q in idx])
    return np.array(vs), np.array(fs, np.int32), np.array(vts)[np.array(fts).reshape(-1)]


for name in sys.argv[1:]:
    d = np.load(os.path.join(W, f'{name}.npz'))
    V, F, U, O = d['verts'], d['faces'], d['wuv'].reshape(-1, 3, 2), d['opaque']
    H = float(np.ptp(V[:, 2]))
    of = np.where(O)[0]; used = np.unique(F[of]); remap = -np.ones(len(V), int); remap[used] = np.arange(len(used))
    ov, ofc, ouv = V[used], remap[F[of]], U[of].reshape(-1, 2)
    rows = {'height': H, 'faces': int(len(F)), 'opaque': int(len(of)), 'steps': {}}
    if len(of) < 50:   # all cards/water: nothing to collapse
        rows['pick'] = None; json.dump(rows, open(os.path.join(W, f'ladder_{name}.json'), 'w'), indent=1)
        print(f'{name:16s} total {len(F):6d} opaque {len(of):6d} -> skipped (alpha only)'); continue
    for r in RATIOS:
        tmp = os.path.join(W, 'obj'); os.makedirs(tmp, exist_ok=True)
        write_obj(os.path.join(tmp, 'in.obj'), ov, ofc, ouv)
        ms = ml.MeshSet(); ms.load_new_mesh(os.path.join(tmp, 'in.obj')); ms.load_new_mesh(os.path.join(tmp, 'in.obj'))
        ms.meshing_decimation_quadric_edge_collapse_with_texture(targetfacenum=max(int(len(of) * r), 12), qualitythr=.3,
            extratcoordw=1.0, preserveboundary=True, boundaryweight=10.0, optimalplacement=True, preservenormal=True)
        ms.save_current_mesh(os.path.join(tmp, 'out.obj'), save_textures=False)
        dv, df, duv = read_obj(os.path.join(tmp, 'out.obj')); n = len(df)
        a = ms.get_hausdorff_distance(sampledmesh=1, targetmesh=0, samplevert=True, sampleface=True, samplenum=20000)
        b = ms.get_hausdorff_distance(sampledmesh=0, targetmesh=1, samplevert=True, sampleface=True, samplenum=20000)
        mx, mean = max(a['max'], b['max']) / H * 100, max(a['mean'], b['mean']) / H * 100
        ok = mx <= 1.5 and mean <= 0.15
        rows['steps'][f'r{int(r * 100)}'] = {'opaque_after': n, 'total_after': int(len(F) - len(of) + n),
                                             'max_pct': round(mx, 3), 'mean_pct': round(mean, 4), 'pass': ok}
        np.savez(os.path.join(W, f'{name}_r{int(r * 100)}.npz'), verts=dv, faces=df, wuv=duv)
    passing = [k for k, v in rows['steps'].items() if v['pass']]
    rows['pick'] = passing[-1] if passing else None
    json.dump(rows, open(os.path.join(W, f'ladder_{name}.json'), 'w'), indent=1)
    p = rows['steps'].get(rows['pick'], {})
    print(f"{name:16s} total {len(F):6d} opaque {len(of):6d} -> pick {rows['pick']} total {p.get('total_after', len(F)):6d}  "
          + ' '.join(f"{k}:{v['max_pct']}/{v['mean_pct']}{'*' if v['pass'] else ''}" for k, v in rows['steps'].items()))
