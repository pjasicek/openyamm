"""Blender: convert EXR renders (ear_views.py uv passes) to float32 .npy next to them (row 0 at the top).
Args: -- <exr> [...]"""
import bpy, sys
import numpy as np
for p in sys.argv[sys.argv.index('--') + 1:]:
    im = bpy.data.images.load(p)
    W, H = im.size
    a = np.array(im.pixels[:], np.float32).reshape(H, W, 4)[::-1]
    np.save(p[:-4] + '.npy', a)
    print('EXR2NPY', p, a.shape)
