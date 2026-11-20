"""Labelled review grid: rows = poses or clip frames, columns = views, textured, with the pose audit per row.

Args: out_png views items...   item = 'clip:<Action>:<frame>' or 'pose:<module>.<VAR>[<index>]'
  e.g. review/anim_v2/stand.png front,right,three_quarter pose:author_gob.STAND clip:Attack:7
"""
import bpy, sys, os, json, math, importlib, subprocess
import numpy as np
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common

args = sys.argv[sys.argv.index('--') + 1:]
out_png, views, items = args[0], args[1].split(','), args[2:]
sys.argv = [sys.argv[0], '--', 'none']
audit_src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'pose_audit.py')).read()
exec(audit_src.split('report = {}')[0])          # mesh masks, penetration(), joint_metrics()
import author_clips as A

for o in bpy.data.objects:
    if o.type == 'MESH': o.hide_render = o.name != 'Peasant'
scene = bpy.context.scene
common.workbench_clay(scene, textured=True)
scene.display.shading.background_color = (0.36, 0.37, 0.39)
tmp = os.path.join(common.REVIEW, 'tmp'); os.makedirs(tmp, exist_ok=True)


def set_item(item):
    kind, rest = item.split(':', 1)
    if kind == 'clip':
        clip, frame = rest.rsplit(':', 1)
        rig.animation_data.action = bpy.data.actions[clip]
        scene.frame_set(int(float(frame)))
        return f'{clip} f{frame}'
    rig.animation_data.action = None
    mod, var = rest.split('.', 1)
    index = None
    if var.endswith(']'):
        var, index = var[:-1].split('['); index = int(index)
    spec = getattr(importlib.import_module(mod), var)
    if index is not None:
        spec = spec[index][1]
    A.apply_pose(spec)
    return rest


def audit_now():
    dg = bpy.context.evaluated_depsgraph_get(); ev = mesh.evaluated_get(dg); me = ev.to_mesh()
    co = np.empty(len(me.vertices) * 3); me.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
    polys = [tuple(p.vertices) for p in me.polygons]
    tree = BVHTree.FromPolygons([Vector(c) for c in co],
                                [polys[i] for i in range(len(polys)) if body_poly[i] and all(TORSO[j] for j in polys[i])])
    parts = []
    for side in ('Left', 'Right'):
        distal, upper = masks[side]
        shoulder = np.array(rig.pose.bones[f'mixamorig:{side}Arm'].head)
        pen = penetration(co, tree, distal | (upper & (np.linalg.norm(co - shoulder, axis=1) > 0.12)))
        w, t, e, c = joint_metrics(side)
        parts.append(f'{side[0]}: pen {pen[0]*100:.1f}cm/{pen[1]} wrist {w} twist {t} elev {e} hum {joint_metrics.humeral}')
    sw = penetration(co, tree, sword_vert)
    parts.append(f'sword pen {sw[0]*100:.1f}cm/{sw[1]}')
    ev.to_mesh_clear()
    return '   '.join(parts)


rows = []
for n, item in enumerate(items):
    label = set_item(item)
    note = audit_now()
    cells = []
    for v in views:
        prefix = os.path.join(tmp, f'rv_{n:02d}')
        common.render_views(prefix, float(os.environ.get('RV_CZ', 0.80)), float(os.environ.get('RV_H', 1.75)), views=(v,),
                           resolution=(340, 400))
        cells.append(f'{prefix}_{v}.png')
    rows.append({'label': label, 'note': note, 'cells': cells})
    print('ROW', label, note)
compose = """
import json, sys
from PIL import Image, ImageDraw
rows, out = json.loads(sys.argv[1]), sys.argv[2]
cells = [[Image.open(c).convert('RGB') for c in r['cells']] for r in rows]
W = sum(c.width for c in cells[0]); H = cells[0][0].height
sheet = Image.new('RGB', (W, (H + 34) * len(rows)), (30, 30, 34)); draw = ImageDraw.Draw(sheet)
for i, r in enumerate(rows):
    y = i * (H + 34)
    draw.text((6, y + 3), r['label'], fill=(255, 230, 120)); draw.text((6, y + 18), r['note'], fill=(220, 220, 220))
    for k, c in enumerate(cells[i]):
        sheet.paste(c, (k * c.width, y + 34))
sheet.save(out)
"""
os.makedirs(os.path.dirname(os.path.abspath(out_png)), exist_ok=True)
subprocess.run(['/usr/bin/python3', '-c', compose, json.dumps(rows), os.path.abspath(out_png)], check=True)
print('SHEET', out_png)
