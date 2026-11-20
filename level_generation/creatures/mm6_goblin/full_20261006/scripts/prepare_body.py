"""Correct confirmed raw T2 anatomy, preserve part ownership, and export provisional rig input."""
import bpy,bmesh,json,math,hashlib
from pathlib import Path
from mathutils import Vector

P=Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm6_goblin');O=P/'full_20261006'
raw=P/'meshy/body_geometry_v2_network/model_urls_glb.glb'
assert hashlib.sha256(raw.read_bytes()).hexdigest()=='8d76c97a26943c2d7e05d605f252afcc55210c92631acc9ff0439afe7eefe04f'
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(raw));source=next(o for o in bpy.context.scene.objects if o.type=='MESH')
assert len(source.data.vertices)==8230,'Unexpected source geometry; component masks would be stale'
parts=json.loads((O/'review/body_raw/components.json').read_text());objects=[]
removed={2,9,12,6,14,20,43,55,63,65} # both old hoop sets, wrong rear plate/rivets, isolated single triangle
materials={}
for name,color,metal,rough in [('skin',(.31,.34,.13),0,.78),('iron',(.14,.16,.17),.65,.55),('leather',(.20,.10,.045),0,.78),('gold',(.55,.33,.09),.7,.43),('teeth',(.70,.63,.40),0,.54),('eyes',(.30,.25,.065),0,.45)]:
    m=bpy.data.materials.new('provisional_'+name);m.use_nodes=True;m.diffuse_color=(*color,1)
    n=m.node_tree.nodes;b=n.get('Principled BSDF');b.inputs['Metallic'].default_value=metal;b.inputs['Roughness'].default_value=rough
    image=bpy.data.images.new('provisional_'+name,16,16);image.generated_color=(*color,1);image.file_format='PNG';image.pack()
    tex=n.new('ShaderNodeTexImage');tex.image=image;m.node_tree.links.new(tex.outputs['Color'],b.inputs['Base Color']);materials[name]=m

def head_shape(co):
    v=Vector(co);x,y,z=v
    if z>.320:
        w=min(1,max(0,(z-.320)/.022));v.z=.320+(z-.320)*(1+.12*w);v.x*=1+.045*w
        # Local sculpt of the existing connected skull, not a separate horn or face patch.
        if y>.045 and abs(x)<.065:
            v.y+=.043*math.exp(-((z-.435)/.030)**2)*min(1,(y-.045)/.035)
        if y<-.045 and abs(x)<.055:
            v.y-=.014*math.exp(-((z-.349)/.022)**2)*math.exp(-(x/.047)**2)
            v.y-=.004*math.exp(-((z-.424)/.015)**2)
    return v

iron_ids={4,8,11,13,16,17,29,33,34}
leather_ids={1,15,19,22,27}
gold_ids={18,26,28,30,41,58}
skin_ids={0,3,7}
for part in parts:
    i=part['id']
    if i in removed:continue
    indices=part['vertices'];mapping={old:new for new,old in enumerate(indices)};chosen=set(indices)
    verts=[head_shape(source.data.vertices[j].co) for j in indices]
    faces=[tuple(mapping[j] for j in f.vertices) for f in source.data.polygons if f.vertices[0] in chosen]
    me=bpy.data.meshes.new(f'BodyPart_{i}');me.from_pydata(verts,[],faces);me.update();obj=bpy.data.objects.new(f'BodyPart_{i}',me);bpy.context.scene.collection.objects.link(obj)
    material='skin' if i in skin_ids else 'leather' if i in leather_ids else 'gold' if i in gold_ids else 'teeth' if i in {5,23,64} else 'eyes' if i in {32,50} else 'iron'
    me.materials.append(materials[material]);obj['source_part_id']=i;obj['material_identity']=material
    group=obj.vertex_groups.new(name=f'Component_{i}');group.add(list(range(len(me.vertices))),1,'REPLACE')
    # Normals smooth on skin; retain plate and spike edges. Geometry is neither subdivided nor globally smoothed.
    for f in me.polygons:f.use_smooth=material in ['skin','leather','eyes','teeth']
    objects.append(obj)
bpy.data.objects.remove(source,do_unlink=True)
core=next(o for o in objects if o['source_part_id']==0)

for side in [-1,1]:
    outline=[(side*.030,.295),(side*.108,.282),(side*.110,.248),(side*.072,.225),(side*.025,.245)]
    verts=[]
    for x,z in outline:
        ok,hit,normal,index=core.ray_cast(Vector((x,.5,z)),Vector((0,-1,0)))
        assert ok,'Back plate has no anatomical surface beneath it'
        verts.append((x,hit.y+.006,z))
    verts+= [(x,y-.004,z) for x,y,z in verts];count=len(outline)
    faces=[tuple(range(count)),tuple(reversed(range(count,2*count)))]+[(i,(i+1)%count,(i+1)%count+count,i+count) for i in range(count)]
    me=bpy.data.meshes.new('Small rear shoulder plate');me.from_pydata(verts,[],faces);me.update()
    bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free()
    obj=bpy.data.objects.new('RearPlate_R' if side<0 else 'RearPlate_L',me);bpy.context.scene.collection.objects.link(obj);me.materials.append(materials['iron']);obj['material_identity']='iron';objects.append(obj)

for i,(x,y,z) in enumerate([(-.098,.005,.388),(-.111,.010,.402),(-.120,.014,.416)]):
    pos=head_shape((x,y,z));bpy.ops.mesh.primitive_torus_add(major_segments=16,minor_segments=6,location=pos,rotation=(0,math.pi/2,0),major_radius=.008,minor_radius=.0018)
    obj=bpy.context.object;obj.name=f'EarHoop_R_{i+1}';obj.data.materials.append(materials['gold']);obj['material_identity']='gold';objects.append(obj)

# Preserve semantic component membership through the join for later rigid-armor and cloth weighting.
for obj in objects:
    if not obj.vertex_groups:
        g=obj.vertex_groups.new(name=obj.name);g.add(list(range(len(obj.data.vertices))),1,'REPLACE')
    obj.select_set(True)
bpy.context.view_layer.objects.active=core;bpy.ops.object.join();body=bpy.context.object;body.name='GoblinBody_Corrected'
lo=min(v.co.z for v in body.data.vertices);hi=max(v.co.z for v in body.data.vertices);factor=1.65/(hi-lo)
for v in body.data.vertices:v.co=Vector((v.co.x*factor,v.co.y*factor,(v.co.z-lo)*factor))
body.data.update();bpy.context.scene.unit_settings.system='METRIC';bpy.context.scene.unit_settings.scale_length=1
# Unwrap provisional coordinates for the textured humanoid rigging requirement; final UVs follow deformation review.
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=math.radians(66),island_margin=.012);bpy.ops.object.mode_set(mode='OBJECT')
body.data.uv_layers.active.name='ProvisionalUV'
report={'source_sha256':hashlib.sha256(raw.read_bytes()).hexdigest(),'body_height_m':1.65,'vertices':len(body.data.vertices),
        'triangles':sum(len(f.vertices)-2 for f in body.data.polygons),'material_scope':'Simple embedded provisional palette textures for Meshy rigging; not final UVs/material review.',
        'coordinate_contract':'Blender Z up, forward -Y, anatomical right -X. glTF Y up, forward +Z. Source-study (+X right,+Y forward,+Z up) maps to (-X,-Y,+Z) in this Blender master.',
        'corrections':['Removed large invented rear gorget and its rivets; rebuilt two small native rear plates on underlying back surface.','Removed both generated hoop sets; exactly three hoops rebuilt only on anatomical right.','Enlarged head 12% around neck attachment, sculpted rear skull wedge and lower-jaw projection, preserving existing connected face.','Removed one isolated triangle; intentional open component boundaries retained.','Smooth skin shading without global vertex smoothing/subdivision.'],
        'part_groups':[g.name for g in body.vertex_groups],'comparison_scale':'1.65 m selected portable asset scale; runtime actor placement remains separately requested.'}
(O/'review/body_corrected').mkdir(parents=True,exist_ok=True);(O/'review/body_corrected/geometry.json').write_text(json.dumps(report,indent=2)+'\n')
bpy.ops.wm.save_as_mainfile(filepath=str(O/'work/body_corrected_v1.blend'))
bpy.ops.export_scene.gltf(filepath=str(O/'work/body_for_rig_v1.glb'),export_format='GLB',use_selection=True,export_animations=False,export_yup=True,export_image_format='AUTO')
print(json.dumps(report),flush=True)
