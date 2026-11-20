"""Stage C: graded body decimation (face/hands preserved most). Args: ratio factor. Writes work/assembly_v2.blend."""
import bpy, sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
args = sys.argv[sys.argv.index('--') + 1:]
ratio, factor = float(args[0]), float(args[1])
body = bpy.data.objects['Body']
meta = json.loads(bpy.context.scene['pfem_meta'])
hc = meta['head_centre']
groups = {g.index: g.name for g in body.vertex_groups}
g = body.vertex_groups.new(name='decimate_density')
for v in body.data.vertices:
    names = {groups[x.group]: x.weight for x in v.groups}
    hand = sum(w for n, w in names.items() if 'Hand' in n)
    if v.co.z > 1.36:
        w = 0.15 if (v.co.y < hc[1] - 0.02 and v.co.z > 1.38) else 0.45
    elif hand > 0.5:
        w = 0.22
    else:
        w = 1.0
    g.add([v.index], w, 'REPLACE')
m = body.modifiers.new('Decimate', 'DECIMATE')
m.ratio = ratio; m.vertex_group = 'decimate_density'; m.vertex_group_factor = factor
m.use_collapse_triangulate = True
bpy.context.view_layer.objects.active = body
while body.modifiers[0] != m:
    bpy.ops.object.modifier_move_up(modifier=m.name)
bpy.ops.object.modifier_apply(modifier=m.name)
if 'decimate_density' in body.vertex_groups:
    body.vertex_groups.remove(body.vertex_groups['decimate_density'])
def tris(me, cond):
    return sum(len(p.vertices) - 2 for p in me.polygons if cond(me.vertices[p.vertices[0]].co))
print('BODY_TRIS', tris(body.data, lambda c: True), 'head', tris(body.data, lambda c: c.z > 1.36),
      'arms', tris(body.data, lambda c: abs(c.x) > 0.2))
for o in bpy.data.objects:
    if o.type == 'MESH':
        for p in o.data.polygons:
            p.use_smooth = True
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(common.WORK, 'assembly_v2.blend'))
