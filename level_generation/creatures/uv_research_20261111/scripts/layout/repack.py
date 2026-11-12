#!/usr/bin/env python3
"""Re-pack the islands of an existing layout with the xatlas packer copy (xatlas_pack.py in the xatlas venv), keeping
every island's shape and relative scale. Writes an npz layout (pos, uv per triangle corner, glTF v-down).

    repack.py <layout glb | npz> <out npz> [--uv-image name] [--margin 2] [--fine 250] [--steps 10] [--size 2048]
"""
import argparse
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import uvlib  # noqa: E402

VENV = uvlib.CREATURES / 'claude_shared/xatlas_venv/bin/python'
TOOL = Path(__file__).resolve().parent / 'xatlas_pack.py'


def load_layout(path, uv_image=None):
    if str(path).endswith('.npz'):
        d = np.load(path)
        return d['pos'].astype(np.float64), d['uv'].astype(np.float64)
    return uvlib.lod0_uv(path, uv_image)


def vertex_ids(tri_pos):
    keys = np.round(tri_pos.reshape(-1, 3), 5)
    return np.unique(keys, axis=0, return_inverse=True)[1].reshape(-1, 3)


def pack(tri_pos, tri_uv, margin, fine, steps, size=2048, extra=()):
    with tempfile.TemporaryDirectory() as tmp:
        src, dst = Path(tmp) / 'in.npz', Path(tmp) / 'out.npz'
        blender = tri_uv.copy()
        blender[..., 1] = 1.0 - blender[..., 1]
        np.savez(src, uv=blender.astype(np.float32), vert=vertex_ids(tri_pos).astype(np.int32))
        t = time.time()
        r = subprocess.run([str(VENV), '-I', str(TOOL), 'pack', str(src), str(dst), '--size', str(size), '--padding',
                            str(margin), '--fine', str(fine), '--steps', str(steps), *map(str, extra)],
                           capture_output=True, text=True)
        print(r.stdout.strip().splitlines()[-1] if r.stdout.strip() else '', flush=True)
        if r.returncode:
            raise RuntimeError(r.stderr)
        out = np.load(dst)['uv'].astype(np.float64)
        out[..., 1] = 1.0 - out[..., 1]
        return out, time.time() - t


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('layout')
    parser.add_argument('out')
    parser.add_argument('--uv-image')
    parser.add_argument('--margin', type=int, default=2)
    parser.add_argument('--fine', type=int, default=250)
    parser.add_argument('--steps', type=int, default=10)
    parser.add_argument('--size', type=int, default=2048)
    args = parser.parse_args()
    pos, uv = load_layout(args.layout, args.uv_image)
    packed, seconds = pack(pos, uv, args.margin, args.fine, args.steps, args.size)
    np.savez(args.out, pos=pos, uv=packed, seconds=seconds, margin=args.margin)
    union = uvlib.raster_labels(packed, np.zeros(len(packed), int), args.size) >= 0
    print(f'{args.out}: margin {args.margin} atlas {100 * union.mean():.1f} % in {seconds:.0f} s')
