"""Keep accepted cloth/leg contact surfaces exactly; render each selected switch distance."""
import bpy,bmesh,sys,math,json,subprocess,os
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];R=P/'review/triangle_reduction';W=P/'work/round1'
sys.dont_write_bytecode=True
selected=json.loads((R/'selected.json').read_text());camera=json.loads((R/'camera.json').read_text());restored=[]
KEEP={3,4,7,8,16,17,20,21,26,27,28,30,31,35}
for row in selected['levels']:
    if row['level']!=2:continue
    level=row['level'];bpy.ops.wm.open_mainfile(filepath=str(P/row['blend']))
    sc=bpy.context.scene;body=bpy.data.objects['Body'];rig=bpy.data.objects['Rig']
    with bpy.data.libraries.load(str(R/'baseline/work/rig_textured.blend'),link=False) as (a,b):b.objects=['Body']
    original=b.objects[0];sc.collection.objects.link(original)
    original.modifiers.clear();original.hide_render=True
    bpy.ops.object.select_all(action='DESELECT');body.select_set(True);bpy.context.view_layer.objects.active=body
    group=body.vertex_groups['ReductionAllowed'];pid=body.data.attributes['piece']
    group.add([v.index for v in body.data.vertices if pid.data[v.index].value in KEEP],0,'REPLACE')
    mod=body.modifiers.new('NextMeasuredStep','DECIMATE');mod.ratio=.93;mod.use_collapse_triangulate=True
    mod.vertex_group=group.name;mod.vertex_group_factor=.0001
    bpy.ops.object.modifier_move_up(modifier=mod.name);bpy.ops.object.modifier_apply(modifier=mod.name)
    mod=body.modifiers.new('OriginalNormals','DATA_TRANSFER');mod.object=original;mod.use_loop_data=True
    mod.data_types_loops={'CUSTOM_NORMAL'};mod.loop_mapping='POLYINTERP_NEAREST'
    bpy.ops.object.modifier_move_up(modifier=mod.name);bpy.ops.object.modifier_apply(modifier=mod.name)
    changed=body.data.validate(verbose=True,clean_customdata=False);body.data.update()
    # Mesh.validate repairs stale derived edge flags left by the decimator; faces and UVs are retained.
    for ob in list(bpy.data.objects):
        if ob not in (body,rig):bpy.data.objects.remove(ob,do_unlink=True)
    names={b.name for b in rig.data.bones}
    for v in body.data.vertices:
        weights=[w.weight for w in v.groups if body.vertex_groups[w.group].name in names and w.weight>1e-7]
        assert len(weights)==1 and abs(weights[0]-1)<1e-6
    rig.animation_data.action=bpy.data.actions['Standing'];rig.animation_data.action_slot=rig.animation_data.action.slots[0];sc.frame_set(0)
    for slot,label in enumerate(['lch','lch_head']):
        mat=body.data.materials[slot];mat.use_nodes=True;nt=mat.node_tree
        tex=nt.nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(P/f'textures/{label}_basecolor_1k.png'));nt.nodes.active=tex
    sc.render.engine='BLENDER_WORKBENCH';sc.display.shading.light='STUDIO';sc.display.shading.color_type='TEXTURE'
    sc.display.shading.show_cavity=False;sc.display.shading.show_shadows=False;sc.render.film_transparent=True
    sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA'
    sc.render.resolution_x=sc.render.resolution_y=960;sc.render.resolution_percentage=100;sc.display.render_aa='32';sc.view_settings.view_transform='Standard'
    camdata=bpy.data.cameras.new('Round1Camera');camdata.type='PERSP';camdata.lens_unit='FOV';camdata.angle=math.radians(35)
    cam=bpy.data.objects.new('Round1Camera',camdata);sc.collection.objects.link(cam);sc.camera=cam
    row['pre_contact_restore_blend']=row['blend'];row['blend']=f'work/round1/lod{level}_chain_fit.blend'
    row['pre_contact_restore_triangles']=row['triangles'];row['triangles']=sum(len(f.vertices)-2 for f in body.data.polygons)
    row['mesh_validate_repaired']=changed;row['restored_original_pieces']=sorted(KEEP)
    bpy.ops.wm.save_as_mainfile(filepath=str(P/row['blend']))
    dest=R/f'chain_fit/lod{level}';dest.mkdir(parents=True,exist_ok=True)
    tmp=body.copy();tmp.data=body.data.copy();sc.collection.objects.link(tmp);body.hide_render=True
    head=tmp.data.attributes['head'];uv=tmp.data.uv_layers['UVMap'];huv=tmp.data.uv_layers['HeadUV']
    for face in tmp.data.polygons:
        if head.data[face.index].value:
            for li in face.loop_indices:uv.data[li].uv=huv.data[li].uv
    tmp.data.uv_layers.active=uv
    for k in range(8):
        angle=k*math.pi/4;target=Vector((0,.15,.9));cam.location=target+Vector((math.sin(angle),-math.cos(angle),0))*camera['distance_m'][level]
        cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();sc.render.filepath=str(dest/f'{k}.png');bpy.ops.render.render(write_still=True)
    env=dict(os.environ,LCH_IOU_AGGREGATION='pooled')
    subprocess.run(['/usr/bin/python3',str(P/'scripts/round1_metrics.py'),str(dest),str(R/f'pooled/step_00/lod{level}')],check=True,env=env)
    row['render']=str(dest.relative_to(P));row['metrics']=json.loads((dest/'metrics.json').read_text())
    print('RESTORED_CONTACTS',level,row['triangles'],row['metrics']['min_iou'],row['metrics']['min_ssim'],flush=True)
    restored.append(row)
selected['levels']=restored;(R/'chain_fit.json').write_text(json.dumps(selected,indent=2)+'\n')
