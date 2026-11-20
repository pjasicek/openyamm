"""Render clay action samples at fixed cameras for deformation review."""
from pathlib import Path
import json, subprocess
import bpy
from mathutils import Vector
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/anim_v1.blend'))
rig=bpy.data.objects['Unicorn_Rig'];sc=bpy.context.scene
sc.render.engine='BLENDER_WORKBENCH';sc.display.shading.light='STUDIO'
sc.display.shading.color_type='SINGLE';sc.display.shading.single_color=(.65,.70,.64)
sc.display.shading.show_cavity=True;sc.display.shading.show_shadows=False
sc.display.shading.background_type='WORLD'
sc.world=bpy.data.worlds.new('ReviewWorld')
sc.world.color=(.12,.12,.12)
sc.render.resolution_x=500;sc.render.resolution_y=360;sc.render.resolution_percentage=100
cam=bpy.data.objects.new('ReviewCamera',bpy.data.cameras.new('ReviewCamera'))
sc.collection.objects.link(cam);sc.camera=cam;cam.data.type='ORTHO';cam.data.ortho_scale=1.35
rows=[]
for name,times in {'Walking':[0,.25,.5,.85],'Running':[0,.19,.38,.64],'Attack':[0,.55,1.125,1.5],
                   'Hit':[0,.125,.375,.625],'Death':[0,.25,.5,.75],'Standing':[0,.5,1,1.5]}.items():
    rig.animation_data.action=bpy.data.actions[name]
    for view,loc in [('side',(1.5,0,.40)),('quarter',(1,-1,.8))]:
        row=[]
        cam.location=loc;cam.rotation_euler=(Vector((0,0,.38))-cam.location).to_track_quat('-Z','Y').to_euler()
        for i,t in enumerate(times):
            sc.frame_set(1+int(t*sc.render.fps),subframe=t*sc.render.fps-int(t*sc.render.fps))
            path=P/'review'/f'clay_{name}_{view}_{i}.png';sc.render.filepath=str(path)
            bpy.ops.render.render(write_still=True);row.append(str(path))
        rows.append((name+' '+view,row))
code='''import json,sys
from PIL import Image,ImageDraw
rows=json.loads(sys.argv[1]);o=Image.new('RGB',(2000,384*len(rows)),(40,40,40));d=ImageDraw.Draw(o)
for j,(name,paths) in enumerate(rows):
 d.text((8,j*384+362),name,fill='white')
 for i,p in enumerate(paths):o.paste(Image.open(p),(500*i,384*j))
o.save(sys.argv[2])
'''
subprocess.run(['/usr/bin/python3','-c',code,json.dumps(rows),str(P/'review/clay_action_review.png')],check=True)
