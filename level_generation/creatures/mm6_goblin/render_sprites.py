"""Render genuine eight-view MM-style sprite masters from the delivered rig, with one fixed scale and pivot."""
import argparse
import bpy
import hashlib
import json
import math
import numpy as np
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'spritesheets'
SPECS=[('Standing','s',10),('Walk','w',10),('Attack','a',16),('Hit','h',10),
       ('Death','d',12),('Corpse','c',1),('Fidget','f',10)]
PREFIX='rgob'
WIDTH,HEIGHT=355,289

def set_pose(scene,rig,clip,phase):
    rig.animation_data.action=bpy.data.actions[clip['action']]
    rig.animation_data.action_slot=rig.animation_data.action.slots[0]
    frame=clip['frame_start']+phase*clip['duration_seconds']*scene.render.fps
    scene.frame_set(int(frame),subframe=frame-int(frame))

def build(pilot=False):
    assert Path(bpy.data.filepath)==ROOT/'mm6_goblin.blend'
    scene=bpy.context.scene;rig=next(o for o in scene.objects if o.type=='ARMATURE')
    mesh=next(o for o in scene.objects if o.type=='MESH')
    rig.data.pose_position='POSE';rig.rotation_euler=(0,0,0)
    source=json.loads((ROOT/'animations/manifest.json').read_text())
    scene.render.fps=source['fps'];clips=[]
    for name,code,count in SPECS:
        clip=source['clips'][name];duration=clip['duration_seconds'];frames=[]
        for index in range(count):
            phase=index/(count if clip['loop'] else max(1,count-1))
            frames.append({'index':index,'texture_stem':PREFIX+code+chr(97+index),'phase':phase,
                'source_seconds':phase*duration,'display_start_seconds':index*duration/count,
                'duration_seconds':duration/count})
        clips.append({'name':name,'code':code,'count':count,'duration_seconds':duration,'loop':clip['loop'],'frames':frames})
    # Fit dense continuous-motion samples, not just the smaller delivery frame set.
    max_x=0.;max_z=0.;min_z=math.inf
    for name,clip in source['clips'].items():
        count=121 if name in {'Walk','Death'} else 61
        for i in range(count):
            set_pose(scene,rig,clip,i/(count-1))
            evaluated=mesh.evaluated_get(bpy.context.evaluated_depsgraph_get());data=evaluated.to_mesh()
            buffer=np.empty(len(data.vertices)*3,dtype=np.float32);data.vertices.foreach_get('co',buffer)
            matrix=np.array(evaluated.matrix_world);points=buffer.reshape(-1,3) @ matrix[:3,:3].T+matrix[:3,3]
            evaluated.to_mesh_clear()
            max_z=max(max_z,float(points[:,2].max()));min_z=min(min_z,float(points[:,2].min()))
            for direction in range(8):
                angle=direction*math.pi/4
                max_x=max(max_x,float(np.abs(points[:,0]*math.cos(angle)-points[:,1]*math.sin(angle)).max()))
    assert min_z>=-.0005,('Ground penetration before sprite render',min_z)
    margin=12;ground_pixel=HEIGHT-12;aspect=WIDTH/HEIGHT
    horizontal_span=max(2*max_x/(1-2*margin/WIDTH),aspect*max_z/((ground_pixel-margin)/HEIGHT))
    vertical_span=horizontal_span/aspect
    camera=scene.camera;camera.data.type='ORTHO';camera.data.ortho_scale=horizontal_span
    camera.location=(0,-10,(ground_pixel/HEIGHT-.5)*vertical_span);camera.rotation_euler=(math.pi/2,0,0)
    scene.render.engine='CYCLES';scene.cycles.samples=32;scene.cycles.use_denoising=True
    scene.render.resolution_x=WIDTH*2;scene.render.resolution_y=HEIGHT*2;scene.render.resolution_percentage=100
    scene.render.film_transparent=True;scene.render.image_settings.file_format='PNG'
    scene.render.image_settings.color_mode='RGBA';scene.render.image_settings.color_depth='8'
    manifest={'schema_version':1,'prefix':PREFIX,'source_blend':'../mm6_goblin.blend',
        'source_blend_sha256':hashlib.sha256((ROOT/'mm6_goblin.blend').read_bytes()).hexdigest(),
        'frame_size':[WIDTH,HEIGHT],'master_size':[WIDTH*2,HEIGHT*2],'pivot_pixels':[WIDTH/2,ground_pixel],
        'ortho_horizontal_span_m':horizontal_span,'ortho_vertical_span_m':vertical_span,
        'dense_bounds':{'max_abs_projected_x':max_x,'max_z':max_z,'min_z':min_z},
        'directions':[{'index':i,'actor_rotation_degrees':i*45,'mirrored':False} for i in range(8)],
        'view_convention':'0 front; 1 front-right view (nose points screen right); 2 right profile; 4 rear; 5-7 actual opposite views.',
        'lighting':'Fixed studio camera/lights; actor rotates about ground origin. Preserve source color management.',
        'sheet_layout':'Frames in columns, directions 0-7 in rows. No labels or gutters in usable atlases.',
        'timing':'Uniform positive display durations sum to the authored clip duration. Non-looping pose samples include both endpoints; source_seconds records the exact pose time separately from display intervals.',
        'legacy_timing':'See separate legacy_manifest.json for positive integer raw units and a subset of dense Attack/Death frames.',
        'clips':clips}
    OUT.mkdir(exist_ok=True);masters=OUT/'masters_710x578';masters.mkdir(exist_ok=True)
    path=OUT/'render_manifest.json'
    if path.exists():assert json.loads(path.read_text())==manifest,'Source or projection changed: archive the old sprite output first'
    path.write_text(json.dumps(manifest,indent=2)+'\n')
    total=sum(c['count'] for c in clips)*8;done=0
    for clip in clips:
        for frame in clip['frames']:
            for direction in range(8):
                if pilot and not ((clip['name']=='Standing' and frame['index']==0) or
                    (clip['name']=='Attack' and frame['index']==8 and direction in {0,2,4,6}) or
                    (clip['name']=='Death' and frame['index']==clip['count']-1)):
                    continue
                name=frame['texture_stem']+str(direction)+'.png';target=masters/name
                if not target.exists():
                    set_pose(scene,rig,source['clips'][clip['name']],frame['phase'])
                    rig.rotation_euler.z=direction*math.pi/4;bpy.context.view_layer.update()
                    scene.render.filepath=str(target);bpy.ops.render.render(write_still=True)
                done+=1;(OUT/'status.txt').write_text(f'RUNNING {"pilot" if pilot else "full"} {done}/{20 if pilot else total}: {name}')
    (OUT/'status.txt').write_text(f'{"PILOT" if pilot else "RENDER"} COMPLETE: {done} masters')
    print((OUT/'status.txt').read_text())

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--pilot',action='store_true')
    options=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
    build(options.pilot)
