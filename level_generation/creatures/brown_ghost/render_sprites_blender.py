"""Render the finished rig as five stored MM-style directions; run inside GUI Blender through MCP."""
import bpy
import hashlib
import json
import math
import traceback
from pathlib import Path
from mathutils import Vector

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'spritesheets'
SOURCE='Brown ghost sprite studio'
BAKE='Brown ghost directional sprite bake'
SPECS=[('Standing','s',10),('Attack','a',16),('Float','w',10),('Hit','n',10),
       ('Death','d',12),('Corpse','x',1),('Fidget','f',10)]
PREFIX='bg42'

def render_sprites():
    OUT.mkdir(exist_ok=True);(OUT/'masters_512').mkdir(exist_ok=True)
    original=bpy.context.window.scene
    source=bpy.data.scenes[SOURCE]
    assert bpy.data.scenes.get(BAKE) is None,'A sprite-bake scene already exists; inspect its checkpoint before rebuilding'
    bpy.context.window.scene=source
    bpy.ops.scene.new(type='FULL_COPY')
    scene=bpy.context.window.scene;scene.name=BAKE
    rig=next(o for o in scene.objects if o.type=='ARMATURE')
    obj=next(o for o in scene.objects if o.type=='MESH')
    assert next(m for m in obj.modifiers if m.type=='ARMATURE').object==rig
    data=json.loads((ROOT/'animations.json').read_text())
    clips=[]
    for name,code,count in SPECS:
        clip=next(c for c in data['clips'] if c['name']==name)
        duration=(clip['timeline_end']-clip['timeline_start'])/data['fps'] if count>1 else 1.0
        raw_total=round(duration*16)
        raw_lengths=[round((i+1)*raw_total/count)-round(i*raw_total/count) for i in range(count)]
        assert min(raw_lengths)>0 and sum(raw_lengths)==raw_total
        frames=[];elapsed=0
        for index,raw in enumerate(raw_lengths):
            denominator=raw_total if clip['loop'] else raw_total-raw_lengths[-1]
            phase=elapsed/denominator if count>1 else 0
            sample=clip['timeline_start']+phase*(clip['timeline_end']-clip['timeline_start'])
            frames.append({'index':index,'letter':chr(97+index),'texture_stem':f'{PREFIX}{code}{chr(97+index)}',
                           'source_frame':sample,'phase':phase,'frame_length_raw':raw,'duration_ms':raw*62.5})
            elapsed+=raw
        clips.append({'name':name,'code':code,'count':count,'duration_seconds':duration,'loop':clip['loop'],
                      'animation_length_raw':raw_total,'frames':frames})
    # One projection and ground pivot for every frame/direction: never auto-crop individual poses.
    max_x=0;max_z=0;min_z=100
    for clip in clips:
        for entry in clip['frames']:
            frame=entry['source_frame'];scene.frame_set(int(frame),subframe=frame-int(frame))
            for direction in range(5):
                rig.rotation_euler.z=direction*math.pi/4;bpy.context.view_layer.update()
                ev=obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
                points=[ev.matrix_world @ Vector(c) for c in ev.bound_box]
                max_x=max(max_x,max(abs(v.x) for v in points));max_z=max(max_z,max(v.z for v in points))
                min_z=min(min_z,min(v.z for v in points))
    assert min_z>-.02,('Unexpected interpolated floor penetration',min_z)
    margin=12/256;pivot_y=244/256
    scale=max(2*max_x/(1-2*margin),max_z/(pivot_y-margin))
    cam=scene.camera;cam.data.type='ORTHO';cam.data.ortho_scale=scale
    cam.location=(0,-10,(pivot_y-.5)*scale);cam.rotation_euler=(math.pi/2,0,0)
    scene.render.engine='CYCLES';scene.cycles.samples=24;scene.cycles.use_denoising=True
    scene.render.resolution_x=512;scene.render.resolution_y=512;scene.render.resolution_percentage=100
    scene.render.film_transparent=True;scene.render.image_settings.file_format='PNG'
    scene.render.image_settings.color_mode='RGBA';scene.render.image_settings.color_depth='8'
    scene.view_settings.view_transform='Standard';scene.view_settings.look='None'
    manifest={'schema_version':1,'prefix':PREFIX,'source_blend':'../brown_ghost.blend',
              'source_blend_sha256':hashlib.sha256((ROOT/'brown_ghost.blend').read_bytes()).hexdigest(),
              'frame_size':[256,256],'master_size':[512,512],'pivot_pixels':[128,244],
              'ortho_scale':scale,'sampled_world_bounds':{'max_abs_x':max_x,'max_z':max_z,'min_z':min_z},
              'stored_directions':[0,1,2,3,4],
              'directions':[{'index':i,'source':i if i<=4 else 8-i,'mirrored':i>4,
                             'angle_degrees':i*45} for i in range(8)],
              'legacy_flags':['Center','Mirror5','Mirror6','Mirror7'],
              'timing':'frame_length_raw * 8 ticks at 128 Hz; durations preserved with integer raw lengths',
              'sheet_layout':'animation frames in columns, directions in ascending rows; cells are 256x256',
              'clips':clips}
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    total=sum(c['count'] for c in clips)*5;done=0
    try:
        for clip in clips:
            for entry in clip['frames']:
                frame=entry['source_frame'];scene.frame_set(int(frame),subframe=frame-int(frame))
                for direction in range(5):
                    rig.rotation_euler.z=direction*math.pi/4
                    path=OUT/'masters_512'/f"{entry['texture_stem']}{direction}.png"
                    scene.render.filepath=str(path);bpy.ops.render.render(write_still=True)
                    done+=1
                    (OUT/'status.txt').write_text(f"Rendered {done}/{total}: {clip['name']} {entry['index']+1}, direction {direction}")
        scene.frame_set(1);rig.rotation_euler.z=0
        (OUT/'status.txt').write_text(f'RENDER COMPLETE: {done} masters')
    except Exception:
        (OUT/'status.txt').write_text(traceback.format_exc());raise
    finally:
        bpy.context.window.scene=original

if __name__=='__main__':render_sprites()
