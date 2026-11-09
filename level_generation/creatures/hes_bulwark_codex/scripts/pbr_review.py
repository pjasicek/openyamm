"""Review final baked-viewer copies with normal maps, metalness and true factor emission in Eevee."""
import math
from pathlib import Path
import bpy
from mathutils import Vector
P=Path(__file__).resolve().parents[1]
for tier in 'abc':
 bpy.ops.wm.read_factory_settings(use_empty=True)
 scene=bpy.context.scene;scene.render.fps=30
 bpy.ops.import_scene.gltf(filepath=str(P/f'review/viewer/hes_bulwark_{tier}.glb'))
 rig=next(o for o in scene.objects if o.type=='ARMATURE')
 for t in rig.animation_data.nla_tracks:t.mute=True
 engines=[e.identifier for e in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items]
 scene.render.engine='BLENDER_EEVEE_NEXT' if 'BLENDER_EEVEE_NEXT' in engines else 'BLENDER_EEVEE'
 scene.render.resolution_x=scene.render.resolution_y=750;scene.render.resolution_percentage=100
 scene.world=bpy.data.worlds.new('World');scene.world.use_nodes=True
 scene.world.node_tree.nodes['Background'].inputs['Color'].default_value=(.12,.12,.12,1)
 scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.7
 for name,energy,angles in [('Key',2.5,(45,0,-25)),('Fill',1.1,(70,0,160))]:
  light=bpy.data.objects.new(name,bpy.data.lights.new(name,'SUN'));scene.collection.objects.link(light);light.data.energy=energy;light.rotation_euler=tuple(math.radians(v) for v in angles)
 cam=bpy.data.objects.new('Camera',bpy.data.cameras.new('Camera'));scene.collection.objects.link(cam);scene.camera=cam
 cam.data.type='ORTHO';cam.data.ortho_scale=9.0;target=Vector((0,1,1.8));cam.location=Vector((-8,-10,7));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()
 samples=[('Standing',0)]+([('Attack',5),('Dead',0),('Walking',9),('Running',7)] if tier=='b' else [])
 for clip,frame in samples:
  a=next(a for a in bpy.data.actions if a.name==clip or a.name.startswith(clip+'_'))
  rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];scene.frame_set(frame)
  scene.render.filepath=str(P/f'review/geometry/pbr_{tier}_{clip}.png');bpy.ops.render.render(write_still=True)
print('PBR REVIEW RENDERED',flush=True)
