"""Review the fitted hair from every side, with the runtime's back-face culling."""
from pathlib import Path
import bpy, sys, math, subprocess, runpy
from mathutils import Vector
p=Path(__file__).resolve().parents[1]
subprocess.run(['/usr/bin/python3',str(p/'scripts/compose_textures.py')],check=True)
runpy.run_path(str(p/'scripts/export_runtime.py'),run_name='__main__')
sys.path.insert(0,str(p/'scripts')); import common
common.setup_render(); common.workbench_clay(bpy.context.scene,True)
bpy.context.scene.display.shading.show_backface_culling=True
for material in bpy.data.objects['Bedraggled'].data.materials:
    for node in material.node_tree.nodes:
        if node.type=='TEX_IMAGE' and 'basecolor' in node.image.name: material.node_tree.nodes.active=node
scene=bpy.context.scene; scene.render.resolution_x=720; scene.render.resolution_y=720
target=Vector((-.02,.025,1.60))
for index in range(9):
    angle=2*math.pi*(index%8)/8
    location=target+Vector((3*math.sin(angle),-3*math.cos(angle),1.5 if index==8 else .05))
    camera=common.ortho_camera('hair_camera',location,(target-location).to_track_quat('-Z','Y').to_euler(),.34)
    scene.camera=camera; scene.render.filepath=str(p/f'review/hair_v3_{index}.png')
    bpy.ops.render.render(write_still=True); bpy.data.objects.remove(camera,do_unlink=True)
