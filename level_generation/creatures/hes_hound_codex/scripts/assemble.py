"""Fit rigid resin armour and jaw glow, then export the animated body and attachment masters."""
import bpy
import bmesh
import json
import math
import os
import sys
from pathlib import Path
import numpy as np
from mathutils import Vector,Matrix

PROJECT=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(PROJECT/'work/anim_v1.blend'))
rig=bpy.data.objects['Hound_Rig']
body=bpy.data.objects['Hound']
# Meshy's disconnected teeth include two inward shells; normalize them before any export or LOD.
bm=bmesh.new()
bm.from_mesh(body.data)
bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
bm.to_mesh(body.data)
bm.free()
rig.animation_data.action=None
for pb in rig.pose.bones: pb.matrix_basis.identity()
bpy.context.view_layer.update()
sc=bpy.context.scene

def material(name,color,rough=.6,metal=0):
    m=bpy.data.materials.new(name)
    m.use_nodes=True
    m.use_backface_culling=True
    b=m.node_tree.nodes.get('Principled BSDF')
    b.inputs['Base Color'].default_value=(*color,1)
    b.inputs['Roughness'].default_value=rough
    b.inputs['Metallic'].default_value=metal
    return m

hide=material('HoundHide',(.35,.35,.35),.78)
nt=hide.node_tree
bsdf=nt.nodes.get('Principled BSDF')
for name,file,space in [('base','hound_basecolor.png','sRGB'),('normal','hound_normal.png','Non-Color'),
                        ('orm','hound_metal_rough.png','Non-Color')]:
    node=nt.nodes.new('ShaderNodeTexImage')
    node.image=bpy.data.images.load(str(PROJECT/'textures'/file))
    node.image.colorspace_settings.name=space
    if name=='base': nt.links.new(node.outputs['Color'],bsdf.inputs['Base Color'])
    elif name=='normal':
        nm=nt.nodes.new('ShaderNodeNormalMap')
        nt.links.new(node.outputs['Color'],nm.inputs['Color'])
        nt.links.new(nm.outputs['Normal'],bsdf.inputs['Normal'])
    else:
        sep=nt.nodes.new('ShaderNodeSeparateColor')
        nt.links.new(node.outputs['Color'],sep.inputs['Color'])
        nt.links.new(sep.outputs['Green'],bsdf.inputs['Roughness'])
        nt.links.new(sep.outputs['Blue'],bsdf.inputs['Metallic'])
body.data.materials.clear()
body.data.materials.append(hide)
for p in body.data.polygons: p.material_index=0
resin=material('Resin',(.026,.029,.032),.38)
iron=material('Iron',(.11,.12,.13),.53,.9)
glow=material('MawGlow',(0,0,0),1)
gb=glow.node_tree.nodes.get('Principled BSDF')
gb.inputs['Emission Color'].default_value=(1,.16,.01,1)
gb.inputs['Emission Strength'].default_value=1

# Sparse throat fissures follow the hide's weights; only C makes this separate material emissive.
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree
crack=material('ThroatFissures',(0.007,0.006,0.005),.9)
crack.node_tree.nodes.get('Principled BSDF').inputs['Emission Strength'].default_value=1
crack.node_tree.nodes.get('Principled BSDF').inputs['Emission Color'].default_value=(0,0,0,1)
tree=BVHTree.FromObject(body,bpy.context.evaluated_depsgraph_get())
kdt=KDTree(len(body.data.vertices))
for v in body.data.vertices: kdt.insert(v.co,v.index)
kdt.balance()
verts=[]; faces=[]; weights=[]
for side in (-1,1):
    for k,(y,z) in enumerate([(-.94,.81),(-.91,.825),(-.88,.84)]):
        start=len(verts)
        for j in range(4):
            for edge in (-1,1):
                yy=y+(0,.012,.030,.055)[j]
                zz=z+(0,.007*(k+1),-.003,.004)[j]+edge*(.0007,.0022,.0015,.0005)[j]
                hit=tree.ray_cast(Vector((side*.6,yy,zz)),Vector((-side,0,0)),.6)
                assert hit[0] is not None,(side,yy,zz)
                point=hit[0]+hit[1]*.0015
                verts.append(point)
                nearest=kdt.find(hit[0])[1]
                weights.append([(body.vertex_groups[g.group].name,g.weight) for g in body.data.vertices[nearest].groups])
        for j in range(3):
            f=[start+2*j,start+2*j+1,start+2*j+3,start+2*j+2]
            normal=(verts[f[1]]-verts[f[0]]).cross(verts[f[2]]-verts[f[0]])
            if normal.x*side<0:f.reverse()
            faces.append(f)
me=bpy.data.meshes.new('ThroatFissures');me.from_pydata(verts,[],faces);me.update()
fissures=bpy.data.objects.new('ThroatFissures',me);sc.collection.objects.link(fissures)
me.materials.append(crack)
for i,groups in enumerate(weights):
    for name,w in groups:
        vg=fissures.vertex_groups.get(name) or fissures.vertex_groups.new(name=name)
        vg.add([i],w,'REPLACE')
fissures.parent=rig
mod=fissures.modifiers.new('Rig','ARMATURE');mod.object=rig
bpy.ops.object.select_all(action='DESELECT');body.select_set(True);fissures.select_set(True)
bpy.context.view_layer.objects.active=body;bpy.ops.object.join()

# A separate animated bone exposes more of the hot inner mouth during a bite, without an emission texture.
bpy.context.view_layer.objects.active=rig
bpy.ops.object.select_all(action='DESELECT')
rig.select_set(True)
bpy.ops.object.mode_set(mode='EDIT')
maw=rig.data.edit_bones.new('MawGlow')
maw.head=(0,-1.09,.755)
maw.tail=(0,-1.14,.755)
maw.parent=rig.data.edit_bones['Head']
socket=rig.data.edit_bones.new('Socket_Bite')
socket.head=(0,-1.23,.75)
socket.tail=(0,-1.28,.75)
socket.parent=rig.data.edit_bones['Head']
socket.use_deform=False
bpy.ops.object.mode_set(mode='OBJECT')
bpy.ops.mesh.primitive_uv_sphere_add(segments=12,ring_count=6,location=(0,-1.09,.755))
emitter=bpy.context.object
emitter.name='Maw'
emitter.scale=(.030,.067,.013)
bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
emitter.data.materials.append(glow)
emitter.vertex_groups.new(name='MawGlow').add(list(range(len(emitter.data.vertices))),1,'REPLACE')
emitter.parent=rig
mod=emitter.modifiers.new('Rig','ARMATURE')
mod.object=rig
for p in emitter.data.polygons: p.use_smooth=True
bpy.ops.object.select_all(action='DESELECT')
body.select_set(True)
emitter.select_set(True)
bpy.context.view_layer.objects.active=body
bpy.ops.object.join()

for action in bpy.data.actions:
    rig.animation_data.action=action
    if action.slots: rig.animation_data.action_slot=action.slots[0]
    bone=rig.pose.bones['MawGlow']
    end=round(action.frame_range[1])
    for frame in range(end+1):
        t=frame/sc.render.fps
        gain=1.
        if action.name=='Bite': gain=1+1.8*math.exp(-((t-.64)/.18)**2)
        elif action.name=='Pounce': gain=1+1.8*math.exp(-((t-.47)/.12)**2)
        elif action.name=='Death': gain=max(.12,1-t/1.15)
        elif action.name=='Dead': gain=.12
        bone.scale=(1,1,gain)
        bone.keyframe_insert('scale',frame=frame)
rig.animation_data.action=None
for pb in rig.pose.bones: pb.matrix_basis.identity()
bpy.context.view_layer.update()

attachments={}
def mesh_object(name,verts,faces,mat,bone):
    me=bpy.data.meshes.new(name)
    me.from_pydata(verts,[],faces)
    me.update()
    bm=bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    bm.to_mesh(me)
    bm.free()
    obj=bpy.data.objects.new(name,me)
    sc.collection.objects.link(obj)
    me.materials.append(mat)
    attachments.setdefault(name,{'bone':bone,'objects':[]})['objects'].append(obj)
    return obj

def band(name,rx,rz,width,thickness,mat):
    # Measured neck cross-section; the band is thin so head turns clear its front rim.
    center=Vector((0,-.757,.829))
    axis=Vector((0,-1,.10)).normalized()
    up=Vector((0,.10,1)).normalized()
    verts=[]
    n=20
    for rdelta,along in [(0,-width/2),(0,width/2),(thickness,-width/2),(thickness,width/2)]:
        for i in range(n):
            a=2*math.pi*i/n
            verts.append(tuple(center+axis*along+Vector((math.cos(a)*(rx+rdelta),0,0))+
                               up*(math.sin(a)*(rz+rdelta))))
    faces=[]
    for i in range(n):
        j=(i+1)%n
        faces.extend([(i,j,n+j,n+i),(2*n+i,3*n+i,3*n+j,2*n+j),
                      (i,2*n+i,2*n+j,j),(n+i,n+j,3*n+j,3*n+i)])
    return mesh_object(name,verts,faces,mat,'Neck1')

band('collar_ab',.139,.158,.055,.018,resin)
band('collar_c',.143,.166,.095,.032,resin)

def plate(name,center,length,width,height,bone,angle=0):
    # Broad six-sided resin plates with a low ridge; no ornamental microgeometry.
    c=Vector(center)
    outline=[(-.5,-.32),(-.42,.4),(0,.55),(.42,.4),(.5,-.32),(0,-.55)]
    rot=Matrix.Rotation(angle,3,'Y')
    verts=[tuple(c+rot@Vector((x*width,y*length,z))) for z in [-.014,0]
           for x,y in outline]
    verts.append(tuple(c+rot@Vector((0,0,height))))
    faces=[tuple(range(5,-1,-1))]
    for i in range(6):
        j=(i+1)%6
        faces.extend([(i,j,6+j,6+i),(6+i,6+j,12)])
    return mesh_object(name,verts,faces,resin,bone)

for side in [-1,1]:
    plate('shoulders', (side*.17,-.56,.875),.23,.15,.030,'Spine3',side*.7)
for name,bone,y,z,length,width in [('back_front','Spine3',-.43,.911,.24,.23),
                                  ('back_mid','Spine2',-.20,.850,.23,.19),
                                  ('back_rear','Spine1',.04,.817,.22,.21)]:
    plate(name,(0,y,z),length,width,.047,bone)
for i in range(8):
    a=2*math.pi*i/8
    plate('collar_c',(math.cos(a)*.163,-.767,.829+math.sin(a)*.187),.13,.10,.025,
          'Neck1',math.pi/2-a)

# Broken tether ring: a closed tube along a 290-degree arc, capped at both broken ends.
for collar in ['collar_ab','collar_c']:
    verts=[];faces=[]
    n=12;k=6
    for i in range(n+1):
        a=math.radians(35+290*i/n)
        center=Vector((.17,-.768+.043*math.cos(a),.710+.043*math.sin(a)))
        for j in range(k):
            b=2*math.pi*j/k
            verts.append(tuple(center+Vector((.009*math.cos(b),.009*math.sin(b)*math.cos(a),
                                               .009*math.sin(b)*math.sin(a)))))
    for i in range(n):
        for j in range(k):
            q=(j+1)%k
            faces.append((i*k+j,i*k+q,(i+1)*k+q,(i+1)*k+j))
    faces.extend([tuple(range(k-1,-1,-1)),tuple(n*k+j for j in range(k))])
    mesh_object(collar,verts,faces,iron,'Neck1')

(PROJECT/'work/attachments_raw').mkdir(exist_ok=True)
info={}
for name,entry in attachments.items():
    objs=entry['objects']
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs: o.select_set(True)
    bpy.context.view_layer.objects.active=objs[0]
    if len(objs)>1: bpy.ops.object.join()
    obj=bpy.context.object
    obj.name='Hound_'+name
    obj.data.calc_loop_triangles()
    info[name]={'bone':entry['bone'],'triangles':len(obj.data.loop_triangles)}
    lods=[]
    if name.startswith('collar'):
        for level,ratio in enumerate((.5,.25,.125),1):
            lod=obj.copy();lod.data=obj.data.copy();lod.name=obj.name+f'_LOD{level}'
            sc.collection.objects.link(lod)
            bpy.context.view_layer.objects.active=lod
            dec=lod.modifiers.new('LOD','DECIMATE');dec.ratio=ratio;dec.use_collapse_triangulate=True
            bpy.ops.object.modifier_apply(modifier=dec.name)
            lod.select_set(True);lods.append(lod)
    bpy.context.view_layer.objects.active=obj
    bpy.ops.export_scene.gltf(filepath=str(PROJECT/f'work/attachments_raw/hes_hound_{name}.glb'),
        use_selection=True,export_format='GLB',export_yup=True,export_animations=False,export_skins=False)
    for lod in lods: bpy.data.objects.remove(lod,do_unlink=True)
    # Keep the review copy bone-parented with its world-space rest appearance.
    world=obj.matrix_world.copy()
    obj.parent=rig
    obj.parent_type='BONE'
    obj.parent_bone=entry['bone']
    obj.matrix_world=world
(PROJECT/'work/attachments.json').write_text(json.dumps(info,indent=2)+'\n')
rig.animation_data.action=bpy.data.actions['Standing']
sc.frame_set(0)
bpy.ops.wm.save_as_mainfile(filepath=str(PROJECT/'work/assembled.blend'))
bpy.ops.object.select_all(action='DESELECT')
body.select_set(True)
rig.select_set(True)
bpy.context.view_layer.objects.active=rig
bpy.ops.export_scene.gltf(filepath=str(PROJECT/'export/hes_hound_raw.glb'),use_selection=True,
    export_format='GLB',export_yup=True,export_animations=True,export_animation_mode='ACTIONS',
    export_force_sampling=True,export_frame_step=1,export_skins=True,export_all_influences=False,
    export_attributes=False,export_morph=False,export_reset_pose_bones=True,export_anim_slide_to_zero=True)
print('ASSEMBLED',info,flush=True)
sys.stdout.flush()
sys.stderr.flush()
os._exit(0)
