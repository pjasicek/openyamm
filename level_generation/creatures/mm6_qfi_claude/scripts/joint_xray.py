"""G3 X-ray: work/joints.json as red spheres (abdomen joints orange) and the arm/abdomen centrelines as small dots over
the semi-transparent mesh, front and left views. Writes review/joint_xray_<view>.png."""
import bpy, sys, json
from pathlib import Path
P = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(P / 'scripts'))
import common
src = next(P / 'work' / f for f in ('step3.blend', 'step2.blend', 'step1.blend') if (P / 'work' / f).exists())
bpy.ops.wm.open_mainfile(filepath=str(src))
J = json.loads((P / 'work' / 'joints.json').read_text())['joints']
CL = json.loads((P / 'work' / 'centrelines.json').read_text())
ob = bpy.data.objects['Queen']
m = bpy.data.materials.new('xray'); m.diffuse_color = (0.8, 0.8, 0.8, 0.25)
ob.data.materials.clear(); ob.data.materials.append(m)
def sphere(p, r, col):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, location=p, segments=12, ring_count=8)
    o = bpy.context.active_object
    mm = bpy.data.materials.new('j'); mm.diffuse_color = (*col, 1.0); o.data.materials.append(mm)
for k, v in J.items():
    sphere(v, 0.022, (1.0, 0.5, 0.0) if k.startswith('Abdomen') else (0.9, 0.05, 0.05))
for pts in CL.values():
    for p in pts[::2]:
        sphere(p, 0.008, (0.1, 0.3, 1.0))
scene = bpy.context.scene
common.workbench_clay(scene)
scene.display.shading.color_type = 'MATERIAL'
scene.display.shading.show_xray = True
scene.display.shading.xray_alpha = 0.35
common.render_views(str(P / 'review' / 'joint_xray'), 1.2, 2.6, views=('front', 'left'), resolution=(800, 1100))
