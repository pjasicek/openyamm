"""Inspect the retained flying demon in bind pose and prepare its editable local copy."""
import bpy, json, os, sys
from pathlib import Path
from mathutils import Vector
import numpy as np
p=Path(__file__).resolve().parents[1]
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=str(p/'source/mm6_wdm_source.glb'))
rig=next(o for o in bpy.data.objects if o.type=='ARMATURE')
body=bpy.data.objects['Demon']
rig.name='Rig'; body.name='Body'
rig.animation_data.action=None
for track in rig.animation_data.nla_tracks: track.mute=True
for bone in rig.pose.bones: bone.matrix_basis.identity()
bpy.context.view_layer.update()
co=np.array([v.co[:] for v in body.data.vertices])
info={'bones':{b.name:{'head':list(b.head_local),'matrix':[list(r) for r in b.matrix_local],'parent':b.parent.name if b.parent else None} for b in rig.data.bones},'bounds':[co.min(0).tolist(),co.max(0).tolist()]}
(p/'work/source_rest.json').write_text(json.dumps(info,indent=2))
for side in ('Left','Right'):
    gn='mixamorig:'+side+'Hand'
    gi=body.vertex_groups[gn].index
    v=np.array([v.index for v in body.data.vertices if any(g.group==gi and g.weight>.5 for g in v.groups)])
    np.savez(p/('work/hand_'+side+'.npz'),positions=co[v],indices=v,edges=np.array([e.vertices[:] for e in body.data.edges]),all_positions=co)
    print('HAND',side,'bounds',co[v].min(0),co[v].max(0),'vertices',len(v),flush=True)
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/source_bind.blend'))
scene=bpy.context.scene
scene.render.engine='CYCLES'; scene.cycles.device='CPU'; scene.cycles.samples=12
scene.render.resolution_x=900; scene.render.resolution_y=900; scene.render.resolution_percentage=100
scene.world.color=(.15,.15,.15)
camdata=bpy.data.cameras.new('ReviewCamera'); camera=bpy.data.objects.new('ReviewCamera',camdata); scene.collection.objects.link(camera); scene.camera=camera
camdata.type='ORTHO'
lightdata=bpy.data.lights.new('Key','AREA'); lightdata.energy=450; lightdata.shape='DISK'; lightdata.size=4
light=bpy.data.objects.new('Key',lightdata); scene.collection.objects.link(light); light.location=(-2,-3,4)
light.rotation_euler=(Vector((0,0,1))-light.location).to_track_quat('-Z','Y').to_euler()
for name,center,pos,scale in [('source_front',(0,0,1),(0,-5,1.2),2.4),('source_hand',(0.32,-.18,.53),(.55,-2,.6),.4)]:
    camera.location=pos; camera.rotation_euler=(Vector(center)-camera.location).to_track_quat('-Z','Y').to_euler(); camdata.ortho_scale=scale
    scene.render.filepath=str(p/'review'/f'{name}.png')
    bpy.ops.render.render(write_still=True)
print('INSPECTION_DONE',flush=True)
# Blender's PulseAudio shutdown blocks in this sandbox after successful background work.
sys.stdout.flush(); sys.stderr.flush(); os._exit(0)
