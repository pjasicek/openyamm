"""Blender helpers shared by the Reactor's render, animation and export scripts: materials and the idle pose."""
import os

import bpy

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
T = os.path.join(HERE, 'textures')

# Parts drawn in the idle pose; every other toggle bone rests at scale 0.
TOGGLES = (['Arc1', 'Arc2', 'Arc3', 'Arc4', 'ArcBig1', 'ArcBig2', 'ArcBig3', 'Liq100', 'Liq60', 'Liq25', 'Glass', 'GlassBroken', 'Flash',
            'CapGlow', 'BowlGlow', 'DomeTop', 'Spire', 'Crown', 'BowlLower', 'BowlTorn', 'Nozzle', 'GooStream',
            'GooBlob', 'LampRed', 'LampG1', 'LampG2']
           + [f'Shard{k}' for k in range(1, 9)] + [f'Debris{k}' for k in range(1, 9)]
           + [f'{p}{s}_Up' for p in ('LArm', 'UArm') for s in ('L', 'R')])
IDLE_ON = {'Arc1', 'BandWave1', 'LidWave1', 'Liq100', 'Glass', 'CapGlow', 'BowlGlow', 'DomeTop', 'Spire',
           'BowlLower', 'Nozzle', 'LampRed', 'LampG1', 'LampG2'}


def image(name, colorspace):
    img = bpy.data.images.load(os.path.join(T, name), check_existing=True)
    img.colorspace_settings.name = colorspace
    return img


def tex_node(nt, name, colorspace):
    n = nt.nodes.new('ShaderNodeTexImage'); n.image = image(name, colorspace)
    return n


def setup_materials(render=False):
    """Final material node trees. render=True shows unlit parts as emission for Blender previews; the export uses
    plain base-colour materials that fix_gltf.py turns into KHR_materials_unlit."""
    mats = {m.name: m for m in bpy.data.materials}
    for name, mat in mats.items():
        mat.use_nodes = True
        nt = mat.node_tree
        for n in list(nt.nodes):
            nt.nodes.remove(n)
        out = nt.nodes.new('ShaderNodeOutputMaterial')
        bsdf = nt.nodes.new('ShaderNodeBsdfPrincipled')
        nt.links.new(bsdf.outputs[0], out.inputs['Surface'])
        mat.use_backface_culling = name in ('Reactor_Glass', 'Reactor_Flash', 'Reactor_Halo')
        if name == 'Reactor_Metal' and not render:   # unlit at runtime: base colour only (light is baked)
            bc = tex_node(nt, 'rea_metal_basecolor_2k.png', 'sRGB')
            nt.links.new(bc.outputs['Color'], bsdf.inputs['Base Color'])
        elif name == 'Reactor_Metal':
            bc = tex_node(nt, 'rea_metal_basecolor_2k.png', 'sRGB')
            em = nt.nodes.new('ShaderNodeEmission')
            nt.links.new(bc.outputs['Color'], em.inputs['Color'])
            nt.links.new(em.outputs[0], out.inputs['Surface'])
        elif name in ('Reactor_Glow', 'Reactor_Flash', 'Reactor_Halo'):
            bc = tex_node(nt, 'rea_glow_1k.png', 'sRGB')
            nt.links.new(bc.outputs['Color'], bsdf.inputs['Base Color'])
            if render:
                em = nt.nodes.new('ShaderNodeEmission')
                nt.links.new(bc.outputs['Color'], em.inputs['Color'])
                if name in ('Reactor_Flash', 'Reactor_Halo'):
                    tr = nt.nodes.new('ShaderNodeBsdfTransparent'); mix = nt.nodes.new('ShaderNodeMixShader')
                    mix.inputs['Fac'].default_value = 0.7 if name == 'Reactor_Flash' else 0.3
                    nt.links.new(tr.outputs[0], mix.inputs[1]); nt.links.new(em.outputs[0], mix.inputs[2])
                    nt.links.new(mix.outputs[0], out.inputs['Surface'])
                else:
                    nt.links.new(em.outputs[0], out.inputs['Surface'])
        elif name == 'Reactor_Glass':
            bc = tex_node(nt, 'rea_glass_512.png', 'sRGB')
            nt.links.new(bc.outputs['Color'], bsdf.inputs['Base Color'])
            nt.links.new(bc.outputs['Alpha'], bsdf.inputs['Alpha'])
            bsdf.inputs['Roughness'].default_value = 0.08
            bsdf.inputs['Metallic'].default_value = 0.0
        if hasattr(mat, 'surface_render_method'):
            mat.surface_render_method = 'BLENDED' if name in ('Reactor_Glass', 'Reactor_Flash', 'Reactor_Halo') else 'DITHERED'


def idle_pose(rig, on=IDLE_ON):
    for name in TOGGLES:
        pb = rig.pose.bones.get(name)
        if pb is not None:
            pb.scale = (1.0, 1.0, 1.0) if name in on else (0.0, 0.0, 0.0)
