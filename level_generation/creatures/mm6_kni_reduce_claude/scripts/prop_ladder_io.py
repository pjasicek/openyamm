"""OBJ helpers of prop_ladder.py (MeshLab texture-aware collapse needs a textured material per face), importable."""
import os, struct, zlib
import numpy as np


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
