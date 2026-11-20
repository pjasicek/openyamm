from pathlib import Path
import bpy,bmesh,sys,json
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p.parents[2]/'tools'));from build_actor_lods import weld_skin_seams
bpy.ops.import_scene.gltf(filepath=str(p/'export/mm8_m540_runtime_lod0.glb'));ob=bpy.data.objects['OgreMage'];bm=bmesh.new();bm.from_mesh(ob.data);bmesh.ops.delete(bm,geom=[f for f in bm.faces if f.material_index!=1],context='FACES');bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context='VERTS')
def info(label):print(label,len(bm.verts),len(bm.edges),len(bm.faces),'nonmanifold',sum(not e.is_manifold for e in bm.edges),flush=True)
info('BEFORE');weld_skin_seams(bm);info('STANDARD');bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-5);info('POSITION_WELD');bm.verts.ensure_lookup_table();bm.verts.index_update();seen=set();dup=[]
for f in bm.faces:
 key=tuple(sorted(v.index for v in f.verts))
 if key in seen:dup.append(f)
 seen.add(key)
print('DUPLICATES',len(dup),flush=True)
if dup:bmesh.ops.delete(bm,geom=dup,context='FACES_ONLY')
info('DEDUP');bm.to_mesh(ob.data);bm.free()
for o in bpy.context.view_layer.objects:o.select_set(o==ob)
bpy.context.view_layer.objects.active=ob
for ratio in [.5,.25,.125]:
 cp=ob.copy();cp.data=ob.data.copy();bpy.context.collection.objects.link(cp);bpy.context.view_layer.objects.active=cp;m=cp.modifiers.new('probe','DECIMATE');m.ratio=ratio;m.use_collapse_triangulate=True;bpy.ops.object.modifier_apply(modifier=m.name);print('DECIMATE',ratio,len(cp.data.polygons),flush=True)
