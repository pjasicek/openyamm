"""Inspect checker continuity on the frozen UV master and bake its short-range AO."""
import bpy
import sys
import runpy
from pathlib import Path
from mathutils import Vector

PROJECT=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(PROJECT/'work/wolf_uv_repaired.blend'))
mesh=bpy.data.objects['Wolf'];rig=bpy.data.objects['Wolf_Rig'];sc=bpy.context.scene
checker=bpy.data.images.new('UVChecker',1024,1024);checker.generated_type='COLOR_GRID'
mat=bpy.data.materials.new('Checker');mat.use_nodes=True
tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=checker
mat.node_tree.links.new(tex.outputs['Color'],mat.node_tree.nodes.get('Principled BSDF').inputs['Base Color'])
mesh.data.materials.clear();mesh.data.materials.append(mat)
sc.render.engine='BLENDER_WORKBENCH';sc.display.shading.color_type='TEXTURE'
sc.display.shading.light='STUDIO';sc.display.shading.show_cavity=True
sc.world=bpy.data.worlds.new('ReviewWorld');sc.world.color=(.12,.12,.12)
sc.render.resolution_x=900;sc.render.resolution_y=650;sc.render.resolution_percentage=100
cam=bpy.data.objects.new('ReviewCamera',bpy.data.cameras.new('ReviewCamera'))
sc.collection.objects.link(cam);sc.camera=cam;cam.data.type='ORTHO'
for name,direction,center,scale in [('side',(1,0,.08),(0,-.02,.32),1.4),
                                   ('front',(0,-1,.08),(0,-.02,.32),1.25),
                                   ('head',(.8,-1,.25),(0,-.42,.34),.55)]:
    center=Vector(center);cam.location=center+Vector(direction).normalized()*4
    cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale
    sc.render.filepath=str(PROJECT/f'review/checker_{name}.png');bpy.ops.render.render(write_still=True)
sys.argv=['bake_creature_ao.py','--','Wolf',str(PROJECT/'textures/wolf_ao_2k.png'),'.025','2048']
runpy.run_path(str(PROJECT.parent/'claude_shared/bake_creature_ao.py'),run_name='__main__')
