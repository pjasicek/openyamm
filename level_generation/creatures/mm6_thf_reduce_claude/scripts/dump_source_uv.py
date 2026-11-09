"""Body-set triangles of the installed master (../mm6_thf_claude/work/rig_v3.blend: body UVs 0..1, head faces in their
own head layout and skipped) with their uv_region -> work/source_uv.json, to split the installed cloth texels into
cloak/hood and undershirt (compose_tex.py)."""
import json, os
import bmesh, bpy
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(os.path.dirname(HERE), 'mm6_thf_claude', 'work', 'rig_v3.blend'))
mesh = bpy.data.objects['Thief']
bm = bmesh.new(); bm.from_mesh(mesh.data); bmesh.ops.triangulate(bm, faces=bm.faces[:])
uv = bm.loops.layers.uv.active; reg = bm.faces.layers.int['uv_region']; hd = bm.faces.layers.int['head']
tris = [{'region': f[reg], 'uv': [[l[uv].uv.x, l[uv].uv.y] for l in f.loops]} for f in bm.faces if not f[hd]]
json.dump({'regions': json.loads(bpy.context.scene['thf_uv_regions']), 'tris': tris}, open(os.path.join(HERE, 'work', 'source_uv.json'), 'w'))
print('DUMPED', len(tris))
