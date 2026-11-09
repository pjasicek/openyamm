"""D7 temporary mine, shell and wreck silhouettes; our own low-poly greyboxes, metres and glTF Y up."""
from pathlib import Path
import bpy
import importlib.util
import math
from mathutils import Vector

OUT=Path(__file__).resolve().parent/'standins'

def build():
    OUT.mkdir(exist_ok=True)
    def material(name,color,emission=False):
        m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True
        bsdf=m.node_tree.nodes['Principled BSDF'];bsdf.inputs['Base Color'].default_value=(*color,1)
        bsdf.inputs['Roughness'].default_value=.65
        if emission:
            bsdf.inputs['Emission Color'].default_value=(*color,1);bsdf.inputs['Emission Strength'].default_value=1
        return m
    resin=material('resin',(.035,.025,.045));ceramic=material('ceramic',(.65,.59,.44))
    amber=material('amber eye',(1,.52,.12),True);scorch=material('spent',(.055,.045,.05))
    def cube(name,pos,size,mat):
        bpy.ops.mesh.primitive_cube_add(size=1,location=pos)
        o=bpy.context.object;o.name=name;o.scale=size
        bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(mat)
    for name in ('hes_kreegan_mine','hes_kreegan_mine_spent','hes_drone_shell','hes_bulwark_wreck'):
        bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
        if 'mine' in name:
            spent=name.endswith('spent')
            bpy.ops.mesh.primitive_cylinder_add(vertices=12,radius=.3,depth=.015 if spent else .08,
                                                location=(0,0,.0075 if spent else .04))
            bpy.context.object.data.materials.append(scorch if spent else resin)
            if not spent: cube('amber eye',(0,0,.095),(.12,.12,.03),amber)
        elif 'shell' in name:
            bpy.ops.mesh.primitive_uv_sphere_add(segments=12,ring_count=6,radius=1,location=(0,0,.25))
            o=bpy.context.object;o.scale=(1.1,.8,.45)
            bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(ceramic)
            cube('unfinished underside',(0,0,-.08),(1.5,1.05,.12),resin)
        else:
            cube('fallen hull',(0,0,.4),(2.2,1.8,.8),resin)
            cube('broken casing',(.1,.15,.9),(1.5,1.2,.3),ceramic)
            for x in (-1.1,1.1):cube('collapsed leg',(x,0,.16),(.4,2,.32),ceramic)
        bpy.ops.export_scene.gltf(filepath=str(OUT/(name+'.glb')),export_format='GLB',export_yup=True)
    root=Path(__file__).resolve().parents[3]
    spec=importlib.util.spec_from_file_location('zone4',root/'design/kreegan_world/zone4/dungeons/plans_zone4.py')
    z=importlib.util.module_from_spec(spec);spec.loader.exec_module(z)
    boss=next(m for m in z.d7.marks if m['kind']=='boss')
    for k,(x,y) in enumerate(z.couplings()):
        bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
        start=Vector((0,-.56,2.4));end=Vector(((x-boss['x'])/100,(y-boss['y'])/100,5.12))
        points=[start.lerp(end,j/6)-Vector((0,0,.8*math.sin(math.pi*j/6))) for j in range(7)]
        for a,c in zip(points,points[1:]):
            d=c-a
            bpy.ops.mesh.primitive_cylinder_add(vertices=8,radius=.3,depth=d.length,location=(a+c)/2)
            o=bpy.context.object;o.rotation_mode='QUATERNION';o.rotation_quaternion=d.to_track_quat('Z','Y')
            o.data.materials.append(resin)
        bpy.ops.export_scene.gltf(filepath=str(OUT/('d07_bulwark_cable_'+str(k+1)+'.glb')),export_format='GLB',export_yup=True)
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)

if __name__=='__main__':build()
