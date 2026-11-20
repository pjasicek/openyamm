"""Blender helper: every *.exr in a folder -> <name>.npy (float32 H x W x 4, top row first). Args: <folder>"""
import bpy, sys, os
import numpy as np
d = sys.argv[sys.argv.index('--') + 1]
for f in sorted(os.listdir(d)):
    if not f.endswith('.exr'): continue
    im = bpy.data.images.load(os.path.join(d, f)); w, h = im.size
    a = np.array(im.pixels[:], np.float32).reshape(h, w, 4)[::-1]; np.save(os.path.join(d, f[:-4] + '.npy'), a); print('NPY', f, a.shape)
