"""Clay turnaround of a work blend coloured by part. Args: blend tag"""
import bpy, os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
blend, tag = sys.argv[sys.argv.index('--') + 1:][:2]
bpy.ops.wm.open_mainfile(filepath=os.path.join(common.WORK, blend))
o = bpy.data.objects['Werewolf']
parts = json.loads(bpy.context.scene['wfigt1_parts'])
cols = [(0.75, 0.55, 0.5, 1), (0.85, 0.5, 0.2, 1), (0.6, 0.6, 0.7, 1), (0.5, 0.5, 0.6, 1), (0.2, 0.8, 0.8, 1),
        (0.95, 0.8, 0.2, 1), (0.95, 0.95, 0.9, 1), (0.8, 0.3, 0.3, 1), (0.35, 0.35, 0.4, 1), (0.45, 0.45, 0.5, 1)]
o.data.materials.clear()
for i, n in enumerate(parts):
    m = bpy.data.materials.new(n); m.diffuse_color = cols[i % len(cols)]; o.data.materials.append(m)
pa = [0] * len(o.data.polygons); o.data.attributes['part'].data.foreach_get('value', pa)
o.data.polygons.foreach_set('material_index', pa)
o.show_wire = True
scene = bpy.context.scene; common.workbench_clay(scene); scene.display.shading.color_type = 'MATERIAL'
common.render_views(os.path.join(common.REVIEW, tag), 0.8, 1.7, views=('front', 'three_quarter', 'left', 'back'), resolution=(600, 900))
common.render_views(os.path.join(common.REVIEW, tag + '_seat'), 0.75, 0.5, views=('left', 'back'), resolution=(500, 500), target=(0, 0.05))
common.render_views(os.path.join(common.REVIEW, tag + '_head'), 1.38, 0.42, views=('front', 'three_quarter', 'left'), resolution=(500, 500))
