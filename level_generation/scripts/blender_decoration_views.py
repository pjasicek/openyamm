"""Extension of blender_reference_view.py; runs in its prepared native study scene.

First native sprite frame, native scale and bottom anchor, camera-facing as in runtime.
Camera-overlay labels highlight actual source entity positions, not invented decoration.
Inspection lighting and static initial-state art; no actor, animation or runtime-light claim.
"""
import math
import bmesh
from bpy_extras.object_utils import world_to_camera_view

report=json.loads((evidencePath/(MAP+'_decorations.json')).read_text())
config_path=root/'level_generation/decoration_views.json'
config=json.loads(config_path.read_text()) if config_path.exists() else {}
views=config.get(WORLD+'/'+MAP, [])
visible=[e for e in report['records'] if e['visible'] and 'preview' in e]
if not views:
    if KIND=='indoor':
        views=[dict(name='room',target=list(center*128),span=min(extent*128,6500))]
        if visible:
            point=min(visible,key=lambda e:(Vector(e['position'])-center*128).length)
            views[0]['target']=point['position']
        else:
            floors=[f for f in payload['faces'] if f['facet_type']==3 and len(f['vertex_indices'])>=3]
            if floors:
                def floor_area(face):
                    v=[Vector(sourceVertices[i]) for i in face['vertex_indices']]
                    return sum((v[i]-v[0]).cross(v[i+1]-v[0]).length for i in range(1,len(v)-1))
                floor=max(floors,key=floor_area)
                points=[Vector(sourceVertices[i])*128 for i in floor['vertex_indices']]
                views[0]['target']=list(sum(points,Vector())/len(points)+Vector((0,0,128)))
    else:
        models=report['models']
        centers=[(Vector(m['bounds'][0])+Vector(m['bounds'][1]))/2 for m in models
                 if m['events'] and max(m['bounds'][1][i]-m['bounds'][0][i] for i in (0,1))<5000]
        if centers:
            target=max(centers,key=lambda c:sum((c-v).length<5000 for v in centers))
        else:
            target=center*128
        views=[dict(name='settlement',target=list(target),span=12500)]
        rural=[e for e in visible if e.get('nearest_bmodel_xy',0)>2000]
        if rural:
            point=min(rural,key=lambda e:abs(e['position'][0])+abs(e['position'][1]))
            views.append(dict(name='landscape',target=point['position'],span=13000))

scene.render.engine='CYCLES';scene.cycles.samples=12
scene.cycles.transparent_max_bounces=16
scene.render.resolution_x=1440;scene.render.resolution_y=1080
scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
sys.path.insert(0,str(root/'level_generation/scripts'))
from blender_native_decorations import add_billboards
billboards=add_billboards(scene,visible,root)
annotations=bpy.data.collections.new('Inspection annotations '+MAP)
scene.collection.children.link(annotations)

annotation_mat=bpy.data.materials.new('Inspection yellow');annotation_mat.use_nodes=True
nodes=annotation_mat.node_tree.nodes;nodes.clear()
out=nodes.new('ShaderNodeOutputMaterial');emission=nodes.new('ShaderNodeEmission')
emission.inputs['Color'].default_value=(1,.75,.03,1)
annotation_mat.node_tree.links.new(emission.outputs[0],out.inputs[0])


def overlay_text(body,x,y,size):
    curve=bpy.data.curves.new('Study label','FONT');curve.body=body;curve.size=size
    curve.materials.append(annotation_mat)
    obj=bpy.data.objects.new('Study label '+body,curve);annotations.objects.link(obj)
    obj.rotation_euler=camera.rotation_euler
    obj.location=camera.matrix_world@Vector((x,y,-10))
    return obj


metadata=[]
original_meshes={obj:obj.data for obj in sourceCollection.objects if obj.type=='MESH'}
for view in views:
    for obj in list(annotations.objects):bpy.data.objects.remove(obj,do_unlink=True)
    target=Vector(view['target'])/128;span=view['span']/128
    cut_z=view.get('cut_z',view['target'][2]+512) if KIND=='indoor' else None
    if cut_z is not None:
        for obj,original in original_meshes.items():
            previous=obj.data;obj.data=original.copy()
            if previous!=original and previous.users==0:bpy.data.meshes.remove(previous)
            bm=bmesh.new();bm.from_mesh(obj.data)
            bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),
                plane_co=(0,0,cut_z/128),plane_no=(0,0,1),clear_outer=True,dist=.0001)
            bm.to_mesh(obj.data);bm.free();obj.data.update()
        for obj in billboards:obj.hide_render=obj.location.z>cut_z/128
    direction=Vector(view.get('direction',[.45,-.9,1.1])).normalized()
    camera.location=target+direction*span*1.5
    camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler()
    camera.data.type='ORTHO';camera.data.ortho_scale=span
    camera.data.clip_start=.01;camera.data.clip_end=max(span*20,5000)
    for obj in billboards:obj.rotation_euler=camera.rotation_euler
    bpy.context.view_layer.update()
    half_w=span/2;half_h=span*scene.render.resolution_y/scene.render.resolution_x/2
    overlay_text(WORLD+'/'+MAP+' | '+view['name']+' | native decoration study',-half_w*.96,half_h*.90,span*.016)
    if cut_z is not None:
        overlay_text('Section: geometry above Z=%d omitted'%cut_z,-half_w*.96,half_h*.83,span*.010)
    overlay_text('First sprite frame; study light; no actors. Labels = source entity index / asset.',
                 -half_w*.96,-half_h*.94,span*.010)
    candidates=[]
    for e in visible:
        point=Vector(e['position'])/128
        # Do not label a source anchor hidden behind a wall in this cutaway.
        height=e['preview']['pixels'][1]*e['preview']['scale']/128
        visible_probe=None
        for fraction in [.85,.5,.15]:
            probe=point+(camera.rotation_euler.to_quaternion()@Vector((0,height*fraction,0)))
            ray_origin=probe+direction*span*4
            hit,location,normal,index,obj,matrix=scene.ray_cast(
                bpy.context.evaluated_depsgraph_get(),ray_origin,-direction,distance=span*4+.1)
            if hit and obj.name.startswith('Native decor #%d '%e['index']):
                visible_probe=probe;break
        if visible_probe is None:
            continue
        projected=world_to_camera_view(scene,camera,visible_probe)
        if .12<projected.x<.85 and .15<projected.y<.8 and (point-target).length<span*.45:
            candidates.append((e,projected,(point-target).length))
    chosen=[]
    for category in ['trees','plants','rocks','lights','props']:
        matches=sorted([c for c in candidates if c[0]['category']==category],key=lambda c:c[2])
        for candidate in matches:
            if all(math.hypot(candidate[1].x-c[1].x,candidate[1].y-c[1].y)>.13 for c in chosen):
                chosen.append(candidate);break
    if len(chosen)<2:
        for candidate in sorted(candidates,key=lambda c:c[2]):
            if len(chosen)>=3:break
            if all(math.hypot(candidate[1].x-c[1].x,candidate[1].y-c[1].y)>.15 for c in chosen):
                chosen.append(candidate)
    for e,projected,distance in chosen:
        x=(projected.x-.5)*span;y=(projected.y-.5)*half_h*2
        overlay_text('+',x-span*.004,y-span*.004,span*.014)
        overlay_text('#%d %s'%(e['index'],e['name']),x+span*.008,y+span*.014,span*.011)
    if not visible:
        overlay_text('No initially visible native decoration sprites in this map.',
                     -half_w*.9,-half_h*.82,span*.014)
    path=evidencePath/(MAP+'_decor_'+view['name']+'.png')
    scene.render.filepath=str(path);bpy.ops.render.render(write_still=True)
    metadata.append(dict(view=view,section_top_z=cut_z,image=str(path.relative_to(root)),
                         camera_position=list(camera.location*128),
                         highlighted=[dict(index=e['index'],name=e['name'],position=e['position'])
                                      for e,_,_ in chosen]))
(evidencePath/(MAP+'_decor_views.json')).write_text(json.dumps(dict(
    views=metadata,missing_sprites=report['missing_sprites'],
    limitations='Native static geometry/initial decoration first frames, decoded palette and alpha; neutral study lighting, '
                'no actors, scripted changes, emitter particles or dynamic light validation. Labels mark source anchors; '
                'they may identify a sprite partly occluded by geometry. Not a gameplay screenshot.'),indent=2)+'\n')
print('Decoration views complete:',WORLD,MAP,len(views),'native sprites',len(visible))
