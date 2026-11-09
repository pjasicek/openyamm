"""Small, explicitly greybox node fixtures; metres, glTF Y up. No replacement of approved art."""
from pathlib import Path
import bpy

OUTPUT=Path(__file__).resolve().parent/'standins'


def build():
    OUTPUT.mkdir(exist_ok=True)
    def material(name,color):
        m=bpy.data.materials.new(name); m.diffuse_color=(*color,1); m.use_nodes=True
        m.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(*color,1)
        m.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=.65
        return m
    resin=material('greybox resin',(.035,.03,.045)); ceramic=material('greybox ceramic',(.6,.59,.53))
    violet=material('greybox coil',(.65,.43,.95)); amber=material('greybox lens',(.9,.46,.14))
    dark=material('greybox unpowered',(.08,.075,.085))
    frost=material('greybox frost',(.66,.79,.88))
    def cube(name,location,scale,mat):
        bpy.ops.mesh.primitive_cube_add(size=1,location=location)
        o=bpy.context.object; o.name=name; o.scale=scale
        bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
        o.data.materials.append(mat)
    for name in ('hes_lattice_coil','hes_lattice_coil_off','hes_tunnel_lamp','hes_tunnel_lamp_off',
                 'hes_alarm_pylon_off','d06_frost_small','d06_frost_large'):
        bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
        if 'lattice' in name:
            cube('stand',(0,0,.08),(1.1,.55,.16),resin)
            for x in (-.43,.43): cube('prong',(x,0,.68),(.18,.32,1.04),ceramic)
            cube('capacitor',(0,0,.9),(.72,.36,.26),dark if name.endswith('_off') else violet)
        elif 'tunnel' in name:
            cube('crown plate',(0,.03,.0),(.7,.12,.3),ceramic)
            cube('arm',(0,-.4,-.18),(.18,.9,.18),ceramic)
            cube('lens',(0,-.72,-.48),(.4,.25,.18),dark if name.endswith('_off') else amber)
        elif 'pylon' in name:
            cube('pylon',(0,0,1.15),(.6,.5,2.3),resin)
            cube('dead eye',(0,-.27,1.9),(.4,.06,.25),dark)
        else:
            bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1,radius=1,location=(0,0,.05))
            o=bpy.context.object; o.scale=(1.6,.8,.2) if name.endswith('large') else (.9,.55,.13)
            bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
            o.data.materials.append(frost)
        bpy.ops.export_scene.gltf(filepath=str(OUTPUT/(name+'.glb')),export_format='GLB',export_yup=True)
    bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)


if __name__=='__main__': build()
