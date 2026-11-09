"""Build MPFB body with macros from JSON arg, align to scaled Meshy, print torso/head cross-section profiles."""
import bpy, sys, os, json
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
args = sys.argv[sys.argv.index('--') + 1:]
macros = json.loads(args[0]); tag = args[1]
common.enable_mpfb()
from bl_ext.blender_org.mpfb.services.humanservice import HumanService
common.clear_scene()
human = HumanService.create_human(macro_detail_dict=macros, feet_on_ground=True, scale=0.1)
rig = HumanService.add_builtin_rig(human, 'mixamo')
bpy.context.view_layer.update()

def verts(obj, group=None):
    dg = bpy.context.evaluated_depsgraph_get()
    ev = obj.evaluated_get(dg); me = ev.to_mesh()
    co = np.array([tuple(obj.matrix_world @ v.co) for v in me.vertices])
    ev.to_mesh_clear(); return co

body = verts(human)
bpy.ops.import_scene.gltf(filepath=os.path.join(common.PROJECT, 'meshy/detail_source_v1/model_urls_glb.glb'))
meshy_obj = bpy.data.objects['Mesh_0']
m = np.array([tuple(v.co) for v in meshy_obj.data.vertices])
H = body[:, 2].max() - body[:, 2].min()
s = (H + 0.03) / (m[:, 2].max() - m[:, 2].min())
m = m * s; m[:, 2] -= m[:, 2].min() + 0.015; m[:, 0] -= (m[:, 0].max() + m[:, 0].min()) / 2
def profile(co, z, half=0.17):
    sel = co[(abs(co[:, 2] - z) < 0.006) & (abs(co[:, 0]) < half)]
    if len(sel) == 0: return None
    return (round(sel[:, 0].max() - sel[:, 0].min(), 3), round(sel[:, 1].min(), 3), round(sel[:, 1].max(), 3))
# Align body Y so the torso centre at chest level matches Meshy.
def ycentre(co, z):
    sel = co[(abs(co[:, 2] - z) < 0.01) & (abs(co[:, 0]) < 0.12)]
    return (sel[:, 1].min() + sel[:, 1].max()) / 2
dy = ycentre(m, 1.15) - ycentre(body, 1.15)
print('PROFILE', tag, 'H', round(H, 3), 'dy', round(dy, 3))
for z in (1.55, 1.5, 1.45, 1.40, 1.35, 1.30, 1.25, 1.20, 1.15, 1.10, 1.05, 1.00, 0.95):
    b = profile(body, z); mm = profile(m, z)
    b = (b[0], round(b[1] + dy, 3), round(b[2] + dy, 3)) if b else None
    print(f'  z={z:.2f} body={b} meshy={mm}')
# shoulder (outer deltoid) width: max |x| of verts between z 1.25..1.32 with |x|<0.3
for name, co in (('body', body), ('meshy', m)):
    sel = co[(co[:, 2] > 1.22) & (co[:, 2] < 1.30)]
    print('  shoulder_x_extent', name, round(sel[:, 0].max() - sel[:, 0].min(), 3))
bpy.data.objects.remove(meshy_obj, do_unlink=True)
rig.location.y += dy
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(common.WORK, f'body_{tag}.blend'))
