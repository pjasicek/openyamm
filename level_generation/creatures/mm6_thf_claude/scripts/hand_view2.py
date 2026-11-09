"""Hands only (other parts hidden), rest pose, from the palm side, the back of the hand and the thumb side, with
coloured axis markers every 2 cm along z. Args: blend tag"""
import bpy, sys, os, json, math
import numpy as np
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.join(common.WORK, a[0]))
mesh = bpy.data.objects['Thief']; me = mesh.data
PARTS = json.loads(bpy.context.scene['thf_parts'])
part = np.zeros(len(me.polygons), dtype=np.int32); me.attributes['part'].data.foreach_get('value', part)
keep = {PARTS.index('Hand'), PARTS.index('Dagger')} if 'Dagger' in PARTS else {PARTS.index('Hand')}
import bmesh
bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table()
pl = bm.faces.layers.int['part']
bmesh.ops.delete(bm, geom=[f for f in bm.faces if f[pl] not in keep], context='FACES')
bm.to_mesh(me); bm.free()
for o in list(bpy.data.objects):
    if o.type == 'MESH' and o != mesh: bpy.data.objects.remove(o)
sc = bpy.context.scene; common.workbench_clay(sc); sc.display.shading.color_type = 'SINGLE'
sc.display.shading.show_cavity = True
R = os.path.join(common.REVIEW, a[1])
for sd, x in (('R', -0.24), ('L', 0.24)):
    sx = 1 if sd == 'L' else -1
    # palm side camera sits toward the body midline (looking outward), back-of-hand outside, thumb side in front
    for name, ang in (('palm', -90 * sx), ('back', 90 * sx), ('thumb', 0), ('below', None)):
        if ang is None:
            cam = common.ortho_camera('c', (x, -0.05, 0.4), (0, 0, 0), 0.18)
        else:
            r = math.radians(ang)
            cam = common.ortho_camera('c', (x + math.sin(r) * 1.0, -0.05 - math.cos(r) * 1.0, 0.78), (math.radians(90), 0, r), 0.18)
        sc.camera = cam; sc.render.resolution_x = sc.render.resolution_y = 450
        sc.render.filepath = f'{R}_{sd}_{name}.png'; bpy.ops.render.render(write_still=True)
        bpy.data.objects.remove(cam)
