"""Review renders of an exported prop GLB (all LOD objects present before linking): LOD0..3 from one view, plus
LOD0 wireframe-free textured renders at a few yaws. Args: <prop> <glb> <yaw_deg>. Writes <prop>/review/render_*.png"""
import bpy, sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import deco_common as dc
prop, glb, yaw = sys.argv[sys.argv.index('--') + 1:]
out = os.path.join(dc.PROJECT, prop, 'review'); os.makedirs(out, exist_ok=True)
dc.reset(); objs = [o for o in dc.import_gltf(glb) if o.type == 'MESH']
dc.setup_render((512, 512))
bpy.context.scene.eevee.taa_render_samples = 32
base = min(objs, key=lambda o: len(o.name)).name
for o in objs:
    o.hide_render = True
for o in objs:
    o.hide_render = False
    dc.frame_camera([objs[0]], float(yaw), 12)
    level = o.name[len(base) + 4:] if o.name != base else '0'
    dc.render(os.path.join(out, f'render_lod{level}.png'))
    o.hide_render = True
lod0 = next(o for o in objs if o.name == base); lod0.hide_render = False
for extra in (0, 90, 180, 270):
    dc.frame_camera([lod0], float(yaw) + extra, 12)
    dc.render(os.path.join(out, f'render_yaw{extra:03d}.png'))
