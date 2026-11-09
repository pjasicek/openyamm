"""Verify closed hair geometry and exact preservation of the face, body and animation."""
from pathlib import Path
import bpy, bmesh, json, hashlib

p=Path(__file__).resolve().parents[1]
def retained_data(path):
    bpy.ops.wm.open_mainfile(filepath=str(path))
    body=bpy.data.objects['Body']; mesh=body.data
    def vertex(index):
        v=mesh.vertices[index]
        return (tuple(round(x,7) for x in v.co),tuple(sorted((body.vertex_groups[g.group].name,round(g.weight,7)) for g in v.groups)))
    faces=[]
    for face in mesh.polygons:
        if any(mesh.attributes['piece'].data[i].value==105 for i in face.vertices): continue
        faces.append(tuple(sorted((vertex(mesh.loops[li].vertex_index),tuple(round(x,7) for x in mesh.uv_layers['HeadUV'].data[li].uv)) for li in face.loop_indices)))
    animations=[]
    for action in bpy.data.actions:
        curves=[f for layer in action.layers for strip in layer.strips for bag in strip.channelbags for f in bag.fcurves]
        animations.append((action.name,tuple(sorted((f.data_path,f.array_index,tuple(tuple(k.co) for k in f.keyframe_points)) for f in curves))))
    return sorted(faces),sorted(animations)

before=retained_data(p/'work/checkpoint_before_hair_v3/work/rig_textured_uv.blend')
after=retained_data(p/'work/rig_textured_uv.blend')
assert before==after, 'The hair repair changed retained geometry, UVs, weights or animation'
mesh=bpy.data.objects['Body'].data
bm=bmesh.new(); bm.from_mesh(mesh); piece=bm.verts.layers.int['piece']
bmesh.ops.delete(bm,geom=[v for v in bm.verts if v[piece]!=105],context='VERTS')
assert all(e.is_manifold for e in bm.edges)
assert bm.calc_volume(signed=True)>.0005
report={'source_sha256':hashlib.sha256((p/'export/mm8_m620.glb').read_bytes()).hexdigest(),
        'closed_hair_core':True,'boundary_edges':0,'hair_core_triangles':len(bm.faces),
        'retained_geometry_uvs_weights_unchanged':True,'six_civilian_actions_unchanged':True}
bm.free()
(p/'review/validation/hair_v3.json').write_text(json.dumps(report,indent=2)+'\n')
print('HAIR_VERIFIED',report)
