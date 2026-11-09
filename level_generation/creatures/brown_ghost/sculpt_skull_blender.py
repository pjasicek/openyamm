"""Carve a connected anatomical skull volume from the AI-restored/native sprite references."""
import bpy
import bmesh
import math
import json
from math import atan2, pi
from mathutils import Vector
from pathlib import Path
ROOT=Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/brown_ghost')
NAME='Ghost connected skull sculpt'
old=bpy.data.scenes.get(NAME)
scene=bpy.data.scenes.new(NAME+' rebuild')
bpy.context.window.scene=scene
if old:
    for obj in list(old.objects):bpy.data.objects.remove(obj,do_unlink=True)
    bpy.data.scenes.remove(old)
scene.name=NAME
parts=[]
def ellipsoid(name,position,size,rotation=(0,0,0),collect=True):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32,ring_count=24,location=position)
    obj=bpy.context.object;obj.name=name;obj.scale=size;obj.rotation_euler=rotation
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    if collect:parts.append(obj)
    return obj

def link(a,b,radius):
    a,b=Vector(a),Vector(b)
    bpy.ops.mesh.primitive_cylinder_add(vertices=16,radius=radius,depth=(b-a).length,location=(a+b)/2)
    obj=bpy.context.object;obj.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();parts.append(obj)
    ellipsoid('Mandible joint',a,(radius,radius,radius))

def join(objects,name):
    bpy.ops.object.select_all(action='DESELECT')
    for obj in objects:obj.select_set(True)
    bpy.context.view_layer.objects.active=objects[0]
    bpy.ops.object.join();obj=bpy.context.object;obj.name=name
    bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
    return obj

# A continuous cranial/maxillary envelope avoids a stack of bulbous facial primitives.
sections=[(-.122,.060,-.120,.015),(-.085,.072,-.134,.063),(-.035,.108,-.125,.115),
          (.025,.130,-.132,.145),(.09,.130,-.140,.155),(.16,.120,-.126,.136),
          (.205,.092,-.088,.102),(.242,.048,-.037,.054),(.255,.002,.005,.007)]
verts=[];faces=[];count=64
for z,radius,front,back in sections:
    center=(front+back)/2
    for j in range(count):
        a=2*pi*j/count;c=math.cos(a);x=radius*math.sin(a)
        y=center-(center-front)*c**.55 if c>=0 else center+(back-center)*(-c)**.85
        # Gentle anatomical brow relief is part of the same surface.
        y-=.009*math.exp(-((z-.10)/.035)**2)*math.exp(-((abs(x)-.063)/.05)**2)*max(0,c)
        verts.append((x,y,z))
for row in range(len(sections)-1):
    for j in range(count):
        k=row*count+j;q=row*count+(j+1)%count
        faces.append((k,q,q+count,k+count))
faces.append(tuple(reversed(range(count))));faces.append(tuple((len(sections)-1)*count+j for j in range(count)))
mesh=bpy.data.meshes.new('Continuous skull envelope');mesh.from_pydata(verts,[],faces)
bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(mesh);bm.free()
volume=bpy.data.objects.new('Continuous skull envelope',mesh);scene.collection.objects.link(volume);parts.append(volume)
for side in [-1,1]:
    ellipsoid('Mandible ramus',(side*.086,-.012,-.122),(.018,.043,.094))
    link((side*.088,-.030,-.164),(side*.055,-.098,-.203),.019)
    link((side*.055,-.098,-.203),(0,-.115,-.205),.023)
ellipsoid('Intact chin',(0,-.101,-.197),(.057,.039,.026))
skull=join(parts,'Connected cranial and facial volume')
skull.data.remesh_voxel_size=.0038
bpy.ops.object.voxel_remesh()
smooth=skull.modifiers.new('Unify anatomical masses','SMOOTH');smooth.factor=.7;smooth.iterations=8
bpy.ops.object.modifier_apply(modifier=smooth.name)

def subtract(cutter):
    bpy.context.view_layer.objects.active=skull
    modifier=skull.modifiers.new('Carved anatomical cavity','BOOLEAN');modifier.operation='DIFFERENCE'
    modifier.solver='EXACT';modifier.object=cutter
    bpy.ops.object.modifier_apply(modifier=modifier.name)
    bpy.data.objects.remove(cutter,do_unlink=True)

for side in [-1,1]:
    subtract(ellipsoid('Orbital cavity',(side*.060,-.127,.050),(.041,.080,.049),
                       (0,-side*.10,0),False))
    subtract(ellipsoid('Subzygomatic hollow',(side*.105,-.088,-.073),(.025,.058,.030),collect=False))
# A triangular piriform opening, carved through connected nasal/maxillary surfaces.
outline=[(0,.006),(-.012,-.015),(-.021,-.045),(-.013,-.066),(0,-.060),(.013,-.066),(.021,-.045),(.012,-.015)]
verts=[(x,y,z) for y in [-.25,-.075] for x,z in outline]
faces=[tuple(reversed(range(8))),tuple(range(8,16))]
for i in range(8):faces.append((i,(i+1)%8,(i+1)%8+8,i+8))
mesh=bpy.data.meshes.new('Nasal aperture cutter');mesh.from_pydata(verts,[],faces)
bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(mesh);bm.free()
cutter=bpy.data.objects.new('Nasal aperture cutter',mesh);scene.collection.objects.link(cutter)
bpy.context.view_layer.objects.active=cutter
bevel=cutter.modifiers.new('Natural nasal edge','BEVEL');bevel.width=.003;bevel.segments=2
bpy.ops.object.modifier_apply(modifier=bevel.name);subtract(cutter)
# The maxillary envelope ends above the mandible, leaving the anatomical oral gap.
# Reduce the sculpt once. It is later embedded in the existing rig, not remeshed per animation frame.
bpy.context.view_layer.objects.active=skull
modifier=skull.modifiers.new('Sculpt mesh reduction','DECIMATE');modifier.ratio=.12
bpy.ops.object.modifier_apply(modifier=modifier.name)
# Small normal teeth belong in a skull; avoid an exaggerated grin or fangs.
parts=[skull]
for lower in [False,True]:
    for index in range(9):
        x=(index-4)*.012
        y=-.131+4*x*x
        z=-.172 if lower else -.132
        bpy.ops.mesh.primitive_cube_add(size=1,location=(x,y,z))
        tooth=bpy.context.object;tooth.name='Lower tooth' if lower else 'Upper tooth'
        tooth.scale=(.010,.026,.023 if lower else .030)
        bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
        bevel=tooth.modifiers.new('Tooth enamel edges','BEVEL');bevel.width=.0035;bevel.segments=2
        bpy.ops.object.modifier_apply(modifier=bevel.name);parts.append(tooth)
skull=join(parts,'Intact skull with carved sockets and normal dentition')
# Tooth identity must survive joining; spatial mouth bounds also intersect the lower enamel.
adjacency=[set() for v in skull.data.vertices]
for edge in skull.data.edges:
    a,b=edge.vertices;adjacency[a].add(b);adjacency[b].add(a)
remaining=set(range(len(adjacency)));tooth_vertices=set()
while remaining:
    seed=remaining.pop();component={seed};pending=[seed]
    while pending:
        for v in adjacency[pending.pop()] & remaining:
            remaining.remove(v);component.add(v);pending.append(v)
    if len(component)<100:tooth_vertices.update(component)
# Reuse the established material recipes for the bone and shadowed inner cavities.
module={'__name__':'skull_materials'}
exec(compile((ROOT/'author_blender.py').read_text(),'author_blender.py','exec'),module)
bone=module['material']('Sculpted aged ivory',(.15,.14,.10),(.48,.44,.31),12)
shadow=module['material']('Deep anatomical cavity',(.006,.005,.003),(.028,.022,.013),10)
skull.data.materials.clear();skull.data.materials.append(bone);skull.data.materials.append(shadow)
enamel=module['material']('Aged tooth enamel',(.19,.165,.105),(.49,.43,.285),17)
skull.data.materials.append(enamel)
uv=skull.data.uv_layers.new(name='Procedural surface UV')
profile_uv=skull.data.uv_layers.new(name='Skull profile projection')
vertices=[tuple(v.co) for v in skull.data.vertices];faces=[];materials=[];uvs=[]
for v in vertices:uvs.append(((365+1300*v[0])/1402,1-(545-1000*v[2])/1122))
profile_uvs=[((1170-850*v[1])/1402,1-(515-900*v[2])/1122) for v in vertices]
for poly in skull.data.polygons:
    x,y,z=poly.center
    orbit=any(((x-side*.060)/.043)**2+((z-.047)/.052)**2<.90 and -.125<y<-.035 for side in [-1,1])
    nose=abs(x)<.022 and -.083<z<.004 and -.15<y<-.070
    mouth=abs(x)<.070 and -.173<z<-.133 and -.145<y<-.030
    tooth=poly.vertices[0] in tooth_vertices
    poly.material_index=2 if tooth else (1 if orbit or nose or mouth else 0);poly.use_smooth=True
    faces.append(list(poly.vertices));materials.append([3,2,1][poly.material_index])
    for li in poly.loop_indices:
        vi=skull.data.loops[li].vertex_index;uv.data[li].uv=uvs[vi];profile_uv.data[li].uv=profile_uvs[vi]
(ROOT/'sculpt/skull_mesh.json').write_text(json.dumps({'vertices':vertices,'faces':faces,'uv':uvs,'profile_uv':profile_uvs,'materials':materials}))
projection_module={'__name__':'skull_projection'}
exec(compile((ROOT/'skull_projection_material.py').read_text(),'skull_projection_material.py','exec'),projection_module)
skull.data.materials[0]=projection_module['projected_skull_material'](bone)
# Close views make continuity and actual depth inspectable before adapting the whole character.
camdata=bpy.data.cameras.new('Skull detail camera');camdata.type='ORTHO';camdata.ortho_scale=.65
cam=bpy.data.objects.new('Skull detail camera',camdata);scene.collection.objects.link(cam)
cam.location=(0,-3,.045);cam.rotation_euler=(pi/2,0,0);scene.camera=cam
for name,pos,power,size in [('Key',(-1,-2,2),85,1.4),('Fill',(1,-1,.2),12,1)]:
    data=bpy.data.lights.new(name,'AREA');data.energy=power;data.size=size
    obj=bpy.data.objects.new(name,data);scene.collection.objects.link(obj);obj.location=pos
    obj.rotation_euler=(-obj.location).to_track_quat('-Z','Y').to_euler()
world=bpy.data.worlds.new('Skull detail world');world.use_nodes=True
world.node_tree.nodes.get('Background').inputs[1].default_value=.2;scene.world=world
scene.render.engine='CYCLES';scene.cycles.samples=24;scene.cycles.use_denoising=True
scene.render.film_transparent=True;scene.render.resolution_x=640;scene.render.resolution_y=640
scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGBA'
scene.view_settings.view_transform='Standard'
for angle,name in [(0,'skull_front'),(pi/3,'skull_three_quarter'),(pi/2,'skull_profile')]:
    skull.rotation_euler.z=angle;scene.render.filepath=str(ROOT/'review'/(name+'.png'))
    bpy.ops.render.render(write_still=True)
skull.rotation_euler.z=0
scene['references']='reference_restoration/skull_detail_v1.png plus native m242sa0/m242sa2'
bpy.data.libraries.write(str(ROOT/'sculpt/skull_sculpt.blend'),{scene},fake_user=True)
(ROOT/'sculpt/report.json').write_text(json.dumps({'vertices':len(vertices),'faces':len(faces),
 'method':'Voxel-unified skull volume with boolean orbital, nasal and oral cavities; separate anatomical teeth.'},indent=2)+'\n')
