"""Replace only measured geometry; retain accepted rig, clips, textures and actor data."""
import bpy,sys,json,copy,struct,subprocess
from pathlib import Path
sys.dont_write_bytecode=True
P=Path(__file__).resolve().parents[1];sys.path[:0]=[str(P/'scripts'),str(P.parents[2]/'tools')]
from build_actor_lods import read_glb,write_glb,accessor_bytes,append_accessor,merge_shadow
from round4_search import reset,cleanup,triangles
W=P/'work/round4';R=P/'review/round4'
selection=json.loads((R/'selection.json').read_text())
doc,payload=read_glb(P/'work/round4_before/export/mm6_dwa1_runtime_lod0.glb');binary=bytearray(payload)
node=next(n for n in doc['nodes']if n.get('name')=='Dwarf');assert node['mesh']==0
joints=[doc['nodes'][i]['name']for i in doc['skins'][node['skin']]['joints']]
binds=list(struct.iter_unpack('<16f',accessor_bytes(doc,binary,doc['skins'][node['skin']]['inverseBindMatrices'])))
materials={m['name'].split('.')[0]:i for i,m in enumerate(doc['materials'])}
meshes=[]
for level in range(4):
 bodypath=P/selection['body'][level]['blend'];axepath=P/selection['axe'][level]['blend']
 bpy.ops.wm.open_mainfile(filepath=str(bodypath));cleanup();reset();rig=bpy.data.objects['Rig']
 bpy.data.objects.remove(bpy.data.objects['Axe'],do_unlink=True)
 with bpy.data.libraries.load(str(axepath),link=False)as(src,dst):dst.objects=['Axe']
 axe=dst.objects[0];bpy.context.scene.collection.objects.link(axe);axe.name='Axe';axe.parent=rig
 for mod in axe.modifiers:
  if mod.type=='ARMATURE':mod.object=rig
 body=bpy.data.objects['Body']
 for ob in [body,axe]:
  g=ob.vertex_groups.get('_reduction_protect')
  if g:ob.vertex_groups.remove(g)
 for ob in list(bpy.data.objects):
  if ob.type=='ARMATURE'and ob!=rig:bpy.data.objects.remove(ob,do_unlink=True)
 reset();bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(W/f'selected_lod{level}.blend'))
 bpy.ops.object.select_all(action='DESELECT')
 for ob in [body,axe,rig]:ob.select_set(True)
 bpy.context.view_layer.objects.active=body
 geo=W/f'selected_lod{level}.geometry.glb'
 bpy.ops.export_scene.gltf(filepath=str(geo),use_selection=True,export_format='GLB',export_animations=False,export_skins=True,export_all_influences=True)
 source,data=read_glb(geo);mesh={'name':'Body'if level==0 else f'Dwarf_LOD{level}','primitives':[]}
 for n in source['nodes']:
  if 'mesh'not in n:continue
  skin=source['skins'][n['skin']];remap=[joints.index(source['nodes'][i]['name'])for i in skin['joints']]
  matrices=list(struct.iter_unpack('<16f',accessor_bytes(source,data,skin['inverseBindMatrices'])))
  assert max(abs(a-b)for j,m in zip(remap,matrices)for a,b in zip(binds[j],m))<1e-4
  for key,default in [('translation',[0,0,0]),('rotation',[0,0,0,1]),('scale',[1,1,1])]:
   assert max(abs(a-b)for a,b in zip(node.get(key,default),n.get(key,default)))<1e-4,(level,n,key)
  for p in source['meshes'][n['mesh']]['primitives']:
   attrs={}
   for semantic,index in p['attributes'].items():
    accessor=source['accessors'][index];packed=accessor_bytes(source,data,index)
    if semantic.startswith('JOINTS_'):
     code={5121:'B',5123:'H'}[accessor['componentType']];values=[remap[x[0]]for x in struct.iter_unpack('<'+code,packed)];packed=struct.pack('<'+code*len(values),*values)
    attrs[semantic]=append_accessor(doc,binary,accessor,packed)
   idx=p['indices'];mesh['primitives'].append({'attributes':attrs,'indices':append_accessor(doc,binary,source['accessors'][idx],accessor_bytes(source,data,idx)),'material':materials[source['materials'][p['material']]['name'].split('.')[0]]})
 assert sum(doc['accessors'][p['indices']]['count']//3 for p in mesh['primitives'])==triangles(body)+triangles(axe)
 mesh['primitives'].sort(key=lambda p:p['material']);meshes.append(mesh)
doc['meshes']=meshes
single=copy.deepcopy(doc);single['meshes']=single['meshes'][:1]
write_glb(P/'export/mm6_dwa1_runtime_lod0.glb',single,binary)
for mesh in meshes[:4]:doc['meshes'].append(merge_shadow(doc,binary,mesh))
doc['meshes'][0]['extras']={'openyamm_lods':[1,2,3],'openyamm_shadow_lods':[4,5,6,7]}
write_glb(P/'export/mm6_dwa1_lods.glb',doc,binary)
subprocess.run(['/usr/bin/python3',str(P/'scripts/round4_compact.py')],check=True)
subprocess.run(['/usr/bin/python3',str(P/'scripts/package_lods.py')],check=True)
print('ROUND4 GEOMETRY PACKAGED',flush=True)

