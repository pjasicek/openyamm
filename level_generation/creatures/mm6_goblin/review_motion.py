"""Focused motion evidence: evaluated bounds, planted-foot travel and low-cost perspective playback."""
import bpy
import sys
import json
import math
import numpy as np
from pathlib import Path
from mathutils import Vector

ROOT=Path(__file__).resolve().parent
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from model_common import look_at

def frame_at(scene,clip,t):
    f=clip.get('frame_start',1)+clip['duration_seconds']*24*t
    scene.frame_set(int(f),subframe=f-int(f))

def bounds(scene):
    deps=bpy.context.evaluated_depsgraph_get();low=np.full(3,np.inf);high=-low
    for obj in scene.objects:
        if obj.type!='MESH' or obj.get('review_only'):continue
        evaluated=obj.evaluated_get(deps);mesh=evaluated.to_mesh()
        coords=np.empty(len(mesh.vertices)*3,dtype=np.float32);mesh.vertices.foreach_get('co',coords)
        if len(coords):
            matrix=np.array(obj.matrix_world);points=coords.reshape(-1,3) @ matrix[:3,:3].T+matrix[:3,3]
            low=np.minimum(low,points.min(axis=0));high=np.maximum(high,points.max(axis=0))
        evaluated.to_mesh_clear()
    return {'min':low.tolist(),'max':high.tolist()}

def build(clip_names=None,output_name='motion_playback_current',manifest_override=None):
    manifest=manifest_override or json.loads((ROOT/'animations/manifest.json').read_text())
    source=bpy.data.scenes[manifest['scene']]
    bpy.context.window.scene=source;bpy.ops.scene.new(type='FULL_COPY')
    scene=bpy.context.window.scene;scene.name='MM6 Goblin motion review'
    rig=next(o for o in scene.objects if o.type=='ARMATURE')
    report={'source_scene':manifest['scene'],'clips':{}}
    saved=[]
    for name,clip in manifest['clips'].items():
        rig.animation_data.action=bpy.data.actions[clip['action']];rig.animation_data.action_slot=rig.animation_data.action.slots[0]
        samples=[];start=None;end=None
        count=121 if name=='Death' else 9
        for i in range(count):
            phase=i/(count-1)
            frame_at(scene,clip,phase);sample={'phase':phase,**bounds(scene)};samples.append(sample)
            matrices=np.array([np.array(b.matrix) for b in rig.pose.bones])
            if i==0:start=matrices
            if i==count-1:end=matrices
        report['clips'][name]={'samples':samples,'min_ground_z':min(s['min'][2] for s in samples)}
        if clip['loop']:report['clips'][name]['loop_max_bone_matrix_delta']=float(np.abs(start-end).max())
        if name=='Death':death_end=end.copy()
        if name=='Corpse':report['death_corpse_max_bone_matrix_delta']=float(np.abs(death_end-start).max())
    # Foot bone orientation is held through stance, so a fixed local sole marker follows the same world motion.
    clip=manifest['clips']['Walk'];rig.animation_data.action=bpy.data.actions[clip['action']];rig.animation_data.action_slot=rig.animation_data.action.slots[0]
    contacts={}
    for side,start_t in [('L',0.),('R',.5)]:
        points=[]
        for i in range(6):
            t=start_t+i*.08;frame_at(scene,clip,t)
            point=rig.pose.bones['foot.'+side].head.copy();point.y-=manifest['walk_speed_m_s']*clip['duration_seconds']*t
            points.append(tuple(point))
        points=np.array(points);contacts[side]={'world_contact_range_m':np.ptp(points,axis=0).tolist()}
    report['walk_contacts']=contacts
    (ROOT/'animations/motion_review.json').write_text(json.dumps(report,indent=2)+'\n')
    # A floor makes floating contacts and penetration visible; it never belongs to the export.
    bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,0));floor=bpy.context.object
    floor.name='Motion review ground';floor['review_only']=True
    mat=bpy.data.materials.new('Motion review neutral floor');mat.use_nodes=True
    mat.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value=(.065,.07,.075,1)
    mat.node_tree.nodes.get('Principled BSDF').inputs['Roughness'].default_value=.9
    floor.data.materials.append(mat)
    camera=scene.camera;camera.data.type='PERSP';camera.data.lens=52
    camera.location=(-2.7,-4.8,2.35);look_at(camera,(0,0,.87))
    scene.render.resolution_x=480;scene.render.resolution_y=520;scene.cycles.samples=8
    scene.render.film_transparent=False
    output=ROOT/'review'/output_name;output.mkdir(exist_ok=True)
    for name,clip in manifest['clips'].items():
        if clip_names is not None and name not in clip_names:continue
        rig.animation_data.action=bpy.data.actions[clip['action']];rig.animation_data.action_slot=rig.animation_data.action.slots[0]
        count=round(clip['duration_seconds']*24)
        if name=='Corpse':count=1
        for i in range(count):
            t=0 if count==1 else i/(count if clip['loop'] else count-1)
            frame_at(scene,clip,t)
            scene.render.filepath=str(output/f'{name.lower()}_{i:03d}.png');bpy.ops.render.render(write_still=True)
            saved.append({'clip':name,'index':i,'phase':t,'file':str(Path(scene.render.filepath).relative_to(ROOT))})
            (ROOT/'motion_review_status.txt').write_text(f'RUNNING playback {name} {i+1}/{count}')
    (output/'frames.json').write_text(json.dumps(saved,indent=2)+'\n')
    bpy.context.window.scene=source
    (ROOT/'motion_review_status.txt').write_text('COMPLETE '+output_name)
    print('Motion bounds, contact diagnostics and perspective playback complete')

if __name__=='__main__':build()
