"""Close-up clay views of work/<blend> coloured by the face attribute `part` (0 body grey, 1 eyes green, 2 fangs
white, 3 claws yellow, 4 tail blue). Usage: part_views.py <blend> <prefix> <cx> <cy> <cz> <size> [jaw degrees]"""
import bpy, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', a[0]))
cx, cy, cz, s = map(float, a[2:6])
JAW = float(a[6]) if len(a) > 6 else 0.0
rig = bpy.data.objects.get('Saber_Rig')
if JAW and rig:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import posing as P
    if rig.animation_data: rig.animation_data.action = None
    P.reset(rig); P.rotate_world(rig, 'Jaw', (1, 0, 0), JAW)
me = bpy.data.objects['Saber'].data
COL = {0: (0.7, 0.7, 0.68), 1: (0.1, 0.9, 0.2), 2: (1, 1, 1), 3: (1, 0.85, 0), 4: (0.3, 0.4, 1), 5: (0.8, 0.1, 0.1)}
ca = me.color_attributes.new('pc', 'FLOAT_COLOR', 'CORNER')
for p in me.polygons:
    c = COL[me.attributes['part'].data[p.index].value]
    for li in p.loop_indices: ca.data[li].color = (*c, 1)
me.color_attributes.active_color = ca
for view, loc in {'front': (cx, cy - 3, cz), 'quarter': (cx + 1.6, cy - 2.4, cz + 0.6), 'side': (cx + 3, cy, cz)}.items():
    C.render(loc, (cx, cy, cz), s, os.path.join(HERE, 'review', f'{a[1]}_{view}.png'), res=(600, 600), floor=False,
             color='VERTEX')
