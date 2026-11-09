"""Fixed-camera contact sheets of every authored clip; playback is recorded separately in the viewer."""
import bpy
import json
import subprocess
from pathlib import Path
from mathutils import Vector

PROJECT=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(PROJECT/'work/anim_v1.blend'))
rig=bpy.data.objects['Wolf_Rig'];sc=bpy.context.scene
out=PROJECT/'review/motion_clay';out.mkdir(exist_ok=True)
sc.render.engine='BLENDER_WORKBENCH'
sc.display.shading.light='STUDIO';sc.display.shading.show_cavity=True
sc.display.shading.color_type='SINGLE';sc.display.shading.single_color=(.7,.7,.7)
sc.world=bpy.data.worlds.new('ReviewWorld');sc.world.color=(.12,.12,.12)
sc.render.resolution_x=480;sc.render.resolution_y=340;sc.render.resolution_percentage=100
cam=bpy.data.objects.new('ReviewCamera',bpy.data.cameras.new('ReviewCamera'))
sc.collection.objects.link(cam);sc.camera=cam;cam.data.type='ORTHO';cam.data.ortho_scale=1.5
clips=json.loads((PROJECT/'work/animation_report.json').read_text())
records=[]
for name,info in clips.items():
    rig.animation_data.action=bpy.data.actions[name]
    for view,direction in [('side',(1,0,.08)),('quarter',(.8,-1,.5))]:
        center=Vector((0,-.02,.32));cam.location=center+Vector(direction).normalized()*4
        cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler()
        for i in range(6):
            time=i*info['duration']/5;frame=time*24+1
            sc.frame_set(int(frame),subframe=frame%1)
            path=out/f'{name}_{view}_{i}.png';sc.render.filepath=str(path)
            bpy.ops.render.render(write_still=True)
            records.append({'clip':name,'view':view,'time':time,'path':str(path)})
(out/'frames.json').write_text(json.dumps(records,indent=2)+'\n')
subprocess.run(['/usr/bin/python3','-c',
"from PIL import Image,ImageDraw;import json,sys;from pathlib import Path;p=Path(sys.argv[1]);rs=json.loads((p/'frames.json').read_text());out=Image.new('RGB',(1440,len(rs)//6*190));d=ImageDraw.Draw(out);[(out.paste(Image.open(r['path']).resize((240,170)),((i%6)*240,(i//6)*190)),d.text(((i%6)*240+4,(i//6)*190+172),r['clip']+' '+r['view']+' %.3f'%r['time'],fill='white')) for i,r in enumerate(rs)];out.save(p/'sheet.png')",
str(out)],check=True)
