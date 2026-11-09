"""Review tier assemblies and write viewer GLBs; baked tier colours are review-only."""
import bpy, os, sys, math, json, hashlib
from pathlib import Path
from mathutils import Vector, Matrix
PROJECT=Path(__file__).resolve().parents[1]
def render(path, loc, tgt, scale, res=(900, 600)):
    sc = bpy.context.scene
    sc.render.engine = 'BLENDER_EEVEE'
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.film_transparent = False
    if sc.world is None:
        sc.world = bpy.data.worlds.new('w')
    sc.world.use_nodes = True
    bg = sc.world.node_tree.nodes.get('Background')
    bg.inputs['Color'].default_value = (0.32, 0.31, 0.33, 1); bg.inputs['Strength'].default_value = 0.9
    if 'Sun' not in bpy.data.objects:
        sd = bpy.data.lights.new('Sun', 'SUN'); sd.energy = 3.2
        sun = bpy.data.objects.new('Sun', sd); sc.collection.objects.link(sun)
        sun.rotation_euler = (math.radians(50), 0, math.radians(-35))
        bpy.ops.mesh.primitive_plane_add(size=12, location=(0, 0, 0)); fl = bpy.context.object; fl.name = 'Floor'
        fm = bpy.data.materials.new('floor'); fm.use_nodes = True
        fb = next(n for n in fm.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
        fb.inputs['Base Color'].default_value = (0.38, 0.37, 0.39, 1); fb.inputs['Roughness'].default_value = 0.95
        fl.data.materials.append(fm)
    cd = bpy.data.cameras.new('c'); cd.type = 'ORTHO'; cd.ortho_scale = scale
    cam = bpy.data.objects.new('c', cd); sc.collection.objects.link(cam)
    d = (Vector(tgt) - Vector(loc)).normalized()
    cam.matrix_world = Matrix.Translation(Vector(loc)) @ d.to_track_quat('-Z', 'Y').to_matrix().to_4x4()
    sc.camera = cam
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(cam, do_unlink=True)



(PROJECT/'review/viewer').mkdir(exist_ok=True)
(PROJECT/'review/tier_renders').mkdir(exist_ok=True)
models=[]
for tier,label in [('a','Kennel Hound'),('b','Hellhound'),('c','Pyre Hound')]:
    bpy.ops.wm.open_mainfile(filepath=str(PROJECT/'work/assembled.blend'))
    rig=bpy.data.objects['Hound_Rig']
    body=bpy.data.objects['Hound']
    for o in list(bpy.data.objects):
        if o.type!='MESH' or o==body: continue
        keep=o.name=='Hound_collar_'+('c' if tier=='c' else 'ab') or (tier!='a' and not o.name.startswith('Hound_collar'))
        if not keep: bpy.data.objects.remove(o,do_unlink=True)
    mat=bpy.data.materials['HoundHide']
    for node in mat.node_tree.nodes:
        if node.type=='TEX_IMAGE' and 'hound_basecolor' in node.image.name:
            node.image=bpy.data.images.load(str(PROJECT/f'textures/hound_{tier}_review.png'))
    glow=bpy.data.materials['MawGlow'].node_tree.nodes.get('Principled BSDF')
    factor={'a':.22,'b':.60,'c':1}[tier]
    glow.inputs['Emission Color'].default_value=(factor,.16*factor,.01*factor,1)
    fissure=bpy.data.materials['ThroatFissures'].node_tree.nodes.get('Principled BSDF')
    fissure.inputs['Emission Strength'].default_value=1
    gain=.55 if tier=='c' else 0.
    fissure.inputs['Emission Color'].default_value=(gain,.16*gain,.01*gain,1)
    for clip,frame,focus in [('Standing',0,'body'),('Pounce',28,'body'),('Dead',0,'body'),('Bite',38,'head')]:
        act=bpy.data.actions[clip]
        rig.animation_data.action=act
        if act.slots: rig.animation_data.action_slot=act.slots[0]
        bpy.context.scene.frame_set(frame)
        if focus=='head': loc,tgt,scale=(2,-3,1.3),(0,-1.02,.79),.9
        else: loc,tgt,scale=(3.4,-4,1.9),(0,-.1,.5),3.2
        render(str(PROJECT/f'review/tier_renders/{tier}_{clip}.png'),loc,tgt,scale)
    for o in list(bpy.data.objects):
        if o.name in ['Floor','Sun']: bpy.data.objects.remove(o,do_unlink=True)
    rig.animation_data.action=bpy.data.actions['Standing']
    bpy.context.scene.frame_set(0)
    for o in bpy.data.objects: o.select_set(o.type in ('MESH','ARMATURE'))
    bpy.context.view_layer.objects.active=rig
    out=PROJECT/f'review/viewer/hes_hound_{tier}.glb'
    bpy.ops.export_scene.gltf(filepath=str(out),use_selection=True,export_format='GLB',export_yup=True,
        export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,export_frame_step=1,
        export_skins=True,export_all_influences=False,export_attributes=False,export_morph=False,
        export_reset_pose_bones=True,export_anim_slide_to_zero=True)
    h=hashlib.sha256(out.read_bytes()).hexdigest()
    models.append(dict(id='hound_'+tier,label=label,revision='hound_colour_3',url=out.name+'?v='+h[:12],sha256=h))
report=json.loads((PROJECT/'work/animation_report.json').read_text())
manifest=dict(revision='hound_colour_3',model='hes_hound_b.glb',default_clip='Bite',default_model='hound_b',
    models=models,model_sha256=models[1]['sha256'],feedback='feedback/user_feedback.json',
    clips={k:dict(label=k,duration=v['duration'],mode='loop' if v['loop'] else 'once',
        provenance='Procedural canine motion, measured IK feet',anchors=[]) for k,v in report.items()},issues=[])
(PROJECT/'review/viewer/manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
sys.stdout.flush()
sys.stderr.flush()
os._exit(0)
