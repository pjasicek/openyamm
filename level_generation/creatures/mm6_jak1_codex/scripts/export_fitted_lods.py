"""Fit colour LODs to measured switch-size silhouettes, then retain one runtime rig."""
import bpy,bmesh,json,sys,copy,struct,subprocess,math,numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));sys.path.insert(0,str(P.parents[2]/'tools'))
sys.dont_write_bytecode=True
import reduction_rebake as red
from build_actor_lods import read_glb,write_glb,accessor_bytes,append_accessor,merge_shadow
W=P/'work/round2/reduction';R=P/'review/round2/reduction'
selected=json.loads((R/'selection.json').read_text());source=P/selected['blend'];maps=P/selected['maps']
chosen=json.loads((R/'lod_selection.json').read_text())
# Geometry-only exports are merged into the canonical LOD0 without resampling any animation.
before,original=read_glb(P/'export/mm6_jak1_runtime_lod0.glb');document=copy.deepcopy(before);binary=bytearray(original)
node=next(n for n in before['nodes']if n.get('name')=='Jackalman');mi=node['mesh'];joints=[before['nodes'][i]['name']for i in before['skins'][node['skin']]['joints']]
bind=list(struct.iter_unpack('<16f',accessor_bytes(before,original,before['skins'][node['skin']]['inverseBindMatrices'])));material_indices={m['name']:i for i,m in enumerate(before['materials'])};lods=[]
for row in chosen:
 level=row['level'];bpy.ops.wm.open_mainfile(filepath=str(P/row['blend']));body=bpy.data.objects['Jackalman'];rig=bpy.data.objects['Rig'];red.rest(rig);bpy.ops.object.select_all(action='DESELECT');body.select_set(True);rig.select_set(True);bpy.context.view_layer.objects.active=rig
 path=W/f'lod{level}.geometry.glb';bpy.ops.export_scene.gltf(filepath=str(path),use_selection=True,export_format='GLB',export_animations=False,export_skins=True,export_all_influences=True,export_attributes=False)
 d,b=read_glb(path);n=next(n for n in d['nodes']if n.get('name')=='Jackalman');skin=d['skins'][n['skin']];remap=[joints.index(d['nodes'][i]['name'])for i in skin['joints']];bm=list(struct.iter_unpack('<16f',accessor_bytes(d,b,skin['inverseBindMatrices'])))
 assert all(abs(x-y)<1e-4 for j,m in zip(remap,bm)for x,y in zip(bind[j],m))
 mesh={'name':f'Jackalman_LOD{level}','primitives':[]}
 for primitive in d['meshes'][n['mesh']]['primitives']:
  attrs={}
  for semantic,index in primitive['attributes'].items():
   a=d['accessors'][index];packed=accessor_bytes(d,b,index)
   if semantic.startswith('JOINTS_'):
    code={5121:'B',5123:'H'}[a['componentType']];values=[remap[v[0]]for v in struct.iter_unpack('<'+code,packed)];packed=struct.pack('<'+code*len(values),*values)
   attrs[semantic]=append_accessor(document,binary,a,packed)
  i=primitive['indices'];mesh['primitives'].append({'attributes':attrs,'indices':append_accessor(document,binary,d['accessors'][i],accessor_bytes(d,b,i)),'material':material_indices[d['materials'][primitive['material']]['name']]})
 lods.append(len(document['meshes']));document['meshes'].append(mesh)
shadows=[]
for index in [mi]+lods:
 shadow=merge_shadow(document,binary,document['meshes'][index]);shadows.append(len(document['meshes']));document['meshes'].append(shadow)
document['meshes'][mi].setdefault('extras',{}).update(openyamm_lods=lods,openyamm_shadow_lods=shadows)
counts=[sum(document['accessors'][p['indices']]['count']//3 for p in document['meshes'][i]['primitives'])for i in [mi]+lods]
assert all(a>b for a,b in zip(counts,counts[1:]))
write_glb(P/'export/mm6_jak1_lods.glb',document,binary)
(P/'export/lods.json').write_text(json.dumps({'triangles':counts,'colour_meshes':[mi]+lods,'shadow_meshes':shadows,'source':'export/mm6_jak1_runtime_lod0.glb','rig_clips_retained_bytewise':True},indent=2))
print('FITTED LODS',counts,flush=True)
