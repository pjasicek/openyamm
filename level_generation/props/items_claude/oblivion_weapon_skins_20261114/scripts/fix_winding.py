#!/usr/bin/env python3
"""Winds a weapon template's triangles with their normals (README.md, "Winding"; approved 2026-11-14).

Oblivion's templates as exported wound every triangle against its vertex normals, and the engine culls by winding, so
it drew their far sides (guards, pommels and grips near black, a blade's back). This reverses the corner order of every
primitive whose triangles mostly disagree with their normals (the same [0, 2, 1] flip write_skin.py made for the skins)
and leaves a primitive that already agrees alone, so it can run twice.

The file is rewritten in place. Run it on the template's source, assets_source/engine/view_model/<template>.glb, then
cook the runtime copy (python3 tools/cook_models.py --only engine/view_model/<template>.glb); assets_dev holds only the
cooked copy since 2026-11-14. The pre-fix originals are in work/templates_backup_20261114/.

A layout made on the old order (work/<template>/uv_template.npy and maps/uv_tris.npz, one UV per template corner) is
permuted with it, so prep.py's output stays valid for later skins.

Usage: python3 fix_winding.py [--check] <template.glb>...
"""
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import glb_io


def main():
    check = '--check' in sys.argv
    for path in [a for a in sys.argv[1:] if a != '--check']:
        doc, binary = glb_io.read(path)
        views = [glb_io.view_bytes(doc, binary, i) for i in range(len(doc['bufferViews']))]
        report = []
        flipped_any = False
        for mesh in doc['meshes']:
            for prim in mesh['primitives']:
                tri = np.array(glb_io.accessor(doc, binary, prim['indices'])).reshape(-1, 3)
                share = glb_io.share_wound_with_normals(doc, binary, prim)
                report.append(f"{mesh.get('name')}: {len(tri)} tris, {share * 100:.1f} % with normals")
                if share >= 0.5 or check:
                    continue
                accessor = doc['accessors'][prim['indices']]
                users = [a for a in doc['accessors'] if a.get('bufferView') == accessor['bufferView']]
                assert len(users) == 1 and 'byteStride' not in doc['bufferViews'][accessor['bufferView']]
                accessor.pop('byteOffset', None)
                views[accessor['bufferView']] = np.ascontiguousarray(tri[:, [0, 2, 1]].ravel()).tobytes()
                flipped_any = True
        name = os.path.splitext(os.path.basename(path))[0]
        if flipped_any:
            # Same inode: open for writing truncates the file every hard link shares.
            glb_io.write(path, doc, views)
            work = os.path.join(PROJECT, 'work', name)
            npy = os.path.join(work, 'uv_template.npy')
            if os.path.exists(npy):
                np.save(npy, np.load(npy)[:, [0, 2, 1]])
                report.append('uv_template.npy permuted')
            npz = os.path.join(work, 'maps', 'uv_tris.npz')
            if os.path.exists(npz):
                np.savez(npz, uv=np.load(npz)['uv'][:, [0, 2, 1]])
                report.append('maps/uv_tris.npz permuted')
        print('WINDING', name, 'flipped' if flipped_any else 'unchanged', '; '.join(report))


if __name__ == '__main__':
    main()
