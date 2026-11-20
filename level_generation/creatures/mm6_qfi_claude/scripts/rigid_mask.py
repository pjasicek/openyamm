"""Rigid armour mask for build_rig.py, from the textured master (work/anim_v4.blend: the queen's UVMap is the body
retexture's layout; vertex order equals work/step3.blend's). Per body vertex (part 0), the texture under its corners:
  - metal: Meshy's metallic map > 0.5 (breastplate cups, strap studs),
  - strap: base colour luminance < 0.09 (black leather) on the chest: between the waist and 3 cm under the shoulder
    tops, |x| < 0.24 (the black forearms and hands are outside it).
Writes work/rigid_mask.json {"metal": [...], "strap": [...]} (vertex indices)."""
import bpy, json
import numpy as np
from pathlib import Path
P = Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P / 'work' / 'anim_v4.blend'))
rig = bpy.data.objects['Rig']; q = bpy.data.objects['Queen']; me = q.data
rig.animation_data_create(); rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
def load_image(path):
    im = bpy.data.images.load(str(path))
    w, h = im.size
    px = np.empty(w * h * 4, np.float32); im.pixels.foreach_get(px)
    return px.reshape(h, w, 4)[::-1]                    # Blender stores rows bottom-up


metal_im = load_image(P / 'meshy/body_retexture_v1/texture_urls_0_metallic.png')[..., 0]
base_im = load_image(P / 'meshy/body_retexture_v1/texture_urls_0_base_color.png')[..., :3]
H, W = metal_im.shape
J = json.loads((P / 'work' / 'joints.json').read_text())
PLACE = json.loads((P / 'work' / 'placement.json').read_text())
off = np.array(PLACE['queen_actor_location'])
waist = J['report']['torso']['waist_z'] + off[2]
top = J['report']['torso']['shoulder_top_z'] + off[2] - 0.03
part = np.array([p.value for p in me.attributes['part'].data])
uv = me.uv_layers['UVMap'].data
co = np.array([tuple(v.co) for v in me.vertices])
metal = np.zeros(len(co)); dark = np.zeros(len(co)); n = np.zeros(len(co))
for p in me.polygons:
    if part[p.index]:
        continue
    for li, vi in zip(p.loop_indices, p.vertices):
        u, v = uv[li].uv
        x = min(W - 1, max(0, int(u * W))); y = min(H - 1, max(0, int((1 - v) * H)))
        metal[vi] += metal_im[y, x]
        dark[vi] += base_im[y, x] @ np.array([0.2126, 0.7152, 0.0722])
        n[vi] += 1
ok = n > 0
metal = np.where(ok, metal / np.maximum(n, 1), 0); dark = np.where(ok, dark / np.maximum(n, 1), 1)
chest = (co[:, 2] > waist) & (co[:, 2] < top) & (np.abs(co[:, 0] - off[0]) < 0.24)
m_ids = np.where(ok & (metal > 0.5) & chest)[0]
s_ids = np.where(ok & (dark < 0.09) & chest & ~(metal > 0.5))[0]
# the straps over the shoulder tops (above the chest band, up to 6 cm over the shoulder line, |x| < 0.26)
top_band = (co[:, 2] >= top) & (co[:, 2] < top + 0.09) & (np.abs(co[:, 0] - off[0]) < 0.26)
u_ids = np.where(ok & (dark < 0.09) & top_band & ~(metal > 0.5))[0]
(P / 'work' / 'rigid_mask.json').write_text(json.dumps({'metal': m_ids.tolist(), 'strap': s_ids.tolist(),
                                                        'strap_top': u_ids.tolist(), 'top_z': float(top)}))
print('RIGID strap over the shoulders', len(u_ids))
print('RIGID metal', len(m_ids), 'strap', len(s_ids), 'chest verts', int(chest.sum()))
