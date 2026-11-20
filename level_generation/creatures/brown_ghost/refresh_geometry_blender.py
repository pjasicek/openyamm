"""Refresh fixed-topology geometry/correctives without rebuilding unchanged animation clips."""
import bpy
import json
from mathutils import Vector, Matrix
from pathlib import Path
ROOT=Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/brown_ghost')
module={'__name__':'ghost_geometry'}
source=ROOT/'author_blender.py';exec(compile(source.read_text(),str(source),'exec'),module)
geometry=module['geometry']
scene=bpy.data.scenes['Brown ghost sprite studio'];bpy.context.window.scene=scene
rig=scene.objects['Ghost RIG'];obj=next(o for o in scene.objects if o.type=='MESH')
keys=obj.data.shape_keys;plan=json.loads((ROOT/'poses.json').read_text())
base=geometry('s',0)
assert len(base.v)==len(obj.data.vertices)
assert [tuple(p.vertices) for p in obj.data.polygons]==base.f
for group in obj.vertex_groups:group.remove(list(range(len(base.v))))
for index,weights in enumerate(base.weights):
    for name,weight in weights.items():
        if weight>0:obj.vertex_groups[name].add([index],weight,'REPLACE')
for vertex,basis,co in zip(obj.data.vertices,keys.key_blocks['Basis'].data,base.v):
    vertex.co=co;basis.co=co
for item in plan:
    data=geometry(item['kind'],item['phase'])
    skin={}
    for name,(head,tail) in data.joints.items():
        rest=rig.data.bones[name];direction=Vector(tail)-Vector(head)
        transform=Matrix.Translation(Vector(head)) @ direction.to_track_quat('Y','Z').to_matrix().to_4x4()
        transform=transform @ Matrix.Diagonal((1,direction.length/rest.length,1,1))
        skin[name]=transform @ rest.matrix_local.inverted()
    key=keys.key_blocks[f"{item['kind']}_{item['frame']:03d}_cloth_corrective"]
    inverse={}
    for vertex,co,weights in zip(key.data,data.v,base.weights):
        signature=tuple(weights.items())
        if signature not in inverse:
            transform=Matrix(((0,0,0,0),)*4)
            for name,weight in weights.items():transform+=skin[name]*weight
            inverse[signature]=transform.inverted_safe()
        vertex.co=inverse[signature] @ Vector(co)
obj.data.update();scene.frame_set(1);bpy.context.view_layer.update()
