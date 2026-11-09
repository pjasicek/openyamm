"""Textured review of work/anim_v4.blend at rest: body faces with the body retexture's base colour on UVMap, head
faces (part = 1) with the head retexture's base colour on HeadUV (unlit Workbench texture view), plus the rock.
Writes review/tex_<view>.png and head close-ups review/tex_head_<view>.png. Images: work/texture_preview.json
{"body": path, "head": path} (defaults: the Meshy base colours)."""
import bpy, sys, json
import numpy as np
from pathlib import Path
P = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(P / 'scripts'))
import common
cfg_path = P / 'work' / 'texture_preview.json'
cfg = json.loads(cfg_path.read_text()) if cfg_path.exists() else {}
body_img = cfg.get('body', str(P / 'meshy/body_retexture_v1/texture_urls_0_base_color.png'))
head_img = cfg.get('head', str(P / 'meshy/head_retexture_v1/texture_urls_0_base_color.png'))
bpy.ops.wm.open_mainfile(filepath=str(P / 'work' / 'anim_v4.blend'))
rig = bpy.data.objects['Rig']; q = bpy.data.objects['Queen']; me = q.data
rig.animation_data_create(); rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()


def mat(name, img, uv):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree
    bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    t = nt.nodes.new('ShaderNodeTexImage'); t.image = bpy.data.images.load(img)
    u = nt.nodes.new('ShaderNodeUVMap'); u.uv_map = uv
    nt.links.new(u.outputs['UV'], t.inputs['Vector']); nt.links.new(t.outputs['Color'], bsdf.inputs['Base Color'])
    return m


me.materials.clear()
me.materials.append(mat('body', body_img, 'UVMap'))
me.materials.append(mat('head', head_img, 'HeadUV'))
part = [p.value for p in me.attributes['part'].data]
me.polygons.foreach_set('material_index', part)
# Workbench texture mode samples the ACTIVE UV layer only: show the head pass separately
scene = bpy.context.scene
common.workbench_clay(scene, textured=True)
PLACE = (lambda d: d.get('queen_actor_location', d['queen_location']))(json.loads((P / 'work' / 'placement.json').read_text()))
bpy.data.objects['Rock'].hide_render = True
me.uv_layers.active = me.uv_layers['UVMap']
common.render_views(str(P / 'review' / 'tex'), PLACE[2] + 1.2, 2.6, views=('front', 'left', 'back', 'three_quarter'),
                    resolution=(500, 650), target=(PLACE[0], PLACE[1]))
me.uv_layers.active = me.uv_layers['HeadUV']
common.render_views(str(P / 'review' / 'tex_head'), PLACE[2] + 2.0, 0.75, views=('front', 'three_quarter', 'left'),
                    resolution=(500, 500), target=(PLACE[0], PLACE[1]))
