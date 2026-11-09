"""Validate the actual packaged lower LODs with base runtime animations at 48 Hz."""
import bpy,sys,json,struct,copy,subprocess,shutil
from pathlib import Path
from mathutils.kdtree import KDTree
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True;sys.path.insert(0,str(P/'scripts'))
from round3_candidate_gates import check
from rebake_render import render
def read(path):
 raw=path.read_bytes();n=struct.unpack_from('<I',raw,12)[0];return json.loads(raw[20:20+n]),raw[20+n:]
def write(path,d,tail):
 j=json.dumps(d,separators=(',',':')).encode();j+=b' '*((-len(j))%4);path.write_bytes(struct.pack('<4sII',b'glTF',2,20+len(j)+len(tail))+struct.pack('<I4s',len(j),b'JSON')+j+tail)
files=['review/deformation_scan.json','work/g6_contacts.json','review/head_clearance.json','review/equipment_gate.json','review/round3_motion_gate.json']
saved={f:(P/f).read_bytes()for f in files};selection=json.loads((P/'review/rebake/final_selection.json').read_text());counts=json.loads((P/'export/lods.json').read_text());levels=globals().get('LOD_LEVELS',[1,2,3]);allresults={}
for level in [i for i in [1,2,3]if i not in levels]:
 result=json.loads((P/f'review/rebake/runtime_lod{level}_gates.json').read_text());result['silhouette']=json.loads((P/f'review/rebake/runtime_lod{level}_metrics.json').read_text());assert result['passed']and result['silhouette']['actor']['passed'];allresults[str(level)]=result

try:
 for level in levels:
  tag=selection[str(level)]['tag'];bpy.ops.wm.open_mainfile(filepath=str(P/f'work/rebake/{tag}_baked.blend'));body=bpy.data.objects['Body'];kd=KDTree(len(body.data.vertices));pieces=[a.value for a in body.data.attributes['piece'].data]
  for v in body.data.vertices:kd.insert(body.matrix_world@v.co,v.index)
  kd.balance();d,tail=read(P/'export/mm6_lzd_lods.glb');node=next(n for n in d['nodes']if n.get('mesh')==0);node['mesh']=d['meshes'][0]['extras']['openyamm_lods'][level-1]
  glb=P/f'work/rebake/runtime_lod{level}.glb';write(glb,d,tail)
  bpy.ops.wm.read_factory_settings(use_empty=True);bpy.context.scene.render.fps=30;bpy.ops.import_scene.gltf(filepath=str(glb));body=bpy.data.objects['Lizard'];body.name='Body';rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');rig.name='Rig';at=body.data.attributes.new('piece','INT','POINT');worst=0
  for v in body.data.vertices:
   _,i,dist=kd.find(body.matrix_world@v.co);at.data[v.index].value=pieces[i];worst=max(worst,dist)
  assert worst<1e-5,worst
  path=P/f'work/rebake/runtime_lod{level}.blend';bpy.ops.wm.save_as_mainfile(filepath=str(path));result=check(path);result['rest_position_error_m']=worst;result['runtime_triangles']={'body':counts['body'][level],'bow':counts['bow'][level]};allresults[str(level)]=result
  (P/f'review/rebake/runtime_lod{level}_gates.json').write_text(json.dumps(result,indent=2))
  for f in files:shutil.copyfile(P/f,P/f"review/rebake/runtime_lod{level}_{Path(f).name}")
  print('RUNTIME_LOD_GATE',level,{k:v for k,v in result.items()if k!='motion'},result['motion']['issues'],flush=True)
  assert result['passed'],level
  render(path,f'runtime_lod{level}',level,parts=['actor'],samples=64 if level==3 else 16)
  metrics=json.loads(subprocess.check_output(['/usr/bin/python3',str(P/'scripts/rebake_measure.py'),f'runtime_lod{level}',str(level),'8','actor','reference64'if level==3 else'reference_pbr'],text=True));result['silhouette']=metrics;(P/f'review/rebake/runtime_lod{level}_metrics.json').write_text(json.dumps(metrics,indent=2));assert metrics['actor']['passed'],metrics
finally:
 for f,data in saved.items():(P/f).write_bytes(data)
(P/'review/rebake/runtime_lod_validation.json').write_text(json.dumps(allresults,indent=2))
selected=json.loads((P/'review/reduction/selected.json').read_text())
for part in ['body','bow']:
 for level in range(4):
  entry=selected[part][str(level)];entry.setdefault('authoring_triangles',entry['triangles']);entry['triangles']=counts[part][level]
(P/'review/reduction/selected.json').write_text(json.dumps(selected,indent=2))
print('RUNTIME_LODS_PASS',flush=True)
