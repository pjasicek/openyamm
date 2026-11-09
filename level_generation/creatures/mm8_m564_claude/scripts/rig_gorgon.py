"""Fit a bovine skeleton to measured mesh slices; preserve rigid hoof and horn tips."""
from pathlib import Path
import json
import bpy
import numpy as np
from mathutils import Vector

P = Path(__file__).resolve().parents[1]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(P/'meshy/smart_topology_v2/model_urls_glb.glb'))
mesh = next(o for o in bpy.context.scene.objects if o.type == 'MESH')
for obj in list(bpy.data.objects):
    if obj != mesh:
        bpy.data.objects.remove(obj, do_unlink=True)
mesh.parent = None
bpy.context.view_layer.objects.active = mesh
mesh.select_set(True)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
floor = min(v.co.z for v in mesh.data.vertices)
for v in mesh.data.vertices:
    v.co.z -= floor
mesh.name = mesh.data.name = 'Gorgon'
for face in mesh.data.polygons:
    face.use_smooth = True

chains = {
    'Spine': (None, [(0,.21,.285), (0,.075,.285), (0,-.045,.30), (0,-.17,.31)]),
    'Neck': ('Spine3', [(0,-.17,.31), (0,-.29,.31)]),
    'Head': ('Neck1', [(0,-.29,.31), (0,-.425,.255)]),
    'Tail': ('Spine1', [(0,.25,.355), (0,.30,.34), (0,.34,.30), (0,.38,.225),
                         (0,.43,.175), (0,.475,.147)]),
}
names = {'Spine':['Spine1','Spine2','Spine3'], 'Neck':['Neck1'], 'Head':['Head'],
         'Tail':[f'Tail{i}' for i in range(1,6)]}
for side, sign in [('L',1),('R',-1)]:
    # Median leg sections from work/source_vertices.npy; hips/shoulders lie inside the body.
    chains['Front_'+side] = ('Spine3', [(sign*.075,-.17,.28), (sign*.083,-.135,.18),
                           (sign*.09,-.15,.09), (sign*.098,-.174,.028), (sign*.098,-.20,.012)])
    chains['Hind_'+side] = ('Spine1', [(sign*.078,.21,.28), (sign*.078,.18,.205),
                          (sign*.078,.238,.12), (sign*.09,.23,.033), (sign*.095,.203,.013)])
    names['Front_'+side] = [f'UpperArm_{side}',f'ForeArm_{side}',f'FrontPastern_{side}',f'FrontHoof_{side}']
    names['Hind_'+side] = [f'Thigh_{side}',f'Shin_{side}',f'HindPastern_{side}',f'HindHoof_{side}']
data = bpy.data.armatures.new('Gorgon_Rig')
rig = bpy.data.objects.new('Gorgon_Rig',data)
bpy.context.scene.collection.objects.link(rig)
bpy.ops.object.select_all(action='DESELECT')
rig.select_set(True)
bpy.context.view_layer.objects.active = rig
bpy.ops.object.mode_set(mode='EDIT')
for chain,(parent,points) in chains.items():
    previous = data.edit_bones.get(parent) if parent else None
    for i,name in enumerate(names[chain]):
        b = data.edit_bones.new(name)
        b.head, b.tail = points[i], points[i+1]
        b.parent = previous
        b.use_connect = previous is not None and i>0
        b.align_roll(Vector((0,0,1)) if chain in ('Spine','Neck','Head','Tail') else Vector((0,-1,0)))
        previous=b
bpy.ops.object.mode_set(mode='OBJECT')
mesh.select_set(True)
bpy.ops.object.parent_set(type='ARMATURE_AUTO')
unweighted = [v.index for v in mesh.data.vertices if not v.groups]
assert not unweighted, f'Heat weighting left {len(unweighted)} vertices'

def rigid(ids,name):
    if not ids:
        return
    for group in mesh.vertex_groups:
        group.remove(ids)
    mesh.vertex_groups[name].add(ids,1,'REPLACE')

for side,sign in [('L',1),('R',-1)]:
    for kind,front in [('Front',True),('Hind',False)]:
        ids=[v.index for v in mesh.data.vertices if v.co.x*sign>0 and
             ((v.co.y<0)==front) and v.co.z<.035]
        assert ids
        rigid(ids,f'{kind}Hoof_{side}')
rigid([v.index for v in mesh.data.vertices if v.co.y<-.30], 'Head')
bpy.context.view_layer.objects.active=mesh
bpy.ops.object.vertex_group_limit_total(limit=4)
bpy.ops.object.vertex_group_normalize_all(lock_active=False)
assert all(1<=len(v.groups)<=4 for v in mesh.data.vertices)
info={'bones':len(data.bones),'unweighted_vertices':0,'max_influences':4,'chains':chains,
      'rigid_parts':'Hoof tips below z=.035 and head forward of y=-.30',
      'source':'meshy/smart_topology_v2/model_urls_glb.glb','ground_offset':-floor}
(P/'work/rig_measurements.json').write_text(json.dumps(info,indent=2)+'\n')
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rig_v1.blend'))
print('RIG',info['bones'],'bones; 0 unweighted vertices',flush=True)
