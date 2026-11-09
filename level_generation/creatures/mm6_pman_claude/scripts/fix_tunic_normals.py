"""Make Tunic face winding consistent and outward (Meshy collar had inverted islands)."""
import bpy, bmesh, json
m = bpy.data.objects['Peasant']; PARTS = json.loads(bpy.context.scene['pfem_parts'])
bm = bmesh.new(); bm.from_mesh(m.data); bm.faces.ensure_lookup_table()
pl = bm.faces.layers.int.get('part')
tun = [f for f in bm.faces if f[pl] == PARTS.index('Tunic')]
before = [f.normal.copy() for f in tun]
bmesh.ops.recalc_face_normals(bm, faces=tun)
bm.normal_update()
changed = sum(1 for f, n in zip(tun, before) if f.normal.dot(n) < 0)
bm.to_mesh(m.data); bm.free()
print('TUNIC normals changed', changed, 'of', len(tun))
bpy.ops.wm.save_mainfile()
