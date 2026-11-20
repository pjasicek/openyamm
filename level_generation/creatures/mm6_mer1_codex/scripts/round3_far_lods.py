import bpy,bmesh,sys,json
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import reduction_common as C
selection=json.loads((P/'review/reduction/selection.json').read_text());entries=[selection['body'][0]]
def isolate(obj,keep):
 me=obj.data;bm=bmesh.new();bm.from_mesh(me);bmesh.ops.delete(bm,geom=[f for f in bm.faces if f.material_index not in keep],context='FACES');bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context='VERTS');bm.to_mesh(me);bm.free()
 mats=list(me.materials);indices=[f.material_index for f in me.polygons];me.materials.clear()
 for i in keep:me.materials.append(mats[i])
 for f,i in zip(me.polygons,indices):f.material_index=keep.index(i)
for level,targets in [(1,[1400,700,300]),(2,[1080,460,190]),(3,[400,165,120])]:
 bpy.ops.wm.open_mainfile(filepath=str(P/'work/round3/body_lod0.blend'));C.reset();original=bpy.data.objects['Body'];parts=[]
 for mi,target in enumerate(targets):
  ob=original.copy();ob.data=original.data.copy();bpy.context.scene.collection.objects.link(ob);isolate(ob,[mi]);group=ob.vertex_groups['_reduction_protect']
  for v in ob.data.vertices:
   w=next((g.weight for g in v.groups if g.group==group.index),0)
   if w:group.add([v.index],min(w,.65),'REPLACE')
  C.reduce(ob,target/C.triangles(ob));parts.append(ob)
 bpy.data.objects.remove(original,do_unlink=True)
 for ob in bpy.data.objects:ob.select_set(ob in parts)
 bpy.context.view_layer.objects.active=parts[0];bpy.ops.object.join();o=parts[0];o.name='Body';C.reset();bpy.ops.file.pack_all();dest=P/f'work/round3/body_lod{level}.blend';bpy.ops.wm.save_as_mainfile(filepath=str(dest));entries.append({'blend':str(dest.relative_to(P)),'textures':'work/round3/shared_textures','triangles':C.triangles(o)})

selection['body']=entries;(P/'review/reduction/selection.json').write_text(json.dumps(selection,indent=2));f=P/'review/round3/reduction.json';d=json.loads(f.read_text());d['body']=entries;f.write_text(json.dumps(d,indent=2));print(entries,flush=True)
assert all(x['triangles']<=cap for x,cap in zip(entries[1:],[2400,1730,685]))
