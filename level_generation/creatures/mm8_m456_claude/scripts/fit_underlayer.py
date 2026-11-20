"""Fit the existing mail sleeves into the rigid cuirass and keep their roots on the chest."""
import bpy, bmesh
from pathlib import Path
p = Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p / 'work/master_uv.blend'))
body = bpy.data.objects['Body']
me = body.data

def smooth(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)

# The old shoulder balls were independent of both sleeve and chest; remove them.
balls = {v.index for v in me.vertices if me.attributes['piece'].data[v.index].value == 35
         and any(body.vertex_groups[g.group].name.endswith('_UpperArm') and g.weight > .99 for g in v.groups)}
assert len(balls) == 228
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
bmesh.ops.delete(bm, geom=[bm.verts[i] for i in balls], context='VERTS')
bm.to_mesh(me); bm.free()
changed = 0
for v in me.vertices:
    pc = me.attributes['piece'].data[v.index].value
    if pc in (6, 7):
        # Preserve the textured continuous sleeve, widening only its buried root to fill the armhole.
        shape = 1 - smooth((abs(v.co.x) - .11) / .12)
        v.co.y = -.006 + (v.co.y + .006) * (1 + .40 * shape)
        v.co.z = 1.25 + (v.co.z - 1.25) * (1 + .30 * shape)
        root = (1 - max(0.0, min(1.0, (abs(v.co.x) - .075) / .325))) * smooth((v.co.z - .9) / .28)
        old = {body.vertex_groups[g.group].name: g.weight for g in v.groups}
        weights = {n: w * (1 - root) for n, w in old.items()}
        weights['B_Spine2'] = weights.get('B_Spine2', 0) + root
        for g in list(v.groups):
            body.vertex_groups[g.group].remove([v.index])
        weights = dict(sorted(weights.items(), key=lambda x: -x[1])[:4])
        total = sum(weights.values())
        for n, w in weights.items():
            if w > 1e-6:
                body.vertex_groups[n].add([v.index], w / total, 'REPLACE')
        changed += root > 0
    if pc in (31, 32):
        # These straps lie above the elbow and must not swing with the forearm.
        side = 'R' if pc == 31 else 'L'
        assert v.co.z > bpy.data.objects['Rig'].data.bones[f'B_{side}_Forearm'].head_local.z
        for g in list(v.groups):
            body.vertex_groups[g.group].remove([v.index])
        body.vertex_groups[f'B_{side}_UpperArm'].add([v.index], 1, 'REPLACE')
    if pc == 35 and v.co.z < 1.11:
        v.co.x *= .8
        v.co.y = -.025 + (v.co.y + .025) * .75
assert changed > 400
ids = [v.index for v in me.vertices if me.attributes['piece'].data[v.index].value == 11 and v.co.z < 1.52]
low = min(me.vertices[i].co.z for i in ids)
for i in ids:
    v = me.vertices[i]
    v.co.z = 1.45 + (v.co.z - low) * (.07 / (1.52 - low))
for v in me.vertices:
    assert abs(sum(g.weight for g in v.groups) - 1) < .001
bpy.ops.wm.save_as_mainfile(filepath=str(p / 'work/master_uv_fitted.blend'))
print('SHOULDER_ROOTS', changed, 'removed independent balls', len(balls))
