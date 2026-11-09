"""Fit a equine skeleton to measured mesh slices; preserve rigid hoof and horn tips."""
from pathlib import Path
import json
import bpy
import numpy as np
from mathutils import Vector

P = Path(__file__).resolve().parents[1]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(P/'meshy/smart_topology_v1/model_urls_glb.glb'))
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
mesh.name = mesh.data.name = 'Unicorn'
for face in mesh.data.polygons:
    face.use_smooth = True

chains = {
    'Spine': (None, [(0,.18,.405), (0,.065,.405), (0,-.065,.405), (0,-.19,.405)]),
    'Neck': ('Spine3', [(0,-.19,.405), (0,-.25,.49), (0,-.32,.565)]),
    'Head': ('Neck2', [(0,-.32,.565), (0,-.395,.465)]),
    'Tail': ('Spine1', [(0,.278,.475), (0,.335,.44), (0,.387,.36), (0,.425,.26),
                      (0,.459,.15), (0,.474,.065)]),
}
names = {'Spine':['Spine1','Spine2','Spine3'], 'Neck':['Neck1','Neck2'], 'Head':['Head'],
         'Tail':[f'Tail{i}' for i in range(1,6)]}
for side, sign in [('L',1),('R',-1)]:
    # Per-leg slices retain the generated rest stance; IK later places level soles on the floor.
    front_y=-.228 if side=='L' else -.166
    hind_y=.153 if side=='L' else .250
    chains['Front_'+side] = ('Spine3', [(sign*.052,-.19,.355), (sign*.051,-.177,.265),
                           (sign*.051,-.186,.175), (sign*.055,front_y,.027),
                           (sign*.055,front_y-.027,.009)])
    chains['Hind_'+side] = ('Spine1', [(sign*.065,.18,.405), (sign*.060,.15,.29),
                          (sign*.055,.22,.195), (sign*.057,hind_y,.028),
                          (sign*.057,hind_y-.028,.010)])
    names['Front_'+side] = [f'UpperArm_{side}',f'ForeArm_{side}',f'FrontPastern_{side}',f'FrontHoof_{side}']
    names['Hind_'+side] = [f'Thigh_{side}',f'Shin_{side}',f'HindPastern_{side}',f'HindHoof_{side}']
data = bpy.data.armatures.new('Unicorn_Rig')
rig = bpy.data.objects.new('Unicorn_Rig',data)
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
# Heat failed on both source and watertight proxy; explicit regions prevent cross-limb influence.
for bone in data.bones:mesh.vertex_groups.new(name=bone.name)
def smooth(a,b,x):
    u=max(0,min(1,(x-a)/(b-a)))
    return u*u*(3-2*u)
def weights(point,bones):
    values={}
    for name in bones:
        bone=data.bones[name];a=bone.head_local;b=bone.tail_local;delta=b-a
        t=max(0,min(1,(point-a).dot(delta)/delta.length_squared))
        distance=(point-a-delta*t).length
        values[name]=1/(distance*distance+.00012)**2
    total=sum(values.values())
    return {name:value/total for name,value in values.items()}
def blend(a,b,t):
    return {name:a.get(name,0)*(1-t)+b.get(name,0)*t for name in a.keys()|b.keys()}
for v in mesh.data.vertices:
    x,y,z=v.co
    w=weights(v.co,names['Spine'])
    neck=smooth(.38,.46,z)*(1-smooth(-.19,-.10,y))
    w=blend(w,weights(v.co,names['Neck']+['Head']),neck)
    tail=smooth(.255,.31,y)
    w=blend(w,weights(v.co,names['Tail']),tail)
    lateral=1-smooth(.235,.29,z)*(1-smooth(.018,.05,abs(x)))
    if y<-.10 and z<.37:
        side='L' if x>0 else 'R'
        w=blend(w,weights(v.co,names['Front_'+side]),(1-smooth(.255,.37,z))*lateral)
    if .045<y<.30 and z<.39:
        side='L' if x>0 else 'R'
        w=blend(w,weights(v.co,names['Hind_'+side]),(1-smooth(.255,.39,z))*lateral)
    selected=sorted(w.items(),key=lambda item:item[1],reverse=True)[:4]
    total=sum(value for name,value in selected)
    for name,value in selected:
        if value>1e-7:mesh.vertex_groups[name].add([v.index],value/total,'REPLACE')
mod=mesh.modifiers.new('Armature','ARMATURE');mod.object=rig;mesh.parent=rig
assert all(v.groups for v in mesh.data.vertices)

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
rigid([v.index for v in mesh.data.vertices if v.co.y<-.342], 'Head')
bpy.context.view_layer.objects.active=mesh
bpy.ops.object.vertex_group_limit_total(limit=4)
bpy.ops.object.vertex_group_normalize_all(lock_active=False)
assert all(1<=len(v.groups)<=4 for v in mesh.data.vertices)
info={'bones':len(data.bones),'unweighted_vertices':0,'max_influences':4,'chains':chains,
      'rigid_parts':'Hoof tips below z=.035 and skull/horn forward of y=-.342',
      'source':'meshy/smart_topology_v1/model_urls_glb.glb','ground_offset':-floor,'weights':'anatomical regions with segment-distance blending; heat failed on source and proxy'}
(P/'work/rig_measurements.json').write_text(json.dumps(info,indent=2)+'\n')
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rig_v1.blend'))
print('RIG',info['bones'],'bones; 0 unweighted vertices',flush=True)
