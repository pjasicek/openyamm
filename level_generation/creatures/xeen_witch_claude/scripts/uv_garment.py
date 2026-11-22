"""Raster of the garment label (garments.py) per texel of the body's UVMap: work/uv_garment_2k.png (8-bit, 255 =
outside every triangle), for the texture compose (region mask limited to the body and tatter shells, classes).
Each triangle covers its centre samples plus its corners, edge midpoints and centroid (sub-texel faces still land).
Args: -- <blend> [size]"""
import bpy, sys, os
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(a[0])); N = int(a[1]) if len(a) > 1 else 2048
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
me = bpy.data.objects['Body'].data
gv = np.zeros(len(me.vertices), np.int32); me.attributes['garment'].data.foreach_get('value', gv)
uvd = me.uv_layers['UVMap'].data
img = np.full((N, N), 255, np.uint8)
for p in me.polygons:
    g = int(gv[p.vertices[0]])
    uv = np.array([tuple(uvd[li].uv) for li in p.loop_indices]) * N
    pts = np.c_[uv[:, 0], N - uv[:, 1]]
    for k in range(1, len(pts) - 1):
        A, B, C = pts[0], pts[k], pts[k + 1]
        x0, y0 = np.floor(np.minimum(np.minimum(A, B), C)).astype(int); x1, y1 = np.ceil(np.maximum(np.maximum(A, B), C)).astype(int)
        x0, y0 = max(x0, 0), max(y0, 0); x1, y1 = min(x1, N - 1), min(y1, N - 1)
        xs, ys = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
        d = (B[1] - C[1]) * (A[0] - C[0]) + (C[0] - B[0]) * (A[1] - C[1])
        if abs(d) > 1e-12:
            l1 = ((B[1] - C[1]) * (xs - C[0]) + (C[0] - B[0]) * (ys - C[1])) / d
            l2 = ((C[1] - A[1]) * (xs - C[0]) + (A[0] - C[0]) * (ys - C[1])) / d
            inside = (l1 >= -1e-6) & (l2 >= -1e-6) & (1 - l1 - l2 >= -1e-6)
            img[ys[inside].astype(int), xs[inside].astype(int)] = g
        for q in (A, B, C, (A + B) / 2, (B + C) / 2, (A + C) / 2, (A + B + C) / 3):
            xi, yi = int(min(max(q[0], 0), N - 1)), int(min(max(q[1], 0), N - 1))
            img[yi, xi] = g
pix = np.zeros((N, N, 4), np.float32); pix[..., 0] = pix[..., 1] = pix[..., 2] = img / 255.0; pix[..., 3] = 1
im = bpy.data.images.new('g', N, N, alpha=False); im.colorspace_settings.name = 'Non-Color'
im.pixels = pix[::-1].ravel().tolist(); im.filepath_raw = os.path.join(HERE, 'work', f'uv_garment_{N // 1024}k.png')
im.file_format = 'PNG'; im.save()
print('UVGARMENT covered', round(float((img != 255).mean()), 3), {int(k): int((img == k).sum()) for k in np.unique(img)})
