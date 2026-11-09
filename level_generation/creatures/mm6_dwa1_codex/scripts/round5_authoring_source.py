"""Reduce the connected authoring topology, retaining the accepted runtime weights and rig."""
import bpy,bmesh,sys,json
from pathlib import Path
from mathutils.kdtree import KDTree
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True;sys.path.insert(0,str(P/'scripts'));import round4_search as S
bpy.ops.wm.open_mainfile(filepath=str(P/'work/round4_before/work/export_reimport.blend'));S.reset();rig=bpy.data.objects['Rig'];refs={}
for name in ['Body','Axe']:
 ob=bpy.data.objects[name];kd=KDTree(len(ob.data.vertices));weights={};names=[g.name for g in ob.vertex_groups]
 for v in ob.data.vertices:kd.insert(ob.matrix_world@v.co,v.index);weights[v.index]={names[g.group]:g.weight for g in v.groups}
 kd.balance();refs[name]=(kd,weights,names,[m for m in ob.data.materials])
with bpy.data.libraries.load(str(P/'work/round4_before/work/runtime_master.blend'),link=False)as(src,dst):
 print('AUTHOR_OBJECTS',src.objects,flush=True);dst.objects=['Dwarf']
source=dst.objects[0];assert source is not None;group=source.vertex_groups['Axe'].index;axeids={v.index for v in source.data.vertices if any(g.group==group and g.weight>.99 for g in v.groups)};assert axeids
receipt={}
for name,removeaxe in [('Body',True),('Axe',False)]:
 ob=bpy.data.objects[name];me=source.data.copy();me.transform(source.matrix_world);bm=bmesh.new();bm.from_mesh(me);bm.verts.ensure_lookup_table();bmesh.ops.delete(bm,geom=[v for v in bm.verts if (v.index in axeids)==removeaxe],context='VERTS');bm.to_mesh(me);bm.free();ob.data=me
 kd,weights,names,mats=refs[name];indices=[f.material_index for f in me.polygons];me.materials.clear()
 for m in mats:me.materials.append(m)
 for f,i in zip(me.polygons,indices):f.material_index=i
 ob.vertex_groups.clear()
 for n in names:ob.vertex_groups.new(name=n)
 worst=0
 for v in me.vertices:
  _,idx,dist=kd.find(v.co);worst=max(worst,dist)
  for n,w in weights[idx].items():ob.vertex_groups[n].add([v.index],w,'REPLACE')
 assert worst<1e-5,(name,worst);me.normals_split_custom_set([(0.,0.,0.)]*len(me.loops));receipt[name]={'triangles':S.triangles(ob),'vertices':len(me.vertices),'accepted_position_max_distance_m':worst};print('AUTHORING_SOURCE',name,receipt[name],flush=True)
bpy.data.objects.remove(source,do_unlink=True)
for ob in list(bpy.data.objects):
 if ob.type=='ARMATURE'and ob!=rig:bpy.data.objects.remove(ob,do_unlink=True)
S.cleanup();S.reset();bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/round5/authoring_source.blend'));(P/'review/round5/source_topology.json').write_text(json.dumps(receipt,indent=2)+'\n')
