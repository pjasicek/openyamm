"""Reimport the final GLB and compare deformed surfaces against the editable master in every clip."""
from pathlib import Path
import bpy,json,sys
import numpy as np
from mathutils import Vector
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'dragon_master.blend'))
rig=bpy.data.objects['Rig'];mesh=bpy.data.objects['Body'];sc=bpy.context.scene
sc.render.fps=24

def sample(obj):
 ev=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());data=ev.to_mesh()
 co=np.array([tuple(ev.matrix_world@v.co) for v in data.vertices]);ev.to_mesh_clear();return co
samples={};durations={}
for act in bpy.data.actions:
 rig.animation_data.action=act
 end=float(act.frame_range[1]);duration=end/24;durations[act.name]=duration
 for t in (0,duration*.25,duration*.5,duration*.75,duration):
  f=t*24;sc.frame_set(int(f),subframe=f-int(f));samples[act.name,t]=sample(mesh)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.context.scene.render.fps=24
bpy.ops.import_scene.gltf(filepath=str(P/'export/mm8_m492.glb'))
mesh=bpy.data.objects['Body'];rig=next(m.object for m in mesh.modifiers if m.type=='ARMATURE')
sc=bpy.context.scene
report={}
# Use Blender's KDTree so this check needs no extra Blender Python dependencies.
from mathutils.kdtree import KDTree
for (name,t),expected in samples.items():
 act=next(a for a in bpy.data.actions if a.name==name or a.name.endswith('_'+name) or a.name.endswith('|'+name))
 rig.animation_data.action=act
 if act.slots:rig.animation_data.action_slot=act.slots[0]
 f=t*24+float(act.frame_range[0]);sc.frame_set(int(f),subframe=f-int(f));actual=sample(mesh)
 tree=KDTree(len(expected))
 for i,co in enumerate(expected):tree.insert(co,i)
 tree.balance();error=max(tree.find(Vector(co))[2] for co in actual)
 report.setdefault(name,[]).append({'time':t,'max_surface_error_m':error,'minimum_z_m':float(actual[:,2].min())})
 assert error<(2e-5 if abs(t*24-round(t*24))<1e-6 else .001),(name,t,error)
(P/'work/export_parity.json').write_text(json.dumps(report,indent=2)+'\n')
print('EXPORT_PARITY',len(report),'clips',max(s['max_surface_error_m'] for v in report.values() for s in v))
