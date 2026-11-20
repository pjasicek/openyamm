"""Compare the full mesh and both reduction trials from identical cameras and action times."""
import bpy
import json
import subprocess
from pathlib import Path
from mathutils import Vector

PROJECT=Path(__file__).resolve().parents[1];out=PROJECT/'review/reduction'
rows=[]
for revision,source in [('full','work/anim_v1.blend'),('step1','review/reduction/step_01.blend'),
                        ('step2','review/reduction/step_02.blend')]:
    bpy.ops.wm.open_mainfile(filepath=str(PROJECT/source));sc=bpy.context.scene
    rig=bpy.data.objects['Wolf_Rig'];sc.render.engine='BLENDER_WORKBENCH'
    sc.display.shading.light='STUDIO';sc.display.shading.show_cavity=True
    sc.display.shading.color_type='SINGLE';sc.display.shading.single_color=(.7,.7,.7)
    sc.world=bpy.data.worlds.new('ReviewWorld');sc.world.color=(.12,.12,.12)
    sc.render.resolution_x=600;sc.render.resolution_y=420;sc.render.resolution_percentage=100
    cam=bpy.data.objects.new('ReviewCamera',bpy.data.cameras.new('ReviewCamera'))
    sc.collection.objects.link(cam);sc.camera=cam;cam.data.type='ORTHO'
    for clip,time in [('Standing',0),('Walking',.375),('Attack',.5),('Death',.625)]:
        rig.animation_data.action=bpy.data.actions[clip];frame=time*24+1
        sc.frame_set(int(frame),subframe=frame%1)
        center=Vector((0,-.02,.32));cam.location=center+Vector((.8,-1,.5)).normalized()*4
        cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=1.5
        path=out/f'{revision}_{clip}.png';sc.render.filepath=str(path);bpy.ops.render.render(write_still=True)
        rows.append({'revision':revision,'clip':clip,'time':time,'path':str(path)})
(out/'review_frames.json').write_text(json.dumps(rows,indent=2)+'\n')
subprocess.run(['/usr/bin/python3','-c',
"from PIL import Image,ImageDraw;import json,sys;from pathlib import Path;p=Path(sys.argv[1]);rs=json.loads((p/'review_frames.json').read_text());out=Image.new('RGB',(1800,1760));d=ImageDraw.Draw(out);[(out.paste(Image.open(r['path']),((i//4)*600,(i%4)*440)),d.text(((i//4)*600+6,(i%4)*440+422),r['revision']+' '+r['clip'],fill='white')) for i,r in enumerate(rs)];out.save(p/'comparison.png')",
str(out)],check=True)
