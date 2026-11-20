"""Recover semantic sets by exact rest-position match, then probe the actual reimported export."""
import bpy,sys,runpy,json
from mathutils.kdtree import KDTree
from pathlib import Path
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/master_export.blend'));body=bpy.data.objects['Body'];kd=KDTree(len(body.data.vertices));pieces=[a.value for a in body.data.attributes['piece'].data]
for v in body.data.vertices:kd.insert(body.matrix_world@v.co,v.index)
kd.balance();bpy.ops.wm.read_factory_settings(use_empty=True);bpy.context.scene.render.fps=30;bpy.ops.import_scene.gltf(filepath=str(P/'export/mm6_lzd_raw.glb'));body=bpy.data.objects['Lizard'];body.name='Body';rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');rig.name='Rig';at=body.data.attributes.new('piece','INT','POINT');worst=0
for v in body.data.vertices:
 _,i,d=kd.find(body.matrix_world@v.co);at.data[v.index].value=pieces[i];worst=max(worst,d)
assert worst<1e-5,worst
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/export_reimport.blend'));print('ROUNDTRIP_REST_ERROR',worst)
clips=['Standing','Walking','Running','Attack','Cast','Hit','Death','Dead','Fidget']
for script,args in [('scan_deformation.py',[P/'work/export_reimport.blend']),('g6_contacts.py',[P/'work/export_reimport.blend',*clips]),('g6_head_clearance.py',[P/'work/export_reimport.blend',*clips]),('equipment_gate.py',[]),('round3_gates.py',[P/'work/export_reimport.blend']),('render_master.py',[])]:
 sys.argv=[script,'--',*map(str,args)];runpy.run_path(str(P/'scripts'/script),run_name='__main__')
