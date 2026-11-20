"""Preview of the step1 labels (work/step1_labels.json): body grey, hair brown, wings blue. Args: -- <step1 blend> <out prefix>"""
import bpy, sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
src, out = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
L = {int(k): v for k, v in json.load(open(os.path.join(common.WORK, 'step1_labels.json'))).items()}
COL = {'body': (0.7, 0.7, 0.7, 1), 'hair': (0.5, 0.25, 0.05, 1), 'wing': (0.3, 0.45, 0.95, 1)}
for ob in (bpy.data.objects['Body'], bpy.data.objects['Wings']):
    me = ob.data; pv = [0] * len(me.vertices); me.attributes['piece'].data.foreach_get('value', pv)
    col = me.color_attributes.new('lab', 'FLOAT_COLOR', 'POINT')
    for i, p in enumerate(pv):
        col.data[i].color = COL[L[p]]
    me.color_attributes.active_color = col
sc = bpy.context.scene; common.workbench_clay(sc); sc.display.shading.color_type = 'VERTEX'
common.render_views(out, 1.0, 2.6, views=('front', 'left', 'back'), resolution=(900, 900))
common.render_views(out + '_head', 1.5, 0.6, views=('left', 'back'), resolution=(500, 500))
