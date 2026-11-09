"""Stress pose coloured by part (which shell pokes through which). Args: blend tag. Uses stress_pose.py's pose."""
import bpy, sys, os, json
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.argv = sys.argv[:sys.argv.index('--') + 1] + sys.argv[sys.argv.index('--') + 1:][:2]
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'stress_pose.py')).read().split('sc = bpy.context.scene')[0])
mesh = bpy.data.objects['Cleric']; me = mesh.data
PARTS = json.loads(bpy.context.scene['cle_parts'])
cols = [(0.3, 0.45, 0.9, 1), (0.85, 0.85, 0.85, 1), (0.15, 0.15, 0.4, 1), (0.9, 0.7, 0.5, 1), (0.6, 0.4, 0.2, 1), (0.9, 0.6, 0.1, 1)]
me.materials.clear()
for n, c in zip(PARTS, cols):
    m = bpy.data.materials.new(n); m.diffuse_color = c; me.materials.append(m)
part = np.zeros(len(me.polygons), dtype=np.int32); me.attributes['part'].data.foreach_get('value', part)
me.polygons.foreach_set('material_index', part)
sc = bpy.context.scene
common.workbench_clay(sc)
sc.display.shading.color_type = 'MATERIAL'
common.render_views(os.path.join(common.REVIEW, a[1]), 0.85, 1.9, views=('front', 'three_quarter', 'back'), resolution=(600, 900))
common.render_views(os.path.join(common.REVIEW, a[1] + '_torso'), 0.95, 0.75, views=('front', 'three_quarter'), resolution=(700, 700))
