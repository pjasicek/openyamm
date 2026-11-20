"""Inspect the immutable Meshy rig/stock returns in isolated scenes."""
import bpy, json, math
from pathlib import Path
from mathutils import Vector
from mathutils.kdtree import KDTree

ROOT=Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm6_goblin')
OUT=ROOT/'full_20261006'
JOBS=ROOT/'meshy/body_rig_v1'

def vertices():
    return [o.matrix_world@v.co for o in bpy.context.scene.objects if o.type=='MESH' for v in o.data.vertices]

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(OUT/'work/body_for_rig_v1.glb'))
reference=vertices()
tree=KDTree(len(reference))
for i,v in enumerate(reference):tree.insert(v,i)
tree.balance()
report={}
for label,filename in [('rig','result_rigged_character_glb_url.glb'),('stock_walk','result_basic_animations_walking_glb_url.glb'),('stock_run','result_basic_animations_running_glb_url.glb')]:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(JOBS/filename))
    meshes=[o for o in bpy.context.scene.objects if o.type=='MESH'];arms=[o for o in bpy.context.scene.objects if o.type=='ARMATURE'];assert len(arms)==1
    arm=arms[0]
    record={'source':str((JOBS/filename).relative_to(ROOT)),'armature':arm.name,'matrix_world':[list(r) for r in arm.matrix_world],
      'bones':{b.name:{'head':list(b.head_local),'tail':list(b.tail_local),'parent':b.parent.name if b.parent else None,'length':b.length,'matrix':[list(r) for r in b.matrix_local]} for b in arm.data.bones},
      'actions':[{'name':a.name,'frame_range':list(a.frame_range),'slots':[s.identifier for s in a.slots]} for a in bpy.data.actions],'meshes':[]}
    for o in meshes:
        sums=[sum(g.weight for g in v.groups if o.vertex_groups[g.group].name in arm.data.bones) for v in o.data.vertices]
        counts=[sum(g.weight>1e-5 and o.vertex_groups[g.group].name in arm.data.bones for g in v.groups) for v in o.data.vertices]
        record['meshes'].append({'name':o.name,'vertices':len(o.data.vertices),'triangles':sum(len(p.vertices)-2 for p in o.data.polygons),'groups':[g.name for g in o.vertex_groups],
          'uv_layers':[u.name for u in o.data.uv_layers],'matrix_world':[list(r) for r in o.matrix_world],'max_influences':max(counts),'unweighted':sum(s<1e-5 for s in sums),'max_weight_sum_error':max(abs(s-1) for s in sums)})
    if label=='rig':
        points=vertices();distances=[tree.find(v)[2] for v in points]
        reverse=KDTree(len(points))
        for i,v in enumerate(points):reverse.insert(v,i)
        reverse.balance()
        record['static_geometry_parity']={'max_return_to_input_m':max(distances),'max_input_to_return_m':max(reverse.find(v)[2] for v in reference),'mean_return_to_input_m':sum(distances)/len(distances)}
    scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=8;scene.cycles.use_denoising=True
    scene.render.resolution_x=480;scene.render.resolution_y=640;scene.render.resolution_percentage=100
    scene.world=bpy.data.worlds.new('Neutral rig review');scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.22,.22,.22,1);scene.world.node_tree.nodes['Background'].inputs[1].default_value=.7
    scene.view_settings.view_transform='Standard';scene.view_settings.look='None'
    target=Vector((0,0,.825))
    for name,pos,power,size in [('key',(3,-4,4),850,4),('fill',(-4,-2,2),450,4),('rim',(2,4,3),550,3)]:
        light=bpy.data.lights.new(name,'AREA');light.energy=power;light.size=size;obj=bpy.data.objects.new(name,light);scene.collection.objects.link(obj);obj.location=Vector(pos);obj.rotation_euler=(target-obj.location).to_track_quat('-Z','Y').to_euler()
    camera=bpy.data.objects.new('Rig review camera',bpy.data.cameras.new('Rig review camera'));scene.collection.objects.link(camera);scene.camera=camera;camera.data.type='ORTHO';camera.data.ortho_scale=1.98
    clay=bpy.data.materials.new('Rig neutral clay');clay.use_nodes=True;clay.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(.44,.48,.45,1);clay.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=.8;scene.view_layers[0].material_override=clay
    directory=OUT/'review'/label;directory.mkdir(parents=True,exist_ok=True)
    action=arm.animation_data.action if arm.animation_data else None
    frames=[1] if label=='rig' else [action.frame_range[0]+(action.frame_range[1]-action.frame_range[0])*t for t in (0,.25,.5,.75)]
    for i,f in enumerate(frames):
        scene.frame_set(int(f),subframe=f-int(f))
        for view,offset in [('front',(0,-5,0)),('right',(-5,0,0))]:
            camera.location=target+Vector(offset);camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(directory/f'{i:02d}_{view}.png');bpy.ops.render.render(write_still=True)
    if label=='rig':
        for side,sign in [('R',-1),('L',1)]:
            wrist=next((arm.matrix_world@b.head for b in arm.pose.bones if b.name.endswith(('RightHand' if side=='R' else 'LeftHand'))),Vector((sign*.6,0,.73)))
            center=wrist+Vector((sign*.025,0,-.07));camera.data.ortho_scale=.37
            for view,offset in [('front',(0,-2,0)),('back',(0,2,0))]:
                camera.location=center+Vector(offset);camera.rotation_euler=(center-camera.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(directory/f'hand_{side}_{view}.png');bpy.ops.render.render(write_still=True)
    (directory/'inspection.json').write_text(json.dumps(record,indent=2)+'\n')
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'work'/f'{label}_import.blend'))
    report[label]=record
    print(label,len(arm.data.bones),'bones',record['meshes'],flush=True)
(OUT/'review/rig_inspection.json').write_text(json.dumps(report,indent=2)+'\n')
