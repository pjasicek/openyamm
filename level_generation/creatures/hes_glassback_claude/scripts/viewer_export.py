"""Review GLBs and textured renders per tier from work/crest_v3.blend (reduced LOD0, clips, crest pieces on bones).
Tier A = Glassback Pup (short crest), B = Glassback (full crest), C = Glassback Bull (tall crest), each with its baked
review textures (tier_textures.py). Writes review/viewer/hes_glassback_<tier>.glb (body + its crest as bone children,
all clips) and Eevee renders into work/renders/<tier>_<shot>.png. Args: -- [shots|noshots]"""
import bpy, os, sys, math
import numpy as np
from mathutils import Vector, Matrix
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C
args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
SHOTS = not args or args[0] != 'noshots'
TIERS = {'hgb_a': 'short', 'hgb_b': 'full', 'hgb_c': 'tall'}
GLOW = {'hgb_a': (0.55, 0.95, 0.88), 'hgb_b': (0.12, 1.0, 0.78), 'hgb_c': (0.82, 1.0, 0.86)}
T = C.path('textures')
os.makedirs(C.path('review/viewer'), exist_ok=True); os.makedirs(C.path('work/renders'), exist_ok=True)


def setup(tier):
    bpy.ops.wm.open_mainfile(filepath=C.path('work/crest_v3.blend'))
    rig = bpy.data.objects[C.RIG]; body = bpy.data.objects[C.MESH]; me = body.data
    for o in list(bpy.data.objects):
        if o.name.startswith('Crest') and (not o.name.startswith(f'Crest_{TIERS[tier]}_') or '_LOD' in o.name):
            bpy.data.objects.remove(o, do_unlink=True)
    hd = np.zeros(len(me.polygons), np.int32); me.attributes['head'].data.foreach_get('value', hd)
    huv, buv = me.uv_layers['HeadUV'].data, me.uv_layers['UVMap'].data
    for p in me.polygons:
        if hd[p.index]:
            for li in p.loop_indices:
                buv[li].uv = huv[li].uv
    me.uv_layers.remove(me.uv_layers['HeadUV'])

    def mat(name, base, normal=None, mr=None, rough=0.85):
        m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree
        b = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
        img = bpy.data.images.load(base); t = nt.nodes.new('ShaderNodeTexImage'); t.image = img
        nt.links.new(t.outputs['Color'], b.inputs['Base Color'])
        if normal:
            ni = bpy.data.images.load(normal); ni.colorspace_settings.name = 'Non-Color'
            tn = nt.nodes.new('ShaderNodeTexImage'); tn.image = ni; nm = nt.nodes.new('ShaderNodeNormalMap')
            nt.links.new(tn.outputs['Color'], nm.inputs['Color']); nt.links.new(nm.outputs['Normal'], b.inputs['Normal'])
        if mr:
            mi = bpy.data.images.load(mr); mi.colorspace_settings.name = 'Non-Color'
            tm = nt.nodes.new('ShaderNodeTexImage'); tm.image = mi; sp = nt.nodes.new('ShaderNodeSeparateColor')
            nt.links.new(tm.outputs['Color'], sp.inputs['Color']); nt.links.new(sp.outputs['Green'], b.inputs['Roughness'])
        else:
            b.inputs['Roughness'].default_value = rough
        b.inputs['Metallic'].default_value = 0.0
        return m

    me.materials.clear()
    me.materials.append(mat('Glassback', C.path(f'work/tier_{tier}_body.png'), os.path.join(T, 'hgb_normal_1k.png'),
                            os.path.join(T, 'hgb_metal_rough_1k.png')))
    me.materials.append(mat('GlassbackHead', C.path(f'work/tier_{tier}_head.png'),
                            os.path.join(T, 'hgb_head_normal_1k.png'), os.path.join(T, 'hgb_head_metal_rough_1k.png')))
    for p in me.polygons:
        p.material_index = int(hd[p.index])
    glass = mat('Glass', C.path(f'work/tier_{tier}_glass.png'), mr=os.path.join(T, 'hgb_glass_metal_rough_256.png'))
    glow = bpy.data.materials.new('Glow'); glow.use_nodes = True
    gb = next(n for n in glow.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    # the engine draws it unlit at its emissive colour: base = emission here, so lit previews and three.js agree
    gb.inputs['Base Color'].default_value = (*(0.5 * c for c in GLOW[tier]), 1); gb.inputs['Roughness'].default_value = 1.0
    gb.inputs['Emission Color'].default_value = (*GLOW[tier], 1); gb.inputs['Emission Strength'].default_value = 0.5
    for o in bpy.data.objects:
        if o.name.startswith('Crest'):
            o.data.materials[0] = glass; o.data.materials[1] = glow      # clear() would reset every face to slot 0
    return rig, body


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


SHOTLIST = {
    'quarter': ((3.4, -4.0, 1.9), (0, -0.1, 0.55), 3.6),
    'side': ((6, -0.05, 0.6), (0, -0.05, 0.6), 3.4),
    'front': ((0, -6, 0.75), (0, 0, 0.6), 2.4),
    'back': ((-1.2, 6, 1.6), (0, 0, 0.6), 2.6),
    'head': ((1.4, -2.6, 1.0), (0, -1.2, 0.72), 1.0),
    'crest': ((1.8, -1.2, 2.4), (0, -0.45, 1.1), 1.6),
    'throat': ((1.3, -2.4, 0.3), (0, -1.0, 0.55), 1.1),
}
for tier, size in TIERS.items():
    rig, body = setup(tier)
    rig.animation_data.action = bpy.data.actions['Standing']; bpy.context.scene.frame_set(1)
    if SHOTS:
        for name, (loc, tgt, scale) in SHOTLIST.items():
            render(C.path(f'work/renders/{tier}_{name}.png'), loc, tgt, scale)
        if tier == 'hgb_b':
            for clip, frames in (('Walking', (1, 4, 7, 10)), ('Running', (1, 4, 7)), ('Attack', (1, 10, 15, 22)),
                                 ('Hit', (4,)), ('Death', (12, 24, 49)), ('Fidget', (14, 30)), ('Standing', (1,))):
                rig.animation_data.action = bpy.data.actions[clip]
                for f in frames:
                    bpy.context.scene.frame_set(f)
                    render(C.path(f'work/renders/clip_{clip}_{f:02d}.png'), (3.4, -4.0, 1.9), (0, -0.1, 0.5), 3.6,
                           res=(600, 400))
            rig.animation_data.action = bpy.data.actions['Standing']; bpy.context.scene.frame_set(1)
    for o in list(bpy.data.objects):
        if o.name in ('Floor', 'Sun'):
            bpy.data.objects.remove(o, do_unlink=True)
    for o in bpy.data.objects:
        o.select_set(o.type in ('MESH', 'ARMATURE'))
    bpy.context.view_layer.objects.active = rig
    out = C.path(f'review/viewer/hes_glassback_{tier[-1]}.glb')
    bpy.ops.export_scene.gltf(filepath=out, use_selection=True, export_format='GLB', export_yup=True,
                              export_animations=True, export_animation_mode='ACTIONS', export_force_sampling=True,
                              export_frame_step=1, export_skins=True, export_attributes=False,
                              export_image_format='JPEG', export_reset_pose_bones=True, export_anim_slide_to_zero=True)
    print('VIEWER', tier, out)
