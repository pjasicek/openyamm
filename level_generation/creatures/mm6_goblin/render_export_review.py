"""Matched source/baked/export views; run in an isolated Blender checkpoint for repeatable comparisons."""
import argparse
import bpy
import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parent
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from model_common import look_at

VIEWS={
    'front':((0,-5,.98),(0,0,.98),2.12,'Standing',0),
    'side':((5,0,.98),(0,0,.98),2.12,'Standing',0),
    'back':((0,5,.98),(0,0,.98),2.12,'Standing',0),
    'oblique':((-3,-5,1.12),(0,0,.98),2.12,'Standing',0),
    'head':((-.5,-3,1.79),(0,-.02,1.72),.52,'Standing',0),
    'neck_back':((.4,3,1.7),(0,.02,1.54),.48,'Standing',0),
    'torso':((-.7,-2,1.28),(0,0,1.25),.72,'Standing',0),
    'hand':((1,-2,1),(.42,-.06,.85),.45,'Standing',0),
    'feet':((-.7,-2,.5),(0,-.06,.15),.56,'Standing',0),
    'attack':((-3,-5,1.35),(0,0,1.0),2.55,'Attack',.34),
    'corpse':((-2,-3,2.6),(0,-.02,.12),2.25,'Corpse',0),
}

def build(scene_name,stage,view_names=None,manifest_override=None):
    scene=bpy.data.scenes[scene_name];bpy.context.window.scene=scene
    rig=next(o for o in scene.objects if o.type=='ARMATURE')
    rig.data.pose_position='POSE'
    manifest=manifest_override or json.loads((ROOT/'animations/manifest.json').read_text())
    camera=scene.camera;camera.data.type='ORTHO'
    scene.render.engine='CYCLES';scene.cycles.samples=32
    scene.render.resolution_x=800;scene.render.resolution_y=800;scene.render.resolution_percentage=100
    scene.render.film_transparent=True;scene.render.image_settings.file_format='PNG'
    output=ROOT/'review'/('export_'+stage);output.mkdir(exist_ok=True)
    records=[]
    for name,(position,target,scale,clip,phase) in VIEWS.items():
        if view_names is not None and name not in view_names:continue
        camera.location=position;look_at(camera,target);camera.data.ortho_scale=scale
        rig.animation_data.action=bpy.data.actions[manifest['clips'][clip]['action']];rig.animation_data.action_slot=rig.animation_data.action.slots[0]
        frame=manifest['clips'][clip].get('frame_start',1)+manifest['clips'][clip]['duration_seconds']*manifest['fps']*phase
        scene.frame_set(int(frame),subframe=frame-int(frame))
        scene.render.filepath=str(output/(name+'.png'));bpy.ops.render.render(write_still=True)
        records.append({'view':name,'clip':clip,'phase':phase,'camera':position,'target':target,'scale':scale})
        (output/'status.txt').write_text('RUNNING '+name)
    (output/'views.json').write_text(json.dumps(records,indent=2)+'\n')
    (output/'status.txt').write_text('COMPLETE')

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--scene',required=True);parser.add_argument('--stage',required=True)
    parser.add_argument('--views',nargs='+')
    options=parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    build(options.scene,options.stage,options.views)
