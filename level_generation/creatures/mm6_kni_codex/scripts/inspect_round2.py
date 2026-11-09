import bpy,json,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1]
for f in ['work/textured_master.blend','work/body_gate_master.blend']:
 bpy.ops.wm.open_mainfile(filepath=str(P/f));body=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];print('INSPECT',f,len(body.data.vertices),len(body.data.polygons),len(rig.data.bones),list(body.data.attributes.keys()),flush=True)
 if f=='work/body_gate_master.blend':
  pv=np.zeros(len(body.data.vertices),np.int32);body.data.attributes['piece'].data.foreach_get('value',pv);np.savez(P/'work/round2/pieces.npz',co=np.array([tuple(v.co)for v in body.data.vertices]),piece=pv);print('PIECES',np.unique(pv,return_counts=True),flush=True)
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(P/'work/round2/baseline_mm6_kni.glb'));print('RUNTIME',[(o.name,o.type,len(o.data.vertices)if o.type=='MESH'else 0)for o in bpy.data.objects],flush=True)
m=bpy.data.objects['KnightPlate'].modifiers.new('Probe','DECIMATE');print('GROUPFACTOR',m.bl_rna.properties['vertex_group_factor'].hard_min,m.bl_rna.properties['vertex_group_factor'].hard_max,flush=True)
