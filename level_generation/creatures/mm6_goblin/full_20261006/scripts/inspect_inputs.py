"""Owned, read-only source ingestion into disposable review scenes; originals are never saved."""
import bpy, bmesh, json, math
from pathlib import Path
from mathutils import Vector, Matrix

PROJECT=Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm6_goblin')
OUT=PROJECT/'full_20261006'
state=json.loads((PROJECT/'stage1_20261006/creature_3d_progress.json').read_text())
inputs=[]
if not (OUT/'review/sword_candidate/inspection.json').exists():
    inputs.append(('sword_candidate',PROJECT/'meshy_restart_20260923/sword_attack_01/corsair_goblin_sword.glb'))
job=state['meshy']['jobs'].get('body_geometry_v2_network',{})
if 'model_urls_glb' in job.get('downloads',{}) and not (OUT/'review/body_raw/inspection.json').exists():
    inputs.append(('body_raw',PROJECT/job['downloads']['model_urls_glb']['path']))
if (OUT/'work/body_for_rig_v1.glb').exists():
    inputs.append(('body_corrected',OUT/'work/body_for_rig_v1.glb'))

for label,path in inputs:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(path))
    meshes=[o for o in bpy.context.scene.objects if o.type=='MESH']
    assert meshes, 'Empty source import'
    report={'source':str(path.relative_to(PROJECT)),'objects':[],'scene_scale':bpy.context.scene.unit_settings.scale_length}
    for o in meshes:
        bm=bmesh.new();bm.from_mesh(o.data)
        report['objects'].append({'name':o.name,'vertices':len(o.data.vertices),'triangles':sum(len(p.vertices)-2 for p in o.data.polygons),
           'materials':[m.name if m else None for m in o.data.materials],'uv_layers':[u.name for u in o.data.uv_layers],
           'boundary_edges':sum(e.is_boundary for e in bm.edges),'nonmanifold_edges':sum(not e.is_manifold for e in bm.edges),
           'loose_vertices':sum(not v.link_faces for v in bm.verts),'tiny_faces':sum(f.calc_area()<1e-12 for f in bm.faces),
           'matrix_world':[list(row) for row in o.matrix_world]})
        bm.free()
    if label=='sword_candidate':
        for o in meshes:o.matrix_world=Matrix.Rotation(math.pi/2,4,'X')@o.matrix_world
    bounds=[o.matrix_world@Vector(c) for o in meshes for c in o.bound_box]
    lo=Vector([min(v[a] for v in bounds) for a in range(3)]);hi=Vector([max(v[a] for v in bounds) for a in range(3)])
    report['review_bounds']={'min':list(lo),'max':list(hi)}
    height=max(hi.z-lo.z,.01);target=Vector(((lo.x+hi.x)/2,(lo.y+hi.y)/2,(lo.z+hi.z)/2))
    scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=12;scene.cycles.use_denoising=True
    scene.render.resolution_x=600;scene.render.resolution_y=800;scene.render.resolution_percentage=100
    scene.world=bpy.data.worlds.new('Neutral review world');scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.24,.24,.24,1)
    scene.world.node_tree.nodes['Background'].inputs[1].default_value=.7
    scene.view_settings.view_transform='Standard';scene.view_settings.look='None'
    for name,pos,power,size in [('key',(2,-3,3),350,2.5),('fill',(-3,-1,2),180,3),('rim',(1,3,2.5),220,2)]:
        light=bpy.data.lights.new(name,'AREA');light.energy=power*height*height;light.shape='DISK';light.size=size*height
        obj=bpy.data.objects.new(name,light);scene.collection.objects.link(obj);obj.location=target+Vector(pos)*height
        obj.rotation_euler=(target-obj.location).to_track_quat('-Z','Y').to_euler()
    camera=bpy.data.objects.new('Review camera',bpy.data.cameras.new('Review camera'));scene.collection.objects.link(camera);scene.camera=camera;camera.data.type='ORTHO';camera.data.ortho_scale=height*1.20
    directory=OUT/'review'/label;directory.mkdir(parents=True,exist_ok=True)
    clay=bpy.data.materials.new('Neutral clay');clay.diffuse_color=(.44,.48,.45,1);clay.use_nodes=True
    clay.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(.44,.48,.45,1);clay.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=.8
    for view,offset in [('front',(0,-3,0)),('right',(-3,0,0)),('back',(0,3,0)),('quarter',(-2,-3,.15))]:
        camera.location=target+Vector(offset)*height;camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler()
        if label.startswith('body_'):scene.view_layers[0].material_override=clay
        scene.render.filepath=str(directory/(view+'.png'));bpy.ops.render.render(write_still=True)
    (directory/'inspection.json').write_text(json.dumps(report,indent=2)+'\n')
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'work'/(label+'_inspection.blend')))
    print(label, 'reviewed structure',sum(o['triangles'] for o in report['objects']),'triangles',flush=True)
