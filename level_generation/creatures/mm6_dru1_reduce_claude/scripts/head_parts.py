"""Head-set parts of the reduced candidate (work/ladder_fel3.blend, REA_CAND default Cand_66): head-set faces are
the atlas's right half (u > 0.5). Head faces of the big piece (welded to the torso) = face (face, ears, neck, choker,
scalp); the separate pieces are the hood (region-mask cloth) and the hair shell. Writes face attribute 'hpart' (0 body, 1 face, 2 hair, 3 hood) and work/head_parts.blend;
prints counts and 3D areas. Usage: blender -b -P head_parts.py"""
import os, bpy, bmesh
import numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'ladder_fel3.blend'))
c = bpy.data.objects[os.environ.get('REA_CAND', 'Cand_66')]; me = c.data
def load(name):
    im = bpy.data.images.load(os.path.join(HERE, 'work', name))
    return np.array(im.pixels[:], np.float32).reshape(im.size[1], im.size[0], im.channels)[::-1]
mask = load('dru1_region_mask_head_atlas.png')[..., 0]
im = bpy.data.images.load(os.path.join(HERE, 'work', 'basecolor.png'))
img = np.array(im.pixels[:], np.float32).reshape(im.size[1], im.size[0], im.channels)[::-1, :, :3]  # top row first
H, W = img.shape[:2]
uv = me.uv_layers['UVMap'].data
bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table()
# connected pieces (vertex connectivity)
piece = [-1] * len(bm.faces); n = 0
for f0 in bm.faces:
    if piece[f0.index] >= 0: continue
    stack = [f0]; piece[f0.index] = n
    while stack:
        f = stack.pop()
        for v in f.verts:
            for g in v.link_faces:
                if piece[g.index] < 0: piece[g.index] = n; stack.append(g)
    n += 1
piece = np.array(piece)
cent = np.array([[sum(uv[l].uv[k] for l in p.loop_indices) / 3 for k in (0, 1)] for p in me.polygons])
headset = cent[:, 0] > .5
col = img[np.clip(((1 - cent[:, 1]) * H).astype(int), 0, H - 1), np.clip((cent[:, 0] * W).astype(int), 0, W - 1)]
r, g, b = col.T
skin = (r > .5) & (g > r * .55) & (b > r * .35)
area = np.array([p.area for p in me.polygons])
sizes = np.bincount(piece)
py = np.clip(((1 - cent[:, 1]) * H).astype(int), 0, H - 1); px = np.clip((cent[:, 0] * W).astype(int), 0, W - 1)
cloth = mask[py, px] > .3
# the hood and the hair shell are their own pieces; every head face of the big piece is face / neck / scalp skin
cls = np.zeros(len(me.polygons), int)
for pc in np.unique(piece[headset]):
    sel = headset & (piece == pc)
    print('PIECE', pc, 'faces', sizes[pc], 'head faces', int(sel.sum()), 'skin %.2f cloth %.2f' % (skin[sel].mean(), cloth[sel].mean()))
    cls[sel] = 1 if sizes[pc] == sizes.max() else (3 if cloth[sel].mean() > .5 else 2)
hpart = cls.astype(np.int32)
a = me.attributes.get('hpart') or me.attributes.new('hpart', 'INT', 'FACE')
a.data.foreach_set('value', hpart.tolist())
for k, name in [(1, 'face'), (2, 'hair'), (3, 'hood')]:
    print('PART', name, int((hpart == k).sum()), 'faces, %.4f m2' % area[hpart == k].sum())
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'head_parts.blend'))
