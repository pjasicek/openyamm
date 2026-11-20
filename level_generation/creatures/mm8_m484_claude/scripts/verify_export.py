"""Compare deformed surfaces after an isolated reimport of the actual portable GLB."""
import bpy,json
import numpy as np
from pathlib import Path
from mathutils.kdtree import KDTree
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'delivery/mm8_minotaur.blend'))
sc=bpy.context.scene;r=bpy.data.objects['Rig'];b=bpy.data.objects['M484'];samples={};report={};assert set(bpy.data.actions.keys())=={'Standing','Walking','Running','Attack','AttackOneHand','Cast','Hit','Death','Dead','Fidget'}
def coords(obj):
 e=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());me=e.to_mesh();a=np.array([tuple(e.matrix_world@v.co) for v in me.vertices]);e.to_mesh_clear();return a
def frame(f):sc.frame_set(int(f),subframe=float(f-int(f)))
for act in bpy.data.actions:
 r.animation_data.action=act;r.animation_data.action_slot=act.slots[0]
 frames=np.linspace(*act.frame_range,17)
 if act.name in ('Attack','AttackOneHand','Cast','Death'):frames=np.arange(act.frame_range[0],act.frame_range[1]+.1,1)
 for f in frames:
  frame(f);samples[(act.name,float(f))]=coords(b)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
for a in list(bpy.data.actions):bpy.data.actions.remove(a)
sc.render.fps=60;bpy.ops.import_scene.gltf(filepath=str(P/'export/mm8_m484_lod0.glb'))
r=next(o for o in sc.objects if o.type=='ARMATURE')
for track in r.animation_data.nla_tracks:track.mute=True
meshes=[o for o in sc.objects if o.type=='MESH' and any(m.type=='ARMATURE' for m in o.modifiers)];assert len(meshes)==1
for (name,f),source in samples.items():
 act=next(a for a in bpy.data.actions if a.name==name or a.name.startswith(name+'_'))
 r.animation_data.action=act;r.animation_data.action_slot=act.slots[0];frame(f)
 target=np.concatenate([coords(o) for o in meshes]);tree=KDTree(len(source))
 for i,co in enumerate(source):tree.insert(co,i)
 tree.balance();dist=np.array([tree.find(co)[2] for co in target]);record=report.setdefault(name,{'samples':0,'max_surface_error_mm':0})
 record['samples']+=1;record['max_surface_error_mm']=max(record['max_surface_error_mm'],float(dist.max()*1000))
 if dist.max()>=.001:print('PARITY_FAILURE',name,f,'SOURCE',source.min(0),source.max(0),'TARGET',target.min(0),target.max(0),'WORST',target[int(dist.argmax())], 'SLOT',r.animation_data.action_slot.identifier)
 assert dist.max()<.001,(name,f,float(dist.max()))
(P/'review/export_parity.json').write_text(json.dumps(report,indent=1));print('EXPORT_PARITY',report)
