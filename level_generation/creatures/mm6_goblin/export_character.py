"""Create the ordinary portable character project and GLB from an inspected isolated material bake."""
import bpy
import json
import struct
from pathlib import Path
from mathutils import Vector

ROOT=Path(__file__).resolve().parent

def build():
    manifest=json.loads((ROOT/'animations/manifest.json').read_text())
    scene=bpy.data.scenes['MM6 Goblin baked studio'];bpy.context.window.scene=scene
    rigs=[o for o in scene.objects if o.type=='ARMATURE'];assert len(rigs)==1
    meshes=[o for o in scene.objects if o.type=='MESH'];assert len(meshes)==1
    rig=rigs[0];mesh=meshes[0]
    expected={v['action'] for v in manifest['clips'].values()}
    assert {a.name for a in bpy.data.actions}==expected,'Export from an isolated seven-action checkpoint'
    rig.name='MM6 Goblin Rig';mesh.name='MM6 Goblin'
    world=mesh.matrix_world.copy();mesh.parent=rig;mesh.matrix_world=world
    rig.data.pose_position='POSE';rig.animation_data.action=bpy.data.actions[manifest['clips']['Standing']['action']]
    rig.animation_data.action_slot=rig.animation_data.action.slots[0]
    for material in mesh.data.materials:
        assert not any(n.type=='ATTRIBUTE' for n in material.node_tree.nodes),'Portable materials must use baked textures'
    for attribute in list(mesh.data.color_attributes):mesh.data.color_attributes.remove(attribute)
    for attribute in list(mesh.data.attributes):
        if attribute.name.startswith(('Source','Neck')) or attribute.name=='SculptPosition':
            mesh.data.attributes.remove(attribute)
    scene.frame_set(1);scene.frame_start=1;scene.frame_end=49
    scene.render.fps=manifest['fps']
    for obj in scene.objects:obj.select_set(False)
    rig.select_set(True);mesh.select_set(True);scene.view_layers[0].objects.active=rig
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type=='VIEW_3D':
                space=area.spaces.active;space.shading.type='MATERIAL';space.overlay.show_extras=False
                space.region_3d.view_location=(0,0,.98);space.region_3d.view_distance=3.1
                space.region_3d.view_rotation=Vector((.5,1,-.1)).to_track_quat('-Z','Y')
    note=bpy.data.texts.new('READ ME - MM6 Goblin')
    note.write('MM6 Goblin: rigged reconstruction from the native gob sprite family.\n'
        'Actions: Standing, Walk, Attack, Hit, Death, Corpse, Fidget.\n'
        'Select MM6 Goblin Rig and choose an Action in the Action Editor.\n'
        'For manual posing: unlink the active Action, enter Pose Mode, select bones, and reset location/rotation/scale.\n'
        'root moves the character; weapon.R controls its right-hand scimitar; skirt.00 through skirt.21 pose the strips.\n'
        'Walk is in place: 0.64 m stride per 0.75 s cycle, travel toward -Y at 0.853333 m/s.\n'
        'Death contains fractional-frame keys: do not round them or resample to 24 fps for export.\n'
        'Units are meters, Z up. Textures are packed. Review cameras/lights are excluded from GLB.\n'
        'Detailed source checkpoints, scripts and native/AI references are in the project directory.\n'
        'See README.md and PROGRESS.md for the actual acceptance/review status.\n')
    bpy.ops.file.pack_all()
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'mm6_goblin.blend'))
    # The unsampled FK export path does not apply slide-to-zero consistently. Normalize its input keys explicitly.
    # The saved editable project retains Blender's frame-1 convention; only this isolated export state is shifted.
    for name,clip in manifest['clips'].items():
        action=bpy.data.actions[clip['action']];offset=clip['frame_start']
        for layer in action.layers:
            for strip in layer.strips:
                for bag in strip.channelbags:
                    for curve in bag.fcurves:
                        for key in curve.keyframe_points:
                            key.co.x-=offset;key.handle_left.x-=offset;key.handle_right.x-=offset
                        curve.update()
    scene.frame_set(0)
    target=ROOT/'mm6_goblin.glb'
    bpy.ops.export_scene.gltf(filepath=str(target),export_format='GLB',use_selection=True,use_active_scene=True,
        export_animations=True,export_animation_mode='ACTIONS',export_anim_single_armature=True,
        export_force_sampling=False,export_frame_range=False,export_optimize_animation_size=False,
        export_anim_slide_to_zero=True,
        export_yup=True,export_cameras=False,export_lights=False,export_tangents=True)
    data=target.read_bytes();length,kind=struct.unpack_from('<II',data,12)
    assert kind==0x4e4f534a
    gltf=json.loads(data[20:20+length]);animations=[]
    for animation in gltf.get('animations',[]):
        inputs=[gltf['accessors'][s['input']] for s in animation['samplers']]
        animations.append({'name':animation.get('name'),'channels':len(animation['channels']),
            'start':min(a['min'][0] for a in inputs),'end':max(a['max'][0] for a in inputs),
            'max_input_samples':max(a['count'] for a in inputs)})
    assert {a['name'] for a in animations}==set(manifest['clips']),'All seven exact clips must be exported'
    for animation in animations:
        assert abs(animation['start'])<1e-7
        assert abs(animation['end']-manifest['clips'][animation['name']]['duration_seconds'])<1e-7
    report={'file_bytes':len(data),'skins':len(gltf.get('skins',[])),'materials':len(gltf.get('materials',[])),
        'images':len(gltf.get('images',[])),'animations':animations,'extensions':gltf.get('extensionsUsed',[]),
        'status':'Export candidate; structural inventory is not visual/deformation acceptance'}
    (ROOT/'export_work/glb_report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report))

if __name__=='__main__':build()
